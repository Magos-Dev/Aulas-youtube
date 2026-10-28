"""Mockups salvos, um por lead, na pasta da conta (dados/contas/<id>/mockups/).

Cada lead tem <hash>.html (o site pronto) e <hash>.json (lead, origem, data e o rascunho:
HTML/CSS/JS, bibliotecas e imagens que a pessoa montou, para poder editar depois).
"""
import hashlib
import json
from datetime import datetime

from comum import pasta

LIMITE = 30_000_000  # caracteres do site pronto (as imagens vão embutidas)


class ErroMockup(Exception):
    pass


def _base(link):
    return pasta() / "mockups" / hashlib.sha1(link.encode("utf-8")).hexdigest()[:20]


def salvar(link, nome, html, rascunho=None, origem="manual"):
    if not isinstance(link, str) or not link.strip():
        raise ErroMockup("Escolha um lead.")
    if not isinstance(html, str) or "<" not in html:
        raise ErroMockup("O mockup está vazio.")
    if len(html) > LIMITE:
        raise ErroMockup("O mockup ficou grande demais (máx. 30 MB). Use menos imagens ou imagens menores.")
    meta = {"link": link, "nome": str(nome or "")[:120], "origem": origem if origem in ("manual", "ia") else "manual",
            "salvo_em": datetime.now().isoformat(timespec="seconds"), "rascunho": rascunho if isinstance(rascunho, dict) else {}}
    b = _base(link)
    b.parent.mkdir(parents=True, exist_ok=True)
    (b.parent / (b.name + ".html")).write_text(html, encoding="utf-8")
    (b.parent / (b.name + ".json")).write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return {k: meta[k] for k in ("link", "nome", "origem", "salvo_em")}


def obter(link):
    b = _base(link or "")
    try:
        meta = json.loads((b.parent / (b.name + ".json")).read_text(encoding="utf-8"))
        html = (b.parent / (b.name + ".html")).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None
    return {**meta, "html": html}


def listar():
    """{link: {nome, origem, salvo_em}} dos mockups salvos da conta (sem o conteúdo)."""
    out = {}
    for arq in (pasta() / "mockups").glob("*.json"):
        try:
            m = json.loads(arq.read_text(encoding="utf-8"))
            out[m["link"]] = {k: m.get(k, "") for k in ("nome", "origem", "salvo_em")}
        except (OSError, ValueError, KeyError):
            continue
    return out
