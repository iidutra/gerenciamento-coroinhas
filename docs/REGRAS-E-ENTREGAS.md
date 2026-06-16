# Pastoral dos Coroinhas — Regras de negócio e entregas

Documento de referência com **regras de domínio**, **permissões**, **configurações** e **o que foi implementado** nas sessões de desenvolvimento (até jun/2026).

---

## 1. Pessoas e perfis

```
Usuario (login)
  ├── Coordenador / Secretario / Padre  → staff pastoral (sem FK de domínio)
  ├── Pai       → FK Responsavel → M2M Coroinha (filhos)
  └── Coroinha  → FK Coroinha (conta opcional do próprio coroinha)

Coroinha (entidade pastoral — existe sem login)
Responsavel (pai/mãe — existe sem login; vinculado na inscrição ou cadastro)
```

| Perfil | Login | Destino após login |
|--------|-------|-------------------|
| Coordenador | e-mail | `/dashboard` — gestão completa |
| Secretário | e-mail | `/dashboard` — gestão (coordenador + secretário) |
| Padre | e-mail | `/dashboard` — **somente leitura** nas áreas de gestão |
| Pai | CPF | `/portal` |
| Coroinha | CPF | `/portal` |

- Login unificado: **CPF ou e-mail** na mesma tela; o backend detecta pelo formato.
- Staff usa e-mail; família usa CPF.

### Senha inicial e primeiro acesso

- Senha inicial após aprovação de inscrição: **últimos 4 dígitos do CPF** (`senha_inicial_cpf`).
- Conta criada com `must_change_password=True` — troca obrigatória no 1º login.
- Coroinha menor **sem CPF** na ficha: só o responsável (Pai) acessa o portal por ele.
- Recuperação de senha (família): CPF + **data de nascimento** (do coroinha ou de um filho, no caso do pai) + nova senha.

---

## 2. Permissões (API)

| Classe | Quem |
|--------|------|
| `IsCoordenador` | Apenas Coordenador |
| `IsGestorCoroinhas` | Coordenador **ou** Secretário |
| `IsStaffPastoral` | Coordenador, Secretário **ou** Padre |
| `IsFamilia` | Pai ou Coroinha |
| `IsFamiliaOuStaff` | Família ou staff (preview portal) |

### Matriz resumida

| Ação | Coordenador | Secretário | Padre | Pai/Coroinha |
|------|:-----------:|:----------:|:-----:|:------------:|
| Ver dashboard, listagens | ✓ | ✓ | ✓ (leitura) | — |
| Alterar coroinhas, escalas, presença, formação | ✓ | ✓ | — | — |
| Aprovar/rejeitar inscrições | ✓ | ✓ | — | — |
| Abrir/fechar inscrições online | ✓ | ✓ | — | — |
| Cadastrar coroinha manualmente | ✓ | ✓ | — | — |
| Enviar mensagens (Comunicação) | ✓ | ✓ | — | — |
| Gerenciar usuários staff | ✓ | — | — | — |
| Portal família | — | — | — | ✓ |
| Inscrição pública | — | — | — | ✓ (se abertas) |

Frontend espelha com `podeGerenciarCoroinhas()` (Coordenador + Secretário) e banner de leitura para Padre.

---

## 3. Inscrições

### Fluxo público

1. Visitante acessa `/inscricao` **somente se** `inscricoes_abertas=true`.
2. Envia ficha (JSON ou multipart com foto) → `POST /api/v1/inscricoes/publica`.
3. Validações: CPF responsável válido; nome e data de nascimento do coroinha obrigatórios.
4. Rate limit por IP: padrão **10 tentativas / hora** (`INSCRICAO_RATE_LIMIT_*`).
5. Inscrição fica `Pendente`; dados ficam em snapshot JSON imutável (`Inscricao.dados`).

### Controle de abertura

Modelo **`ConfiguracaoParoquial`** (registro único, `pk=1`):

| Fonte | Prioridade |
|-------|------------|
| Env `INSCRICOES_ABERTAS=True` | **Sobrescreve tudo** — força abertas |
| Flag no banco `inscricoes_abertas` | Controlada pelo coordenador/secretário |
| Padrão | **Fechadas** |

Endpoints:

- `GET /api/v1/config/publica` — público; home e `/inscricao` consultam
- `GET /api/v1/config/inscricoes` — staff
- `PATCH /api/v1/config/inscricoes` — gestores (`{ "inscricoes_abertas": true|false }`)

UI:

- Home: banner dourado “Inscrições abertas” + link (`HomeHeroActions`)
- Dashboard → Inscrições: toggle abrir/fechar
- Link de inscrição **oculto** na home quando fechado

### Aprovação e rejeição

**Aprovar** (`InscricaoService.aprovar`):

