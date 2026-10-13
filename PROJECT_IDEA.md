# AI-Powered Land Pre-Purchase Verification System

**Problem Statement:** P5 — Citizen Pre-Purchase Verification
**Intelligence Layer:** P3-style land fraud detection

> Before you buy land, know the risk. A decision-support tool that checks land records, ownership history, mutation and registration data for fraud signals, then explains the risk in simple Bangla or English.

---

## 1. Background and Problem

Buying land is one of the largest financial decisions most families in Bangladesh make, yet it is also one of the riskiest. Land information is spread across several records and offices:

- **Khatian / Porcha (Record of Rights)** – who is recorded as the owner and their share.
- **Dag (Plot) Number** – the physical plot inside a Mouza.
- **Mutation (Namjari / Jomakharij)** – updating the owner's name in the record after a transfer.
- **Registration (Dolil / Deed)** – the registered sale, gift, heba or inheritance documents.
- **Legal status** – pending court cases, government acquisition (khas or acquired land), disputes, mortgages.

An ordinary buyer usually lacks the legal and technical knowledge to read and cross-check all of these documents. Sellers can (deliberately or not) provide incomplete, outdated, conflicting or forged information. Common resulting problems are:

| Risk | What happens |
|---|---|
| Ownership mismatch | The seller is not the person in the current record of rights. |
| Double-selling | The same plot (or share) is sold to more than one buyer. |
| Mutation conflict | Mutation was never done, was done for another person, or conflicts with the deed. |
| Area / share inconsistency | The seller sells more land than they actually own. |
| Legal dispute | The land is under litigation, acquisition or another restriction. |
| Suspicious transfers | Rapid chains of transfers, unusual prices or patterns typical of fraud. |

The result is lost savings, years of court cases, and family and social conflict. Citizens need a simple way to **screen a property before paying any money**.

## 2. Proposed Solution

A web application where a citizen either:

