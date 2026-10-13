# JomiCheck — কেনার আগে যাচাই করুন (Check Before You Buy)

Lawyer-grade pre-purchase land verification for citizens of Bangladesh.

A buyer enters the District, Upazila, Mouza, Dag, Khatian and the seller's name. JomiCheck checks the land the way an experienced land lawyer would — ownership, inheritance shares, mutation, litigation, khas and acquisition status, mortgages, prior agreements, power of attorney, survey lineage and fraud patterns — and returns a transparent risk score where **every finding cites the relevant law** and is explained in plain Bangla or English. Each report is sealed with a SHA-256 hash and a QR code so altered copies can be detected.

**LandTech 2026 — LandTech Innovation Hackathon**
Track: Digital Land Records, Verification & Digitization
Problem statement: **P5 — Citizen Pre-Purchase Verification**, with **P3 — Fraud & Double-Selling Detection** as the intelligence layer and **P2**-style hashing for report integrity.

> JomiCheck is a decision-support and risk-screening tool. It is not official legal verification or legal advice. **All data in this prototype is synthetic.**

---

## Features

| Area | What JomiCheck does |
|---|---|
| Ownership | Matches the seller (Bangla or English name, fuzzy and prefix-aware) with recorded owners, heirs, deed buyers and attorneys |
| Double-selling | Detects land the seller already sold by registered deed |
| Inheritance | Faraiz calculator (spouse, sons, daughters, father, mother; 'awl, radd, Umariyyatan) and over-selling detection for heirs |
| Mutation | Flags land still in a deceased owner's name or a deed buyer without approved mutation (Registration Act s.52A) |
| Land status | Khas, vested, abandoned, waqf, debottor, forest land; acquisition notices |
| Litigation | Civil suits, Land Survey Tribunal cases, Section 144, injunctions on transfer |
| Encumbrance | Active mortgages and registered bainanama with other buyers |
| Power of attorney | Revoked, unregistered, management-only, or principal deceased |
| Minors | Sale of a minor's share without court permission |
| Pre-emption | Hak-e-Shufa exposure from co-sharers (SAT Act s.96) |
| Survey lineage | CS → SA → RS → BS → mutation chain, with unexplained owner changes flagged |
| Fraud patterns | Rapid repeated transfers, deeds far below mouza rate, deeds by people with no recorded right |
| Purchase-intent alert | Warns when other buyers checked the same plot in the last 30 days |
| Report | Risk gauge, findings with law and action, ownership timeline, document checklist, seller questions, site-visit checklist, next steps, print/PDF |
| Khatian view | Latest record of rights in the official column layout: serial, owner and father's name, share in ana-gonda-kora-kranti, dag, land class, area, remarks, mutation case |
| Purchase cost | Stamp duty, registration fee, local government tax, source tax and mutation fees by area type; flags deeds priced below the government mouza minimum |
| Unit converter | Decimal (shotok), katha, bigha, acre, ojutangsho, square feet, square metre, hectare |
| Integrity | SHA-256 seal + QR code; `/verify-report` shows whether a copy matches the registry |
| Assistant | "Ask about this report" in Bangla/English — built-in legal glossary offline, or any OpenAI-compatible LLM grounded only on the report facts |
| Records panel | Django admin over all synthetic land records |

### Risk scoring

| Tier | Examples | Effect |
|---|---|---|
| Critical | Seller not the owner, double-selling, khas/vested land, acquisition, injunction, invalid POA | Result is **HIGH** regardless of score |
| Major | Litigation, survey break, over-selling, minor's land, mortgage, rapid transfers, mutation missing, prior bainanama | +20 to +30 |
| Minor | Conflicting deed, pre-emption, wrong khatian, under-priced deed, tax arrears | +5 to +10 |

Score is capped at 100. LOW 0–30, MEDIUM 31–60, HIGH 61–100.

---

## Architecture

```
Citizen ─▶ Next.js web app ─▶ Django REST API ─▶ Verification engine ─▶ Sealed report
                                   │                 ├─ seller resolution & name matching
                                   │                 ├─ Faraiz inheritance
                                   │                 ├─ legal / fraud / lineage rules
                                   │                 └─ guidance (documents, questions, steps)
                                   ├─ Land records DB (synthetic)
                                   ├─ Report integrity (SHA-256 + QR)
                                   └─ Assistant (built-in glossary or LLM)
```

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, lucide-react |
| Backend | Django 6, Django REST Framework, django-cors-headers |
| Matching | RapidFuzz |
| Integrity | hashlib (SHA-256), qrcode (SVG) |
| Database | SQLite for the prototype (PostgreSQL-ready) |

```
backend/
  land/            models, admin, synthetic data generator (seed.py), location & demo APIs
  verification/    engine.py, catalog.py (rules + bilingual text + law), faraiz.py,
                   matching.py, guidance.py, assistant.py, tests/
  reports/         Report model, integrity.py (hash + QR), report APIs, tests
  costs/           rates.py (all purchase-cost rates in one place), calculator, API, tests
frontend/src/
  app/             /, /verify, /report/[id], /verify-report, /inheritance, /costs
  components/      gauge, findings, timeline, lineage, inheritance table, assistant, integrity
  lib/             API client, Bangla/English i18n
```

---

## Running locally

Requirements: Python 3.12+, Node.js 20+.

### Backend

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo            # loads the synthetic dataset
python manage.py createsuperuser      # optional, for the records panel at /admin
python manage.py runserver 8000
```

### Frontend

```bash
cd frontend
cp .env.example .env.local            # NEXT_PUBLIC_API_URL=http://localhost:8000/api
npm install
npm run dev
```

Open http://localhost:3000.

### AI assistant (Gemma via Google AI Studio)

The "Ask about this report" assistant uses Google's open **Gemma** model through the Google AI Studio (Gemini API) OpenAI-compatible endpoint.

```bash
cd backend
cp .env.example .env                  # then paste your key from https://aistudio.google.com/apikey
python manage.py check_llm --list     # Gemma models your key can use
python manage.py check_llm            # sends a test question and prints the answer
```

Set `LLM_MODEL` in `backend/.env` to one of the listed Gemma models. Any other OpenAI-compatible server (e.g. a local Ollama) works by changing `LLM_API_URL` and `LLM_MODEL`. Without a key, the assistant falls back to its built-in bilingual glossary, and each answer in the UI shows which source produced it.

Only the computed report (synthetic data) is sent to the model. The risk score and flags always come from the rule engine; the model only explains them.

### Tests

```bash
cd backend && python manage.py test        # 35 tests: Faraiz, demo scenarios, khatian notation, costs, API, tamper detection
cd frontend && npx tsc --noEmit && npx eslint src && npm run build
```

---

## Demo scenarios

All 13 are on the home page and in the "quick fill" list on `/verify`.

| # | Scenario | Dag / Mouza | Seller | Result |
|---|---|---|---|---|
| 1 | Clean property | 101 Rampur | Jamal Hossain | LOW 6 |
| 2 | Ownership mismatch + double-selling | 125 Rampur | Rahim Uddin | HIGH 91 |
| 3 | Heir selling more than Faraiz share | 118 Rampur | Karim Mia | MEDIUM 55 |
| 4 | Bought by deed, mutation rejected | 132 Rampur | Shafiq Ahmed | MEDIUM 34 |
| 5 | Khas land | 140 Charabag | Bashir Ahmed | HIGH 80 |
| 6 | Government acquisition | 150 Charabag | Liton Das | HIGH 40 |
| 7 | Suit with injunction | 160 Charabag | Habib Ullah | HIGH 70 |
| 8 | Bank mortgage | 170 Charabag | Sumon Ali | MEDIUM 31 |
| 9 | Revoked power of attorney | 180 Charabag | Faruk Ahmed | HIGH 35 |
| 10 | Prior bainanama by co-owner | 190 Notunhat | Delwar Hossain | MEDIUM 36 |
| 11 | Break in survey records | 205 Notunhat | Rafiq Mondol | MEDIUM 36 |
| 12 | Rapid low-price transfers | 215 Notunhat | Imran Hossain | MEDIUM 33 |
| 13 | Widow selling minor heir's land | 225 Shantipur | Nasima Begum | HIGH 80 |

---

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/locations/` | District → Upazila → Mouza tree |
| GET | `/api/mouzas/<id>/plots/` | Dag numbers in a mouza |
| GET | `/api/demo-cases/` | Planted demo scenarios |
| POST | `/api/verify/` | Run verification and store a sealed report |
| POST | `/api/inheritance/` | Standalone Faraiz calculator |
| POST | `/api/costs/estimate/` | Purchase cost estimate (`price_bdt`, `area_type`, optional `area_acre` + `mouza_rate_per_acre`) |
| GET | `/api/reports/<id>/` | Report with QR code |
| GET | `/api/reports/<id>/verify/?h=<sha256>` | Authenticity check |
| POST | `/api/reports/<id>/ask/` | Report assistant |

---

## Data sources

**All land records are synthetic**, generated by `backend/land/seed.py` (`python manage.py seed_demo`). Every person, plot, khatian, deed, mutation, case, mortgage and power of attorney is fictional; NIDs are dummy numbers such as `0000000001`. Only district and upazila names are real public administrative names. No real personal data is used, and no government portal is accessed, scraped or queried.

Purchase-cost rates in `backend/costs/rates.py` and the khatian column layout were compiled by the team from public information in October 2026. They are indicative; the app tells users to confirm them at the sub-registry and AC Land office.

## Legal references

The rule catalog (`backend/verification/catalog.py`) cites the Registration Act 1908 (s.17A, s.52A), Transfer of Property Act 1882 (s.53C, s.58), State Acquisition and Tenancy Act 1950 (s.96, s.145A), Land Crime Prevention and Remedy Act 2023, Land Development Tax Act 2023, Power of Attorney Act 2012, Acquisition and Requisition of Immovable Property Act 2017, Vested Property Return Act 2001, Guardians and Wards Act 1890, Code of Civil Procedure Order XXXIX and Muslim personal law (Faraiz). These are for decision support and are being reviewed with our faculty mentor and the Department of Law.

## AI tools used

<!-- Team: keep this section accurate and complete before submission. -->

- **Cursor (AI coding assistant)** — used to help scaffold the Django and Next.js projects, draft code for the verification engine, data generator, API and UI, and write tests and documentation. All code was reviewed, run and tested by the team, and both team members can explain it.
- **Gemma (Google, via Google AI Studio)** — powers the in-app report assistant. It receives only the computed report for synthetic data, answers in Bangla or English, and never decides the risk; the rule engine does.

## Open-source libraries

Django (BSD-3), Django REST Framework (BSD-3), django-cors-headers (MIT), qrcode (BSD), RapidFuzz (MIT), Next.js (MIT), React (MIT), Tailwind CSS (MIT), lucide-react (ISC), IBM Plex and Noto Sans Bengali fonts (SIL OFL 1.1).

## Changes since Round 1

_To be filled in before the Final Round._

## Team

| Role | Name |
|---|---|
| Team Leader (student) | _TBD_ |
| Student member | _TBD_ |
| Faculty mentor | _TBD_ |
| Industry mentor | _TBD_ |
