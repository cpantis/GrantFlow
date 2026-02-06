# GrantFlow PRD - Product Requirements Document

## Problem Statement
GrantFlow - Platformă enterprise end-to-end care automatizează depunerea dosarelor de finanțare: identificare eligibilitate, colectare date oficiale, generare documentație, implementare și monitorizare proiecte finanțate pentru persoane juridice din România.

## Architecture
- **Frontend**: React 19 + Tailwind CSS + shadcn/ui + React Router
- **Backend**: FastAPI (Python) + MongoDB (Motor async driver)
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key (emergentintegrations)
- **Auth**: JWT-based (email + password) + Email verification + Password reset
- **External APIs**: MOCKED (ONRC, ANAF, AFIR, SICAP, OCR)

## What's Been Implemented (Jan 2026)

### Iteration 1 - Core Platform (All 5 Phases)
- Auth (register, login, JWT)
- Organizations (CUI lookup, ONRC mock, ANAF mock, financial data)
- Projects (state machine 12 states, transitions, milestones, expenses)
- Documents (upload, versioning, taxonomy)
- AI Agents (GPT-5.2: eligibility, validation, navigator chat)
- Marketplace (specialist profiles)
- Admin (dashboard, audit log, users)
- Compliance (submission readiness checks)

### Iteration 2 - RBAC + Email + OCR
- **RBAC complet**: Owner/Împuternicit/Consultant permission model
  - Owner: full access (manage members, authorizations, projects, export, audit)
  - Împuternicit: limited by authorization scope (read org, write projects, upload docs)
  - Consultant: project-specific only (read, upload docs, compliance)
  - Authorization expiry enforcement
  - Context-aware permissions (org vs project vs document)
- **Email Verification + Password Reset**:
  - Registration returns verification_token
  - POST /verify-email with token
  - Resend verification endpoint
  - Password reset request (rate-limited, 3 per hour)
  - Password reset confirm with token (1h expiry)
  - Change password with current password
  - Dashboard email verification banner
  - Frontend /reset-password page (request → confirm → done)
  - Frontend /verify-email page
- **OCR Pipeline**:
  - MOCK OCR engine with realistic field extraction
  - Per-document-type templates (CI, bilanț, factură, contract, împuternicire)
  - Per-field confidence scores
  - OCR status: completed / needs_review / low_confidence
  - Human-in-the-loop field correction
  - OCR trigger, view, correct API endpoints
  - Frontend OCR button on each document
  - OCR results modal with confidence visualization
  - Inline field correction for low-confidence fields
  - Audit logging for OCR corrections

## Testing Results
- Iteration 1: Backend 100% (16/16), Frontend 95%
- Iteration 2: Backend 100% (30/30), Frontend 85%

## Backlog

### P0 - Critical
- Real ONRC/ANAF API integration
- ZIP package generation for submission
- Real email sending (SendGrid/Resend)

### P1 - Important
- Real OCR integration (Tesseract/cloud OCR)
- Milestones/expenses management UI forms
- Reimbursement requests
- Document signing workflow
- Notification system

### P2
- KPI dashboard with charts
- Portal export profiles (MySMIS, AFIR, PNRR)
- Multi-language support
- GDPR compliance tools
- Specialist verification workflow

## Next Tasks
1. ZIP package generation for Conform state
2. Milestones/expenses management forms
3. Real email integration
4. Notification system
