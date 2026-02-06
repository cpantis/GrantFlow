# GrantFlow PRD

## Architecture
- Frontend: React 19 + Tailwind CSS + shadcn/ui (Light theme)
- Backend: FastAPI + MongoDB
- AI: OpenAI GPT-5.2 via Emergent LLM Key
- Email: Resend (real transactional emails)
- External APIs: MOCKED (ONRC, ANAF, OCR)

## Implemented Features

### Iteration 1 - Core Platform
- Auth, Organizations, Projects (12-state machine), Documents, AI Agents, Marketplace, Admin, Compliance

### Iteration 2 - RBAC + Email + OCR
- Full RBAC (owner/imputernicit/consultant), Email verification + Password reset, OCR Pipeline

### Iteration 3 - UI Polish + Real Email
- Light/white professional futuristic theme
- "Organizații" → "Firme" throughout
- Resend email integration (verification + password reset)
- AI response markdown formatting (react-markdown)

## Testing
- Iter 1: Backend 100% (16/16)
- Iter 2: Backend 100% (30/30)
- Iter 3: Backend 100% (30/30), Frontend 100%

## Backlog
- P0: ZIP package generation, Real ONRC/ANAF APIs
- P1: Milestones/expenses UI, Document signing, Notifications
- P2: KPI charts, Portal exports, Multi-language, GDPR tools