- Cria/atualiza `Responsavel` e `Coroinha` (status `EmFormacao`)
- Transfere foto pendente da inscrição
- Cria `Usuario` Pai (CPF responsável) e Coroinha (se CPF válido informado)
- Notifica responsável (opcional, padrão ligado) via WhatsApp/e-mail
- Audit log: `INSCRICAO_APROVADA`

**Rejeitar**:

- Status `Rejeitada`; mensagem opcional ao responsável
- Audit log: `INSCRICAO_REJEITADA`

Sacramentos (batizado, 1ª Eucaristia, crisma): booleanos na ficha — **não bloqueiam** aprovação.

### Cadastro manual (sem inscrição online)

- Dashboard → Coroinhas → **Cadastrar coroinha**
- `POST /api/v1/coroinhas/` — Coordenador/Secretário
- Não cria usuário automaticamente (apenas entidade `Coroinha`)
- Uso típico: pastoral já existente, inscrições fechadas

---

## 4. Escalas e presença

### Montagem de escala

- **Sorteio equilibrado**: prioriza quem serviu **menos nos últimos 90 dias**; exclui quem já está escalado **no mesmo dia**.
- **Seleção manual**: lista explícita de IDs.
- Candidatos: coroinhas `Ativo` ou `EmFormacao`.
- Uma escala por par `(data, missa)`.

### Notificação automática

- Ao montar escala: se `NOTIFICACAO_ESCALA_AUTOMATICA=True` (padrão), dispara mensagem.
- Canal padrão: `NOTIFICACAO_ESCALA_CANAL=WhatsApp` (ou Email).
- Template padrão usa `{nome}`, `{data}`, `{missa}`, `{horario}`, `{funcao}`.
- Reenvio manual por escala no dashboard.

### Presença

- Por item de escala: Presente / Ausente.
- Audit: quem registrou.
- **Relatório — taxa de presença** = presenças / (presenças + faltas); escalas futuras sem registro **não entram** no denominador.

---

## 5. Comunicação (WhatsApp e e-mail)

### Canais

- Mensagens em massa: Dashboard → Comunicação
- Templates: `{nome}`, `{escala}`, `{idade}`, `{funcao}`, `{data}`, `{missa}`, `{horario}`
- Processamento **assíncrono** via Celery (`processar_mensagem`)

### Modo simulação vs envio real

| Canal | Configurado quando | Sem config |
|-------|-------------------|------------|
| E-mail | `EMAIL_HOST` definido | Registra histórico, `simulacao=true` |
| WhatsApp | Ver provedor abaixo | Registra histórico, `simulacao=true` |

Status no painel: `GET /api/v1/config/comunicacao` (staff).

### WhatsApp — provedores (`WHATSAPP_PROVIDER`)

| Provedor | Variáveis | Formato |
|----------|-----------|---------|
| **`waha`** (recomendado) | Serviço Railway `/waha`; `WHATSAPP_API_URL`, `WHATSAPP_API_TOKEN`, `WHATSAPP_WAHA_SESSION` | POST `/api/sendText` — `{session, chatId: "5569...@c.us", text}` + header `X-Api-Key` |
| `http` | `WHATSAPP_API_URL`, opcional `WHATSAPP_API_TOKEN` | POST `{ "to": "5569...", "message": "..." }` |
| `evolution` | URL `.../message/sendText/{instancia}`, `WHATSAPP_API_TOKEN` (header `apikey`) | POST `{ "number", "text" }` |
| `meta` | `WHATSAPP_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` | Graph API v21.0 |

Telefones normalizados para E.164 BR (`WHATSAPP_DEFAULT_COUNTRY_CODE=55`).

### Notificações de inscrição

Ao aprovar/rejeitar, `InscricaoNotificacaoService` tenta:

1. E-mail do responsável
2. WhatsApp do responsável (ou telefone principal)
3. Telefone do coroinha (fallback)

---

## 6. Portal família

- Rota: `/portal` (Pai e Coroinha)
- Pai com vários filhos: seleciona coroinha → mesma visão que o filho teria
- Escopo **read-only**: escalas, presenças, formações, notícias
- Staff preview: `/dashboard/portal`
- **Evento do mês**: notícia destacada no portal e listagem — ver seção 8

---

## 7. Conteúdo e notícias

- Notícias ordenadas **cronologicamente** (data do evento ou publicação)
- Agrupamento por mês no dashboard
- Importação calendário paroquial 2026: `python manage.py importar_calendario_paroquial`
- Documentos do portal: URL externa (não upload de arquivo)

---

## 8. Regras de UI implementadas

### Evento do mês (`eventoDoMes`)

1. Filtra notícias do mês corrente
2. Preferência: itens com `destaque`; senão, com `data_evento`
3. Entre futuros: o **mais próximo**; se só passados: o **mais recente**

Usado em: `PortalCorpo`, dashboard de notícias (sem filtro/busca ativos).

### UX mobile — navegação

