# coletar_leads

Pipeline para coletar leads de negócios locais no Google Maps e visualizar num painel HTML.

**Primeira vez aqui?** Siga o [PASSO_A_PASSO.md](PASSO_A_PASSO.md). Quer ajudar a melhorar? Veja [CONTRIBUINDO.md](CONTRIBUINDO.md). Este repositório não traz login, sessão do WhatsApp nem leads: cada pessoa usa o seu WhatsApp (QR code próprio) e não precisa de conta do Google.

## Estrutura

```
coletar_leads/
├── server.py              # painel local: serve a página e roda a busca em segundo plano
├── fila.py                # fila de envio automático (limite diário, intervalo, horário) e follow-ups
├── respostas.py           # detecta respostas e pedidos para parar (opt-out) e atualiza o CRM
├── whatsapp_web.py        # conexão com o WhatsApp Web via Playwright (QR code, sessão salva)
├── crm_db.py              # SQLite: CRM, números verificados, fila e respostas
├── comum.py               # caminhos e nomes de arquivo compartilhados
├── scraper_maps.py        # 1. busca no Maps e salva nome + link
├── detalhar_leads.py      # 2. abre cada link e extrai telefone, site, redes, nota...
├── gerar_pagina.py        # 3. gera o painel HTML (o template está embutido no script)
├── dados/                 # uma busca = um conjunto de arquivos, identificado por <nicho>__<cidade>
│   ├── dados_maps_<busca>.json         # saída do passo 1 (nome + link)
│   ├── leads_detalhados_<busca>.json   # saída do passo 2
│   ├── leads_detalhados_<busca>.csv    # saída do passo 2 (lido pelo painel)
│   ├── meta_<busca>.json               # nicho e cidade originais da busca
│   ├── crm.db                          # banco do CRM (criado ao usar o painel; não versionar)
│   └── wa_perfil/                      # sessão do WhatsApp Web (login salvo; não versionar)
├── saida/
│   └── pagina_leads.html      # painel final (gerado, pode ser recriado)
├── docs/
│   └── guia_google_maps.md    # tutorial passo a passo do scraper
└── .env/                  # ambiente virtual Python (venv)
```

## Como usar

Ative o venv e instale o Playwright (uma vez):

```bash
pip install playwright
playwright install
```

### Pelo painel (recomendado)

```bash
python server.py
```

Abre `http://localhost:8765`. Clique em **Buscar leads**, informe nicho e cidade e acompanhe o progresso na barra lateral. Ao terminar, os leads entram na lista sozinhos, separados por nicho. A busca roda sem janela; marque "Mostrar o navegador" se o Google pedir captcha.

### Pelo terminal

1. `python scraper_maps.py` — informe nicho e cidade; gera `dados/dados_maps_<nicho>__<cidade>.json`.
2. `python detalhar_leads.py <busca> [N]` — detalha os leads (`<busca>` é o nome que o passo 1 imprime; `N` limita a quantidade).
3. `python gerar_pagina.py` — gera `saida/pagina_leads.html` estático (sem o botão de busca).

## Painel

Barra de navegação à esquerda com duas áreas:

- **Leads** — lista por nicho, pontuação por produto, ficha com acompanhamento e mensagens prontas.
  - **Copiar mensagem** e **Enviar no WhatsApp** (ícone). Com `python server.py`, o envio sai pelo WhatsApp conectado na aba WhatsApp (o painel abre a conversa na janela do Edge controlada pelo Playwright e envia; o contato só é registrado no CRM se o envio der certo). Se o número não tiver WhatsApp ou o WhatsApp não estiver conectado, aparece um aviso e nada é registrado. Na página estática (sem servidor) o botão abre `https://wa.me/55<telefone>?text=<mensagem>` no seu navegador.
  - Celular: botão em destaque. Telefone fixo: botão secundário "(fixo)", pois pode não ter WhatsApp. Sem telefone: sem botão.
