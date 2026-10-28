import csv
import json
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

from comum import Cancelado, chaves_coletadas, pasta


REDES = {
    "instagram": "instagram.com",
    "facebook": "facebook.com",
    "tiktok": "tiktok.com",
    "youtube": "youtube.com",
    "linkedin": "linkedin.com",
    "whatsapp": "wa.me",
    "x": "twitter.com",
}
CAMPOS = ["nome", "telefone", "redes_sociais", "tem_site", "site",
          "avaliacao", "qtd_avaliacoes", "endereco", "horarios", "link"]


def texto(page, seletor):
    loc = page.locator(seletor).first
    if loc.count() == 0:
        return ""
    try:
        return loc.inner_text(timeout=2000).strip()
    except Exception:
        return ""


def classificar_redes(urls):
    achadas = {}
    for url in urls:
        for nome, dominio in REDES.items():
            if dominio in url and nome not in achadas:
                achadas[nome] = url.split("?")[0]
    return achadas


def redes_do_site(ctx, site):
    """Abre o site da empresa e procura links de redes sociais."""
    p = ctx.new_page()
    try:
        p.goto(site, timeout=15000, wait_until="domcontentloaded")
        hrefs = p.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        return classificar_redes(hrefs)
    except Exception:
        return {}
    finally:
        p.close()


def extrair(page, ctx, item):
    page.goto(item["link"], timeout=60000)
    page.wait_for_selector("h1", timeout=20000)
    page.wait_for_timeout(1500)

    nome = texto(page, "h1") or item["nome"]
    endereco = texto(page, 'button[data-item-id="address"] .Io6YTe')
    telefone = texto(page, 'button[data-item-id^="phone:tel:"] .Io6YTe')

    site = ""
    a = page.locator('a[data-item-id="authority"]').first
    if a.count():
        site = a.get_attribute("href") or ""

    nota = texto(page, "div.F7nice span[aria-hidden='true']")
    qtd = ""
    txt_qtd = texto(page, "div.F7nice span[aria-label*='avalia']")
    m = re.search(r"([\d.]+)", txt_qtd)
    if m:
        qtd = m.group(1).replace(".", "")

    # Horários: expande a linha de horário e lê a tabela
    horarios = ""
    abrir = page.locator('[data-item-id="oh"], div[aria-label*="Horário"], button[aria-label*="horário" i]').first
    if abrir.count():
        try:
            abrir.click(timeout=2000)
            page.wait_for_timeout(500)
        except Exception:
            pass
    linhas = page.locator("table tr").all_inner_texts()
    horarios = " | ".join(" ".join(l.split()) for l in linhas if l.strip())

    # Redes sociais: o próprio "site" pode ser um perfil; senão procura dentro do site
    redes = classificar_redes([site]) if site else {}
    tem_site = bool(site) and not redes
    if site and not redes:
        redes = redes_do_site(ctx, site)

    return {
        "nome": nome,
        "telefone": telefone,
        "redes_sociais": redes,
        "tem_site": "sim" if tem_site else "não",
        "site": site if tem_site else "",
        "avaliacao": nota,
        "qtd_avaliacoes": qtd,
        "endereco": endereco,
        "horarios": horarios,
        "link": item["link"],
    }


def detalhar(k, limite=None, log=print, headless=False, cancelado=lambda: False,
             progresso=lambda i, n, nome: None):
    """Abre cada link de dados_maps_<k>.json e grava leads_detalhados_<k>.csv/.json (na pasta da conta)."""
    with open(pasta() / f"dados_maps_{k}.json", encoding="utf-8") as f:
        itens = json.load(f)
    if limite:
        itens = itens[:limite]
    saida_json = pasta() / f"leads_detalhados_{k}.json"
    saida_csv = pasta() / f"leads_detalhados_{k}.csv"
    resultados = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            ctx = browser.new_context(locale="pt-BR")
            page = ctx.new_page()

            for i, item in enumerate(itens, 1):
                if cancelado():
                    raise Cancelado()
                progresso(i, len(itens), item["nome"])
                log(f"[{i}/{len(itens)}] {item['nome']}")
                try:
                    resultados.append(extrair(page, ctx, item))
                except Exception as e:
                    log(f"   falhou: {e}")
                    resultados.append({"nome": item["nome"], "link": item["link"]})

                with open(saida_json, "w", encoding="utf-8") as f:
                    json.dump(resultados, f, ensure_ascii=False, indent=4)
        finally:
            browser.close()

    with open(saida_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        w.writeheader()
        for r in resultados:
            r = dict(r)
            if isinstance(r.get("redes_sociais"), dict):
                r["redes_sociais"] = "; ".join(f"{k}: {v}" for k, v in r["redes_sociais"].items())
            w.writerow(r)

    log(f"Pronto! Salvo em {saida_json.name} e {saida_csv.name} (pasta dados/)")
    return len(resultados)


def main():
    # uso: python detalhar_leads.py <busca> [N]
    ks = chaves_coletadas()
    if len(sys.argv) < 2 or sys.argv[1] not in ks:
        print("Informe a busca: python detalhar_leads.py <busca> [N]")
        print("Buscas coletadas:", ", ".join(ks) or "nenhuma (rode scraper_maps.py antes)")
        return
    detalhar(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)


if __name__ == "__main__":
    main()