- Header fixo mobile (`app-mobile-header`): menu + título + **Sair**
- Sidebar: link Sair no rodapé (desktop e drawer)
- `PageHeader`: botão Sair visível só em `lg+` (evita duplicata no mobile)

### Avatar

- Foto do coroinha ou avatar gerado por iniciais/nome

---

## 9. Segurança e limites

| Recurso | Padrão | Variáveis |
|---------|--------|-----------|
| Login / recuperar senha | 5 falhas / hora por CPF+e-mail+IP | `AUTH_RATE_LIMIT_*` |
| Inscrição pública | 10 envios / hora por IP | `INSCRICAO_RATE_LIMIT_*` |

- Rate limit de auth conta **apenas tentativas falhas**; sucesso limpa o contador.
- JWT para API autenticada; audit log persistente (login, presença, inscrição, mensagens).

---

## 10. Infraestrutura (Railway)

| Serviço | Função |
|---------|--------|
| API | Django + Gunicorn |
| Worker | Celery (mensagens WhatsApp) |
| Frontend | Next.js |
| **WAHA** | WhatsApp HTTP API — volume `/app/.sessions` |
| PostgreSQL | Dados |
| Redis | Cache + fila Celery |

### Mídia (fotos)

- Volume Railway em `/app/media` + `SERVE_MEDIA=True`
- URLs: `https://<api>/media/coroinhas/fotos/...`
- Alternativa: Cloudflare R2 + `USE_S3=True`
- PDF de escala do mês lê foto via storage configurado

### URLs produção (referência)

- API: `https://gerenciamento-coroinhas-production.up.railway.app`
- Frontend: `https://coroinhas-frontend-production.up.railway.app`
- WAHA: `https://waha-production-59ae.up.railway.app` (dashboard em `/dashboard`)

---

## 11. Cronologia do que foi feito

Commits publicados em `main` (GitHub → deploy Railway):

| Commit | Entrega |
|--------|---------|
| `576e242` | Infra Railway, notificações de escala, portal família, UX mobile inicial |
| `ea9d931` | Monorepo Railway (root `/backend`, `/frontend`), scripts deploy |
| `792a0d7` | Avatar padrão, notícias cronológicas, rate limit auth só em falhas |
| `ea1f4ec` | **Evento do mês** no portal e notícias |
| `bf71a07` | **Storage persistente** de fotos (volume `/app/media`, `setup_media`) |
| `59e6533` | **Inscrições controladas** pelo coordenador, cadastro manual, aprovar/rejeitar com mensagem |

### Em andamento (local, ainda não commitado)

| Área | Entrega |
|------|---------|
| WhatsApp | `WhatsAppService` (http / evolution / meta), normalização E.164, `GET /config/comunicacao`, banner no painel Comunicação, testes `test_whatsapp.py` |
| UX mobile | Botão **Sair** no header mobile + sidebar; oculto duplicado no `PageHeader` |
| Docs | Este arquivo, `.env.railway.example`, README (seção WhatsApp) |

---

## 12. Pendências conhecidas

- [ ] Commit/push das alterações WhatsApp + botão Sair
- [ ] Configurar credenciais WhatsApp no Railway (Meta, Evolution ou webhook)
- [ ] Configurar SMTP (opcional)
- [ ] `INSCRICOES_ABERTAS=False` em produção (dashboard Railway se CLI falhar)
- [ ] Trocar senha do coordenador de produção
- [ ] Sentry / observabilidade
- [ ] Cobertura de testes backend meta 80% (CI exige 65%)
- [ ] Corrigir texto da notificação de aprovação (“6 primeiros dígitos”) — código usa **4 últimos** dígitos do CPF

---

## 13. Endpoints de configuração (resumo)

| Método | Rota | Quem | Retorno |
|--------|------|------|---------|
| GET | `/api/v1/config/publica` | Público | `{ inscricoes_abertas }` |
| GET | `/api/v1/config/inscricoes` | Staff | status + quem atualizou |
| PATCH | `/api/v1/config/inscricoes` | Gestor | toggle inscrições |
| GET | `/api/v1/config/comunicacao` | Staff | email + whatsapp configurados, provedor, simulação |

---

## 14. Arquivos de referência no código

| Tema | Arquivos principais |
|------|---------------------|
| Domínio (Cursor rule) | `.cursor/rules/coroinhas-domain.mdc` |
| Inscrições | `backend/apps/membership/services/inscricao_service.py`, `configuracao_service.py` |
| WhatsApp | `backend/apps/communication/services/whatsapp_service.py` |
| Escalas | `backend/apps/scheduling/services/escala_service.py` |
| Permissões | `backend/apps/identity/permissions.py` |
| Portal / evento mês | `frontend/src/lib/noticias.ts`, `PortalCorpo.tsx` |
| Nav mobile | `frontend/src/components/AppShell.tsx`, `Sidebar.tsx` |
| Env produção | `.env.railway.example`, `.env.prod.example` |
