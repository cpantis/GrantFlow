# GrantFlow PRD

## Architecture
- Frontend: React 19 + Tailwind CSS + shadcn/ui (Light theme, 15px base)
- Backend: FastAPI + MongoDB
- AI: OpenAI GPT-5.2 via Emergent LLM Key
- Email: Resend (real transactional emails)
- ONRC: REAL via OpenAPI.ro
- ANAF/SICAP/AFIR: MOCKED with realistic data

## Implemented Features

### Core Platform (Iter 1-3)
- Auth JWT + Email verification + Password reset (Resend)
- Organizations with REAL ONRC data (OpenAPI.ro)
- Projects with 12-state machine
- Documents with OCR pipeline
- AI Agents (GPT-5.2), Marketplace, Admin, Compliance
- RBAC (owner/imputernicit/consultant)
- Light theme, "Firme" terminology, AI Markdown formatting

### EU Funding Module (Iter 7 - NEW)
- Programs → Measures → Sessions hierarchy (PNRR, AFIR, POC, POR)
- SICAP CPV code search with reference prices
- AFIR reference prices search
- 8 draft templates (Plan afaceri, Cerere finanțare, Studiu fezabilitate, Declarații, Memoriu, Deviz)
- Project configuration (type: bunuri/constructii/servicii/mixt, location, theme)
- Legislation upload (guides, evaluation procedures)
- Procurement search engine (SICAP + AFIR)
- AI draft generation from templates
- Conformity evaluation agent (AI checks entire project against grid)
- Project Writing page (/projects/:id/writing) with 6 tabs

## Testing: Backend 100%, Frontend functional

## Backlog
- P0: Real SICAP/AFIR API, ZIP package, ANCPI integration
- P1: Custom draft templates per user, Geoportal location, Document auto-numbering
- P2: Portal export profiles, Notification system
