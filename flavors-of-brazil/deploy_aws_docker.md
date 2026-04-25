# Deploy na VPS AWS com Docker Compose

Guia rapido para publicar o Flask na sua VPS/EC2 usando `docker-compose.yml`.

## 1. Preparar a EC2

No Security Group da instancia, libere:

- SSH: porta `22`, preferencialmente apenas para seu IP.
- HTTP: porta `80`.
- HTTPS: porta `443`.
- Temporario, se for acessar sem proxy: porta `6000`.

Instale Docker e Compose Plugin no Ubuntu:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

Saia do SSH e entre novamente para o grupo `docker` valer.

## 2. Enviar o projeto

Copie a pasta `flavors-of-brazil` para a VPS, por exemplo:

```bash
/home/ubuntu/flavors-of-brazil
```

Entre na pasta:

```bash
cd /home/ubuntu/flavors-of-brazil
```

## 3. Configurar `.env`

```bash
cp .env.example .env
nano .env
```

Exemplo para Docker:

```env
SECRET_KEY=troque-por-uma-chave-longa-e-aleatoria
SITE_URL=https://flavorsofbrazil.com
APP_PORT=6000
DATABASE_URL=sqlite:////app/instance/flavors.db
FLASK_DEBUG=0
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120
```

Configure SMTP se quiser envio de e-mail:

```env
SMTP_HOST=smtp.seudominio.com
SMTP_PORT=587
SMTP_USER=contato@flavorsofbrazil.com
SMTP_PASSWORD=sua-senha
SMTP_FROM=contato@flavorsofbrazil.com
ADMIN_NOTIFICATION_EMAIL=rsouza@greatstoriesfilms.com
```

## 4. Preparar volumes persistentes

```bash
mkdir -p instance static/uploads
sudo chown -R 1000:1000 instance static/uploads
```

Essas pastas guardam:

- `instance/flavors.db`: banco SQLite.
- `static/uploads/`: imagens enviadas pelo formulario/admin.

## 5. Subir a aplicacao

```bash
docker compose build
docker compose up -d
docker compose ps
docker compose logs -f web
```

O container roda automaticamente:

```bash
python run.py init-db
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

Admin inicial:

```text
admin@flavorsofbrazil.com
ChangeMe123!
```

Troque essa senha antes de divulgar o site.

## 6. Acesso sem proxy

Com `APP_PORT=6000`:

```text
http://IP_DA_EC2:6000
```

Se quiser expor direto em HTTP:

```env
APP_PORT=80
```

Depois:

```bash
docker compose up -d
```

## 7. Recomendado: Nginx com HTTPS

Deixe o app em `APP_PORT=6000` e use Nginx na porta 80/443.

Exemplo de bloco Nginx:

```nginx
server {
    server_name flavorsofbrazil.com www.flavorsofbrazil.com;

    location / {
        proxy_pass http://127.0.0.1:6000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Instale SSL com Certbot:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo certbot --nginx -d flavorsofbrazil.com -d www.flavorsofbrazil.com
```

## 8. Atualizar o site

Depois de enviar novos arquivos:

```bash
docker compose build
docker compose up -d
docker compose logs -f web
```

## 9. Backup

Backup minimo:

```bash
tar -czf flavors-backup-$(date +%F).tar.gz instance static/uploads .env
```
