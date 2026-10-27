# Passo a passo: rodar o coletar_leads na sua máquina

Tudo roda **localmente, no seu computador**. Este repositório não traz nenhum login, sessão, banco ou lead de ninguém: você começa do zero e os seus dados ficam só com você.

## O que você precisa

- Windows, macOS ou Linux
- Python 3.10 ou mais novo
- Microsoft Edge ou Google Chrome instalado (usado para o WhatsApp Web)
- Um celular com WhatsApp (para escanear o seu próprio QR code, só se for usar os envios)

## 1. Baixar o projeto

```bash
git clone https://github.com/Magos-Dev/Aulas-youtube.git
cd Aulas-youtube
git checkout aula-002-coletar-leads
cd coletar_leads
```

## 2. Criar o ambiente e instalar

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

## 3. Abrir o painel

```bash
python server.py
```

O painel abre em `http://localhost:8765`.

## 4. Buscar leads (Google Maps)

1. Clique em **Buscar leads**.
2. Informe o nicho (ex.: `pizzaria`) e a cidade (ex.: `Curitiba, PR`).
3. Acompanhe o progresso na barra lateral. Ao terminar, os leads aparecem na lista.

**Não é preciso entrar com e-mail e senha do Google.** O Google Maps é consultado como visitante, sem login. Por isso nenhuma conta do Google é pedida nem guardada pelo projeto.

Se o Google mostrar um captcha, marque **Mostrar o navegador** e resolva na janela que abrir.

## 5. Conectar o seu WhatsApp (opcional)

1. No painel, abra a aba **WhatsApp** e clique em **Conectar número**.
2. No celular: WhatsApp > Aparelhos conectados > Conectar um aparelho, e escaneie o QR code.
3. O login fica salvo em `dados/wa_perfil/`, **só no seu computador** (a pasta está no `.gitignore`).

> Use o seu próprio número. Nunca envie `dados/wa_perfil/` para ninguém: quem tem essa pasta acessa o seu WhatsApp.

## 6. Usar o CRM e a fila

- **CRM**: arraste os cartões entre as etapas; use **+ Adicionar etapa** para criar novas.
- **Fila**: define limite diário, intervalo e horário de envio. Comece com limites baixos.
- Quem responde "pare" é bloqueado automaticamente.

Veja o [README.md](README.md) para o detalhe de cada aba.

## Uso responsável

Respeite a LGPD e os termos do WhatsApp e do Google. Envie só para quem faz sentido receber, não faça disparo em massa e sempre aceite pedidos para parar.

## Problemas comuns

| Sintoma | O que fazer |
|---|---|
| `playwright` não encontrado | Ative o venv (passo 2) e rode `pip install -r requirements.txt` |
| O WhatsApp Web não abre | Instale o Edge/Chrome, ou defina `WA_NAVEGADOR=chrome` antes de `python server.py` |
| Porta 8765 ocupada | Defina `PAINEL_PORTA=8800` antes de rodar |
| Quero recomeçar do zero | Apague `dados/crm.db` e `dados/wa_perfil/` |
