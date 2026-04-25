# Flavors of Brazil Food Festival - Georgia Edition 2026

Site oficial completo para o **Flavors of Brazil Food Festival - Georgia Edition 2026**, com pagina publica, restaurantes participantes, inscricao online, painel administrativo, banco SQLite local, SEO basico e assets visuais premium.

## Tecnologias

- Python 3.10+
- Flask
- Flask-SQLAlchemy
- SQLite para desenvolvimento
- Suporte a MySQL via `DATABASE_URL`
- Templates Jinja2
- CSS e JavaScript sem build step

## Estrutura

```text
flavors-of-brazil/
  app/
    __init__.py
    routes.py
    models.py
    forms.py
    auth.py
    email_utils.py
    seo.py
    content.py
  templates/
  static/
    css/style.css
    js/main.js
    uploads/
    assets/
      logo.png
      generated/
  migrations/
  config.py
  run.py
  wsgi.py
  passenger_wsgi.py
  requirements.txt
  .env.example
  deploy_hostinger.md
```

## Rodar localmente

No macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py init-db
python run.py
```

No Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py init-db
python run.py
```

Acesse:

```text
http://127.0.0.1:5000
```

## Rodar com Docker Compose

Na VPS, copie `.env.example` para `.env` e ajuste pelo menos `SECRET_KEY`, `SITE_URL` e `APP_PORT`.

Para SQLite dentro do container, use:

```env
DATABASE_URL=sqlite:////app/instance/flavors.db
```

Depois rode:

```bash
docker compose build
docker compose up -d
```

O compose sobe o app com Gunicorn em:

```text
http://IP_DA_VPS:6000
```

Se quiser expor direto na porta 80, defina `APP_PORT=80` no `.env`. Em producao, o ideal e usar Nginx ou Caddy na frente com HTTPS e proxy para `127.0.0.1:6000`.

Dados persistentes:

- Banco SQLite: `instance/flavors.db`
- Uploads: `static/uploads/`

Para deploy na AWS/EC2, veja tambem `deploy_aws_docker.md`.

## Admin de desenvolvimento

O seed cria o usuario:

```text
E-mail: admin@flavorsofbrazil.com
Senha: ChangeMe123!
```

Altere essa senha antes de publicar em producao. A senha padrao e apenas para desenvolvimento.

## Rotas publicas

- `/`
- `/restaurantes`
- `/restaurantes/<slug>`
- `/inscricao`
- `/obrigado`
- `/termos`
- `/privacidade`
- `/sitemap.xml`
- `/robots.txt`

## Rotas admin

- `/admin`
- `/admin/dashboard`
- `/admin/inscricoes`
- `/admin/inscricoes/<id>`
- `/admin/restaurantes`
- `/admin/logout`

## Fluxo de inscricao

1. Restaurante envia o formulario em `/inscricao`.
2. A inscricao e salva no banco.
3. Se SMTP estiver configurado, o sistema envia e-mail para o restaurante e para os organizadores.
4. No painel, a organizacao altera status, registra observacoes, data de gravacao e status do video.
5. O botao **Publicar restaurante** cria ou atualiza a pagina publica do restaurante.
6. O restaurante publicado aparece em `/restaurantes` e na home.

## Status disponiveis

- Recebida
- Em curadoria
- Aprovada
- Recusada
- Aguardando pagamento
- Pagamento recebido
- Confirmada
- Publicada

## Configuracao por ambiente

Copie `.env.example` para `.env` e ajuste:

```bash
cp .env.example .env
```

Variaveis importantes:

- `SECRET_KEY`: chave secreta Flask.
- `SITE_URL`: dominio publico, por exemplo `https://flavorsofbrazil.com`.
- `DATABASE_URL`: SQLite local ou MySQL em producao.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`: SMTP opcional.
- `ADMIN_NOTIFICATION_EMAIL`: e-mail que recebe novas inscricoes.

Se SMTP nao estiver configurado, o sistema nao quebra: ele salva a inscricao no banco e ignora o envio de e-mail.

## Banco de dados

Inicializar banco:

```bash
python run.py init-db
```

O comando cria:

- Tabelas `users`, `applications`, `restaurants`, `settings`
- Usuario admin de desenvolvimento
- Configuracoes iniciais do festival
- 3 restaurantes ficticios publicados

## Uploads

Uploads ficam em:

```text
static/uploads/
```

Formatos aceitos:

- JPG
- PNG
- WebP

Limite padrao:

```text
8 MB
```

## SEO implementado

- Title tags individuais
- Meta description
- Open Graph
- Twitter Card
- Sitemap dinamico
- Robots.txt
- URLs amigaveis com slug
- Schema.org Event na home
- Schema.org Restaurant nas paginas individuais
- Alt text em imagens

## Idiomas

O header possui seletor de idioma:

- PT-BR
- EN
- ES

A estrutura esta pronta para ampliar traducoes em `app/content.py`.

## Observacoes de produto

Este projeto nao implementa votacao, ranking, avaliacoes publicas, comentarios publicos ou competicao. A primeira edicao foi modelada como circuito promocional e colaborativo.

## Assets

O logo original foi copiado para:

```text
static/assets/logo.png
```

Os placeholders premium em WebP ficam em:

```text
static/assets/generated/
```

Substitua esses arquivos por fotografias reais mantendo os mesmos nomes, ou altere as referencias no admin/restaurantes.
