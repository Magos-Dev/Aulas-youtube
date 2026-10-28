"""CRM em SQLite, um banco por conta (dados/contas/<id>/crm.db): status, anotações, histórico, cores,
números verificados, fila de envios, respostas e configurações (fila, etapas, chaves do Gemini e do Pexels)."""
import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta

from comum import pasta


def _banco():
    return pasta() / "crm.db"


FIXOS = ["enviado", "respondeu", "reuniao", "fechado", "sem"]  # etapas que o sistema usa; não podem ser excluídas
STATUS = {"novo", *FIXOS}
ID_CUSTOM = re.compile(r"^c_[a-z0-9]{3,16}$")  # etapas criadas pelo usuário
COR = re.compile(r"^#[0-9a-fA-F]{6}$")


def status_valido(s):
    return isinstance(s, str) and (s in STATUS or bool(ID_CUSTOM.match(s)))


def _con():
    con = sqlite3.connect(_banco(), timeout=10)
    con.execute("""CREATE TABLE IF NOT EXISTS crm (
        link TEXT PRIMARY KEY, status TEXT NOT NULL, notas TEXT NOT NULL DEFAULT '',
        proximo TEXT NOT NULL DEFAULT '', hist TEXT NOT NULL DEFAULT '[]', atualizado TEXT NOT NULL)""")
    con.execute("CREATE TABLE IF NOT EXISTS config (chave TEXT PRIMARY KEY, valor TEXT NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS wa_numeros (numero TEXT PRIMARY KEY, tem INTEGER NOT NULL, verificado TEXT NOT NULL)")
    con.execute("""CREATE TABLE IF NOT EXISTS fila (
        id INTEGER PRIMARY KEY AUTOINCREMENT, link TEXT NOT NULL, nome TEXT NOT NULL, numero TEXT NOT NULL,
        texto TEXT NOT NULL, etapa TEXT NOT NULL, produto TEXT NOT NULL DEFAULT '', tag TEXT NOT NULL DEFAULT '',
        estado TEXT NOT NULL, criado TEXT NOT NULL, enviado_em TEXT NOT NULL DEFAULT '', erro TEXT NOT NULL DEFAULT '')""")
    con.execute("CREATE TABLE IF NOT EXISTS respostas (chave TEXT PRIMARY KEY, visto TEXT NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS optout (numero TEXT PRIMARY KEY, motivo TEXT NOT NULL, quando TEXT NOT NULL)")
    if "seg" not in [c[1] for c in con.execute("PRAGMA table_info(fila)")]:
        con.execute("ALTER TABLE fila ADD COLUMN seg TEXT NOT NULL DEFAULT ''")  # follow-ups que acompanham a abertura (JSON)
    return con


def _agora():
    return datetime.now().isoformat(timespec="microseconds")


# ---------- CRM ----------
def ler():
    """Devolve {'crm': {link: {..., 'atu': versão}}, 'cores': {etapa: '#rrggbb'}} no formato da página."""
    with closing(_con()) as con:
        crm = {link: {"status": st, "notas": nt, "proximo": px, "hist": json.loads(h), "atu": at}
               for link, st, nt, px, h, at in con.execute("SELECT link,status,notas,proximo,hist,atualizado FROM crm")}
        row = con.execute("SELECT valor FROM config WHERE chave='cores'").fetchone()
        col = con.execute("SELECT valor FROM config WHERE chave='colunas'").fetchone()
    return {"crm": crm, "cores": json.loads(row[0]) if row else {}, "colunas": json.loads(col[0]) if col else []}


def _gravar(con, link, c):
    at = _agora()
    con.execute("""INSERT INTO crm(link,status,notas,proximo,hist,atualizado) VALUES(?,?,?,?,?,?)
        ON CONFLICT(link) DO UPDATE SET status=excluded.status, notas=excluded.notas,
        proximo=excluded.proximo, hist=excluded.hist, atualizado=excluded.atualizado""",
                (link, c["status"], c["notas"], c["proximo"], json.dumps(c["hist"], ensure_ascii=False), at))
    return at


def _linha(con, link):
    r = con.execute("SELECT status,notas,proximo,hist FROM crm WHERE link=?", (link,)).fetchone()
    if r:
        return {"status": r[0], "notas": r[1], "proximo": r[2], "hist": json.loads(r[3])}
    return {"status": "novo", "notas": "", "proximo": "", "hist": []}


