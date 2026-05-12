# PFIC Tool — Build Status

**Last updated:** 2026-05-12  
**Phase:** MVP COMPLETE (Weeks 1–7)  
**Test status:** 71/71 passing  
**Frontend build:** ✅ Clean (0 errors)

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
| | `pfic_engine/verification/cross_check.py` | ✅ |
| Output | `pfic_engine/output/pdf_generator.py` | ✅ Form 8621 workpaper PDF |
| | `pfic_engine/output/line16a_statement.py` | ✅ §6501(c)(8) attachment |
| | `pfic_engine/output/excel_workpaper.py` | ✅ 3-sheet Excel workpapers |
| Database | `api/db/models.py` | ✅ SQLAlchemy ORM, all 10 tables |
| | `api/db/seed_static.py` | ✅ Idempotent seed |
| API | `api/main.py` | ✅ FastAPI app, CORS, auto-seed on startup |
| | `api/auth.py` | ✅ JWT register/login |
| | `api/deps.py` | ✅ DI: get_db, get_current_user |
| | `api/routes/clients.py` | ✅ CRUD |
| | `api/routes/holdings.py` | ✅ CRUD |
| | `api/routes/transactions.py` | ✅ CRUD + CSV import |
| | `api/routes/calculations.py` | ✅ Run + retrieve |
| | `api/routes/exports.py` | ✅ PDF / Line16a / Excel download |

### Frontend `pfic-tool/frontend/src/`

| File | Status |
|------|--------|
| `api.ts` | ✅ Typed API client for all endpoints |
| `App.tsx` | ✅ React Router: Login / Dashboard / ClientDetail / PFICWorkspace |
| `pages/Login.tsx` | ✅ Register + sign in |
| `pages/Dashboard.tsx` | ✅ Client list + new client form |
| `pages/ClientDetail.tsx` | ✅ Holdings list + new holding form |
| `pages/PFICWorkspace.tsx` | ✅ 5-step wizard: Info → Transactions → Parameters → Results → Export |

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
- Single user per account (no multi-firm) — Phase 2D
- §6621 rate table needs verification against IRS IRB publications before production use
- Form 8621 PDF is a workpaper, not a pixel-perfect IRS form fill (no PDF template)

---

## What's Left for Full Production

- Week 8: E2E testing with 5 complete scenarios, security review, Railway/Render deploy
- Phase 2: multi-currency, MTM, QEF, firm management
