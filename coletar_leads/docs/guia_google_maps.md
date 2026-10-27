# Automação Passo a Passo: Coletando Dados do Google Maps com Python e Playwright

Este guia mostra como criar um bot para extrair nomes e links de estabelecimentos do Google Maps usando Python.

## Passo 1: Instalar o Playwright

Abra o seu terminal ou prompt de comando e instale a biblioteca do Playwright para Python, seguida pela instalação dos navegadores necessários.

```bash
pip install playwright
playwright install
```

## Passo 2: Importar bibliotecas e iniciar o navegador

Crie um arquivo chamado `scraper_maps.py`. Usaremos a API síncrona do Playwright por ser mais simples para automações diretas. Configuramos `headless=False` para que você possa ver o navegador operando.

```python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    # Inicia o navegador visível
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Acessa o Google Maps
    page.goto("https://www.google.com/maps", timeout=60000)
```

## Passo 3: Automatizar a barra de pesquisa

O script precisa aguardar a caixa de pesquisa carregar, inserir o termo desejado e pressionar "Enter". Usamos os seletores padrão do Google Maps.

```python
termo_pesquisa = "Restaurantes em Guarapuava, PR"

page.wait_for_selector('input#searchboxinput')
page.fill('input#searchboxinput', termo_pesquisa)
page.press('input#searchboxinput', 'Enter')
```

## Passo 4: Rolar os resultados (Infinite Scroll)

O Google Maps carrega os resultados dinamicamente na barra lateral. Para coletar mais do que apenas os 5 primeiros locais, o script precisa posicionar o mouse sobre a área de resultados e simular a rolagem da roda do mouse (scroll).

```python
# Aguarda o primeiro resultado aparecer
page.wait_for_selector('a[href*="/maps/place/"]', timeout=15000)

# Posiciona o mouse sobre o primeiro item e rola para baixo várias vezes
page.hover('a[href*="/maps/place/"]')
for i in range(5): # Aumente este número para rolar mais
    page.mouse.wheel(0, 3000)
    time.sleep(1.5) # Pausa para dar tempo do Maps carregar os novos itens
```

## Passo 5: Extrair os dados dos locais

Como as classes CSS do Google Maps mudam constantemente, a forma mais segura de encontrar as listagens é buscar por links que contenham `/maps/place/`. O nome do local geralmente fica salvo no atributo `aria-label`.

```python
locais = page.locator('a[href*="/maps/place/"]').all()
dados_coletados = []

for local in locais:
    nome = local.get_attribute('aria-label')
    link = local.get_attribute('href')
    
    if nome:
        dados_coletados.append({"nome": nome, "link": link})
        
print(f"Total coletado: {len(dados_coletados)}")
```

---

## Código Completo

Aqui está a junção de todas as etapas em um script funcional e pronto para rodar.

```python
from playwright.sync_api import sync_playwright
import time
import json

def coletar_dados_maps(termo_pesquisa):
    with sync_playwright() as p:
        print("Iniciando o navegador...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Acessando o Google Maps...")
        page.goto("https://www.google.com/maps", timeout=60000)

        print(f"Pesquisando por: {termo_pesquisa}")
        page.wait_for_selector('input#searchboxinput')
        page.fill('input#searchboxinput', termo_pesquisa)
        page.press('input#searchboxinput', 'Enter')

        print("Aguardando carregamento dos resultados...")
        page.wait_for_selector('a[href*="/maps/place/"]', timeout=15000)

        print("Realizando rolagem da página...")
        page.hover('a[href*="/maps/place/"]')
        for i in range(10):
            page.mouse.wheel(0, 5000)
            time.sleep(1.5)

        print("Extraindo informações...")
        locais = page.locator('a[href*="/maps/place/"]').all()
        resultados = []

        for local in locais:
            nome = local.get_attribute('aria-label')
            link = local.get_attribute('href')
            
            if nome:
                resultados.append({
                    "nome": nome,
                    "link": link
                })

        # Remove duplicatas que o Maps às vezes gera na rolagem
        resultados_unicos = {r['link']: r for r in resultados}.values()
        lista_final = list(resultados_unicos)

        print(f"\nColeta finalizada! Foram encontrados {len(lista_final)} locais únicos.")
        
        # Salva os resultados em um arquivo JSON
        with open('dados_maps.json', 'w', encoding='utf-8') as f:
            json.dump(lista_final, f, ensure_ascii=False, indent=4)
            
        print("Dados salvos no arquivo 'dados_maps.json'.")
        
        browser.close()

# Executa a automação
coletar_dados_maps("Pizzarias em Guarapuava, PR")
```