"""Planos vendidos (ver docs/planos.md). Mudar preço ou limite é só editar aqui."""

PLANOS = {
    "largada": {"nome": "Largada", "preco": 97, "usuarios": 1, "numeros": 1, "leads_mes": 1000,
                "buscas_simultaneas": 1, "contatos_dia": 40,
                "resumo": "Para quem prospecta sozinho"},
    "tracao": {"nome": "Tração", "preco": 197, "usuarios": 3, "numeros": 3, "leads_mes": 5000,
               "buscas_simultaneas": 1, "contatos_dia": 120,
               "resumo": "Para pequenas equipes de vendas"},
    "escala": {"nome": "Escala", "preco": 397, "usuarios": 8, "numeros": 6, "leads_mes": 15000,
               "buscas_simultaneas": 2, "contatos_dia": 300,
               "resumo": "Para agências com várias frentes"},
}
PADRAO = "largada"
EXTRA_NUMERO = 39   # R$/mês por número de WhatsApp a mais
EXTRA_USUARIO = 29  # R$/mês por usuário a mais


def valido(plano):
    return plano in PLANOS


def publico():
    return {k: dict(v, id=k) for k, v in PLANOS.items()}
