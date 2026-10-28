# Planos: proposta e viabilidade

Proposta de três planos para vender o painel (busca de leads no Google Maps, CRM, mockups com IA e prospecção pelo WhatsApp). Números de mercado pesquisados em outubro de 2026; os de WhatsApp e Gemini vêm de fornecedores e blogs, não da documentação oficial, então confirme antes de anunciar.

## Os três planos

| | **Largada** | **Tração** | **Escala** |
|---|---|---|---|
| Para quem | profissional sozinho começando a prospectar | pequena agência ou loja com vendedores | agência com equipe e várias frentes |
| Preço sugerido | R$ 97/mês | R$ 197/mês | R$ 397/mês |
| Usuários (equipe) | 1 | 3 | 8 |
| Números de WhatsApp conectados | 1 | 3 | 6 |
| Leads extraídos do Maps por mês | 1.000 | 5.000 | 15.000 |
| Buscas rodando ao mesmo tempo | 1 | 1 | 2 |
| Primeiros contatos por dia (soma dos números) | até 40 | até 120 | até 300 |
| Follow-ups automáticos e opt-out | sim | sim | sim |
| Verificar se o telefone tem WhatsApp | sim | sim | sim |
| CRM Kanban com etapas personalizadas | sim | sim | sim |
| Mockups com IA | com a chave grátis do próprio cliente | idem + fotos do Pexels | idem + fotos criadas pela IA (o cliente paga o Google) |
| Distribuir leads entre vendedores | não | sim | sim + relatório por vendedor |
| Suporte | e-mail | WhatsApp | prioritário + reunião de implantação |

Extras para qualquer plano: **número de WhatsApp adicional R$ 39/mês**, **usuário adicional R$ 29/mês**. Plano anual: 2 meses grátis.

Nomes alternativos, se preferir outro tom: *Radar / Alcance / Domínio* ou, brincando com o nome do projeto, *Primeiro PIX / PIX Recorrente / PIX Todo Dia*.

## Por que esses números

### Mercado (preços publicados em reais)

Ferramentas parecidas cobram de R$ 50 a R$ 400 por mês na faixa que interessa. Exemplos: buscaProfissa R$ 49,90 (1 número) a R$ 199,90 (5 números); VProspect R$ 97 / R$ 297 / R$ 497; ProspectaZap R$ 89 / R$ 297 / R$ 897; LeadMap Pro R$ 97 / R$ 197 / R$ 397 (com CRM e IA só no último); SocialHub R$ 99 (1 usuário, 1 WhatsApp) a R$ 399 (5 usuários); SpeedLead cobra R$ 29,90 por número extra. O diferencial deste painel é juntar no mesmo lugar a busca, o CRM, os follow-ups e o **mockup de site com IA**, que nenhum dos citados oferece.

### Quantos contatos por dia (WhatsApp Web, o modo atual)

- Não existe número oficial seguro. O WhatsApp bane por **denúncias e baixa taxa de resposta**, não por uma contagem fixa. Mensagem fria em massa é o caminho mais rápido para perder o número.
- Fornecedores recomendam: número novo começa com no máximo ~50 mensagens por dia, menos de 30 por hora, e passa por 3 a 30 dias de "aquecimento" antes de subir.
- Por isso o limite proposto é de **~40 primeiros contatos por número por dia** (os follow-ups são poucos e vão para quem já recebeu a abertura). Número novo deve começar com 15 a 20 por dia na primeira semana (a fila já tem limite diário, intervalo de 90 a 180 s e horário comercial).
- **Vários números:** dá para conectar vários. Cada um é uma janela de navegador própria com a sua sessão. Espalhar o volume entre números reduz o risco de cada um, mas não elimina: cada número ainda precisa de taxa de resposta boa. Cada número precisa ser um chip real do cliente.

### API oficial do WhatsApp (alternativa para o plano Escala no futuro)

- Começa com **250 pessoas por dia** (por portfólio da Meta, não por número; desde outubro de 2025 todos os números do portfólio dividem o mesmo limite) e sobe com verificação e qualidade.
- Cada mensagem de marketing no Brasil custa cerca de **US$ 0,0625 (~R$ 0,32)**, mais a margem do intermediário (15 a 25%).
- Ela **exige consentimento (opt-in)** para mensagens de marketing, então também não resolve a prospecção fria. Serve para quem já é contato do cliente.

### Gemini (mockups)

- Com a **chave grátis do próprio cliente**, o custo para você é zero e a cota é dele. Os guias falam em cerca de 1.500 pedidos por dia nos modelos Flash, mas há fontes com números bem menores para alguns modelos; nos testes deste projeto, o 3.5 Flash funcionou na conta gratuita.
- Os modelos **Pro** e a **criação de imagens** saíram do plano gratuito (o teste com a sua chave confirmou: imagem respondeu "cota excedida, ative o faturamento").
- Se um dia quiser incluir IA no plano com a sua chave, o custo é de centavos por mockup, mas a sua cota vira o gargalo de todos os clientes.

