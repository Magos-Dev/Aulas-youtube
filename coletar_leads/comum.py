"""Caminhos e nomes de arquivo compartilhados entre os scripts.

Cada conta (empresa cliente) tem a própria pasta em dados/contas/<id>/ com leads, CRM, fila,
configurações e a sessão do WhatsApp. O código descobre a pasta pela conta "atual" da thread:
o servidor define a conta no início de cada pedido e de cada tarefa em segundo plano.
"""
import json
import os
import re
import threading
import unicodedata
from pathlib import Path

RAIZ = Path(os.environ.get("PAINEL_DADOS") or Path(__file__).parent / "dados")
_ctx = threading.local()
# server.py liga isto: com o servidor rodando, toda operação precisa dizer de qual conta é,
# para nunca cair na pasta de outra empresa por esquecimento
MODO_SERVIDOR = False


class Cancelado(Exception):
    pass


class SemConta(RuntimeError):
    pass


def definir_conta(conta_id):
    _ctx.conta = int(conta_id) if conta_id else None


def conta_atual():
    c = getattr(_ctx, "conta", None)
    if c:
        return c
    if MODO_SERVIDOR:
        raise SemConta("Operação sem conta definida.")
    return int(os.environ.get("PAINEL_CONTA", "1"))  # scripts de terminal: conta 1 (ou PAINEL_CONTA)


def pasta(conta_id=None):
    p = RAIZ / "contas" / str(int(conta_id or conta_atual()))
    p.mkdir(parents=True, exist_ok=True)
    return p


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "leads"


def chave(nicho, cidade):
    """Identifica uma busca: 'borracharias__guarapuava-pr'."""
    return f"{slug(nicho)}__{slug(cidade)}"


def salvar_meta(k, nicho, cidade):
    (pasta() / f"meta_{k}.json").write_text(
        json.dumps({"nicho": nicho, "cidade": cidade}, ensure_ascii=False), encoding="utf-8")


def ler_meta(k):
    try:
        return json.loads((pasta() / f"meta_{k}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def chaves_coletadas():
    return sorted(p.stem.removeprefix("dados_maps_") for p in pasta().glob("dados_maps_*.json"))