- **CRM** — Kanban com as colunas **1º contato enviado** (abertura enviada, aguardando resposta), **Respondeu**, **Reunião marcada**, **Fechado** e **Sem interesse**. Cada coluna tem uma legenda e cada cartão mostra a última ação e a data do próximo follow-up (em vermelho se atrasado). Arraste o cartão para mudar o status.
  - Clicar no cartão abre uma **janela central** com: etapa no funil, dados do cliente, por que foi abordado (produto e motivos da pontuação), **passo a passo** com data, produto, técnica e o texto exato de cada mensagem enviada, próximo passo sugerido (follow-up ou fechamento, com Copiar e Enviar no WhatsApp), anotações e atalho para a ficha completa.
  - **Etapas editáveis:** o botão **+ Adicionar etapa** (no fim do quadro) cria uma coluna nova; o **lápis** renomeia; o **✕** exclui (só as criadas por você; os leads dela voltam para "1º contato enviado"). **Arraste o título** de uma coluna para mudar a posição: a linha colorida mostra onde ela vai cair, e ao soltar a ordem fica salva. As 5 etapas originais não podem ser excluídas, porque as automações usam "1º contato enviado", "Respondeu" e "Sem interesse", mas podem ser renomeadas, recoloridas e reordenadas. Ordem, nomes e cores ficam no banco (`config`, chave `colunas`) e no `localStorage` (`crm_colunas`). As etapas novas também aparecem no filtro e no seletor de etapa da ficha e do cartão.
  - **Cores por etapa:** azul (1º contato enviado), âmbar (Respondeu), roxo (Reunião marcada), verde (Fechado) e vermelho (Sem interesse). Coluna, cartão e etiquetas da lista usam a cor da etapa; ao arrastar, o cartão assume a cor da coluna nova. O quadradinho de cor no título de cada coluna troca a cor; **Restaurar cores** devolve às 5 etapas originais as cores padrão.
  - O mesmo negócio achado em duas buscas (ex.: lanchonetes e padaria) aparece uma vez só no Kanban.
- **WhatsApp** — botão **Conectar número** abre o WhatsApp Web numa janela do Edge e mostra o **QR code** no painel (também aparece na janela). Escaneie em WhatsApp > Aparelhos conectados. O login fica salvo em `dados/wa_perfil/`: nas próximas vezes conecta sozinho, sem QR. **Fechar navegador** encerra a janela sem perder a sessão. Só funciona com `python server.py`.
  - **Verificar telefones dos leads** (aba WhatsApp): abre cada número em `web.whatsapp.com/send?phone=55...` só para ver se há conta, sem enviar nada (3 a 6 s por número, com barra de progresso e botão Cancelar). Só roda com o WhatsApp conectado e só verifica os números ainda não conhecidos. O resultado (e o de cada envio feito pelo painel) fica na tabela `wa_numeros` de `dados/crm.db`.
  - Efeito nos leads: a ficha mostra "WhatsApp: sim / não / não verificado"; número **sem WhatsApp** perde o botão de enviar e reduz a pontuação do produto de atendimento no WhatsApp; número **confirmado** ganha pontos.
- **Fila** — envio automático do primeiro contato. Veja a seção abaixo.
- **Menu lateral** — recolhido (só ícones) ou expandido (ícone + nome). Clicar num item ou na seta no topo expande/recolhe; a escolha fica salva.

### WhatsApp (WhatsApp Web via Playwright)

Não precisa de Docker nem de Evolution API: o próprio Playwright controla o WhatsApp Web, como se você usasse o navegador.

