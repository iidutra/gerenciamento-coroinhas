# Pastoral dos Coroinhas

Sistema paroquial para gestão de coroinhas — escalas, presenças, formações e portal das famílias.

## Stack

- **Backend:** Django 5 + DRF + JWT + PostgreSQL + Redis
- **Frontend:** Next.js + TypeScript + Tailwind
- **Infra:** Docker Compose (local/prod), **Railway** (recomendado), GitLab CI

## Início rápido (sem Docker — recomendado no Windows)

```powershell
Copy-Item .env.local.example .env
.\scripts\dev-local.ps1
```

Em **outro terminal**:

```powershell
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:3000
- API: http://localhost:8000/api/v1

**Criar coordenador:**

```powershell
.\scripts\dev-local.ps1 -CriarCoordenador -Email coord@paroquia.org -Senha admin123
```

**Dados e usuários de demonstração:**

```powershell
.\scripts\dev-local.ps1 -SeedDemo
```

| Perfil | Login | Senha | Destino |
|--------|-------|-------|---------|
| Coordenador | `coord@paroquia.org` | `admin123` | Dashboard |
| Secretário | `secretario@paroquia.org` | `demo123` | Dashboard |
| Padre | `padre@paroquia.org` | `demo123` | Dashboard (somente leitura) |
| Pai | CPF `111.444.777-35` | `demo123` | Portal |
| Coroinha | CPF `529.982.247-25` | `demo123` | Portal |

Login único: informe **CPF ou e-mail** na mesma tela — o sistema detecta automaticamente.

Usa SQLite + cache em memória — não precisa de PostgreSQL, Redis nem Docker.

---

## Docker — desenvolvimento

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## Deploy — Railway (recomendado)

Hospedagem gerenciada com **PostgreSQL + Redis** como plugins. Custo típico **~US$ 5–15/mês** ( Hobby + uso).

### Arquitetura (4 serviços)

| Serviço | Root directory | Config |
|---------|----------------|--------|
| **API** | `/backend` | `backend/railway.toml` (auto) |
| **Worker** (Celery) | `/backend` | `backend/railway.toml` + `SERVICE_ROLE=worker` |
| **Frontend** | `/frontend` | `frontend/railway.toml` (auto) |
| **PostgreSQL** | plugin | linkar `DATABASE_URL` |
| **Redis** | plugin | linkar `REDIS_URL` |

### Passo a passo

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub/GitLab**
2. **Add PostgreSQL** e **Add Redis** no projeto
3. Crie o serviço **API**:
   - Root Directory: `/backend` (Settings → **não** preencha Config file manualmente)
   - Variables (ver `.env.railway.example`):
     - `SECRET_KEY`, `DEBUG=False`
     - `CORS_ALLOWED_ORIGINS=https://<frontend>.up.railway.app`
     - `SERVE_MEDIA=True` (+ volume em `/app/media` para fotos)
   - Reference variables: `${{Postgres.DATABASE_URL}}`, `${{Redis.REDIS_URL}}`
   - **Generate Domain** → anote a URL da API
4. Crie o serviço **Worker**:
   - Root Directory: `/backend`
   - Variable: `SERVICE_ROLE=worker`
   - Mesmas variables da API (DATABASE_URL, REDIS_URL, SECRET_KEY)
5. Crie o serviço **Frontend**:
   - Root Directory: `/frontend`
   - Variable **antes do build**: `NEXT_PUBLIC_API_URL=https://<api>.up.railway.app/api/v1`
   - Generate Domain
6. Atualize `CORS_ALLOWED_ORIGINS` na API com a URL pública do frontend
7. Criar coordenador (Railway CLI ou one-off command):

```bash
railway link   # serviço API
railway run python manage.py criar_coordenador --email coord@paroquia.org --senha 'SuaSenha'
```

- Health API: `https://<api>.up.railway.app/api/v1/health`
- Admin: `https://<api>.up.railway.app/admin/`

### Fotos (mídia)

Containers são efêmeros. Escolha uma opção:

- **Volume Railway** montado em `/app/media` + `SERVE_MEDIA=True` (simples)
- **Cloudflare R2** + `USE_S3=True` (persistente, recomendado longo prazo)

### Domínio customizado

Railway → serviço Frontend/API → **Custom Domain** → configure CNAME. Atualize `CORS`, `NEXT_PUBLIC_API_URL` e redeploy o frontend.

### CLI (opcional)

```powershell
npm i -g @railway/cli
railway login
.\scripts\railway-set-monorepo.ps1   # Root Directory /backend e /frontend
.\scripts\railway-deploy.ps1         # deploy manual se o GitHub falhar
```

### Erro "Railpack could not determine how to build"

