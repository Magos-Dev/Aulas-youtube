"""Passo 6: fila de envio do primeiro contato, com limite diário, intervalo aleatório e horário comercial.

Só envia mensagens aprovadas (ou todas, se "aprovar automaticamente" estiver ligado) e só com o
envio automático ligado. Cada envio bem-sucedido entra no CRM (status, histórico e follow-up).
Uma thread só atende todas as contas ativas, uma de cada vez; cada conta tem o próprio estado e intervalo.
"""
import json
import random
import threading
import time
from datetime import datetime, timedelta

import contas
import crm_db
import whatsapp_web
from comum import conta_atual, definir_conta

_estados = {}  # conta_id -> {"motivo", "proximo_em"}
_lock = threading.Lock()
_proximos = {}  # conta_id -> time.time() a partir do qual pode enviar de novo
_parar = threading.Event()


def estado():
    with _lock:
        e = _estados.get(conta_atual(), {"motivo": "Envio automático desligado.", "proximo_em": ""})
        return dict(e, hoje=crm_db.enviados_hoje())


def _motivo(m, proximo_em=""):
    with _lock:
        _estados[conta_atual()] = {"motivo": m, "proximo_em": proximo_em}


def _no_horario(cfg, agora=None):
    h = (agora or datetime.now()).strftime("%H:%M")
    return cfg["hora_ini"] <= h <= cfg["hora_fim"]


def passo():
    """Uma rodada da conta atual: envia no máximo uma mensagem se todas as condições permitirem."""
    conta = conta_atual()
    cfg = crm_db.config_fila()
    if not cfg["ativo"]:
        return _motivo("Envio automático desligado.")
    if whatsapp_web.status()["estado"] != "conectado":
        return _motivo("Aguardando o WhatsApp conectar.")
    if not _no_horario(cfg):
        return _motivo(f"Fora do horário ({cfg['hora_ini']} às {cfg['hora_fim']}).")
    if crm_db.enviados_hoje() >= cfg["limite_dia"]:
        return _motivo(f"Limite de {cfg['limite_dia']} envios de hoje atingido.")
    proximo = _proximos.get(conta, 0.0)
    if proximo > time.time():
        return _motivo("Aguardando o intervalo entre envios.", datetime.fromtimestamp(proximo).strftime("%H:%M:%S"))
    item = crm_db.fila_proxima()
    if not item:
        return _motivo("Fila vazia: nada aprovado para enviar.")
    if crm_db.esta_bloqueado(item["numero"]):
        crm_db.fila_marcar(item["id"], "cancelada", "Cliente pediu para parar.")
        return
    if item["etapa"] != "Abertura" and crm_db.status_do_lead(item["link"]) != "enviado":
        crm_db.fila_marcar(item["id"], "cancelada", "O lead respondeu ou foi encerrado; follow-up cancelado.")
        return
    _motivo(f"Enviando para {item['nome']}...")
    r = whatsapp_web.enviar(item["numero"], item["texto"])
    if r.get("ok"):
        crm_db.fila_marcar(item["id"], "enviada")
        crm_db.registrar_envio(item["link"], item["etapa"], item["produto"], item["tag"], item["texto"],
                               item["numero"], json.loads(item["seg"]) if item["seg"] else None, item["nome"])
    elif r.get("erro") == "sem_whatsapp":
        crm_db.fila_marcar(item["id"], "sem_whatsapp", r["detalhe"])
    elif r.get("erro") == "desconectado":
        pass  # volta a tentar quando reconectar; o item continua aprovado
    else:
        crm_db.fila_marcar(item["id"], "erro", r.get("detalhe", "falha ao enviar"))
    _proximos[conta] = time.time() + random.uniform(cfg["intervalo_min"], cfg["intervalo_max"])
    _motivo("Aguardando o intervalo entre envios.", datetime.fromtimestamp(_proximos[conta]).strftime("%H:%M:%S"))


def _quando(iso):
    """Lê a data de um item do histórico (local, ou UTC com 'Z' quando veio do navegador) como horário local."""
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return d.astimezone().replace(tzinfo=None) if d.tzinfo else d


def agendar_followups(agora=None):
    """Passo 7: cria os follow-ups de quem recebeu a abertura e não respondeu, e encerra quem passou do prazo.

    Cadência (configurável), contada a partir da abertura:
      1º follow-up após `followup1_horas`, fechamento após `followup2_dias`, encerra após `encerrar_dias`.
    Devolve {'criados': n, 'encerrados': n}.
    """
    cfg = crm_db.config_fila()
    agora = agora or datetime.now()
    criados = encerrados = 0
    if not (cfg["followups_auto"] or cfg["encerrar_auto"]):
        return {"criados": 0, "encerrados": 0}
    for link, hist in crm_db.leads_enviados():
        abertura = next((h for h in hist if h.get("etapa") == "Abertura" and h.get("seg") and h.get("numero")), None)
        if not abertura:
            continue  # contato manual antigo, sem os textos seguintes guardados
        passou = agora - _quando(abertura["d"])
        enviadas = {h.get("etapa") for h in hist}
        seg = abertura["seg"]
        nome = (abertura.get("nome") or "")
        proximo = None
        if len(seg) > 0 and seg[0]["etapa"] not in enviadas and passou >= timedelta(hours=cfg["followup1_horas"]):
            proximo = seg[0]
        elif len(seg) > 1 and seg[0]["etapa"] in enviadas and seg[1]["etapa"] not in enviadas \
                and passou >= timedelta(days=cfg["followup2_dias"]):
            proximo = seg[1]
        if proximo and cfg["followups_auto"]:
            criados += crm_db.fila_adicionar([{"link": link, "nome": nome or link, "numero": abertura["numero"],
                                               "texto": proximo["txt"], "etapa": proximo["etapa"],
                                               "produto": abertura.get("produto", ""), "tag": proximo.get("tag", "")}])
        elif cfg["encerrar_auto"] and passou >= timedelta(days=cfg["encerrar_dias"]) \
                and all(s["etapa"] in enviadas for s in seg):
            encerrados += crm_db.encerrar_sem_resposta(link, cfg["encerrar_dias"])
    return {"criados": criados, "encerrados": encerrados}


_ultimo_agendamento = {}  # conta_id -> time.time()


def _loop():
    while not _parar.is_set():
        try:
            ids = contas.ativas()
        except Exception:
            ids = []
        for conta in ids:
            definir_conta(conta)
            try:
                if time.time() - _ultimo_agendamento.get(conta, 0.0) > 60:
                    _ultimo_agendamento[conta] = time.time()
                    agendar_followups()
                passo()
            except Exception as e:  # nunca derruba o servidor nem trava as outras contas
                _motivo(f"Erro: {e}")
        definir_conta(None)
        _parar.wait(5)


def iniciar():
    threading.Thread(target=_loop, daemon=True).start()
