"""Passo 5: detecta respostas de clientes na lista de conversas do WhatsApp Web e atualiza o CRM.

A thread do navegador (whatsapp_web.py) lê as conversas com mensagens não lidas e chama
`processar(linhas)`. Aqui as conversas são ligadas aos leads (pelo número no título ou pelo nome)
e cada resposta nova move o cartão para "Respondeu" e vai para o histórico.
"""
import re
import unicodedata

import crm_db
from gerar_pagina import carregar_leads

# linhas da conversa que não são o texto da mensagem: hora, dia da semana, data, contador
NAO_TEXTO = re.compile(
    r"^(\d{1,2}[:h]\d{2}|ontem|yesterday|hoje|today|\d{1,2}/\d{1,2}(/\d{2,4})?|"
    r"(segunda|terça|quarta|quinta|sexta|sábado|domingo)(-feira)?|monday|tuesday|wednesday|thursday|friday|saturday|sunday)$",
    re.I)


# pedidos para parar de receber mensagens (texto já normalizado: minúsculo, sem acento)
OPT_OUT = re.compile(
    r"^(parar|pare|stop|sair|remover|chega|cancelar)$|"
    r"\b(para|pare|parar) de (me )?(mandar|enviar|chamar|mexer|incomodar|insistir|ligar)\b|"
    r"\bnao (quero|tenho interesse|preciso|me (mande|envie|chame|procure|ligue))\b|"
    r"\bme (tire|tira|remova|remove|exclua|exclui|esqueca|esqueca)\b|"
    r"\b(sem interesse|descadastr\w*|spam|denunci\w*|bloquear|bloqueando|unsubscribe)\b")


def pediu_para_parar(texto):
    return bool(OPT_OUT.search(_norm(texto)))


def _norm(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def previa(linhas, titulo):
    """Texto da última mensagem mostrada na linha da conversa."""
    sobra = [l for l in linhas if l != titulo and not NAO_TEXTO.match(l) and not l.isdigit()]
    return sobra[-1] if sobra else ""


def _indice():
    por_numero, por_nome, numero_do_link = {}, {}, {}
    for l in carregar_leads():
        d = re.sub(r"\D", "", l.get("telefone", ""))
        if len(d) in (10, 11):
            por_numero.setdefault(d[-8:], set()).add(l["link"])
            numero_do_link[l["link"]] = "55" + d
        por_nome.setdefault(_norm(l["nome"]), set()).add(l["link"])
    return por_numero, por_nome, numero_do_link


def processar(linhas):
    """`linhas`: [{titulo, linhas, naoLidas}]. Devolve quantas respostas novas foram registradas."""
    por_numero, por_nome, numero_do_link = _indice()
    novas = 0
    for r in linhas:
        if (r.get("naoLidas") or 0) <= 0 or not r.get("titulo"):
            continue
        titulo = r["titulo"]
        d = re.sub(r"\D", "", titulo)
        links = por_numero.get(d[-8:], set()) if len(d) >= 10 else por_nome.get(_norm(titulo), set())
        texto = previa(r.get("linhas", []), titulo)
        if not links or not texto:
            continue
        chave = f"{d or _norm(titulo)}|{texto}|{r['naoLidas']}"
        if crm_db.resposta_vista(chave):
            continue
        parar = pediu_para_parar(texto)
        for link in links:
            if parar:
                crm_db.registrar_optout(link, numero_do_link.get(link, ""), texto)
            else:
                crm_db.registrar_resposta(link, texto)
        crm_db.marcar_resposta(chave)
        novas += 1
    return novas
