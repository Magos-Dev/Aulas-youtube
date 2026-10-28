# coletar_leads

Pipeline para coletar leads de negócios locais no Google Maps e visualizar num painel HTML.

## Estrutura

```
coletar_leads/
├── server.py              # painel local: serve a página e roda a busca em segundo plano
├── auth.py                # usuários, senhas (hash PBKDF2), sessões, equipe da conta
├── contas.py              # contas das empresas clientes, banco da plataforma e migração
├── planos.py              # planos Largada, Tração e Escala (preço e limites; edite aqui)
├── pagina_login.py        # tela de login, cadastro da empresa e primeiro acesso (/login)
├── fila.py                # fila de envio automático (limite diário, intervalo, horário) e follow-ups
├── respostas.py           # detecta respostas e pedidos para parar (opt-out) e atualiza o CRM
├── whatsapp_web.py        # conexão com o WhatsApp Web via Playwright (QR code, sessão salva)
├── crm_db.py              # SQLite: CRM, números verificados, fila e respostas
├── gemini.py              # chave do Gemini e geração do mockup de site com IA
├── fotos.py               # fotos do mockup: Pexels (grátis) ou criadas pela IA (pago)
├── mockups.py             # mockups salvos por lead (o site pronto + o código para editar depois)
├── comum.py               # pasta da conta atual (por thread) e nomes de arquivo compartilhados
├── scraper_maps.py        # 1. busca no Maps e salva nome + link
├── detalhar_leads.py      # 2. abre cada link e extrai telefone, site, redes, nota...
├── gerar_pagina.py        # 3. gera o painel HTML (o template está embutido no script)
├── dados/                 # nada aqui vai para o Git
│   ├── plataforma.db                   # contas, usuários e sessões de login
│   ├── contas/<id>/                    # tudo de uma empresa cliente (a sua é a conta 1)
│   │   ├── dados_maps_<busca>.json         # saída do passo 1 (nome + link); busca = <nicho>__<cidade>
│   │   ├── leads_detalhados_<busca>.json   # saída do passo 2
│   │   ├── leads_detalhados_<busca>.csv    # saída do passo 2 (lido pelo painel)
│   │   ├── meta_<busca>.json               # nicho e cidade originais da busca
│   │   ├── crm.db                          # CRM, fila, respostas e configurações (inclusive chaves do Gemini/Pexels)
│   │   └── wa_perfil/                      # sessão do WhatsApp Web da empresa
│   ├── contas_excluidas/               # pastas de contas excluídas (dá para recuperar)
│   └── backup/                         # cópia do crm.db antigo feita na migração
├── saida/
│   └── pagina_leads.html      # painel final (gerado, pode ser recriado)
├── docs/
│   ├── guia_google_maps.md    # tutorial passo a passo do scraper
│   └── planos.md              # proposta de planos e pesquisa de viabilidade
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

Abre `http://localhost:8765` (vai para a tela de login; veja a seção abaixo). Clique em **Buscar leads**, informe nicho e cidade e acompanhe o progresso na barra lateral. Ao terminar, os leads entram na lista sozinhos, separados por nicho. A busca roda sem janela; marque "Mostrar o navegador" se o Google pedir captcha.

### Login e usuários

Todo o painel exige login (página `/login`). Roteiro:

| Passo | O que entra | Situação |
|---|---|---|
| 1 | Login, cadastro, primeiro administrador, proteção de todas as páginas e rotas | feito |
| 2 | Painel do admin: listar usuários, aprovar, bloquear, trocar senha, mudar papel, excluir | feito |
| 3 | Contas de clientes (empresas) com plano e dados separados; equipe por conta; admin da plataforma | feito |
| 4 | Vários números de WhatsApp por conta, com a fila repartindo os envios | pendente |
| 5 | Limites do plano aplicados (leads, contatos/dia, números, usuários) | pendente |
| 6 | Cobrança (PIX e cartão, teste grátis) | pendente |
| 7 | Hospedagem: HTTPS, cookies seguros, backup do banco | pendente |

