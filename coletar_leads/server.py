"""Servidor local do painel: serve a página e roda coleta + detalhamento em segundo plano.

Uso: python server.py  (abre http://localhost:8765)
"""
import ipaddress
import json
import os
import random
import re
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import auth
import comum
import contas
import crm_db
import fila
import gemini
import mockups
import planos
import respostas
import whatsapp_web
from comum import Cancelado, chave, conta_atual, definir_conta, slug
from detalhar_leads import detalhar
from gerar_pagina import carregar_leads, renderizar
from pagina_login import HTML as PAGINA_LOGIN
from scraper_maps import coletar

HOST, PORTA = "127.0.0.1", int(os.environ.get("PAINEL_PORTA", 8765))
LOCK = threading.RLock()
# busca de leads e verificação de números: cada conta tem as suas (uma não vê nem trava a outra)
_POR_CONTA = {}


def _da_conta():
    c = conta_atual()
    with LOCK:
        if c not in _POR_CONTA:
            _POR_CONTA[c] = {
                "job": {"status": "idle", "etapa": "", "nicho": "", "nicho_id": "", "cidade": "", "atual": 0, "total": 0,
                        "nome": "", "erro": "", "log": [], "versao": 0},
                "ver": {"status": "idle", "atual": 0, "total": 0, "com": 0, "sem": 0, "erro": ""},
                "cancelar": threading.Event(), "cancelar_ver": threading.Event()}
        return _POR_CONTA[c]


def numeros_dos_leads():
    """Telefones únicos dos leads, no formato 55DDDNNNNNNNN(N)."""
    vistos = {}
    for l in carregar_leads():
        d = re.sub(r"\D", "", l.get("telefone", ""))
        if len(d) in (10, 11):
            vistos["55" + d] = True
    return list(vistos)


def verificar_lote(conta):
    definir_conta(conta)
    dc = _da_conta()
    ver, cancelar = dc["ver"], dc["cancelar_ver"]
    try:
        pendentes = [n for n in numeros_dos_leads() if n not in crm_db.numeros_wa()]
        with LOCK:
            ver.update(status="running", atual=0, total=len(pendentes), com=0, sem=0, erro="")
        for i, n in enumerate(pendentes, 1):
            if cancelar.is_set():
                break
            r = whatsapp_web.verificar(n)
            if not r.get("ok"):
                if r.get("erro") in ("desconectado",):
                    raise RuntimeError(r["detalhe"])
                continue  # timeout ou falha pontual: tenta de novo na próxima rodada
            with LOCK:
                ver["atual"] = i
                ver["com" if r["tem"] else "sem"] += 1
            time.sleep(random.uniform(3, 6))  # intervalo humano entre as conversas
        with LOCK:
            ver["status"] = "cancelled" if cancelar.is_set() else "done"
    except Exception as e:
        with LOCK:
            ver.update(status="error", erro=str(e) or e.__class__.__name__)


def atualizar(**kw):
    with LOCK:
        _da_conta()["job"].update(kw)


def log(msg):
    print(f"[conta {conta_atual()}] {msg}", flush=True)
    with LOCK:
        job = _da_conta()["job"]
        job["log"] = (job["log"] + [msg])[-40:]


def rodar(conta, nicho, cidade, limite, mostrar):
    definir_conta(conta)
    k = chave(nicho, cidade)
    cancelar = _da_conta()["cancelar"]
    try:
        atualizar(etapa="coletando", atual=0, total=0, nome="")
        coletar(nicho, cidade, log=log, headless=not mostrar, cancelado=cancelar.is_set)
        atualizar(etapa="detalhando")
        detalhar(k, limite=limite, log=log, headless=not mostrar, cancelado=cancelar.is_set,
                 progresso=lambda i, n, nome: atualizar(atual=i, total=n, nome=nome))
        with LOCK:
            job = _da_conta()["job"]
            job.update(status="done", etapa="", versao=job["versao"] + 1)
    except Cancelado:
        atualizar(status="cancelled", etapa="")
    except Exception as e:  # mostra o motivo na página
        log(f"Erro: {e}")
        atualizar(status="error", etapa="", erro=str(e) or e.__class__.__name__)


