from playwright.sync_api import sync_playwright
import json
import time

from comum import DADOS, Cancelado, chave, salvar_meta

SEL_LINK = 'a[href*="/maps/place/"]'
VOLTAS_ROLAGEM = 10


def coletar(nicho, cidade, log=print, headless=False, interativo=False, cancelado=lambda: False):
    """Busca 'nicho em cidade' no Google Maps e salva dados/dados_maps_<chave>.json.

    Devolve a chave da busca. `interativo` só vale no terminal (pausa em captcha).
    """
    k = chave(nicho, cidade)
    with sync_playwright() as p:
        log("Abrindo o navegador...")
        browser = p.chromium.launch(headless=headless, args=["--start-maximized"] if not headless else [])
        try:
            page = browser.new_context(no_viewport=not headless, locale="pt-BR").new_page()

            log("Acessando o Google Maps...")
            page.goto("https://www.google.com/maps?hl=pt-BR", timeout=60000)

            # Tela de consentimento de cookies, se aparecer
            for texto in ("Aceitar tudo", "Rejeitar tudo", "Accept all", "Reject all"):
                botao = page.get_by_role("button", name=texto)
                if botao.count():
                    botao.first.click()
                    break

            busca = 'input#searchboxinput, input[name="q"], input[role="combobox"]'
            try:
                page.wait_for_selector(busca, state="visible", timeout=20000)
            except Exception:
                page.screenshot(path="erro_maps.png")
                if not interativo:
                    raise RuntimeError("Caixa de busca do Google Maps não encontrada (veja erro_maps.png). "
                                       "Tente de novo com 'Mostrar navegador' marcado.")
                input("Se houver captcha/aviso no navegador, resolva e pressione Enter...")
                page.wait_for_selector(busca, state="visible", timeout=20000)

            termo = f"{nicho} em {cidade}"
            log(f"Buscando: {termo}")
            caixa = page.locator(busca).first
            caixa.click()
            caixa.press_sequentially(termo, delay=40)
            time.sleep(0.5)
            caixa.press("Enter")

            log("Aguardando resultados...")
            page.wait_for_selector(SEL_LINK, timeout=20000)

            log("Rolando a lista...")
            page.hover(SEL_LINK)
            for i in range(VOLTAS_ROLAGEM):
                if cancelado():
                    raise Cancelado()
                page.mouse.wheel(0, 5000)
                time.sleep(1.5)

            resultados = {}
            for local in page.locator(SEL_LINK).all():
                nome = local.get_attribute("aria-label")
                link = local.get_attribute("href")
                if nome and link:
                    resultados[link] = {"nome": nome, "link": link}
        finally:
            browser.close()

    lista = list(resultados.values())
    log(f"Coleta finalizada: {len(lista)} locais únicos.")
    DADOS.mkdir(exist_ok=True)
    salvar_meta(k, nicho, cidade)
    with open(DADOS / f"dados_maps_{k}.json", "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=4)
    return k


if __name__ == "__main__":
    n = input("Digite o nicho (ex: Pizzarias): ").strip()
    c = input("Digite a cidade (ex: Guarapuava, PR): ").strip()
    k = coletar(n, c, interativo=True)
    print(f"Salvo. Próximo passo: python detalhar_leads.py {k}")
