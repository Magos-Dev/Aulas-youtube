# 📋 Documento de Briefing & Arquitetura Web: Aura Café

---

## 1. Visão Geral do Projeto
- **Nome da Marca:** Aura Café
- **Segmento:** Cafeteria Artesanal de Luxo & Microtorrefação Especial
- **Proposta de Valor:** Grãos de altitude com pontuação SCA 88+, extrações manuais de precisão e ambiente sensorial refinado (Dark Luxury).
- **Objetivo do Site:**
  - Posicionar a marca com autoridade visual imediata.
  - Exibir o cardápio curado e a carta de cafés sazonais.
  - Estimular reservas de mesas e pedidos de grãos premium via WhatsApp.
- **Público-Alvo:** Profissionais liberais, executivos, entusiastas de café especial e público que consome experiências gastronômicas premium.

---

## 2. Identidade Visual & Design System

### 🎨 Paleta de Cores
| Aplicação | Nome | Hex | Descrição |
| :--- | :--- | :--- | :--- |
| **Fundo Primário** | Carvão Profundo | `#0C0C0E` | Base escura para criar contraste e elegância |
| **Superfícies / Cards** | Grafite Nobre | `#16161A` | Cor de fundo para seções secundárias e cards |
| **Destaque Principal** | Dourado Acetinado | `#C5A059` | Botões, detalhes, bordas ativas e ícones |
| **Destaque Suave** | Champanhe | `#E2C896` | Efeitos de hover e badges sutis |
| **Texto Primário** | Off-White Puro | `#F4F4F5` | Máxima legibilidade em fundo escuro |
| **Texto Secundário** | Cinza Neutro | `#9CA3AF` | Descrições e notas de rodapé |

### 🔤 Tipografia
- **Títulos (H1, H2, H3):** *Playfair Display* ou *Cinzel* (Serifada clássica, sofisticada).
- **Corpo de Texto & Menus:** *Inter*, *Plus Jakarta Sans* ou *Montserrat* (Sem serifa, limpa, legível).

---

## 3. Estrutura e Copywriting Página a Página (Passo a Passo)

### 🔹 Seção 1: Header / Navbar Fixa
- **Logotipo:** Tipografia refinada `AURA CAFÉ` com o emblema dourado centralizado ou à esquerda.
- **Links de Navegação:**
  1. O Café
  2. Experiências
  3. Menu Curado
  4. Localização
- **Botão CTA (Direita):** `Reservar Mesa` (estilo outline dourado).

---

### 🔹 Seção 2: Hero Section (Apresentação Principal)
- **Tag superior (Badge):** `MICROTORREFAÇÃO & GASTRONOMIA DE LUXO`
- **Headline (H1):** `A excelência do café especial, elevada a uma experiência sensorial única.`
- **Subtítulo:** `Grãos selecionados em microlotes de alta altitude, extraídos com rigor artesanal em um ambiente intimista e sofisticado.`
- **Ações (CTAs):**
  - Botão Primário: `Explorar o Menu` (Preenchimento dourado `#C5A059`, texto escuro).
  - Botão Secundário: `Conhecer o Espaço` (Borda sutil, link com âncora para a seção Sobre).
- **Mídia:** Fotografia panorâmica do balcão em mármore escuro com a máquina de espresso iluminada por luz âmbar.

---

### 🔹 Seção 3: Diferenciais / O Conceito (3 Pilares)
Três cards minimalistas com borda delicada (`1px solid #27272A`) e ícones dourados:
1. **Origens Raras (SCA 88+):** Grãos arábica puros colhidos à mão nas melhores regiões cafeeiras do país.
2. **Extração de Precisão:** Baristas premiados e métodos que valorizam notas florais, achocolatadas e cítricas.
3. **Pâtisserie Autoral:** Folhados artesanais, viennoiserie fresca e harmonizações exclusivas para cada método.

---

### 🔹 Seção 4: Menu Curado em Destaque
- **Aba de Filtro:** `[Espressos & Métodos]` | `[Viennoiserie & Doces]` | `[Grãos Especiais]`
- **Itens de Amostra:**
  - **Flat White Dourado:** Ristretto duplo, leite texturizado aveludado e finalização com infusão de fava de baunilha.
  - **Cold Brew Signature:** Maturação a frio por 18 horas em barril de carvalho tostado.
  - **Pain au Chocolat Artesanal:** Massa folhada com manteiga francesa e recheio de chocolate 70% cacau de origem.
- **CTA Secundário:** `[Baixar Carta Completa em PDF]`

---

### 🔹 Seção 5: Sobre o Espaço (Storytelling)
- **Layout:** Duas colunas (Foto do ambiente à esquerda, texto à direita).
- **Título (H2):** `Mais que uma cafeteria, um refúgio para desacelerar.`
- **Texto:** `Cada detalhe do Aura Café foi planejado para desacelerar o ritmo urbano: a acústica suave, o mármore escuro que acolhe o vapor do espresso e o aroma inconfundível dos nossos microlotes recém-torrados.`

---

### 🔹 Seção 6: Informações de Visita & CTA Final
- **Título:** `Viva a experiência Aura.`
- **Horário de Funcionamento:** Terça a Domingo, das 08h às 21h.
- **Endereço:** Unidade Conceito — Centro Nobre.
- **Botão Direto:** `Agendar Visita / Falar no WhatsApp` (redirecionamento com mensagem personalizada: *"Olá! Gostaria de reservar uma mesa no Aura Café."*).

---

### 🔹 Seção 7: Footer (Rodapé)
- **Logo reduzida:** `AURA CAFÉ`
- **Links rápidos:** Políticas de Privacidade, Imprensa, Contato.
- **Redes Sociais:** Ícones para Instagram e WhatsApp.
- **Copyright:** `© Aura Café. Todos os direitos reservados.`

---

## 4. Guia de Execução Técnica para a Live

1. **Setup Inicial (0 a 10 min):**
   - Criar diretório do projeto: `/aura-cafe`.
   - Adicionar pasta `/assets/images` com a logo, a foto hero e o cardápio.
   - Criar `index.html` e importar fontes do Google Fonts (`Playfair Display` + `Plus Jakarta Sans`).

2. **Configuração de Estilo (10 a 25 min):**
   - Configurar Tailwind CSS via CDN ou arquivo de variáveis CSS:
     ```css
     :root {
       --bg-primary: #0C0C0E;
       --bg-card: #16161A;
       --accent-gold: #C5A059;
       --text-primary: #F4F4F5;
     }
     ```

3. **Montagem da Estrutura (25 a 70 min):**
   - Codificar Navbar com efeito `backdrop-blur`.
   - Montar Hero Section com texto sobreposto à imagem.
   - Criar grid responsivo (1 coluna no mobile, 3 colunas no desktop) para os diferenciais e menu.

4. **Refinamento & Mobile (70 a 85 min):**
   - Ajustar espaçamentos, tamanhos de fonte em telas pequenas e transições suaves nos botões (`transition: all 0.3s ease`).

5. **Deploy & Conclusão (85 a 100 min):**
   - Subir o projeto para Vercel, Netlify ou GitHub Pages ao vivo com a audiência.