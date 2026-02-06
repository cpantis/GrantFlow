# GrantFlow PRD - Product Requirements Document

## Problem Statement
GrantFlow - Platformă enterprise end-to-end care automatizează depunerea dosarelor de finanțare: identificare eligibilitate, colectare date oficiale, generare documentație, implementare și monitorizare proiecte finanțate pentru persoane juridice din România.

## Architecture
- **Frontend**: React 19 + Tailwind CSS + shadcn/ui + React Router
- **Backend**: FastAPI (Python) + MongoDB (Motor async driver)
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key (emergentintegrations)
- **Auth**: JWT-based (email + password)
- **External APIs**: MOCKED (ONRC, ANAF, AFIR, SICAP)

## User Personas
1. **Owner firmă** - Administrator legal, acces complet la workspace firmă
2. **Împuternicit** - Delegat de owner, scope limitat conform împuternicire
3. **Consultant/Specialist** - Expert extern, task-uri atribuite pe proiect
4. **Admin platformă** - Gestiune utilizatori, audit, sistem

## Core Requirements
- Autentificare JWT (register, login, profil)
- Management organizații (CUI lookup ONRC, certificat constatator, date ANAF)
- RBAC (Owner, Împuternicit, Consultant)
- Management documente (upload, versionare, taxonomie, OCR pipeline)
- Motor proiecte cu State Machine (12 stări, tranziții deterministe)
- AI Agents (Eligibilitate, Redactor, Validator, Evaluator, Navigator)
- Conformitate & Eligibilitate (scoring, checklist depunere)
- Marketplace specialiști
- Implementare & Monitorizare (milestones, buget vs cheltuieli)
- Admin & Audit log

## What's Been Implemented (Jan 2026)

### Backend (FastAPI)
- Auth API (register, login, profile, JWT)
- Organizations API (CRUD, CUI lookup, ONRC mock, ANAF mock, financial data)
- Projects API (CRUD, state machine, transitions, milestones, expenses)
- Documents API (upload, versioning, taxonomy, filters)
- Compliance API (eligibility check via GPT-5.2, validation, navigator chat, submission readiness)
- Marketplace API (specialist profiles, listing, assignment)
- Admin API (dashboard, audit log, user management)

### Frontend (React)
- Login & Registration pages (dark theme, Chivo + IBM Plex Sans)
- Dashboard (KPIs, recent projects, organizations)
- Organizations (list, add by CUI, detail with tabs: general, members, financial, CAEN)
- Projects (list, create, detail with state machine visualization, compliance, budget, history, AI Navigator chat)
- Documents (library with upload, filters by org/type/phase, taxonomy badges)
- Compliance (project status overview, AI Navigator chat)
- Marketplace (specialist profiles, create profile)
- Admin (stats, audit log, users, project states)
- Collapsible sidebar navigation
- Protected routes with JWT auth

### AI Integration
- GPT-5.2 via Emergent LLM Key for:
  - Eligibility checking
  - Document coherence validation
  - Navigator chatbot (context-aware)

## Testing Results
- Backend: 100% (16/16 tests passed)
- Frontend: 95% (19/20 tests passed)
- All MOCKED APIs working correctly

## Backlog (P0-P2)

### P0 - Critical
- Real ONRC/ANAF API integration (when available)
- Email verification on registration
- Password reset flow
- ZIP package generation for submission

### P1 - Important
- OCR pipeline integration (document parsing)
- Full RBAC enforcement (owner/imputernicit/consultant permissions)
- Document signing workflow
- Milestones management UI
- Expenses tracking UI
- Reimbursement requests

### P2 - Nice to have
- Specialist verification workflow
- KPI dashboard with charts
- Notification system
- Multi-language support
- Export reports (PDF)
- GDPR compliance tools
- Portal export profiles (MySMIS, AFIR, PNRR)

## Next Tasks
1. Implement ZIP package generation (Conform → download)
2. Add milestone/expense management forms in project detail
3. Implement full RBAC middleware enforcement
4. Add email verification flow
5. OCR document processing pipeline
