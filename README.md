# Agenda Modesta

## 1. Pre-requisitos

- Docker Desktop (com Docker Compose)
- Git
- Opcional para fluxo sem Docker: uv, Python 3.13 e Node.js com npm

## 2. Clonar o repositorio

```bash
git clone https://github.com/MoonAmon/agenda__modesta.git
cd agenda__modesta
```

## 3. Configurar variaveis de ambiente

Este projeto usa os arquivos abaixo:

- .envs/.local/.django
- .envs/.local/.postgres
- .envs/.local/.ngrok

Se precisar recriar os arquivos, use os exemplos a seguir.

### 3.1 Exemplo de .envs/.local/.django

```env
USE_DOCKER=yes
IPYTHONDIR=/app/.ipython

REDIS_URL=redis://redis:6379/0

CELERY_FLOWER_USER=debug
CELERY_FLOWER_PASSWORD=debug

GOOGLE_CALENDAR_ID=seu_calendario@group.calendar.google.com
GOOGLE_CALENDAR_CREDENTIALS_FILE=/app/google-credentials.json
GOOGLE_CALENDAR_WEBHOOK_URL=https://seu-dominio.ngrok-free.dev/agenda/google/webhook/

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
```

### 3.2 Exemplo de .envs/.local/.postgres

```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=agenda_modesta
POSTGRES_USER=debug
POSTGRES_PASSWORD=debug
```

### 3.3 Exemplo de .envs/.local/.ngrok (opcional)

```env
NGROK_AUTHTOKEN=seu_token_ngrok
NGROK_DOMAIN=seu-dominio.ngrok-free.dev
```

## 4. Configurar Google Calendar (Service Account)

Crie o arquivo google-credentials.json na raiz do projeto com a chave da Service Account.

No container, o caminho esperado pela aplicacao e:

- /app/google-credentials.json

Checklist:

- Compartilhe o calendario com o email da Service Account
- Preencha GOOGLE_CALENDAR_ID corretamente

## 5. Subir com Docker (recomendado)

### 5.1 Build da imagem

```bash
docker compose -f docker-compose.local.yml build
```

### 5.2 Subir os containers

```bash
docker compose -f docker-compose.local.yml up -d --remove-orphans
```

Observacoes:

- O Django executa migrate automaticamente ao iniciar o container
- O compose local sobe django, postgres, redis, mailpit, celeryworker, celerybeat e flower

### 5.3 Rodar Tailwind em watch (desenvolvimento CSS)

```bash
docker compose -f docker-compose.local.yml --profile dev up -d tailwind
```

### 5.4 Rodar ngrok para webhook (opcional)

```bash
docker compose -f docker-compose.local.yml up -d ngrok
```

## 6. Criar superusuario

Modo interativo:

```bash
docker compose -f docker-compose.local.yml run --rm django python ./manage.py createsuperuser
```

Modo sem interacao (usa DJANGO*SUPERUSER*\*):

```bash
docker compose -f docker-compose.local.yml run --rm django python ./manage.py createsuperuser --noinput
```

## 7. URLs locais

- Aplicacao: http://127.0.0.1:8000
- Admin: http://127.0.0.1:8000/admin
- Mailpit: http://127.0.0.1:8025
- Flower: http://127.0.0.1:5555
- Ngrok dashboard: http://127.0.0.1:4040

## 8. Comandos uteis do dia a dia

### 8.1 Logs

```bash
docker compose -f docker-compose.local.yml logs -f
docker compose -f docker-compose.local.yml logs -f django
```

### 8.2 Comandos manage.py

```bash
docker compose -f docker-compose.local.yml run --rm django python ./manage.py showmigrations
docker compose -f docker-compose.local.yml run --rm django python ./manage.py makemigrations
docker compose -f docker-compose.local.yml run --rm django python ./manage.py migrate
docker compose -f docker-compose.local.yml run --rm django python ./manage.py shell_plus
```

### 8.3 Parar os servicos

```bash
docker compose -f docker-compose.local.yml down
```

### 8.4 Limpeza completa (remove volumes)

```bash
docker compose -f docker-compose.local.yml down -v
```

## 9. Testes e qualidade de codigo

### 9.1 Testes

```bash
docker compose -f docker-compose.local.yml run --rm django uv run pytest
```

### 9.2 Cobertura

```bash
docker compose -f docker-compose.local.yml run --rm django uv run coverage run -m pytest
docker compose -f docker-compose.local.yml run --rm django uv run coverage html
```

### 9.3 Mypy

```bash
docker compose -f docker-compose.local.yml run --rm django uv run mypy agenda_modesta
```

## 10. Fluxo opcional sem Docker

Use apenas se quiser rodar tudo no host local.

### 10.1 Instalar dependencias Python

```bash
uv sync
```

### 10.2 Instalar dependencias front-end

```bash
npm install
```

### 10.3 Build CSS

```bash
npm run build:css
```

Ou modo watch:

```bash
npm run watch:css
```

### 10.4 Definir variaveis minimas no ambiente local

Exemplo no Windows (PowerShell):

```powershell
$env:DATABASE_URL="postgres://debug:debug@127.0.0.1:5432/agenda_modesta"
$env:REDIS_URL="redis://127.0.0.1:6379/0"
```

### 10.5 Migrar e subir servidor

```bash
uv run python manage.py migrate
uv run python manage.py runserver_plus 0.0.0.0:8000
```

## 11. Troubleshooting rapido

### Erro de conexao com banco

- Verifique .envs/.local/.postgres
- Confirme se o container postgres esta rodando

### Webhook Google nao chega

- Verifique se o ngrok esta ativo
- Confira se GOOGLE_CALENDAR_WEBHOOK_URL esta publico e com https

### Falha na autenticacao Google

- Confirme google-credentials.json na raiz do projeto
- Confirme permissao da Service Account no calendario

## 12. Licenca

MIT
