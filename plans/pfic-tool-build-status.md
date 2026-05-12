# PFIC Tool — Build Status

**Last updated:** 2026-05-13  
**Phase:** MVP COMPLETE + Results UI enhanced  
**Test status:** 71/71 passing  
**Frontend build:** ✅ Clean (0 TypeScript errors)

---

## How to Run

```bash
cd /mnt/d/claude/pfic-tool
./start.sh
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs

**DB:** SQLite auto-created at `backend/pfic_tool_dev.db` on first run. No PostgreSQL needed locally.  
For production: set `DATABASE_URL=postgresql://user:pass@host/pfic_tool`

---

## What Changed (2026-05-13 session)

### Results Page Redesign (Step 4)
`PFICWorkspace.tsx` — Step 4 completely rewritten to show full step-by-step breakdown:

1. **125% Test panel** — 4 info cards: current distribution, prior 3-year average, benchmark (×1.25), excess distribution
2. **Step 1: Holding Period** — first year → tax year, total days, daily rate (excess ÷ total days)
3. **Step 2: Year-by-Year Allocation & Tax** — table with: year, days, allocated amount, effective rate, deferred tax (current year shows "ordinary income" badge, no tax/interest)
4. **Step 3: §6621 Interest** — table per prior-PFIC year: deferred tax, filing deadline start date, interest amount; COVID extension years flagged with ⚠ COVID badge (2019 → 2020-07-15; 2020 → 2021-05-17)
5. **Form 8621 Part V Summary** — lines 15e(1), 15e(2), 16c, 16f, grand total (16c+f)

### UI Fixes
- Amount columns in transaction table and allocation table: added `pr-8` spacing between amount and next column
- Delete transaction: confirmation dialog before delete
- No auto-selection of tax year — user must explicitly pick the year they want to calculate

### Live Data: CINDY / BOT PFIC
- Client "CINDY" inserted with holding "BOT" (§1291 method, first PFIC year 2015)
- Transactions: 2015-09-15 purchase (996.819 units @ $9,400); distributions 2019–2022 ($9,203.35 / $14,533.19 / $17,747.52 / $18,013.71)
- 2022 calculation verified: excess $728.69, additional tax $238.65, interest $42.25, **grand total $280.90**

---

## Complete File Map

### Backend `pfic-tool/backend/`

| Module | File | Status |
|--------|------|--------|
| Calculation engine | `pfic_engine/core/decimal_utils.py` | ✅ |
| | `pfic_engine/core/tax_constants.py` | ✅ 157 §6621 rates, max tax rates, §7503 deadlines |
| | `pfic_engine/core/date_utils.py` | ✅ |
| | `pfic_engine/section_1291/excess_dist.py` | ✅ 125% test |
| | `pfic_engine/section_1291/daily_allocation.py` | ✅ |
| | `pfic_engine/section_1291/interest.py` | ✅ §6622 daily compound |
| | `pfic_engine/section_1291/deferred_tax.py` | ✅ |
| | `pfic_engine/lot/fifo.py` | ✅ FIFO lot matching |
| | `pfic_engine/lot/lot_tracker.py` | ✅ |
| | `pfic_engine/verification/cross_check.py` | ✅ 5 internal consistency checks |
| Output | `pfic_engine/output/pdf_generator.py` | ✅ Form 8621 workpaper PDF |
| | `pfic_engine/output/line16a_statement.py` | ✅ §6501(c)(8) daily allocation attachment |
| | `pfic_engine/output/excel_workpaper.py` | ✅ 3-sheet Excel workpapers |
| Database | `api/db/models.py` | ✅ SQLAlchemy ORM, all 10 tables |
| | `api/db/seed_static.py` | ✅ Idempotent seed |
| API | `api/main.py` | ✅ FastAPI app, CORS, auto-seed on startup |
| | `api/auth.py` | ✅ JWT register/login (router not yet mounted) |
| | `api/deps.py` | ✅ No-auth default user for dev |
| | `api/routes/clients.py` | ✅ CRUD |
| | `api/routes/holdings.py` | ✅ CRUD |
| | `api/routes/transactions.py` | ✅ CRUD + CSV import |
| | `api/routes/calculations.py` | ✅ Run + retrieve |
| | `api/routes/exports.py` | ✅ PDF / Line16a / Excel download |

### Frontend `pfic-tool/frontend/src/`

| File | Status | Notes |
|------|--------|-------|
| `api.ts` | ✅ | Typed API client for all endpoints |
| `App.tsx` | ✅ | React Router: Dashboard / ClientDetail / PFICWorkspace |
| `pages/Dashboard.tsx` | ✅ | Client list + new client form |
| `pages/ClientDetail.tsx` | ✅ | Holdings list + new holding form |
| `pages/PFICWorkspace.tsx` | ✅ | 5-step wizard — Step 4 redesigned 2026-05-13 |

---

## Test Coverage

| File | Tests |
|------|-------|
| `test_tax_constants.py` | 12 — rate table, deadlines, COVID dates |
| `test_excess_dist.py` | 10 — 125% test, edge cases |
| `test_daily_allocation.py` | 9 — classification, rounding, leap year |
| `test_interest.py` | 11 — §6622 compounding, COVID deadline integration |
| `test_fifo.py` | 8 — lot matching, splitting, LotTracker |
| `test_deferred_tax.py` | 7 — per-year tax, COVID interest start |
| `test_db.py` | 14 — tables, seed, spot-checks, CRUD, JSONB |
| **Total** | **71 / 71** |

---

## Known Limitations (MVP scope)

- USD-only (no FX engine) — multi-currency is Phase 2A
- §1296 MTM and QEF not implemented — Phase 2B/2C
- Single user per account, no firm-level access control — Phase 2D
- Auth router exists (`api/auth.py`) but not mounted in `main.py` — all requests share a default user
- §6621 rate table needs audit against IRS IRB publications before production filing use (2026 Q2 may be coded as 7% — IRS confirmed 6%)

---

## What's Left for Full Production

- Week 8: E2E testing with 5 complete scenarios, security review, Railway/Render deploy
- P0: Audit §6621 rate table against IRS IRBs 1987–present; fix 2026 Q2 rate
- P1: Quarterly interest breakdown in Excel workpaper; IRC citations on Line 16a PDF; Interest Verifier panel
- Phase 2A: Multi-currency (OANDA spot rate + FRED fallback)
- Phase 2B/C: §1296 MTM, QEF elections
- Phase 2D: Multi-user / multi-firm, mount auth router