def salvar_crm(crm):
    """Grava os leads recebidos com controle de versão otimista.

    Cada lead traz `atu` (a versão que a página viu). Se o servidor mudou o lead depois disso
    (ex.: chegou uma resposta), a gravação é recusada e o lead volta em `conflitos` para a página
    recarregar. Devolve {'salvos': n, 'atu': {link: versão}, 'conflitos': [link]}.
    """
    atu, conflitos, salvos = {}, [], 0
    with closing(_con()) as con, con:
        for link, c in crm.items():
            if not isinstance(c, dict) or not isinstance(link, str) or not status_valido(c.get("status")):
                continue
            novo = {"status": c["status"], "notas": str(c.get("notas", ""))[:5000],
                    "proximo": str(c.get("proximo", ""))[:10],
                    "hist": [h for h in c.get("hist", []) if isinstance(h, dict)][-200:]}
            link = link[:2000]
            row = con.execute("SELECT atualizado FROM crm WHERE link=?", (link,)).fetchone()
            if row:
                if c.get("atu") != row[0]:
                    conflitos.append(link)
                    atu[link] = row[0]
                    continue
                if _linha(con, link) == novo:
                    atu[link] = row[0]
                    continue
            atu[link] = _gravar(con, link, novo)
            salvos += 1
    return {"salvos": salvos, "atu": atu, "conflitos": conflitos}


def registrar_envio(link, etapa, produto, tag, texto, numero="", seg=None, nome=""):
    """Chamado pelo servidor após um envio automático: marca como enviado e agenda o follow-up."""
    with closing(_con()) as con, con:
        c = _linha(con, link)
        if c["status"] == "novo":
            c["status"] = "enviado"
        entrada = {"d": datetime.now().isoformat(timespec="seconds"), "etapa": etapa,
                   "produto": produto, "tag": tag, "txt": texto, "auto": True}
        if numero:
            entrada["numero"] = numero
        if nome:
            entrada["nome"] = nome
        if seg:
            entrada["seg"] = seg
        c["hist"].append(entrada)
        dias = 3 if len(c["hist"]) > 1 else 2
        c["proximo"] = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")
        _gravar(con, link, c)


def registrar_resposta(link, texto):
    """Chamado ao detectar resposta do cliente: move para 'respondeu' e guarda o texto no histórico."""
    with closing(_con()) as con, con:
        c = _linha(con, link)
        if c["status"] in ("novo", "enviado"):
            c["status"] = "respondeu"
        c["hist"].append({"d": datetime.now().isoformat(timespec="seconds"), "etapa": "Resposta do cliente",
                          "txt": texto, "auto": True})
        c["proximo"] = ""
        _gravar(con, link, c)


def registrar_optout(link, numero, texto):
    """Cliente pediu para parar: encerra o lead, cancela o que está na fila e bloqueia o número."""
    with closing(_con()) as con, con:
        c = _linha(con, link)
        c["status"], c["proximo"] = "sem", ""
        c["hist"].append({"d": datetime.now().isoformat(timespec="seconds"), "etapa": "Pediu para parar (opt-out)",
                          "txt": texto, "auto": True})
        _gravar(con, link, c)
        if numero:
            con.execute("INSERT OR REPLACE INTO optout(numero,motivo,quando) VALUES(?,?,?)",
                        (numero, texto[:200], datetime.now().isoformat(timespec="seconds")))
        con.execute("UPDATE fila SET estado='cancelada', erro='Cliente pediu para parar' "
                    "WHERE (link=? OR numero=?) AND estado IN ('pendente','aprovada')", (link, numero or "-"))


def encerrar_sem_resposta(link, dias):
    c_ = None
    with closing(_con()) as con, con:
        c_ = _linha(con, link)
        if c_["status"] != "enviado":
            return False
        c_["status"], c_["proximo"] = "sem", ""
        c_["hist"].append({"d": datetime.now().isoformat(timespec="seconds"),
                           "etapa": f"Encerrado: sem resposta em {dias} dias", "auto": True})
        _gravar(con, link, c_)
        con.execute("UPDATE fila SET estado='cancelada', erro='Lead encerrado' WHERE link=? AND estado IN ('pendente','aprovada')", (link,))
    return True


def optouts():
    with closing(_con()) as con:
        return [{"numero": n, "motivo": m, "quando": q} for n, m, q in con.execute("SELECT numero,motivo,quando FROM optout ORDER BY quando DESC")]


def esta_bloqueado(numero):
    with closing(_con()) as con:
        return con.execute("SELECT 1 FROM optout WHERE numero=?", (numero,)).fetchone() is not None