- Navegador: Edge (já vem no Windows). Para usar o Google Chrome, defina `WA_NAVEGADOR=chrome`.
- A janela abre visível, pois o WhatsApp Web não aceita o Chromium sem janela do Playwright. Não feche a janela durante o uso.
- Rotas: `GET /api/whatsapp/status` (estado e QR), `POST /api/whatsapp/conectar`, `POST /api/whatsapp/enviar` (`{numero, texto}` → `{ok}` ou `{ok:false, erro: sem_whatsapp|desconectado|timeout|...}`), `POST /api/whatsapp/sair`, `GET /api/whatsapp/numeros`, `GET /api/whatsapp/verificacao`, `POST /api/whatsapp/verificar` e `POST /api/whatsapp/verificar/cancel`. Estados: `parado`, `iniciando`, `qr`, `conectado`, `erro`.
- Use um chip dedicado à prospecção, não o seu número principal. Automatizar o WhatsApp Web não é oficial, e o WhatsApp pode restringir números que mandam muitas mensagens frias.
- `dados/wa_perfil/` guarda o login: trate como senha e não compartilhe.

### Fila de envio e respostas (passos 5 e 6)

**Fila** (aba Fila, `fila.py`):
- Entra na fila por **Adicionar à fila** (em cada mensagem da ficha do lead) ou por **Enfileirar aberturas**, que pega todos os leads ainda "novos" com WhatsApp **confirmado** (rode a verificação antes). Número e etapa repetidos são ignorados.
- Cada item começa **aguardando aprovação**. Você aprova um a um, em lote ou liga "aprovar automaticamente".
- O servidor só envia se: o **envio automático está ligado**, o WhatsApp está conectado, está dentro do **horário** (padrão 08:00 às 18:00), não passou do **limite diário** (padrão 15) e já passou o **intervalo aleatório** (padrão 90 a 180 s) desde o último envio.
- Cada envio bem-sucedido vira "Contato enviado" no CRM, com texto, produto e técnica no histórico (marcado como automático) e follow-up em 2 dias. Número sem WhatsApp vira "Sem WhatsApp"; falha vira "Erro" com o motivo.
- Configuração e fila ficam em `dados/crm.db` (tabelas `fila` e `config`).

**Respostas** (`respostas.py`): a cada ~12 s a janela do WhatsApp Web lê a lista de conversas. Conversa **com mensagem não lida** cujo título bate com o telefone (ou o nome) de um lead move o cartão para **Respondeu**, guarda o texto no histórico, apaga a data de follow-up e mostra um aviso no painel. Cada resposta é tratada uma vez só (tabela `respostas`). Depois de cada envio o navegador volta à tela inicial para a resposta aparecer como "não lida".

**Follow-ups automáticos** (passo 7, `fila.py`): ao enviar a **abertura**, o painel guarda no histórico do lead o número, o nome e os dois textos seguintes (follow-up e fechamento) do mesmo produto. A cada minuto o servidor confere quem está em "Contato enviado" e ainda não respondeu e, com **Criar follow-ups** ligado:

| Quando (desde a abertura) | O que acontece |
|---|---|
| 24 h (`followup1_horas`) | entra na fila o "Follow-up (sem resposta em 24h)" |
| 3 dias (`followup2_dias`) | entra na fila o "Fechamento" |
| 7 dias (`encerrar_dias`), depois dos dois enviados | o lead vai para "Sem interesse" com o registro "Encerrado: sem resposta em 7 dias" (opção `encerrar_auto`) |

Os prazos mudam na aba Fila. Os follow-ups passam pelas mesmas regras de aprovação, limite diário, intervalo e horário. Um follow-up na fila é **cancelado** se, antes de sair, o cliente respondeu ou o lead foi encerrado. Contatos manuais antigos (feitos antes do passo 7, sem os textos guardados) não recebem follow-up automático.

**Opt-out ("parar")**: se a resposta do cliente indicar que não quer mais mensagens ("pare", "parar", "para de me mandar", "não tenho interesse", "me tira da lista", "sem interesse", "spam", "descadastrar"...), o lead vai para "Sem interesse", o que está na fila para ele é cancelado e o **número é bloqueado**: nunca mais entra na fila nem é enviado. A aba Fila lista os números bloqueados, com botão **Reativar**. O painel não responde nada ao cliente. Um simples "não" não conta como opt-out, pois pode ser resposta a uma pergunta.

