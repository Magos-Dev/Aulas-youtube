"""Conexão com o WhatsApp Web via Playwright (navegador real, sem Evolution/Docker).

Cada conta (empresa) tem a sua sessão: uma thread própria dona do navegador, com o login (QR code)
salvo em dados/contas/<id>/wa_perfil/, então só é preciso escanear uma vez. O navegador abre visível:
o QR também aparece lá, e dá para acompanhar os envios.

As funções do módulo (status, conectar, enviar, verificar, sair) agem sobre a conta atual da thread
(comum.conta_atual()).

Estados: parado | iniciando | qr | conectado | erro
"""
import base64
import os
import queue
import re
import threading
import time
import urllib.parse

from playwright.sync_api import sync_playwright

import crm_db
from comum import conta_atual, definir_conta, pasta

URL = "https://web.whatsapp.com/"
# Edge vem no Windows e é suportado pelo WhatsApp Web; use WA_NAVEGADOR=chrome para o Google Chrome
NAVEGADOR = os.environ.get("WA_NAVEGADOR", "msedge")
LOGADO = "#pane-side"
QR = "canvas"
on_conversas = None  # callback(linhas) chamado com as conversas não lidas (ver respostas.py), na thread da conta
LER_CONVERSAS = """() => [...document.querySelectorAll('#pane-side [role="listitem"], #pane-side [role="row"]')].map(el => {
  const t = el.querySelector('span[title]');
  const un = [...el.querySelectorAll('[aria-label]')].map(x => x.getAttribute('aria-label'))
    .find(a => /n[ãa]o lida|unread/i.test(a)) || '';
  const m = un.match(/\\d+/);
  return {titulo: t ? t.getAttribute('title') : '', linhas: el.innerText.split('\\n').map(s => s.trim()).filter(Boolean),
          naoLidas: m ? +m[0] : (un ? 1 : 0)};
})"""
INTERVALO_LEITURA = 12  # segundos entre leituras da lista de conversas
COMPOSER = 'footer div[contenteditable="true"]'
INVALIDO = re.compile(r"inv[aá]lido|invalid", re.I)


def _abrir(page, numero, texto=""):
    """Abre a conversa com o número. Devolve None se abriu, ou o dict de erro (sem_whatsapp, timeout)."""
    page.goto(f"{URL}send?phone={numero}" + (f"&text={urllib.parse.quote(texto)}" if texto else ""), timeout=60000)
    limite = time.time() + 45
    while time.time() < limite:
        if page.locator(COMPOSER).count():
            return None
        if page.locator('div[role="dialog"]').filter(has_text=INVALIDO).count():
            return {"ok": False, "erro": "sem_whatsapp", "detalhe": "Este número não tem WhatsApp."}
        time.sleep(0.5)
    return {"ok": False, "erro": "timeout", "detalhe": "A conversa não abriu a tempo."}


def _verificar(page, numero):
    """Só abre a conversa para ver se o número tem WhatsApp. Não envia nada."""
    r = _abrir(page, numero)
    if r is None:
        return {"ok": True, "tem": True}
    return {"ok": True, "tem": False} if r["erro"] == "sem_whatsapp" else r


def _enviar(page, numero, texto):
    """Abre a conversa pelo link de envio e manda a mensagem. Roda na thread do navegador."""
    erro = _abrir(page, numero, texto)
    if erro:
        return erro
    caixa = page.locator(COMPOSER).first
    page.wait_for_timeout(1500)  # deixa o texto do link terminar de entrar na caixa
    if not (caixa.inner_text() or "").strip():
        return {"ok": False, "erro": "sem_texto", "detalhe": "A mensagem não entrou na caixa de texto."}
    caixa.press("Enter")
    page.wait_for_timeout(1500)
    page.goto(URL, timeout=60000)  # sai da conversa: respostas só aparecem como "não lidas" fora dela
    return {"ok": True}