def reativar_numero(numero):
    with closing(_con()) as con, con:
        con.execute("DELETE FROM optout WHERE numero=?", (numero,))


def leads_enviados():
    """[(link, status, hist)] dos leads em 'enviado', para o agendador de follow-ups."""
    with closing(_con()) as con:
        return [(l, json.loads(h)) for l, h in con.execute("SELECT link,hist FROM crm WHERE status='enviado'")]


def status_do_lead(link):
    with closing(_con()) as con:
        r = con.execute("SELECT status FROM crm WHERE link=?", (link,)).fetchone()
    return r[0] if r else "novo"


# ---------- cores do Kanban ----------
def salvar_cores(cores):
    ok = {k: v for k, v in cores.items() if status_valido(k) and isinstance(v, str) and COR.match(v)}
    with closing(_con()) as con, con:
        con.execute("INSERT INTO config(chave,valor) VALUES('cores',?) ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
                    (json.dumps(ok),))
    return ok


# ---------- etapas (colunas) do Kanban ----------
def salvar_colunas(lista):
    """Guarda a ordem, nomes e cores das etapas. As etapas fixas que faltarem voltam ao final."""
    padrao = {"enviado": ("1º contato enviado", "Abertura enviada, aguardando resposta", "#3b82f6"),
              "respondeu": ("Respondeu", "Conversa em andamento", "#f59e0b"),
              "reuniao": ("Reunião marcada", "Apresentação ou proposta combinada", "#8b5cf6"),
              "fechado": ("Fechado", "Virou cliente", "#22c55e"),
              "sem": ("Sem interesse", "Não contatar de novo", "#ef4444")}
    limpa, vistos = [], set()
    for c in lista[:30]:
        if not isinstance(c, dict) or c.get("id") in vistos or c.get("id") == "novo" or not status_valido(c.get("id")):
            continue
        vistos.add(c["id"])
        limpa.append({"id": c["id"], "nome": str(c.get("nome") or c["id"])[:40], "desc": str(c.get("desc", ""))[:80],
                      "cor": c["cor"] if isinstance(c.get("cor"), str) and COR.match(c["cor"]) else "#64748b"})
    for k in FIXOS:
        if k not in vistos:
            limpa.append({"id": k, "nome": padrao[k][0], "desc": padrao[k][1], "cor": padrao[k][2]})
    with closing(_con()) as con, con:
        con.execute("INSERT INTO config(chave,valor) VALUES('colunas',?) ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
                    (json.dumps(limpa, ensure_ascii=False),))
    return limpa


# ---------- números verificados no WhatsApp ----------
def numeros_wa():
    """{numero: True/False} dos telefones já verificados no WhatsApp."""
    with closing(_con()) as con:
        return {n: bool(t) for n, t in con.execute("SELECT numero,tem FROM wa_numeros")}


def salvar_numero_wa(numero, tem):
    with closing(_con()) as con, con:
        con.execute("""INSERT INTO wa_numeros(numero,tem,verificado) VALUES(?,?,?)
            ON CONFLICT(numero) DO UPDATE SET tem=excluded.tem, verificado=excluded.verificado""",
                    (numero, int(bool(tem)), datetime.now().isoformat(timespec="seconds")))


# ---------- fila de envios ----------
CONFIG_FILA = {"limite_dia": 15, "intervalo_min": 90, "intervalo_max": 180,
               "hora_ini": "08:00", "hora_fim": "18:00", "ativo": False, "auto_aprovar": False,
               "followups_auto": False, "followup1_horas": 24, "followup2_dias": 3, "encerrar_dias": 7, "encerrar_auto": True}
HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def config_fila():
    with closing(_con()) as con:
        row = con.execute("SELECT valor FROM config WHERE chave='fila'").fetchone()
    return {**CONFIG_FILA, **(json.loads(row[0]) if row else {})}


def salvar_config_fila(d):
    cfg = config_fila()
    for k in ("limite_dia", "intervalo_min", "intervalo_max"):
        if k in d:
            cfg[k] = max(1, min(int(d[k]), 500 if k == "limite_dia" else 3600))
    for k, (lo, hi) in {"followup1_horas": (1, 720), "followup2_dias": (1, 90), "encerrar_dias": (1, 180)}.items():
        if k in d:
            cfg[k] = max(lo, min(int(d[k]), hi))
    for k in ("hora_ini", "hora_fim"):
        if k in d and HORA.match(str(d[k])):
            cfg[k] = d[k]
    for k in ("ativo", "auto_aprovar", "followups_auto", "encerrar_auto"):
        if k in d:
            cfg[k] = bool(d[k])
    if cfg["intervalo_max"] < cfg["intervalo_min"]:
        cfg["intervalo_max"] = cfg["intervalo_min"]
    with closing(_con()) as con, con:
        con.execute("INSERT INTO config(chave,valor) VALUES('fila',?) ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
                    (json.dumps(cfg),))
    return cfg