CABECALHOS_PROXY = ("X-Forwarded-For", "Cf-Connecting-Ip", "X-Real-Ip", "Forwarded")
# rotas que funcionam sem login; todo o resto exige sessão
PUBLICAS_GET = {"/login", "/api/auth/estado", "/api/auth/eu", "/api/planos"}
PUBLICAS_POST = {"/api/auth/login", "/api/auth/cadastro", "/api/auth/setup", "/api/auth/sair"}


class Handler(BaseHTTPRequestHandler):
    def responder(self, codigo, corpo, tipo="application/json; charset=utf-8", cabecalhos=()):
        dados = corpo if isinstance(corpo, bytes) else (
            corpo.encode("utf-8") if isinstance(corpo, str) else json.dumps(corpo, ensure_ascii=False).encode("utf-8"))
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "same-origin")
        for k, v in cabecalhos:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(dados)

    # ---- login ----
    def _rota(self):
        return self.path.split("?", 1)[0]

    def _token(self):
        c = SimpleCookie()
        try:
            c.load(self.headers.get("Cookie") or "")
        except Exception:
            return ""
        return c[auth.COOKIE].value if auth.COOKIE in c else ""

    def _local(self):
        """Pedido feito no próprio computador do servidor (não vale quando chega por túnel/proxy)."""
        if any(self.headers.get(h) for h in CABECALHOS_PROXY):
            return False
        try:
            return ipaddress.ip_address(self.client_address[0]).is_loopback
        except ValueError:
            return False

    def _ip(self):
        for h in ("Cf-Connecting-Ip", "X-Real-Ip"):
            if self.headers.get(h):
                return self.headers[h].strip()
        if self.headers.get("X-Forwarded-For"):
            return self.headers["X-Forwarded-For"].split(",")[0].strip()
        return self.client_address[0]

    def _https(self):
        return (self.headers.get("X-Forwarded-Proto", "").lower() == "https" or '"https"' in self.headers.get("Cf-Visitor", "")
                or os.environ.get("PAINEL_HTTPS") == "1")

    def _cookie(self, token, max_age):
        seguro = "; Secure" if self._https() else ""
        return ("Set-Cookie", f"{auth.COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}{seguro}")

    def usuario(self):
        if not hasattr(self, "_u"):
            self._u = auth.usuario_da_sessao(self._token())
        return self._u

    def _auth_post(self, rota, corpo):
        try:
            if rota == "/api/auth/login":
                token, u = auth.entrar(corpo.get("email"), corpo.get("senha"), self._ip())
                return self.responder(200, {"usuario": u}, cabecalhos=[self._cookie(token, auth.SESSAO_DIAS * 86400)])
            if rota == "/api/auth/cadastro":
                auth.cadastrar(corpo.get("empresa"), corpo.get("nome"), corpo.get("email"), corpo.get("senha"), corpo.get("plano"))
                return self.responder(201, {"mensagem": "Conta criada. Assim que for aprovada, você já pode entrar com este e-mail e senha."})
            if rota == "/api/auth/setup":
                if not self._local():
                    return self.responder(403, {"erro": "O primeiro administrador só pode ser criado no computador do servidor."})
                auth.criar_admin_inicial(corpo.get("empresa"), corpo.get("nome"), corpo.get("email"), corpo.get("senha"))
                token, u = auth.entrar(corpo.get("email"), corpo.get("senha"), self._ip())
                return self.responder(201, {"usuario": u}, cabecalhos=[self._cookie(token, auth.SESSAO_DIAS * 86400)])
            if rota == "/api/auth/sair":
                auth.sair(self._token())
                return self.responder(200, {"ok": True}, cabecalhos=[self._cookie("", 0)])
        except auth.ErroAuth as e:
            return self.responder(e.codigo, {"erro": str(e)})

    def do_GET(self):
        definir_conta(None)
        rota = self._rota()
        if rota == "/login":
            return self.responder(200, PAGINA_LOGIN, "text/html; charset=utf-8")
        if rota == "/api/auth/estado":
            return self.responder(200, {"tem_usuarios": auth.tem_usuarios(), "local": self._local(), "logado": bool(self.usuario())})
        if rota == "/api/planos":
            return self.responder(200, {"planos": planos.publico(), "extra_numero": planos.EXTRA_NUMERO, "extra_usuario": planos.EXTRA_USUARIO})
        if rota not in PUBLICAS_GET and not self.usuario():
            if rota.startswith("/api/"):
                return self.responder(401, {"erro": "Sua sessão terminou. Entre de novo."})
            return self.responder(302, b"", cabecalhos=[("Location", "/login")])
        if rota == "/api/auth/eu":
            return self.responder(200, {"usuario": self.usuario()}) if self.usuario() else self.responder(401, {"erro": "Não logado."})
        definir_conta(self.usuario()["conta"]["id"])  # daqui em diante tudo lê e grava só na pasta desta conta
        if rota.startswith("/api/admin/"):
            if self.usuario()["papel"] != "admin":
                return self.responder(403, {"erro": "Só o administrador pode ver isso."})
            if rota == "/api/admin/usuarios":
                return self.responder(200, {"usuarios": auth.listar_usuarios(), "eu": self.usuario()["id"]})
            if rota == "/api/admin/contas":
                return self.responder(200, {"contas": contas.listar(), "minha": self.usuario()["conta"]["id"], "planos": planos.publico()})
        if rota == "/api/equipe":
            return self.responder(200, auth.equipe(self.usuario()))
        if rota == "/api/mockups":
            return self.responder(200, {"salvos": mockups.listar()})
        if rota == "/api/mockup":
            m = mockups.obter((urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get("lead") or [""])[0])
            return self.responder(200, m) if m else self.responder(404, {"erro": "Este lead ainda não tem mockup salvo."})
        if self.path in ("/", "/pagina_leads.html"):
            self.responder(200, renderizar(servidor=True), "text/html; charset=utf-8")
        elif self.path == "/api/leads":
            self.responder(200, carregar_leads())
        elif self.path == "/api/fila":
            self.responder(200, {"itens": crm_db.fila_listar(), "config": crm_db.config_fila(), "estado": fila.estado(),
                                        "optouts": crm_db.optouts()})
        elif self.path == "/api/whatsapp/numeros":
            self.responder(200, crm_db.numeros_wa())
        elif self.path == "/api/whatsapp/verificacao":
            ver = _da_conta()["ver"]
            with LOCK:
                pend = len([n for n in numeros_dos_leads() if n not in crm_db.numeros_wa()]) if ver["status"] != "running" else 0
                self.responder(200, {**ver, "pendentes": pend})
        elif self.path == "/api/whatsapp/status":
            self.responder(200, whatsapp_web.status())
        elif self.path == "/api/crm":
            self.responder(200, crm_db.ler())
        elif self.path == "/api/gemini":
            self.responder(200, gemini.estado())
        elif self.path == "/api/gemini/modelos":
            try:
                self.responder(200, {"modelos": gemini.modelos(), "imagens": gemini.modelos_imagem(), **gemini.estado()})
            except gemini.ErroGemini as e:
                self.responder(400, {"erro": str(e)})
        elif self.path == "/api/job":
            with LOCK:
                self.responder(200, _da_conta()["job"])
        else:
            self.responder(404, {"erro": "não encontrado"})

    def do_POST(self):
        definir_conta(None)
        # exigir JSON impede que outro site dispare a coleta (força preflight CORS)
        if "application/json" not in (self.headers.get("Content-Type") or ""):
            return self.responder(415, {"erro": "use application/json"})
        if int(self.headers.get("Content-Length") or 0) > 40_000_000:  # mockup com imagens embutidas cabe com folga
            return self.responder(413, {"erro": "Conteúdo grande demais (máx. 40 MB). Use menos imagens ou imagens menores."})
        try:
            corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except ValueError:
            return self.responder(400, {"erro": "JSON inválido"})
        if not isinstance(corpo, dict):
            return self.responder(400, {"erro": "JSON inválido"})

        if self._rota() in PUBLICAS_POST:
            return self._auth_post(self._rota(), corpo)
        if not self.usuario():
            return self.responder(401, {"erro": "Sua sessão terminou. Entre de novo."})
        definir_conta(self.usuario()["conta"]["id"])  # daqui em diante tudo lê e grava só na pasta desta conta
        if self._rota() == "/api/auth/minha-senha":
            try:
                auth.trocar_minha_senha(self.usuario()["id"], corpo.get("atual"), corpo.get("nova"), self._token())
                return self.responder(200, {"ok": True})
            except auth.ErroAuth as e:
                return self.responder(e.codigo, {"erro": str(e)})
        if self._rota().startswith("/api/admin/"):
            if self.usuario()["papel"] != "admin":
                return self.responder(403, {"erro": "Só o administrador pode fazer isso."})
            try:
                if self._rota() == "/api/admin/usuario":
                    return self.responder(200, auth.administrar(self.usuario()["id"], corpo.get("id"), corpo.get("acao"), corpo.get("senha")))
                if self._rota() == "/api/admin/criar-conta":
                    return self.responder(201, auth.admin_criar_conta(corpo.get("empresa"), corpo.get("plano"), corpo.get("nome"),
                                                                      corpo.get("email"), corpo.get("senha")))
                if self._rota() == "/api/admin/conta":
                    alvo = int(corpo.get("id") or 0)
                    r = contas.administrar(alvo, corpo.get("acao"), corpo.get("plano"), self.usuario()["conta"]["id"], corpo.get("nome"))
                    if corpo.get("acao") in ("bloquear", "excluir"):
                        whatsapp_web.sair(alvo)  # fecha o WhatsApp da empresa bloqueada/excluída
                    return self.responder(200, r)
            except (auth.ErroAuth, contas.ErroConta) as e:
                return self.responder(e.codigo, {"erro": str(e)})
            except (TypeError, ValueError):
                return self.responder(400, {"erro": "Conta inválida."})
            return self.responder(404, {"erro": "não encontrado"})
        if self._rota().startswith("/api/equipe/"):
            try:
                if self._rota() == "/api/equipe/criar":
                    return self.responder(201, auth.equipe_criar(self.usuario(), corpo.get("nome"), corpo.get("email"), corpo.get("senha")))
                if self._rota() == "/api/equipe/membro":
                    return self.responder(200, auth.equipe_acao(self.usuario(), corpo.get("id"), corpo.get("acao"), corpo.get("senha")))
            except auth.ErroAuth as e:
                return self.responder(e.codigo, {"erro": str(e)})
            return self.responder(404, {"erro": "não encontrado"})

        if self.path == "/api/job/cancel":
            _da_conta()["cancelar"].set()
            return self.responder(200, {"ok": True})
        if self.path == "/api/whatsapp/conectar":
            return self.responder(200, whatsapp_web.conectar())
        if self.path == "/api/fila/adicionar":
            itens = corpo.get("itens")
            if not isinstance(itens, list):
                return self.responder(400, {"erro": "Envie {itens: [...]}."})
            return self.responder(200, {"novos": crm_db.fila_adicionar(itens[:500])})
        if self.path == "/api/fila/acao":
            if corpo.get("acao") not in ("aprovar_todas", "aprovar", "pausar", "remover", "limpar"):
                return self.responder(400, {"erro": "Ação inválida."})
            crm_db.fila_acao(corpo["acao"], corpo.get("id"))
            return self.responder(200, {"ok": True})
        if self.path == "/api/fila/reativar":
            crm_db.reativar_numero(re.sub(r"\D", "", str(corpo.get("numero", ""))))
            return self.responder(200, {"ok": True})
        if self.path == "/api/fila/config":
            try:
                return self.responder(200, {"config": crm_db.salvar_config_fila(corpo.get("config") or {})})
            except (TypeError, ValueError):
                return self.responder(400, {"erro": "Valores inválidos."})
        if self.path == "/api/whatsapp/verificar":
            dc = _da_conta()
            with LOCK:
                if dc["ver"]["status"] == "running":
                    return self.responder(409, {"erro": "Já existe uma verificação em andamento."})
                if whatsapp_web.status()["estado"] != "conectado":
                    return self.responder(409, {"erro": "Conecte o WhatsApp na aba WhatsApp primeiro."})
                dc["cancelar_ver"].clear()
                dc["ver"].update(status="running", atual=0, total=0, com=0, sem=0, erro="")
            threading.Thread(target=verificar_lote, args=(conta_atual(),), daemon=True).start()
            return self.responder(202, {"ok": True})
        if self.path == "/api/whatsapp/verificar/cancel":
            _da_conta()["cancelar_ver"].set()
            return self.responder(200, {"ok": True})
        if self.path == "/api/whatsapp/enviar":
            return self.responder(200, whatsapp_web.enviar(corpo.get("numero", ""), corpo.get("texto", "")))
        if self.path == "/api/whatsapp/sair":
            return self.responder(200, whatsapp_web.sair())
        if self.path == "/api/crm":
            if not isinstance(corpo.get("crm"), dict):
                return self.responder(400, {"erro": "Envie {crm: {...}}."})
            return self.responder(200, crm_db.salvar_crm(corpo["crm"]))
        if self.path == "/api/gemini/chave":
            try:
                return self.responder(200, gemini.salvar(corpo.get("chave", ""), corpo.get("modelo", "")))
            except gemini.ErroGemini as e:
                return self.responder(400, {"erro": str(e)})
        if self.path == "/api/gemini/modelo":
            try:
                return self.responder(200, gemini.salvar_modelo(corpo.get("modelo", ""), corpo.get("tipo", "modelo")))
            except gemini.ErroGemini as e:
                return self.responder(400, {"erro": str(e)})
        if self.path == "/api/fotos/chave":
            try:
                return self.responder(200, gemini.salvar_pexels(corpo.get("chave", "")))
            except gemini.ErroGemini as e:
                return self.responder(400, {"erro": str(e)})
        if self.path == "/api/voz/transcrever":
            audio = corpo.get("audio")
            if not isinstance(audio, str) or not audio or len(audio) > 12_000_000:
                return self.responder(400, {"erro": "Áudio vazio ou longo demais (máx. 2 minutos)."})
            try:
                texto, modelo = gemini.transcrever(audio, corpo.get("mime", "audio/wav"))
                return self.responder(200, {"texto": texto, "modelo": modelo})
            except gemini.ErroGemini as e:
                return self.responder(400, {"erro": str(e)})
        if self.path == "/api/mockup/salvar":
            try:
                return self.responder(200, mockups.salvar(corpo.get("lead"), corpo.get("nome"), corpo.get("html"),
                                                          corpo.get("rascunho"), corpo.get("origem", "manual")))
            except mockups.ErroMockup as e:
                return self.responder(400, {"erro": str(e)})
        if self.path == "/api/mockup/gerar":
            if not isinstance(corpo.get("lead"), dict):
                return self.responder(400, {"erro": "Escolha um lead."})
            try:
                html, modelo, aviso = gemini.gerar(corpo["lead"], corpo.get("opcoes") or {})
                return self.responder(200, {"html": html, "modelo": modelo, "aviso": aviso})
            except gemini.ErroGemini as e:
                return self.responder(400, {"erro": str(e)})
        if self.path == "/api/colunas":
            if not isinstance(corpo.get("colunas"), list):
                return self.responder(400, {"erro": "Envie {colunas: [...]}."})
            return self.responder(200, {"colunas": crm_db.salvar_colunas(corpo["colunas"])})
        if self.path == "/api/cores":
            if not isinstance(corpo.get("cores"), dict):
                return self.responder(400, {"erro": "Envie {cores: {...}}."})
            return self.responder(200, {"cores": crm_db.salvar_cores(corpo["cores"])})
        if self.path != "/api/job":
            return self.responder(404, {"erro": "não encontrado"})

        nicho = str(corpo.get("nicho", "")).strip()[:80]
        cidade = str(corpo.get("cidade", "")).strip()[:80]
        if not nicho or not cidade:
            return self.responder(400, {"erro": "Informe o nicho e a cidade."})
        try:
            limite = int(corpo.get("limite") or 0) or None
        except (TypeError, ValueError):
            return self.responder(400, {"erro": "Limite deve ser um número."})
        dc = _da_conta()
        with LOCK:
            if dc["job"]["status"] == "running":
                return self.responder(409, {"erro": "Já existe uma busca em andamento."})
            dc["cancelar"].clear()
            dc["job"].update(status="running", etapa="coletando", nicho=nicho, nicho_id=slug(nicho), cidade=cidade,
                       atual=0, total=0, nome="", erro="", log=[])
        threading.Thread(target=rodar, args=(conta_atual(), nicho, cidade, limite, bool(corpo.get("mostrar"))), daemon=True).start()
        self.responder(202, {"ok": True})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    # a coleta com Playwright em thread precisa do loop Proactor no Windows (padrão do Python 3.8+)
    comum.MODO_SERVIDOR = True  # toda operação precisa dizer de qual conta é
    contas.migrar()  # primeira vez: os dados de antes das contas viram a conta 1
    whatsapp_web.on_conversas = respostas.processar
    fila.iniciar()
    srv = ThreadingHTTPServer((HOST, PORTA), Handler)
    url = f"http://localhost:{PORTA}"
    print(f"Painel em {url}  (Ctrl+C para encerrar)")
    if "--sem-navegador" not in sys.argv:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")