1. **Enters land identifiers**: District → Upazila → Mouza → Dag Number → Khatian Number (and the seller's name), **or**
2. **Uploads documents**: deed (dolil), khatian/porcha, mutation papers (DCR, namjari khatian), tax receipts.

The system then:

- extracts the important fields from the documents (OCR + information extraction),
- collects the available ownership, mutation, registration, legal-status and transfer records,
- cross-checks everything for inconsistencies,
- runs fraud-detection rules and anomaly models,
- calculates a transparent **Low / Medium / High** risk score,
- explains every finding in plain **Bangla or English**, and
- generates a downloadable **Property Verification Report** with recommended next steps.

## 3. End-to-End Workflow

| Step | System Action |
|---|---|
| 1 | Citizen enters District, Upazila, Mouza, Dag and Khatian Number, or uploads documents. |
| 2 | System collects available ownership, mutation, registration, legal-status and transfer information. |
| 3 | OCR and document extraction identify names, Dag, Khatian, area and other key fields. |
| 4 | Verification engine compares information across all records. |
| 5 | Fraud detection checks for double-selling, ownership conflicts, suspicious transfers and inconsistencies. |
| 6 | Risk engine calculates a transparent risk level with weighted reasons. |
| 7 | Citizen receives a simple report explaining issues and recommended next verification steps. |

```
Citizen → Web App → FastAPI → Database / Documents → OCR & Extraction
        → Verification Engine → Fraud Detection → Risk Scoring
        → AI Explanation → Property Report
```

## 4. Main Features

### 4.1 Ownership Verification
Compares the seller's name (and optionally NID) with the current owner in the record of rights. Uses fuzzy / entity matching to handle Bangla–English transliteration and spelling variants (e.g. "Md. Rahim Uddin" vs "মোঃ রহিম উদ্দিন"), and also checks the seller's **share** in jointly owned khatians.

### 4.2 Double-Selling Detection
Finds cases where the same Dag (or the same owner's share in a Dag) appears in multiple registered transactions, or where the total area sold exceeds the area owned.

### 4.3 Ownership History Timeline
Shows the chain of title (previous owners → transfers → current owner) as a visual timeline, highlighting gaps or breaks in the chain.

### 4.4 Mutation Verification
Checks that mutation exists and matches the latest deed: right person, right Dag, right area. Flags missing, outdated or conflicting mutations.

### 4.5 Legal Risk Check
Flags any available information about pending cases, disputes, government acquisition, khas land, mortgages or other restrictions on the land.

### 4.6 Document Upload and OCR
Extracts structured data (names, father's name, Dag, Khatian, Mouza, area, deed number, date) from scanned deeds, porcha and mutation documents in Bangla and English.

### 4.7 Risk Score
A 0–100 score mapped to **Low / Medium / High**, always shown together with the specific reasons that produced it, so the result is never a black box.

### 4.8 AI Explanation
An LLM turns technical findings into short, plain-language explanations in Bangla or English, and answers follow-up questions ("What is mutation and why does it matter?").

### 4.9 Verification Report
A clear, printable/PDF summary: property details, ownership timeline, detected issues, risk score, and recommended next steps (e.g. "verify at the AC Land office", "obtain a certified copy of the khatian", "consult a lawyer").

## 5. Example Scenario

**Input**
- Seller: Rahim
- Dag: 125
- Khatian: 456

The seller claims to be the current owner. The system finds that:

- the available record of rights lists a **different owner**, and
- the **same Dag Number appears in another transaction**.

**Result: HIGH RISK — 91/100**

Detected issues:
1. Ownership mismatch
2. Possible double-selling
3. Conflicting transaction information

**Recommendation:** Do not proceed without further official verification.

## 6. AI and Fraud Detection Layer

The system combines **deterministic rules** (for clear, explainable conflicts) with **machine learning** (where patterns are fuzzy) and an **LLM** (for explanation).

| Layer | Technique | Purpose |
|---|---|---|
| Document understanding | PaddleOCR / Tesseract (Bangla + English), field extraction | Turn scans into structured data |
| Entity matching | Fuzzy string matching, transliteration, ML-based name matching | Decide whether "seller" = "recorded owner" |
| Rule engine | Deterministic checks | Ownership mismatch, duplicate sale, area overflow, missing mutation, legal flags |
| Anomaly detection | Scikit-learn (Isolation Forest, LOF) | Unusual transfer frequency, price, timing or chain patterns |
| Risk scoring | Weighted, explainable scoring | Combine all signals into a 0–100 score with reasons |
| AI explanation | Local / open-source LLM | Plain Bangla/English explanation and Q&A |
| Orchestration (optional) | LangGraph | Multi-step AI workflow: extract → verify → detect → explain |

### Example rules and weights

| Check | Signal | Example weight |
|---|---|---|
| Seller ≠ recorded owner | Ownership mismatch | +40 |
| Same Dag/share in multiple active sales | Double-selling | +35 |
| Area being sold > area owned | Area overflow | +25 |
| Mutation missing or in another name | Mutation conflict | +20 |
| Pending case / acquisition / khas | Legal risk | +30 |
| Anomalous transfer pattern (ML) | Suspicious activity | +10 to +20 |
| Document fields disagree with records | Inconsistency | +10 |

Score is capped at 100. Suggested bands: **0–30 Low**, **31–60 Medium**, **61–100 High**.

## 7. Technical Architecture

| Component | Technology |
|---|---|
| Frontend | React / Next.js (Bangla + English UI) |
| Backend API | FastAPI (Python) |
| Database | PostgreSQL + PostGIS (records + plot geometry) |
| OCR | PaddleOCR or Tesseract |
| ML | Scikit-learn (anomaly detection, entity matching) |
| AI | Local / open-source LLM for explanation and document reasoning |
| Workflow (optional) | LangGraph |

### Core data model (simplified)

- **Location**: district, upazila, mouza
- **Plot (Dag)**: dag_no, mouza, area, geometry (PostGIS)
- **Khatian**: khatian_no, plot, owners + shares
- **Person**: name, father's name, NID (optional)
- **Deed / Transaction**: deed_no, date, seller(s), buyer(s), plot, area, price
- **Mutation**: case_no, khatian, new owner, date, status
- **Legal Status**: plot, type (case / acquisition / khas / mortgage), status
- **Verification Report**: inputs, findings, score, explanation, timestamp

### Main API endpoints (example)

- `POST /verify` – submit land identifiers and seller info
- `POST /documents` – upload and OCR a document
- `GET /property/{dag}/history` – ownership timeline
- `GET /report/{id}` – fetch / download the verification report

## 8. Users and Impact

- **Primary users:** ordinary land buyers, especially first-time and rural buyers.
- **Secondary users:** lawyers, real-estate agents, banks (loan collateral checks), NGOs.

**Impact:** fewer fraud victims, fewer land disputes and court cases, more informed decisions, and greater trust in land transactions. It also turns P3-style fraud detection into a practical, citizen-facing product.

## 9. Why This Approach Is Strong

- It directly addresses the citizen's need to make a **safer decision before buying** land (P5).
- **Fraud detection (P3) becomes the intelligence layer** behind the product.
- It combines **explainable rules** with ML and LLMs, so results are trustworthy and understandable.
- It has clear **social impact** while still showing strong AI/ML and backend engineering depth.

## 10. Hackathon Prototype Scope

**In scope**
- Synthetic dataset of mouzas, dags, khatians, owners, deeds, mutations and legal flags (including planted fraud cases).
- Search form plus document upload with OCR.
- Rule engine, a simple anomaly model, and the risk score.
- LLM explanation in Bangla and English.
- Ownership timeline and a downloadable report.

**Demo flow**
1. Search a "clean" property, which returns **Low risk**.
2. Search the Rahim / Dag 125 example, which returns **High risk (91/100)** with reasons.
3. Upload a deed, watch the fields get extracted, and see the mismatch detected.
4. Ask the AI assistant, in Bangla, why the property is risky.

## 11. Important Limitations and Ethics

- Use **synthetic or authorized sample data** unless official government data access is available.
- The system **does not provide official legal verification** without authorized integration with government land systems.
- It is a **decision-support and risk-screening tool**, not a replacement for official verification or legal advice.
- Personal data (names, NIDs, documents) must be handled securely and with consent.
- The quality of results depends on the completeness and accuracy of the available records.

## 12. Future Scope

- Integration with official land portals (e-Mutation, e-Porcha, land registration systems) through authorized APIs.
- Map-based plot view and boundary checks using PostGIS and cadastral maps.
- Mobile app and SMS/USSD access for rural users.
- Fraud alerts and a watchlist for a plot ("notify me if this Dag is transferred").
- Verification support for banks and lawyers.
