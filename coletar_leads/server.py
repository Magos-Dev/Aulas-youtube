"""Servidor local do painel: serve a página e roda coleta + detalhamento em segundo plano.

Uso: python server.py  (abre http://localhost:8765)
"""
import json
import os
import random
import re
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import crm_db
import fila
import respostas
import whatsapp_web
from comum import Cancelado, chave, slug
from detalhar_leads import detalhar
from gerar_pagina import carregar_leads, renderizar
from scraper_maps import coletar

HOST, PORTA = "127.0.0.1", int(os.environ.get("PAINEL_PORTA", 8765))
LOCK = threading.Lock()
JOB = {"status": "idle", "etapa": "", "nicho": "", "nicho_id": "", "cidade": "", "atual": 0, "total": 0,
       "nome": "", "erro": "", "log": [], "versao": 0}
CANCELAR = threading.Event()
VER = {"status": "idle", "atual": 0, "total": 0, "com": 0, "sem": 0, "erro": ""}
CANCELAR_VER = threading.Event()


def numeros_dos_leads():
    """Telefones únicos dos leads, no formato 55DDDNNNNNNNN(N)."""
    vistos = {}
    for l in carregar_leads():
        d = re.sub(r"\D", "", l.get("telefone", ""))
        if len(d) in (10, 11):
            vistos["55" + d] = True
    return list(vistos)


def verificar_lote():
    try:
        pendentes = [n for n in numeros_dos_leads() if n not in crm_db.numeros_wa()]
        with LOCK:
            VER.update(status="running", atual=0, total=len(pendentes), com=0, sem=0, erro="")
        for i, n in enumerate(pendentes, 1):
            if CANCELAR_VER.is_set():
                break
            r = whatsapp_web.verificar(n)
            if not r.get("ok"):
                if r.get("erro") in ("desconectado",):
                    raise RuntimeError(r["detalhe"])
                continue  # timeout ou falha pontual: tenta de novo na próxima rodada
            with LOCK:
                VER["atual"] = i
                VER["com" if r["tem"] else "sem"] += 1
            time.sleep(random.uniform(3, 6))  # intervalo humano entre as conversas
        with LOCK:
            VER["status"] = "cancelled" if CANCELAR_VER.is_set() else "done"
    except Exception as e:
        with LOCK:
            VER.update(status="error", erro=str(e) or e.__class__.__name__)


def atualizar(**kw):
    with LOCK:
        JOB.update(kw)


def log(msg):
    print(msg, flush=True)
    with LOCK:
        JOB["log"] = (JOB["log"] + [msg])[-40:]


def rodar(nicho, cidade, limite, mostrar):
    k = chave(nicho, cidade)
    try:
        atualizar(etapa="coletando", atual=0, total=0, nome="")
        coletar(nicho, cidade, log=log, headless=not mostrar, cancelado=CANCELAR.is_set)
        atualizar(etapa="detalhando")
        detalhar(k, limite=limite, log=log, headless=not mostrar, cancelado=CANCELAR.is_set,
                 progresso=lambda i, n, nome: atualizar(atual=i, total=n, nome=nome))
        with LOCK:
            JOB.update(status="done", etapa="", versao=JOB["versao"] + 1)
    except Cancelado:
        atualizar(status="cancelled", etapa="")
    except Exception as e:  # mostra o motivo na página
        log(f"Erro: {e}")
        atualizar(status="error", etapa="", erro=str(e) or e.__class__.__name__)


class Handler(BaseHTTPRequestHandler):
    def responder(self, codigo, corpo, tipo="application/json; charset=utf-8"):
        dados = corpo if isinstance(corpo, bytes) else (
            corpo.encode("utf-8") if isinstance(corpo, str) else json.dumps(corpo, ensure_ascii=False).encode("utf-8"))
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
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
            with LOCK:
                pend = len([n for n in numeros_dos_leads() if n not in crm_db.numeros_wa()]) if VER["status"] != "running" else 0
                self.responder(200, {**VER, "pendentes": pend})
        elif self.path == "/api/whatsapp/status":
            self.responder(200, whatsapp_web.status())
        elif self.path == "/api/crm":
            self.responder(200, crm_db.ler())
        elif self.path == "/api/job":
            with LOCK:
                self.responder(200, JOB)
        else:
            self.responder(404, {"erro": "não encontrado"})

    def do_POST(self):
        # exigir JSON impede que outro site dispare a coleta (força preflight CORS)
        if "application/json" not in (self.headers.get("Content-Type") or ""):
            return self.responder(415, {"erro": "use application/json"})
        try:
            corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except ValueError:
            return self.responder(400, {"erro": "JSON inválido"})

        if self.path == "/api/job/cancel":
            CANCELAR.set()
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
            with LOCK:
                if VER["status"] == "running":
                    return self.responder(409, {"erro": "Já existe uma verificação em andamento."})
                if whatsapp_web.status()["estado"] != "conectado":
                    return self.responder(409, {"erro": "Conecte o WhatsApp na aba WhatsApp primeiro."})
                CANCELAR_VER.clear()
                VER.update(status="running", atual=0, total=0, com=0, sem=0, erro="")
            threading.Thread(target=verificar_lote, daemon=True).start()
            return self.responder(202, {"ok": True})
        if self.path == "/api/whatsapp/verificar/cancel":
            CANCELAR_VER.set()
            return self.responder(200, {"ok": True})
        if self.path == "/api/whatsapp/enviar":
            return self.responder(200, whatsapp_web.enviar(corpo.get("numero", ""), corpo.get("texto", "")))
        if self.path == "/api/whatsapp/sair":
            return self.responder(200, whatsapp_web.sair())
        if self.path == "/api/crm":
            if not isinstance(corpo.get("crm"), dict):
                return self.responder(400, {"erro": "Envie {crm: {...}}."})
            return self.responder(200, crm_db.salvar_crm(corpo["crm"]))
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
        with LOCK:
            if JOB["status"] == "running":
                return self.responder(409, {"erro": "Já existe uma busca em andamento."})
            CANCELAR.clear()
            JOB.update(status="running", etapa="coletando", nicho=nicho, nicho_id=slug(nicho), cidade=cidade,
                       atual=0, total=0, nome="", erro="", log=[])
        threading.Thread(target=rodar, args=(nicho, cidade, limite, bool(corpo.get("mostrar"))), daemon=True).start()
        self.responder(202, {"ok": True})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    # a coleta com Playwright em thread precisa do loop Proactor no Windows (padrão do Python 3.8+)
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
