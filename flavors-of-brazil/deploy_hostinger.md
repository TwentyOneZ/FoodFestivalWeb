# Deploy na Hostinger

Este projeto foi preparado para ser publicado como app Python/Flask. A disponibilidade do recurso **Python App** depende do plano Hostinger.

## 1. Preparar arquivos

No computador local, teste antes:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py init-db
python run.py
```

No Windows:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py init-db
python run.py
```

Envie a pasta `flavors-of-brazil` para a Hostinger, normalmente para algo como:

```text
/home/USUARIO/flavors-of-brazil
```

Nao envie a pasta `venv`.

## 2. Configurar Python App

No painel da Hostinger, procure por **Python App**.

Configuracao sugerida:

- App root: caminho da pasta `flavors-of-brazil`
- Startup file: `passenger_wsgi.py`
- Application object: `application`
- Python version: 3.10 ou superior

Depois instale dependencias pelo terminal/SSH:

```bash
cd /home/USUARIO/flavors-of-brazil
python -m pip install -r requirements.txt
python run.py init-db
```

## 3. Variaveis de ambiente

Crie um arquivo `.env` na raiz do projeto com base em `.env.example`.

Exemplo:

```env
SECRET_KEY=uma-chave-longa-e-aleatoria
SITE_URL=https://flavorsofbrazil.com
DATABASE_URL=sqlite:///instance/flavors.db
FLASK_DEBUG=0
SMTP_HOST=smtp.hostinger.com
SMTP_PORT=587
SMTP_USER=contact@flavorsofbrazil.com
SMTP_PASSWORD=sua-senha
SMTP_FROM=contact@flavorsofbrazil.com
ADMIN_NOTIFICATION_EMAIL=rsouza@greatstoriesfilms.com
```

Use uma `SECRET_KEY` forte e unica.

## 4. Dominio

No painel da Hostinger:

1. Aponte `flavorsofbrazil.com` para a hospedagem.
2. Ative SSL/HTTPS.
3. Defina `SITE_URL=https://flavorsofbrazil.com`.
4. Reinicie o Python App.

## 5. SQLite em producao inicial

O SQLite funciona para uma primeira fase promocional com volume moderado.

Banco padrao:

```text
instance/flavors.db
```

Cuidados:

- Garanta permissao de escrita na pasta `instance`.
- Inclua backup regular do arquivo `.db`.
- Nao exponha a pasta `instance` publicamente.

## 6. Migrar para MySQL

Crie um banco MySQL na Hostinger e ajuste:

```env
DATABASE_URL=mysql+pymysql://USUARIO:SENHA@HOST/NOME_DO_BANCO?charset=utf8mb4
```

Depois rode:

```bash
python run.py init-db
```

Esse comando cria as tabelas e dados iniciais se ainda nao existirem. Para migrar dados reais do SQLite para MySQL, exporte as tabelas ou use um script de migracao dedicado.

## 7. SMTP

Se SMTP estiver configurado, novas inscricoes enviam e-mail ao restaurante e aos organizadores.

Variaveis:

```env
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
ADMIN_NOTIFICATION_EMAIL=
```

Se SMTP estiver vazio, o sistema continua funcionando e apenas salva as inscricoes no banco.

## 8. Uploads

Uploads ficam em:

```text
static/uploads/
```

Garanta permissao de escrita nessa pasta. Em hospedagem compartilhada, confirme se o processo Python pode gravar no diretorio.

## 9. Proteger o painel admin

Antes de publicar:

1. Troque a senha `ChangeMe123!`.
2. Use HTTPS.
3. Defina `FLASK_DEBUG=0`.
4. Use uma `SECRET_KEY` forte.
5. Restrinja acesso por senha forte e, se possivel, por regra adicional no painel/servidor.

Para trocar senha manualmente, use um shell Python no servidor:

```bash
python
```

```python
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, User
app = create_app()
with app.app_context():
    user = User.query.filter_by(email="admin@flavorsofbrazil.com").first()
    user.password_hash = generate_password_hash("NOVA-SENHA-FORTE")
    db.session.commit()
```

## 10. Se o plano nao tiver Python App

Alternativas:

- Hospedar o Flask em VPS, Render, Railway, Fly.io ou outro provedor e apontar `flavorsofbrazil.com` via DNS.
- Exportar somente o site publico como estatico e manter o formulario/admin em backend externo.
- Usar a hospedagem compartilhada apenas para assets e uma API externa para inscricoes.

Para preservar todas as funcionalidades pedidas, a melhor alternativa sem Python App compartilhado e usar uma VPS ou plataforma que rode Flask continuamente.
