"""Fotos do mockup: troca os marcadores {{FOTO:descrição}} que a IA escreve por fotos reais.

- "banco": busca no Pexels (grátis; cada pessoa usa a própria chave de https://www.pexels.com/api/).
- "ia": cria a foto com um modelo de imagem do Gemini (Nano Banana). Exige faturamento ativo na conta
  Google; se não houver, cai para o Pexels (quando há chave) ou para um fundo em gradiente.
"""
import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import gemini

MARCADOR = re.compile(r"\{\{FOTO:([^{}]{1,160})\}\}")
MAX_FOTOS = 8
MAX_FOTOS_IA = 4


def buscar_pexels(consulta, chave, quantas=5):
    url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": consulta, "per_page": quantas, "orientation": "landscape"})
    req = urllib.request.Request(url, headers={"Authorization": chave, "User-Agent": "coletar_leads"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()).get("photos", [])
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise gemini.ErroGemini("Chave do Pexels recusada. Copie de novo em pexels.com/api.")
        if e.code == 429:
            raise gemini.ErroGemini("Limite do Pexels atingido (200 buscas por hora no plano grátis). Tente mais tarde.")
        raise gemini.ErroGemini(f"O Pexels respondeu com erro {e.code}.")
    except (urllib.error.URLError, TimeoutError):
        raise gemini.ErroGemini("Não consegui falar com o Pexels. Confira a internet.")


def _gradiente(i):
    cores = [("#1e3a8a", "#0ea5e9"), ("#7c2d12", "#f59e0b"), ("#14532d", "#22c55e"), ("#4c1d95", "#ec4899")][i % 4]
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='1600' height='900'><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
           f"<stop offset='0' stop-color='{cores[0]}'/><stop offset='1' stop-color='{cores[1]}'/></linearGradient></defs>"
           f"<rect width='100%' height='100%' fill='url(#g)'/></svg>")
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def _foto_ia(desc, d, nicho):
    corpo = {"contents": [{"parts": [{"text": f"Professional high-end commercial photograph for the website of a {nicho or 'local business'}: "
                                              f"{desc}. Photorealistic, natural light, sharp focus, rich detail, no text, no logos, no watermark."}]}],
             "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}}}
    modelo = d.get("modelo_imagem") or gemini.MODELO_IMAGEM_PADRAO
    r = gemini._chamar("POST", f"{gemini.API}/models/{modelo}:generateContent", d["chave"], corpo, 180)
    for p in r.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        dado = p.get("inlineData") or p.get("inline_data")
        if dado:
            return f"data:{dado.get('mimeType') or dado.get('mime_type') or 'image/png'};base64,{dado['data']}"
    raise gemini.ErroGemini("O modelo de imagem não devolveu foto.")


def resolver(html, modo, d, chave_pexels, nicho=""):
    """Devolve (html com fotos, aviso ou "")."""
    descricoes = list(dict.fromkeys(m.strip() for m in MARCADOR.findall(html)))[:MAX_FOTOS]
    if not descricoes:
        return html, ""
    urls, aviso = {}, ""

    if modo == "ia":
        with ThreadPoolExecutor(4) as ex:
            futuros = {desc: ex.submit(_foto_ia, desc, d, nicho) for desc in descricoes[:MAX_FOTOS_IA]}
        erros = []
        for desc, f in futuros.items():
            try:
                urls[desc] = f.result()
            except gemini.ErroGemini as e:
                erros.append(str(e))
        if erros:
            aviso = erros[0] + (" Usei fotos do Pexels no lugar." if chave_pexels else " Usei fundos em gradiente no lugar.")
        # fotos além do limite de IA reaproveitam as já criadas
        feitas = list(urls.values())
        for i, desc in enumerate(descricoes):
            if desc not in urls and feitas and not erros:
                urls[desc] = feitas[i % len(feitas)]

    faltam = [x for x in descricoes if x not in urls]
    if faltam and chave_pexels and modo in ("banco", "ia"):
        usadas = set()

        erros_px = []

        def uma(desc):
            try:
                return desc, buscar_pexels(desc, chave_pexels)
            except gemini.ErroGemini as e:
                erros_px.append(str(e))
                return desc, []

        with ThreadPoolExecutor(4) as ex:
            resultados = list(ex.map(uma, faltam))
        if erros_px and not aviso:
            aviso = erros_px[0] + " Algumas fotos ficaram como fundo em gradiente."
        for desc, fotos in resultados:
            for f in fotos:  # evita a mesma foto em dois lugares
                if f["id"] not in usadas:
                    usadas.add(f["id"])
                    urls[desc] = f["src"].get("large2x") or f["src"]["large"]
                    break

    for i, desc in enumerate(descricoes):
        urls.setdefault(desc, _gradiente(i))
    html = MARCADOR.sub(lambda m: urls.get(m.group(1).strip(), _gradiente(0)), html)
    return html, aviso