Proposta de planos (Largada, Tração, Escala), limites e a pesquisa de viabilidade: [docs/planos.md](docs/planos.md).

Contas de clientes (passo 3):

- **Cada empresa cliente é uma conta** com plano (Largada, Tração ou Escala, definidos em `planos.py`) e **dados separados**: leads, CRM, fila, respostas, configurações (inclusive a chave do Gemini e do Pexels) e a sessão do WhatsApp ficam em `dados/contas/<id>/`. Contas, usuários e sessões de login ficam em `dados/plataforma.db`. Uma empresa nunca vê nem altera os dados de outra.
- **Como o isolamento funciona:** no começo de cada pedido o servidor define a conta da sessão (`comum.definir_conta`) e todo o código descobre a pasta por `comum.pasta()`. As tarefas em segundo plano (busca no Maps, verificação de números, a sessão do WhatsApp de cada conta e a fila) definem a conta delas ao começar. Com o servidor rodando, uma operação sem conta definida dá erro em vez de cair na pasta de outra empresa. A fila atende todas as contas ativas, uma de cada vez, cada uma com o próprio intervalo, limite e WhatsApp.
- **Papéis:** `papel` é da plataforma (`admin` = você, vê todas as empresas; `usuario` = cliente). `papel_conta` é dentro da empresa (`dono` gerencia a equipe; `membro` usa o painel).
- **Cadastro (Criar conta):** a pessoa informa a empresa, escolhe o plano e cria o login; a **conta** nasce **pendente** e ninguém dela entra até você aprovar na aba **Clientes**.
- **Aba Clientes** (só admin; antiga "Admin"): visão **Contas** (empresa, dono, plano com seletor para trocar, situação, usuários usados/limite, leads coletados, data) com **Aprovar/Recusar**, **Ver usuários**, **Renomear**, **Bloquear/Desbloquear** (bloquear derruba as sessões da empresa e fecha o WhatsApp dela) e **Excluir** (só contas bloqueadas; a pasta vai para `dados/contas_excluidas/`). **+ Nova conta** cria a empresa já ativa com o dono e uma senha temporária. Visão **Usuários**: todas as pessoas com a empresa e o papel, e as ações do passo 2 (o dono de uma conta não pode ser excluído por ali: exclua a conta). O contador laranja soma contas e usuários pendentes. Você não pode bloquear nem excluir a sua própria conta.
- **Aba Equipe** (todos): mostra o plano da empresa (preço, usuários usados/limite, números de WhatsApp, leads por mês, contatos por dia) e as pessoas. O **dono** usa **+ Adicionar pessoa** (senha temporária; a pessoa cria a dela no primeiro acesso) e pode bloquear, trocar a senha e remover membros. O limite de usuários do plano já vale: com o plano cheio, adicionar é recusado. Membros só veem.
- **Migração automática:** na primeira vez que o `server.py` novo roda, se existirem dados no formato antigo (`dados/crm.db`, CSVs, `wa_perfil/` soltos em `dados/`), eles viram a **conta 1** (plano Escala) com você como dono e admin. Antes, o `crm.db` é copiado para `dados/backup/`. Os usuários do `crm.db` antigo vão para `plataforma.db` com a mesma senha. Feche a janela do WhatsApp e o servidor antigo antes de rodar o novo (arquivos abertos não podem ser movidos). Testado numa cópia dos dados reais: 135 leads, 39 cartões do CRM, 5 itens da fila e a sessão do WhatsApp foram para a conta 1.
- **Scripts de terminal** (`scraper_maps.py`, `detalhar_leads.py`, `gerar_pagina.py`) usam a conta 1 (ou a de `PAINEL_CONTA`). Para testes, `PAINEL_DADOS` troca a pasta `dados/` inteira.
- Rotas: `GET /api/planos` (pública), `GET /api/equipe`, `POST /api/equipe/criar` (`{nome, email, senha?}`), `POST /api/equipe/membro` (`{id, acao}`: `aprovar`, `bloquear`, `desbloquear`, `trocar_senha`, `excluir`), `GET /api/admin/contas`, `POST /api/admin/conta` (`{id, acao}`: `aprovar`, `bloquear`, `desbloquear`, `plano` + `plano`, `renomear` + `nome`, `excluir`), `POST /api/admin/criar-conta` (`{empresa, plano, nome, email, senha?}`). `POST /api/auth/cadastro` agora recebe `{empresa, nome, email, senha, plano}` e `POST /api/auth/setup` recebe `empresa`.