### Servidor (o que limita números e buscas)

- Medido aqui: cada janela de WhatsApp Web ocupa **~260 MB** na tela do QR (2 janelas = 516 MB). Logado, com conversas, deve passar disso (não medido).
- Cada busca no Maps abre outro navegador, e leva alguns segundos por lead (abre a ficha, espera carregar, às vezes visita o site): uma busca de 100 leads leva da ordem de 10 minutos.
- Na prática, um servidor de 8 GB de memória atende ~12 a 15 números conectados mais 2 buscas simultâneas. Por isso números e buscas simultâneas são os limites que mais pesam no custo, e por isso o número extra é cobrado.

## Riscos para deixar claros no contrato e na tela

- Automação pelo WhatsApp Web não é oficial: o WhatsApp pode banir o número, e a responsabilidade pelo conteúdo e pela lista é do cliente.
- O painel já ajuda: limite diário, intervalo humano, horário comercial, bloqueio automático de quem pede para parar.
- LGPD: usar só dados públicos de empresas, oferecer saída (opt-out) e não insistir com quem recusou.
- Muitos números conectados a partir do mesmo servidor (mesmo IP) é um risco não medido.

## O que precisa ser construído

| Passo | O que entra |
|---|---|
| 3 | **Contas de clientes (empresas):** cada cliente vira uma conta com plano e dados separados (leads, CRM, fila, chaves). Você vira o **administrador da plataforma**; o dono de cada conta convida a própria equipe até o limite do plano. O painel Admin passa a listar **contas** (plano, uso do mês, situação) e, dentro delas, os usuários. |
| 4 | **Vários números de WhatsApp por conta:** uma janela por número, a fila reparte os envios entre os números e respeita o limite de cada um. |
| 5 | **Limites do plano aplicados:** contadores do mês (leads, contatos, números, usuários), aviso aos 80% e bloqueio ao chegar no limite, com opção de comprar extra. |
| 6 | **Cobrança:** assinatura com PIX e cartão (Asaas, Mercado Pago ou Stripe), teste grátis de 7 dias e bloqueio automático por falta de pagamento. |
| 7 | **Hospedagem:** servidor Linux, HTTPS, backup diário e monitoramento. |

## Fontes

- Limites da API oficial: [respond.io](https://respond.io/help/whatsapp/whatsapp-messaging-limits), [chatarmin](https://chatarmin.com/en/blog/whats-app-messaging-limits), [ActiveCampaign](https://help.activecampaign.com/hc/en-us/articles/21826249568540-WhatsApp-Messaging-Limits-What-You-Need-to-Know), [Clickatell](https://clickatell.com/help-center/whatsapp/sending-receiving-messages/messaging-limits-whatsapp-business/), [uptail](https://www.uptail.ai/blog/whatsapp-business-message-limits-2026-broadcast-caps-tier-progression-what-happens-when-you-hit-the-ceiling)
- Preço da API no Brasil: [Message Central](https://www.messagecentral.com/blog/whatsapp-business-api-pricing-brazil), [whautomate](https://whautomate.com/whatsapp-business-api-pricing-brazil), [MarTechCost](https://martechcost.com/whatsapp-pricing/brazil), [Blueticks](https://blueticks.co/blog/whatsapp-business-pricing-marketing-messages-2026), [CRMiner](https://www.crminer.com.br/en/blog/whatsapp-business-api-cobranca-outubro-2026)
- Aquecimento e banimento: [Whapi.Cloud](https://whapi.cloud/blog/pt/how-to-avoid-whatsapp-ban-2026), [Whapi.Cloud (aquecimento)](https://whapi.cloud/blog/pt/how-to-warm-up-whatsapp-number-real-inbound-conversations), [Chatsac](https://chatsac.com/blog/aquecer-chip-whatsapp-business/), [SocialHub](https://www.socialhub.pro/blog/como-configurar-warm-up-numero-whatsapp-business/), [Eazybe](https://eazybe.com/br/blog/whatsapp-pode-banir-meu-numero-marketing)
- Gemini grátis: [scriptbyai](https://www.scriptbyai.com/gemini-api-free-tier-limits/), [tinkerllm](https://tinkerllm.com/blog/gemini-api-free-tier-limits-rate-quotas/), [pecollective](https://pecollective.com/tools/gemini-free-tier-guide/), [CloudZero](https://www.cloudzero.com/blog/gemini-pricing/)
- Concorrentes: [buscaProfissa](https://buscaprofissa.com.br/), [VProspect](https://vprospect.com.br/), [ProspectaZap](https://prospecta-zap-web.com.br/), [LeadMap Pro](https://leadmappro.com.br/), [SocialHub](https://www.socialhub.pro/funcionalidades/crm-para-whatsapp/), [SpeedLead](https://speedlead.com.br/), [Garimpo](https://garimpoleads.com/), [VexLK](https://leadvexlk.app/), [CRM Whats Pro](https://crmwhatspro.com/)
