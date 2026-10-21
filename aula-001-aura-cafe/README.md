# 🍰 Aura Café — Website

Website sofisticado e elegante para a Aura Café - Cafeteria Artesanal de Luxo.

## 📂 Estrutura do Projeto

```
aura_cafe/
├── index.html           # Página principal (abrir em localhost)
├── server.py           # Servidor Python para localhost
├── imagens/            # Pasta com imagens
│   ├── Logo.jpg
│   ├── bar.jpg
│   ├── fot1.jpg
│   └── instagram.png
└── README.md           # Este arquivo
```

## 🎨 Preparar as Logos (PNG com fundo transparente)

### Passo 1: Converter Logo.jpg para Logo.png

Execute o script de conversão:

```bash
python converter_logo.py
```

Este script vai:
- ✅ Remover o fundo branco da logo
- ✅ Salvar como `Logo.png` com fundo transparente
- ✅ Aplicar otimização de qualidade

**Requisito:** Pillow instalado (`pip install pillow`)

## 🚀 Como Abrir em Localhost

### Opção 1: Python (Recomendado)

1. Abra o terminal/PowerShell na pasta do projeto
2. Execute:
```bash
python server.py
```
3. Acesse em seu navegador:
```
http://localhost:8000
```

### Opção 2: Python (Método alternativo)

```bash
python -m http.server 8000
```
Depois acesse: `http://localhost:8000`

### Opção 3: Node.js (se tiver instalado)

```bash
npx http-server
```

### Opção 4: Abrir direto no navegador

Abra o arquivo `index.html` diretamente no seu navegador (clique duplo no arquivo).

## 📱 Recursos

✅ **Design Dark Luxury** — Paleta sofisticada com ouro acetinado
✅ **Responsivo** — Funciona em mobile, tablet e desktop
✅ **Header Sticky** — Navegação fixa no topo
✅ **Smooth Scroll** — Transições suaves entre seções
✅ **Menu Interativo** — Abas de filtro para café e bolos
✅ **Logo com LED** — Efeito sutil no footer
✅ **Imagens Otimizadas** — Integradas localmente

## 🎨 Cores Principais

| Nome | Hex | Uso |
|------|-----|-----|
| Carvão Profundo | `#0C0C0E` | Fundo primário |
| Grafite Nobre | `#16161A` | Superfícies |
| Dourado Acetinado | `#C5A059` | Destaques |
| Champanhe | `#E2C896` | Acentos suaves |
| Off-White | `#F4F4F5` | Texto principal |
| Cinza Neutro | `#9CA3AF` | Texto secundário |

## 🔤 Tipografia

- **Títulos:** Playfair Display (serif)
- **Corpo:** Inter (sans-serif)

## 📞 Contato

- **WhatsApp:** Link para reservas personalizadas
- **Instagram:** [@adrianoafweb](https://www.instagram.com/adrianoafweb)
- **Email:** hello@auracafe.com
- **Telefone:** (11) 9999-9999

---

**Desenvolvido com precisão e sofisticação.** ☕✨