Como funciona (passo 1):

- **Primeiro acesso:** enquanto não existe nenhum usuário, `/login` mostra **Primeiro acesso** e a primeira conta criada é o **administrador**. Por segurança isso só funciona no próprio computador do servidor (`localhost`); pedidos que chegam por túnel ou proxy (cabeçalhos `X-Forwarded-For`, `Cf-Connecting-Ip`, `X-Real-Ip`, `Forwarded`) recebem 403.
- **Criar conta:** qualquer pessoa pode se cadastrar (nome, e-mail, senha de 8+ caracteres), mas a conta nasce **pendente** e só entra depois que o administrador aprovar (passo 2). Contas **bloqueadas** também não entram. Isso evita que um estranho use os seus leads, o seu WhatsApp e a sua chave do Gemini.
- **Senhas:** guardadas como hash PBKDF2-SHA256 (600 mil iterações, sal próprio por senha) na tabela `usuarios` de `dados/plataforma.db` (era `dados/crm.db` antes do passo 3). Ninguém consegue ler a senha, nem o administrador; quando alguém esquecer, o admin define uma senha nova (passo 2).
- **Sessão:** cookie `painel_sessao` (HttpOnly, SameSite=Lax, 7 dias; ganha `Secure` quando o acesso chega por HTTPS via `X-Forwarded-Proto: https`, Cloudflare ou `PAINEL_HTTPS=1`). No banco (tabela `sessoes`) fica só o hash SHA-256 do código. **Sair** apaga a sessão.
- **Proteção:** sem sessão, páginas redirecionam para `/login` e rotas `/api/...` respondem 401 (o painel volta sozinho para o login). Depois de 5 senhas erradas em 10 minutos, o mesmo IP fica 10 minutos sem tentar. A mensagem de erro não diz se o e-mail existe.
- **No painel:** o rodapé da barra lateral mostra quem está logado (inicial, nome e papel; com o menu aberto) e o botão **Sair**.
- Rotas: `GET /login`, `GET /api/auth/estado` (`tem_usuarios`, `local`, `logado`), `GET /api/auth/eu`, `POST /api/auth/login` (`{email, senha}`), `POST /api/auth/cadastro` (`{nome, email, senha}`), `POST /api/auth/setup` (primeiro admin), `POST /api/auth/sair`, `POST /api/auth/minha-senha` (`{atual, nova}`).

Painel do admin (passo 2):