**Sincronização do CRM:** o painel consulta o servidor a cada 8 s e puxa o que mudou sozinho (respostas e envios automáticos). Cada lead tem uma versão (`atu`); se o servidor mudou um lead enquanto você editava, a gravação é recusada e o painel recarrega a versão do servidor.

Rotas: `GET /api/fila`, `POST /api/fila/adicionar`, `POST /api/fila/acao` (`aprovar`, `aprovar_todas`, `pausar`, `remover`, `limpar`), `POST /api/fila/config`, `POST /api/fila/reativar`.

Outras rotas do CRM: `GET /api/crm` (leads, `colunas` e `cores`), `POST /api/colunas` (`{colunas: [{id, nome, desc, cor}]}`). Etapas criadas têm id `c_xxxxxx`.

### Onde o CRM é salvo

- **Com `python server.py`:** no SQLite `dados/crm.db` (tabelas `crm` e `config`). Qualquer navegador ou computador que abra o painel vê o mesmo CRM. Se o banco estiver vazio, o que já existia no navegador é copiado para ele na primeira abertura. O `localStorage` continua como cópia de segurança.
- **Página estática (`gerar_pagina.py`):** só no `localStorage` do navegador (chaves `crm_leads`, `crm_cores`).

API do servidor (JSON):

| Rota | O que faz |
|---|---|
| `GET /api/crm` | devolve `{crm: {link: {status, notas, proximo, hist}}, cores: {...}}` |
| `POST /api/crm` | `{crm: {...}}` — insere/atualiza os leads enviados (não apaga os outros) |
| `POST /api/cores` | `{cores: {etapa: "#rrggbb"}}` — salva as cores do Kanban |

## Roteiro (passo a passo)

Tudo roda com Playwright, sem Docker.

| # | Etapa | Estado |
|---|---|---|
| 1 | Barra de navegação expansível (Leads / CRM), Kanban arrastável e janela do cartão com histórico da abordagem | feito |
| 2 | Guardar o CRM no servidor (SQLite, `crm_db.py`) | feito |
| 3 | Conectar o WhatsApp pelo QR code (`whatsapp_web.py`, aba WhatsApp) | feito; o QR real foi gerado, falta você escanear |
| 4 | Verificar em lote se cada telefone tem WhatsApp e guardar o resultado (`wa_numeros`) | feito; lógica testada com WhatsApp simulado, falta rodar com o WhatsApp real |
| 5 | Ler respostas dos clientes e mover o cartão para "Respondeu" (`respostas.py`) | feito; lógica testada com dados simulados, falta validar a leitura da lista de conversas no WhatsApp real |
| 6 | Envio do primeiro contato com fila e aprovação manual (limite diário, intervalo aleatório, horário comercial) (`fila.py`) | feito; lógica e tela testadas com WhatsApp simulado, falta testar com o real |
| 7 | Follow-ups agendados (24 h, 3 dias, 7 dias) e opt-out ("parar") | feito; lógica testada com WhatsApp simulado, falta validar com o real |

Os 7 passos do roteiro estão implementados. Falta validar com o WhatsApp real (leitura da lista de conversas, envio, verificação de números).

Cada etapa concluída atualiza este README e a estrutura de pastas acima.

## Campos coletados

`nome`, `telefone`, `redes_sociais`, `tem_site`, `site`, `avaliacao`, `qtd_avaliacoes`, `endereco`, `horarios`, `link`.

## Notas

- Para rodar um segundo servidor sem mexer no principal (testes), defina `PAINEL_PORTA` (padrão 8765) e use outro banco. Cuidado: se já houver um `server.py` na 8765, abrir `localhost:8765` fala com ele, não com o novo.
- Os scripts usam caminhos relativos ao próprio arquivo, então funcionam de qualquer diretório.
- Para alterar o visual do painel, edite o HTML dentro da constante `HTML` em `gerar_pagina.py`; o marcador `__LEADS__` recebe os dados.
- O Google Maps muda seus seletores com frequência; se o `detalhar_leads.py` voltar campos vazios, revise os seletores.
- Use os dados respeitando a LGPD e os termos do Google.
