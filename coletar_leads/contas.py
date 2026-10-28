"""Contas (empresas clientes), banco da plataforma e migração dos dados antigos.

dados/plataforma.db guarda o que é da plataforma: contas, usuários e sessões de login.
Cada conta tem a própria pasta dados/contas/<id>/ (ver comum.py) com o crm.db dela, os leads e o WhatsApp.
"""
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime

import planos
from comum import RAIZ, pasta

STATUS = ("pendente", "ativa", "bloqueada")


class ErroConta(Exception):
    def __init__(self, msg, codigo=400):
        super().__init__(msg)
        self.codigo = codigo


def _agora():
    return datetime.now().isoformat(timespec="seconds")


def con():
    """Conexão com o banco da plataforma (cria as tabelas na primeira vez)."""
    RAIZ.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(RAIZ / "plataforma.db", timeout=10)
    c.execute("""CREATE TABLE IF NOT EXISTS contas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, plano TEXT NOT NULL, status TEXT NOT NULL,
        criado TEXT NOT NULL, dono_id INTEGER)""")
    # senha_hash é PBKDF2 (nunca a senha). papel: 'admin' (plataforma) ou 'usuario'. papel_conta: 'dono' ou 'membro'.
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE, senha_hash TEXT NOT NULL,
        papel TEXT NOT NULL DEFAULT 'usuario', status TEXT NOT NULL DEFAULT 'ativo', criado TEXT NOT NULL,
        ultimo_login TEXT NOT NULL DEFAULT '', trocar_senha INTEGER NOT NULL DEFAULT 0,
        conta_id INTEGER, papel_conta TEXT NOT NULL DEFAULT 'membro')""")
    c.execute("""CREATE TABLE IF NOT EXISTS sessoes (
        token_hash TEXT PRIMARY KEY, usuario_id INTEGER NOT NULL, criado TEXT NOT NULL, expira TEXT NOT NULL)""")
    return c


def _dict(row):
    return {"id": row[0], "nome": row[1], "plano": row[2], "status": row[3], "criado": row[4], "dono_id": row[5]}


def obter(conta_id):
    with closing(con()) as c:
        row = c.execute("SELECT id,nome,plano,status,criado,dono_id FROM contas WHERE id=?", (conta_id,)).fetchone()
    return _dict(row) if row else None


def criar(nome, plano=planos.PADRAO, status="pendente"):
    nome = (nome or "").strip()
    if not 2 <= len(nome) <= 80:
        raise ErroConta("Informe o nome da empresa (de 2 a 80 letras).")
    if not planos.valido(plano):
        raise ErroConta("Plano inválido.")
    with closing(con()) as c:
        cur = c.execute("INSERT INTO contas(nome,plano,status,criado) VALUES(?,?,?,?)", (nome, plano, status, _agora()))
        c.commit()
        conta_id = cur.lastrowid
    pasta(conta_id)
    return obter(conta_id)


def ativas():
    with closing(con()) as c:
        return [r[0] for r in c.execute("SELECT id FROM contas WHERE status='ativa'")]


def _leads_na_pasta(conta_id):
    """Quantos leads a conta já coletou (linhas dos CSVs, sem o cabeçalho)."""
    total = 0
    for arq in pasta(conta_id).glob("leads_detalhados_*.csv"):
        with open(arq, encoding="utf-8-sig") as f:
            total += max(0, sum(1 for _ in f) - 1)
    return total


def listar():
    """Todas as contas com dono, uso de usuários e leads (para o painel Clientes)."""
    with closing(con()) as c:
        rows = c.execute("""SELECT k.id,k.nome,k.plano,k.status,k.criado,k.dono_id,u.nome,u.email,
            (SELECT COUNT(*) FROM usuarios x WHERE x.conta_id=k.id)
            FROM contas k LEFT JOIN usuarios u ON u.id=k.dono_id
            ORDER BY k.status='pendente' DESC, k.nome COLLATE NOCASE""").fetchall()
    out = []
    for r in rows:
        d = _dict(r[:6])
        p = planos.PLANOS.get(d["plano"], {})
        d.update(dono_nome=r[6] or "", dono_email=r[7] or "", usuarios=r[8], limite_usuarios=p.get("usuarios", 0),
                 plano_nome=p.get("nome", d["plano"]), leads=_leads_na_pasta(d["id"]))
        out.append(d)
    return out


def administrar(conta_id, acao, plano=None, conta_do_admin=None, nome=None):
    """Ações do administrador da plataforma sobre uma conta."""
    if acao not in ("aprovar", "bloquear", "desbloquear", "plano", "renomear", "excluir"):
        raise ErroConta("Ação inválida.")
    conta = obter(conta_id)
    if not conta:
        raise ErroConta("Conta não encontrada.", 404)
    if conta_id == conta_do_admin and acao in ("bloquear", "excluir"):
        raise ErroConta("Esta é a sua própria conta.", 409)
    with closing(con()) as c:
        if acao in ("aprovar", "desbloquear"):
            c.execute("UPDATE contas SET status='ativa' WHERE id=?", (conta_id,))
        elif acao == "bloquear":
            c.execute("UPDATE contas SET status='bloqueada' WHERE id=?", (conta_id,))
            c.execute("DELETE FROM sessoes WHERE usuario_id IN (SELECT id FROM usuarios WHERE conta_id=?)", (conta_id,))
        elif acao == "plano":
            if not planos.valido(plano):
                raise ErroConta("Plano inválido.")
            c.execute("UPDATE contas SET plano=? WHERE id=?", (plano, conta_id))
        elif acao == "renomear":
            nome = (nome or "").strip()
            if not 2 <= len(nome) <= 80:
                raise ErroConta("Informe o nome da empresa (de 2 a 80 letras).")
            c.execute("UPDATE contas SET nome=? WHERE id=?", (nome, conta_id))
        elif acao == "excluir":
            if c.execute("SELECT 1 FROM usuarios WHERE conta_id=? AND papel='admin'", (conta_id,)).fetchone():
                raise ErroConta("Esta conta tem um administrador da plataforma. Tire o admin dele antes.", 409)
            c.execute("DELETE FROM sessoes WHERE usuario_id IN (SELECT id FROM usuarios WHERE conta_id=?)", (conta_id,))
            c.execute("DELETE FROM usuarios WHERE conta_id=?", (conta_id,))
            c.execute("DELETE FROM contas WHERE id=?", (conta_id,))
        c.commit()
    if acao == "excluir":
        # os dados não são apagados: a pasta vai para dados/contas_excluidas/ (dá para recuperar)
        origem = RAIZ / "contas" / str(conta_id)
        if origem.exists():
            destino = RAIZ / "contas_excluidas" / f"{conta_id}_{datetime.now():%Y%m%d_%H%M%S}"
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(origem), str(destino))
        return {}
    return {"conta": obter(conta_id)}


# ---------- migração: dados de antes das contas viram a conta 1 ----------
ANTIGOS = ("crm.db", "wa_perfil")
PADROES_ANTIGOS = ("dados_maps_*.json", "leads_detalhados_*.json", "leads_detalhados_*.csv", "meta_*.json")


def migrar(log=print):
    """Roda no início do servidor. Se ainda não existe dados/plataforma.db e há dados soltos em dados/
    (versão de antes das contas), cria a conta 1, move tudo para dados/contas/1/ e leva os usuários
    do crm.db antigo para a plataforma. Faz backup do crm.db antes. Não faz nada nas próximas vezes."""
    if (RAIZ / "plataforma.db").exists():
        return False
    soltos = [RAIZ / n for n in ANTIGOS if (RAIZ / n).exists()]
    for padrao in PADROES_ANTIGOS:
        soltos += list(RAIZ.glob(padrao))
    if not soltos:
        con().close()  # instalação nova: só cria o banco da plataforma
        return False

    log(f"Migrando os dados atuais para a conta 1 ({len(soltos)} itens)...")
    antigo = RAIZ / "crm.db"
    usuarios = []
    if antigo.exists():
        backup = RAIZ / "backup" / f"crm_antes_das_contas_{datetime.now():%Y%m%d_%H%M%S}.db"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(antigo, backup)
        log(f"Backup do banco antigo em {backup}")
        with closing(sqlite3.connect(antigo)) as a:
            tem = {r[0] for r in a.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "usuarios" in tem:
                cols = [r[1] for r in a.execute("PRAGMA table_info(usuarios)")]
                sel = "id,nome,email,senha_hash,papel,status,criado,ultimo_login," + ("trocar_senha" if "trocar_senha" in cols else "0")
                usuarios = a.execute(f"SELECT {sel} FROM usuarios ORDER BY id").fetchall()

    destino = RAIZ / "contas" / "1"
    destino.mkdir(parents=True, exist_ok=True)
    for item in soltos:
        try:
            shutil.move(str(item), str(destino / item.name))
        except PermissionError:
            raise SystemExit(f"Não consegui mover {item.name}: ele está aberto. Feche a janela do WhatsApp e o servidor antigo e rode de novo.")

    with closing(sqlite3.connect(destino / "crm.db")) as a:  # login agora fica só na plataforma
        a.execute("DROP TABLE IF EXISTS usuarios")
        a.execute("DROP TABLE IF EXISTS sessoes")
        a.commit()

    with closing(con()) as c:
        admin = next((u for u in usuarios if u[4] == "admin"), None)
        nome = f"{admin[1]}" if admin else "Minha empresa"
        c.execute("INSERT INTO contas(id,nome,plano,status,criado,dono_id) VALUES(1,?,?, 'ativa', ?, ?)",
                  (nome, "escala", _agora(), admin[0] if admin else None))
        for u in usuarios:
            c.execute("""INSERT INTO usuarios(id,nome,email,senha_hash,papel,status,criado,ultimo_login,trocar_senha,conta_id,papel_conta)
                         VALUES(?,?,?,?,?,?,?,?,?,1,?)""", (*u, "dono" if admin and u[0] == admin[0] else "membro"))
        c.commit()
    log(f"Conta 1 criada ({nome}, plano Escala) com {len(usuarios)} usuário(s).")
    return True