class Sessao:
    """O WhatsApp de uma conta: estado, fila de comandos e a thread dona do navegador."""

    def __init__(self, conta_id):
        self.conta_id = conta_id
        self.lock = threading.Lock()
        self.estado = {"estado": "parado", "qr": "", "erro": ""}
        self.parar = threading.Event()
        self.thread = None
        self.fila = queue.Queue()

    def set(self, **kw):
        with self.lock:
            self.estado.update(kw)

    def status(self):
        with self.lock:
            return dict(self.estado)

    def _rodar(self):
        definir_conta(self.conta_id)  # respostas.py e crm_db rodam nesta thread: dados desta conta
        try:
            perfil = pasta(self.conta_id) / "wa_perfil"
            perfil.mkdir(parents=True, exist_ok=True)
            with sync_playwright() as p:
                ctx = p.chromium.launch_persistent_context(
                    str(perfil), channel=NAVEGADOR, headless=False, locale="pt-BR",
                    viewport={"width": 1100, "height": 800})
                try:
                    page = ctx.pages[0] if ctx.pages else ctx.new_page()
                    page.goto(URL, timeout=60000)
                    ultima_leitura = 0.0
                    while not self.parar.is_set() and ctx.pages:
                        try:
                            fn, args, saida = self.fila.get_nowait()
                        except queue.Empty:
                            pass
                        else:
                            try:
                                saida.update(fn(page, *args))
                            except Exception as e:
                                saida.update(ok=False, erro="falha", detalhe=str(e).splitlines()[0][:200])
                            saida["pronto"].set()
                            continue
                        if page.locator(LOGADO).count():
                            self.set(estado="conectado", qr="", erro="")
                        elif page.locator(QR).count():
                            try:
                                png = page.locator(QR).first.screenshot(timeout=3000)
                                self.set(estado="qr", qr="data:image/png;base64," + base64.b64encode(png).decode(), erro="")
                            except Exception:
                                pass  # o QR é recarregado de tempos em tempos
                        else:
                            self.set(estado="iniciando", qr="")
                        if on_conversas and self.status()["estado"] == "conectado" and time.time() - ultima_leitura > INTERVALO_LEITURA:
                            ultima_leitura = time.time()
                            try:
                                on_conversas(page.evaluate(LER_CONVERSAS))
                            except Exception:
                                pass  # a página pode estar recarregando
                        time.sleep(1.5)
                finally:
                    ctx.close()
        except Exception as e:
            self.set(estado="erro", qr="", erro=str(e).splitlines()[0][:300] or e.__class__.__name__)
            return
        self.set(estado="parado", qr="")

    def conectar(self):
        if self.thread is None or not self.thread.is_alive():
            self.parar.clear()
            self.set(estado="iniciando", qr="", erro="")
            self.thread = threading.Thread(target=self._rodar, daemon=True)
            self.thread.start()
        return self.status()

    def executar(self, fn, numero, *args):
        numero = re.sub(r"\D", "", str(numero))
        if not 10 <= len(numero) <= 15:
            return {"ok": False, "erro": "numero", "detalhe": "Número inválido."}
        if self.status()["estado"] != "conectado":
            return {"ok": False, "erro": "desconectado", "detalhe": "WhatsApp não conectado. Conecte na aba WhatsApp."}
        saida = {"pronto": threading.Event()}
        self.fila.put((fn, (numero, *args), saida))
        if not saida["pronto"].wait(90):
            return {"ok": False, "erro": "timeout", "detalhe": "A operação demorou demais."}
        saida.pop("pronto")
        return saida

    def sair(self):
        self.parar.set()
        if self.thread is not None:
            self.thread.join(timeout=10)
        return self.status()


_sessoes, _sessoes_lock = {}, threading.Lock()


def _sessao(conta_id=None):
    conta_id = conta_id or conta_atual()
    with _sessoes_lock:
        if conta_id not in _sessoes:
            _sessoes[conta_id] = Sessao(conta_id)
        return _sessoes[conta_id]


def status():
    return _sessao().status()


def conectar():
    """Abre o navegador da conta atual (se ainda não estiver aberto) e devolve o estado."""
    return _sessao().conectar()


def enviar(numero, texto):
    """Manda `texto` para `numero` (só dígitos, com 55) pelo WhatsApp da conta atual. Bloqueia até terminar."""
    r = _sessao().executar(_enviar, numero, str(texto)[:4000])
    if r.get("ok"):
        crm_db.salvar_numero_wa(re.sub(r"\D", "", str(numero)), True)
    elif r.get("erro") == "sem_whatsapp":
        crm_db.salvar_numero_wa(re.sub(r"\D", "", str(numero)), False)
    return r


def verificar(numero):
    """Diz se `numero` tem WhatsApp, sem enviar mensagem, e guarda no banco da conta."""
    r = _sessao().executar(_verificar, numero)
    if r.get("ok"):
        crm_db.salvar_numero_wa(re.sub(r"\D", "", str(numero)), r["tem"])
    return r


def sair(conta_id=None):
    """Fecha o navegador da conta. A sessão continua salva: conectar de novo não pede o QR."""
    return _sessao(conta_id).sair()
