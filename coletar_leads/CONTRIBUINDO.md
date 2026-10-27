# Como contribuir

Qualquer pessoa da comunidade pode sugerir melhorias.

1. Faça um **fork** do repositório.
2. Crie uma branch a partir de `aula-002-coletar-leads`: `git checkout -b minha-melhoria`.
3. Faça a alteração e teste na sua máquina (veja o [PASSO_A_PASSO.md](PASSO_A_PASSO.md)).
4. Abra um **Pull Request** para `aula-002-coletar-leads` explicando o que mudou e por quê.

## Regras importantes

- **Nunca envie dados pessoais.** Não faça commit de `dados/wa_perfil/` (sessão do WhatsApp), `dados/crm.db`, arquivos `.json`/`.csv` de leads, `.env` nem qualquer senha ou cookie. O `.gitignore` já bloqueia isso; confira com `git status` antes de enviar.
- **Não coloque login do Google no código.** O projeto não precisa de conta do Google.
- Atualize o [README.md](README.md) quando mudar algo que o usuário vê.
- Mantenha o estilo do código existente (Python simples, sem dependências além do Playwright).