- **Menu Admin** (escudo na barra lateral): só aparece para administradores, com um contador laranja de **cadastros aguardando aprovação** (atualiza a cada minuto). O servidor confere o papel em toda chamada `/api/admin/...` (usuário comum recebe 403).
- **Lista de usuários:** nome, e-mail, papel, situação (Pendente, Ativo, Bloqueado; "senha temporária" quando a pessoa ainda não criou a dela), data de criação e último acesso. Filtros por situação com contagem e busca por nome ou e-mail. Pendentes aparecem primeiro, com fundo amarelado. No celular a tabela vira cartões.
- **Ações:** **Aprovar** / **Recusar** (pendentes; recusar apaga a conta), **Bloquear** (a pessoa sai na hora: as sessões dela são apagadas) / **Desbloquear**, **Trocar senha**, **Tornar admin** / **Tirar admin**, **Excluir**. As ações destrutivas pedem confirmação. Na sua própria linha (marcada "você") só aparece **Trocar senha**: o servidor recusa bloquear, excluir ou tirar o admin de si mesmo, e também recusa deixar o sistema sem nenhum administrador ativo.
- **+ Novo usuário:** o admin cria a conta (nome, e-mail, papel) já **ativa**. **Trocar senha** e **Novo usuário** geram uma **senha temporária** fácil de ditar (ex.: `ecm2-vhhw-mhfb`, sem 0/O/1/l) ou usam a que o admin digitar; ela aparece **uma única vez** com botão Copiar. Quem entra com senha temporária vê a janela **Crie a sua senha** e só usa o painel depois de trocar (não dá para fechar). Trocar a senha de alguém encerra as sessões abertas dessa pessoa.
- **Trocar a minha senha:** qualquer usuário clica no próprio nome no rodapé do menu. Pede a senha atual; as outras sessões dele são encerradas.
- Coluna `trocar_senha` em `usuarios` (migração automática). Rotas: `GET /api/admin/usuarios`, `POST /api/admin/usuario` (`{id, acao}`: `aprovar`, `bloquear`, `desbloquear`, `tornar_admin`, `tornar_usuario`, `trocar_senha` (+ `senha` opcional), `excluir`), `POST /api/admin/criar` (`{nome, email, papel, senha?}`).
- **Celular:** o menu de baixo ganhou Admin e Sair; corrigido um defeito antigo em que tocar num item do menu no celular aplicava o layout de "menu aberto" do computador e espremia a tela.

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
- **Criar mockup** (entre CRM e Fila) — gera uma prévia de site de uma página para o lead escolhido, com nome, nicho, telefone, endereço, horários, nota do Google e botão de WhatsApp. Três estilos (claro, escuro, quente), prévia na tela, **Abrir em nova aba**, **Baixar .html** (arquivo único para mandar ao cliente) e **Copiar mensagem de envio**. O mockup traz uma faixa "Mockup de demonstração". O modelo rápido roda inteiro no navegador, sem servidor. Dá para enviar a **logo** do cliente (até 1,5 MB), que entra no cabeçalho.
  - **✨ Criar com IA (Gemini)** (só com `python server.py`): assistente em 4 passos, com um cabeçalho **Configurações da IA** em cima. Depois de gerar, as 4 caixas **recolhem sozinhas** e a prévia sobe; o cabeçalho mostra o resumo (modelo · estilo · tom · fotos · nº de seções). Clique na **setinha para baixo** (ou em qualquer ponto do cabeçalho) para expandir de novo e ajustar; clique de novo para recolher. **1.** Cole a sua chave gratuita do Gemini, criada em [aistudio.google.com/apikey](https://aistudio.google.com/apikey); o servidor testa a chave antes de salvar e ela fica só em `dados/crm.db` (tabela `config`, chave `gemini`), nunca volta para o navegador nem vai para o GitHub. **Modelo de IA:** depois de salvar a chave, o seletor lista todos os modelos de texto que aquela chave pode usar, consultados no Google (`GET /api/gemini/modelos`), em dois grupos: **Gratuitos** (Flash, Flash-Lite e Gemma, que têm cota grátis no AI Studio, com limite por minuto e por dia) e **Pagos** (Pro e similares, cobrados no faturamento da conta Google). A classificação é uma estimativa pelo nome do modelo; o Google pode mudar as cotas. Trocar o modelo salva na hora (`POST /api/gemini/modelo`). O padrão é `gemini-3.5-flash` (o `gemini-2.5-flash`, padrão antigo, não é mais aceito para chaves novas e é trocado automaticamente). Se o modelo escolhido responder "indisponível", "sobrecarregado" ou demorar demais, o painel tenta sozinho `gemini-3.5-flash`, `gemini-flash-latest`, `gemini-3.5-flash-lite` e `gemini-flash-lite-latest`, e o aviso final diz qual modelo gerou o mockup. **2.** Estilo, tom e cor (ou a IA escolhe). **3.** Seções da página (topo, sobre, serviços, cardápio, galeria, diferenciais, horários, localização, contato, perguntas frequentes). **4.** Logo e pedidos extras. O pedido pode ser escrito ou **falado** pelo botão de **microfone** no canto do campo (vermelho pulsando = ligado; toque de novo para terminar). O texto entra depois do que já estava escrito e dá para corrigir antes de gerar. Dois modos:
    - **Ao vivo (Chrome e Edge):** ditado do próprio navegador; as palavras aparecem no campo enquanto você fala. Quando o navegador encerra o ditado após um silêncio, o painel religa sozinho até você tocar de novo. Se o ditado não estiver disponível (erro de rede/serviço ou fechar logo ao abrir), o painel troca sozinho para o modo por trechos.
    - **Por trechos com o Gemini (Brave, Firefox e reserva):** precisa da chave salva. O painel grava com `MediaRecorder` (webm/opus) e mede o volume do microfone: a cada **pausa** na fala (0,7 s) o trecho é enviado ao Gemini (`POST /api/voz/transcrever`) e o texto entra no campo enquanto você continua falando (cerca de 3 s depois da pausa). Trechos longos sem pausa são cortados a cada 10 s; a gravação vai até 3 minutos. **Trechos sem voz não são enviados**: com silêncio o Gemini inventa frases (ex.: "aquecimento global"), por isso o painel só manda trechos com pelo menos 0,3 s acima do ruído de fundo, e o Gemini é instruído a responder `VAZIO` quando não houver fala clara. No Brave o ditado ao vivo do navegador não funciona, então ele usa sempre este modo. **Gerar com Gemini** manda só os dados do lead e as escolhas; a logo não é enviada ao Google: a IA coloca o marcador `{{LOGO}}` e o painel troca pela imagem. **Tecnologia do mockup:** um único `.html` que abre direto no navegador, sem build: HTML5 + Tailwind CSS (CDN) + CSS próprio + JavaScript puro (menu mobile, rolagem suave, animações de entrada) + Google Fonts + ícones Lucide. TypeScript, React e Node não são usados de propósito: exigiriam compilar e hospedar, e o arquivo precisa abrir sozinho no celular do cliente. O resultado é recebido aos poucos (streaming), então modelos lentos não são cortados por tempo. **Segurança:** como o mockup tem JavaScript, ele roda sempre isolado: a prévia é um `iframe sandbox="allow-scripts"` sem `allow-same-origin`, e **Abrir em nova aba** abre uma página que só contém esse iframe; o painel injeta uma Content-Security-Policy que só libera os CDNs acima e bloqueia qualquer conexão (`connect-src 'none'`).
  - **Personalizar** (passo 2): desmarcar **A IA escolhe tudo** abre um painel com: **Cor principal**; **Adicionar HTML** (entra antes do `<footer>`, exatamente como escrito), **Adicionar CSS** (entra no fim da página, depois do Tailwind, então vale por cima do estilo da IA) e **Adicionar JS** (roda no fim da página); **Bibliotecas** prontas com versão fixa (GSAP + ScrollTrigger, AOS, Swiper, GLightbox, Animate.css, Alpine.js) e um campo para outros links `https://` `.js`/`.css` (as origens desses links entram na Content-Security-Policy do mockup); **Imagens** do cliente (até 20, reduzidas no navegador para no máx. 1600 px), cada uma com o **lugar** (topo, cardápio, produtos, serviços, galeria, sobre, equipe, antes e depois, outro) e uma **legenda** (o nome do arquivo vira a legenda inicial). As imagens não vão para o Google: a IA recebe marcadores `{{IMG1}}`, `{{IMG2}}`... com o lugar e a legenda (em cardápio/produtos ela monta cards com foto e nome, sem inventar preço), e o painel troca pelos arquivos depois. O código do usuário também é mostrado à IA, para ela combinar o visual, mas quem insere é o painel (`gemini._injetar`), para entrar exatamente como foi escrito. Marcar de novo **A IA escolhe tudo** esconde o painel e ignora essas escolhas.
  - **Salvar sem IA** (montar à mão, quando a IA der erro ou para usar o seu próprio modelo): com **A IA escolhe tudo** desmarcado, escreva o HTML, CSS e JS, marque as bibliotecas e adicione as imagens, e clique em **Salvar mockup sem IA** (no fim do Personalizar) ou **Salvar sem IA** (caixa 4, ao lado de Gerar com Gemini). Nada vai para a IA. O HTML pode ser uma página completa (`<!doctype html>...`; as bibliotecas entram no `<head>` e o CSS/JS antes do `</body>`) ou só o conteúdo (o painel cria a página em volta). Cada imagem tem um código (`{{IMG1}}`, `{{IMG2}}`..., clique para copiar) para usar no HTML, ex. `<img src="{{IMG1}}">`; as que não forem usadas entram numa galeria no fim, agrupadas pelo lugar escolhido. Dados do lead que o código pode usar (o mesmo código serve de modelo para qualquer lead): `{{NOME}}`, `{{TELEFONE}}`, `{{WHATSAPP}}` (link wa.me), `{{ENDERECO}}`, `{{CIDADE}}`, `{{BAIRRO}}`, `{{NICHO}}`, `{{NOTA}}`, `{{AVALIACOES}}`, `{{HORARIOS}}` (lista `<ul class="horarios">`) e `{{LOGO}}`.
  - **Mockups salvos por lead:** o mockup montado à mão e o gerado pela IA ficam guardados no servidor, na pasta da conta (`dados/contas/<id>/mockups/<hash>.html` + `.json` com o rascunho: HTML, CSS, JS, bibliotecas, imagens, cor e logo). Ao escolher um lead que já tem mockup, a prévia mostra o salvo (o lead aparece como "· mockup salvo" na lista) e uma faixa com **Editar o código salvo** (devolve tudo para os campos) e **Ver o modelo rápido**. Salvar de novo substitui o anterior. Rotas: `GET /api/mockups`, `GET /api/mockup?lead=<link>`, `POST /api/mockup/salvar` (`{lead, nome, html, rascunho, origem}`; pedidos até 40 MB).
  - **Fotos** (passo 2): **Fotos de banco (Pexels, grátis)**: a IA escreve marcadores `{{FOTO:descrição em inglês}}` e `fotos.py` troca cada um por uma foto real do Pexels (sem repetir), usando a chave grátis de [pexels.com/api](https://www.pexels.com/api/) salva no passo 1 (`POST /api/fotos/chave`, fica em `config`, chave `pexels`). **Fotos criadas pela IA (pago)**: gera até 4 fotos exclusivas com o modelo de imagem escolhido no passo 1 (Nano Banana); o plano gratuito do Gemini não inclui imagens (o Google recusa com 429 sem faturamento ativo), e nesse caso o painel avisa e usa Pexels ou gradientes. **Sem fotos**: gradientes e ícones.
  - **Modelos testados com uma chave gratuita nova (out/2026):** funcionam 3.5 Flash (padrão), 3.6 Flash, 3 Flash, Flash-Lite e Gemma 4; a linha **2.5** aparece na lista do Google mas responde 404 ("no longer available to new users") e foi tirada da lista; Pro, 4 Argon e Omni exigem faturamento; 3.7/3.8 Flash e Flash Latest às vezes respondem 503 (sobrecarga). Quando o modelo escolhido falha, o painel usa um gratuito da reserva e mostra um aviso dizendo qual usou e por quê. Erros comuns (chave recusada, limite gratuito atingido, modelo inexistente) aparecem em português. Rotas: `GET /api/gemini`, `POST /api/gemini/chave` (`{chave, modelo}`; chave vazia remove), `POST /api/mockup/gerar` (`{lead, opcoes}`).
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