O deploy do GitHub usa a **raiz do repositório** por padrão. Em monorepo, configure **Root Directory** em cada serviço:

- API e Worker → `/backend`
- Frontend → `/frontend`

**Não** defina "Config file" manualmente (deixe em branco). Rode `.\scripts\railway-set-monorepo.ps1` ou ajuste no dashboard.

---

## Docker — produção (VPS alternativo)

<details>
<summary>VPS único (Hetzner, DigitalOcean) — clique para expandir</summary>

Stack com `docker-compose.prod.yml`. Ver `scripts/setup-vps.sh` e `.env.prod.example`.

```bash
cp .env.prod.example .env && ./scripts/deploy-vps.sh --build
```

</details>

### Comunicação e filas

- **Celery worker** processa envio de mensagens (e-mail/WhatsApp) de forma assíncrona.
- Sem `EMAIL_HOST` ou `WHATSAPP_API_URL`, os envios ficam em **simulação** (registrados no histórico).
- Configure SMTP e WhatsApp nas variables do Railway ou no `.env`.

### Docker local (teste prod)

```powershell
Copy-Item .env.prod.example .env
docker compose -f docker-compose.prod.yml up --build -d
```

### Docker Desktop com erro 500

1. Abra **Docker Desktop** e aguarde ficar verde (Running)
2. **Settings → Troubleshoot → Restart Docker Desktop**
3. Reinicie o PC se persistir (WSL2)
4. Enquanto isso, use o modo local (`.\scripts\dev-local.ps1`)

---

## Comandos úteis

```powershell
# Testes (backend + frontend)
.\scripts\run-tests.ps1

# Importar calendário paroquial (notícias + formações)
cd backend
python manage.py importar_calendario_paroquial

# Missas recorrentes (dia 13, domingos)
python manage.py setup_missas
```

---

## API principal

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/v1/health` | Health check (público) |
| `POST /api/v1/auth/login` | Login unificado (CPF ou e-mail + senha) |
| `POST /api/v1/auth/recuperar-senha` | CPF + data nascimento + nova senha |
| `GET /api/v1/relatorios/escala-mes?ano=&mes=&formato=pdf` | Exportar escala do mês (PDF) |
| `POST /api/v1/inscricoes/publica` | Inscrição online (rate limit por IP) |
| `GET /api/v1/portal/filhos` | Filhos do pai / preview staff |
| `GET /api/v1/portal/coroinhas/{id}/resumo` | Portal família |
| `GET /api/v1/usuarios-staff/` | Usuários staff (Coordenador) |
| `GET /api/v1/dashboard/stats` | KPIs staff |

---

## Estrutura

```
├── backend/apps/
│   ├── identity/       # Auth, usuários staff
│   ├── membership/     # Coroinha, inscrição, portal
│   ├── scheduling/     # Missas, escalas
│   ├── attendance/     # Presença
│   ├── training/       # Formações
│   ├── communication/  # Mensagens (Celery + e-mail/WhatsApp)
│   └── content/        # Notícias, documentos, import calendário
├── frontend/           # Next.js
├── nginx/              # Proxy reverso (prod)
├── docker-compose.yml
├── docker-compose.prod.yml
└── .gitlab-ci.yml      # lint → test → build
```

---

## CI/CD (GitLab)

Pipeline: **lint** → **test** → **build** → **deploy** (manual na branch `main`)

- Backend: ruff, pytest (cobertura ≥ 65%), `manage.py check`
- Frontend: eslint, vitest, `next build`
- Deploy: build/push de imagens Docker para o GitLab Container Registry + job manual **deploy-vps** (SSH)

Variables CI/CD para deploy automático: `DEPLOY_HOST`, `DEPLOY_USER`, `SSH_PRIVATE_KEY`, opcional `DEPLOY_PATH` (default `/opt/coroinhas`).

---

## Funcionalidades implementadas

- Portal família + preview staff (`/dashboard/portal`)
- Gerenciamento de usuários staff (Coordenador)
- Importação do calendário paroquial 2026 (PDF → notícias/formações)
- Rate limit: login, recuperar senha, inscrição pública
- Canal de notícias com busca, filtros e agrupamento por mês
- Celery + envio assíncrono de mensagens (e-mail/WhatsApp configurável)
- **Notificação automática** ao montar escala (+ reenvio manual por escala)
- Audit log persistente (auth, presença, inscrição, mensagens) — Django Admin
- MinIO opcional para mídia em produção

---

## Próximos passos

- [ ] Deploy no Railway (4 serviços + Postgres + Redis)
- [ ] Volume ou R2 para fotos persistentes
- [ ] Observabilidade (Sentry)
- [ ] Cobertura backend meta 80% (CI exige 65%)
