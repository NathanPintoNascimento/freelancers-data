# freelancers-data

# Sidec Freelancer Platform

Aplicação web desenvolvida com **Flask** e **PostgreSQL** que conecta empresas a freelancers. A empresa pode cadastrar, buscar, avaliar e convocar profissionais diretamente pela plataforma, com disparo automático de e-mail de seleção.

---

##  Funcionalidades

- **Cadastro de freelancers** — formulário com upload de currículo (PDF/DOC)
- **Painel administrativo** — protegido por autenticação via sessão
- **Busca e filtro** — pesquisa por profissão com ordenação por pontuação
- **Sistema de avaliação** — admins avaliam freelancers de 1 a 5; score atualizado em tempo real
- **Notificação por e-mail** — um clique envia um e-mail HTML com botão de contato via WhatsApp
- **Banco de dados PostgreSQL** — schema relacional com integridade referencial

---

##  Estrutura do Projeto

```
sidec-freelancer-platform/
├── app.py                  # Ponto de entrada e todas as rotas
├── requirements.txt        # Dependências Python
└── templates/
    ├── index.html
    ├── login.html
    ├── cadastro.html
    ├── resultados.html
    └── avaliacao.html
```

---


##  Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta para as sessões do Flask |
| `DATABASE_URL` | String de conexão com o PostgreSQL |
| `ADMIN_USERS` | Lista de usuários admin separados por vírgula |
| `ADMIN_PASSWORD` | Senha compartilhada dos admins |
| `EMAIL_SENDER` | Endereço Gmail usado para enviar notificações |
| `EMAIL_PASSWORD` | Senha de app do Gmail (não a senha da conta) |
| `WHATSAPP_NUMBER` | Número de contato exibido nos e-mails de seleção |
| `FLASK_DEBUG` | Use `true` apenas em desenvolvimento |


---

##  Esquema do Banco de Dados

```sql
freelancers (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(100),
    profissao   VARCHAR(50),
    cidade      VARCHAR(50),
    telefone    VARCHAR(20),
    email       VARCHAR(100),
    score       DECIMAL(2,1) DEFAULT 5.0,
    curriculo   VARCHAR(200),
    situacao    VARCHAR(20)
)

avaliacoes (
    id            SERIAL PRIMARY KEY,
    freelancer_id INTEGER REFERENCES freelancers(id) ON DELETE CASCADE,
    nota          INTEGER,
    comentario    TEXT
)
```

As tabelas são criadas automaticamente na primeira execução via `init_db()`.

---

##  Segurança

- Todas as credenciais são carregadas via variáveis de ambiente — nenhum dado sensível no código.
- Rotas administrativas verificam a sessão no servidor antes de qualquer ação.
- Uploads são sanitizados com `werkzeug.utils.secure_filename`.
- `ON DELETE CASCADE` garante integridade referencial ao remover um freelancer.

---

##  Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| Backend | Python 3 · Flask |
| Banco de dados | PostgreSQL · psycopg2 |
| E-mail | smtplib · Gmail SMTP |
| Frontend | Jinja2 · HTML/CSS |
| Deploy | Gunicorn · Render / Railway / Heroku |

---

##  Licença

Projeto desenvolvido para a **Sidec Corporate**. Todos os direitos reservados.
