"""Caminhos e nomes de arquivo compartilhados entre os scripts."""
import json
import re
import unicodedata
from pathlib import Path

DADOS = Path(__file__).parent / "dados"


class Cancelado(Exception):
    pass


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "leads"


def chave(nicho, cidade):
    """Identifica uma busca: 'borracharias__guarapuava-pr'."""
    return f"{slug(nicho)}__{slug(cidade)}"


def salvar_meta(k, nicho, cidade):
    DADOS.mkdir(exist_ok=True)
    (DADOS / f"meta_{k}.json").write_text(
        json.dumps({"nicho": nicho, "cidade": cidade}, ensure_ascii=False), encoding="utf-8")


def ler_meta(k):
    try:
        return json.loads((DADOS / f"meta_{k}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def chaves_coletadas():
    return sorted(p.stem.removeprefix("dados_maps_") for p in DADOS.glob("dados_maps_*.json"))