FILA_COLS = "id,link,nome,numero,texto,etapa,produto,tag,estado,criado,enviado_em,erro".split(",")


def fila_listar():
    with closing(_con()) as con:
        return [dict(zip(FILA_COLS, r)) for r in
                con.execute(f"SELECT {','.join(FILA_COLS)} FROM fila ORDER BY id DESC LIMIT 300")]


def enviados_hoje():
    hoje = datetime.now().strftime("%Y-%m-%d")
    with closing(_con()) as con:
        return con.execute("SELECT COUNT(*) FROM fila WHERE estado='enviada' AND enviado_em LIKE ?", (hoje + "%",)).fetchone()[0]


def fila_adicionar(itens):
    """Enfileira mensagens. Ignora duplicadas (mesmo número e etapa já na fila ou enviadas)."""
    estado = "aprovada" if config_fila()["auto_aprovar"] else "pendente"
    novos = 0
    with closing(_con()) as con, con:
        for it in itens:
            try:
                numero = re.sub(r"\D", "", str(it["numero"]))
                link, nome, texto, etapa = (str(it[k])[:4000] for k in ("link", "nome", "texto", "etapa"))
                seg = it.get("seguintes")
                seg = json.dumps([{k: str(x[k])[:4000] for k in ("etapa", "txt", "tag") if k in x} for x in seg[:3]],
                                 ensure_ascii=False) if isinstance(seg, list) else ''
            except (KeyError, TypeError):
                continue
            if not 10 <= len(numero) <= 15 or not (link and nome and texto and etapa):
                continue
            if con.execute("SELECT 1 FROM optout WHERE numero=?", (numero,)).fetchone():
                continue
            if con.execute("SELECT 1 FROM fila WHERE numero=? AND etapa=? AND estado NOT IN ('cancelada','erro','sem_whatsapp')",
                           (numero, etapa)).fetchone():
                continue
            con.execute("""INSERT INTO fila(link,nome,numero,texto,etapa,produto,tag,seg,estado,criado)
                VALUES(?,?,?,?,?,?,?,?,?,?)""", (link, nome, numero, texto, etapa, str(it.get("produto", ""))[:200],
                                                 str(it.get("tag", ""))[:200], seg, estado,
                                               datetime.now().isoformat(timespec="seconds")))
            novos += 1
    return novos


def fila_acao(acao, id_=None):
    with closing(_con()) as con, con:
        if acao == "aprovar_todas":
            con.execute("UPDATE fila SET estado='aprovada' WHERE estado='pendente'")
        elif acao == "aprovar":
            con.execute("UPDATE fila SET estado='aprovada' WHERE id=? AND estado='pendente'", (id_,))
        elif acao == "pausar":
            con.execute("UPDATE fila SET estado='pendente' WHERE id=? AND estado='aprovada'", (id_,))
        elif acao == "remover":
            con.execute("DELETE FROM fila WHERE id=? AND estado!='enviada'", (id_,))
        elif acao == "limpar":
            con.execute("DELETE FROM fila WHERE estado IN ('enviada','erro','sem_whatsapp','cancelada')")


def fila_proxima():
    with closing(_con()) as con:
        r = con.execute("SELECT id,link,nome,numero,texto,etapa,produto,tag,seg FROM fila WHERE estado='aprovada' ORDER BY id LIMIT 1").fetchone()
    return dict(zip("id link nome numero texto etapa produto tag seg".split(), r)) if r else None


def fila_marcar(id_, estado, erro=""):
    with closing(_con()) as con, con:
        con.execute("UPDATE fila SET estado=?, erro=?, enviado_em=? WHERE id=?",
                    (estado, erro[:300], datetime.now().isoformat(timespec="seconds") if estado == "enviada" else "", id_))


# ---------- respostas já tratadas ----------
def resposta_vista(chave):
    with closing(_con()) as con:
        return con.execute("SELECT 1 FROM respostas WHERE chave=?", (chave,)).fetchone() is not None


def marcar_resposta(chave):
    with closing(_con()) as con, con:
        con.execute("INSERT OR IGNORE INTO respostas(chave,visto) VALUES(?,?)", (chave, _agora()))
