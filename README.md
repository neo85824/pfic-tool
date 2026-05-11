# PFIC Tool

A web-based §1291 Excess Distribution calculator for tax professionals (CPAs / accounting firms).  
Computes Form 8621 Part V figures with full §6622 daily compound interest, FIFO lot tracking, and required IRS attachments.

> **MVP scope:** USD-denominated PFICs, §1291 Excess Distribution method only.  
> §1296 MTM and QEF are planned for Phase 2.

---

## Requirements

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |

No database server needed — SQLite runs automatically on your machine.

---

## Setup

### 1. Clone / locate the project

```bash
cd /mnt/d/claude/pfic-tool   # or wherever you put it
```

### 2. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```bash
cd ../frontend
npm install
```

---

## Start the servers

From the project root, run both servers with one command:

```bash
cd /mnt/d/claude/pfic-tool
./start.sh
```

Or start them separately in two terminals:

**Terminal 1 — Backend:**
```bash
cd backend
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

| Service | URL |
|---------|-----|
| Frontend (app) | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |

> **First run:** The backend automatically creates `backend/pfic_tool_dev.db` (SQLite) and seeds all static IRS data (§6621 rates, max tax rates, filing deadlines). No manual DB setup required.

---

## Usage

### Step 1 — Register an account

Open http://localhost:5173 → click **Register** → enter email + password.

---

### Step 2 — Create a client

On the Dashboard, click **+ New Client**.

| Field | Description |
|-------|-------------|
| Client Code | Your internal identifier, e.g. `SMITH-2024` |
| First Tax Year | Earliest year you need to calculate (optional) |

---

### Step 3 — Add a PFIC holding

Click a client → **+ New PFIC**.

| Field | Description |
|-------|-------------|
| PFIC Name | Fund name, e.g. `Vanguard FTSE All-World UCITS` |
| First PFIC Year | Year the fund first qualified as a PFIC (affects pre-PFIC classification) |
| IRS Reference ID | Alphanumeric ID from prior filings (optional) |

> MVP supports USD-denominated PFICs only.

---

### Step 4 — Open the PFIC Workspace

Click a holding to enter the 5-step workspace.

---

#### Workspace Step 1: PFIC Info

Confirm the tax year you are calculating, then click **Next: Transactions**.

---

#### Workspace Step 2: Transactions

Add all transactions for the PFIC — purchases, sales, and distributions across **all years**, not just the current tax year. Prior-year distributions are required for the 125% excess distribution test.

**Option A — CSV Upload**

Drag-drop or click **Upload CSV**. Expected columns (header row required, order flexible):

| Column | Required | Description |
|--------|----------|-------------|
| `date` | ✅ | ISO format: `2020-03-15` |
| `type` | ✅ | `purchase`, `sale`, `distribution`, `reinvestment`, `return_of_capital` |
| `units` | — | Number of shares (required for purchase/sale) |
| `amount_usd` | ✅ | USD amount |
| `notes` | — | Optional description |

Example CSV:
```csv
date,type,units,amount_usd,notes
2020-01-15,purchase,100,10000.00,Initial purchase
2021-06-30,distribution,,500.00,Annual distribution
2022-06-30,distribution,,800.00,Annual distribution
2023-06-30,distribution,,2500.00,Current year distribution
2024-12-31,sale,100,18000.00,Full exit
```

**Option B — Manual Entry**

Fill in the form fields and click **Add** for each transaction.

---

#### Workspace Step 3: Parameters

Review the calculation parameters and click **▶ Run Calculation**.

The engine uses:
- **IRC §1291(b)(2)(A):** 125% of prior 3-year average as the excess threshold
- **IRC §1291(c)(2):** Historical maximum tax rate for each prior year
- **IRC §6622:** Daily compound interest on deferred tax
- **FIFO lot matching:** Required by IRS (no average cost)
- **§7503 filing deadlines:** Including 2019→2020-07-15 and 2020→2021-05-17 COVID extensions

---

#### Workspace Step 4: Results

| Card | What it means |
|------|---------------|
| Excess Distribution | Amount above the 125% threshold (Line 15e(2)) |
| Additional Tax | Deferred tax on prior-year allocations (Line 16c) |
| §6621 Interest | Daily compound interest on that tax (Line 16f) |
| **Grand Total** | Tax + interest — total additional liability |
| Ordinary Income | Non-excess portion + current/pre-PFIC days (Line 16b) — taxed at your rate |

The year-by-year table shows how the excess is allocated across each year of the holding period:

| Classification | Meaning |
|----------------|---------|
| `prior pfic` | 1987 or later, before current year — bears deferred tax + interest |
| `current year` | Current tax year — taxed as ordinary income |
| `pre pfic` | Before 1987 — taxed as ordinary income |

---

#### Workspace Step 5: Export

| Document | Required? | Description |
|----------|-----------|-------------|
| **Form 8621 Workpaper** (PDF) | — | Part V summary with all line numbers |
| **Line 16a Attachment** (PDF) | **⚠ Required** | Daily allocation statement per §6501(c)(8) — without this, the IRS audit statute of limitations never starts |
| **Excel Workpapers** (XLSX) | — | 3 sheets: Summary, Year Detail, Daily Allocation |

> Attach the **Line 16a PDF** to the filed Form 8621. This is a legal requirement.

---

## Running tests

```bash
cd backend
python -m pytest tests/ -v
```

Expected: **71 passed**.

---

## Production deployment

Set the following environment variables before starting:

```bash
DATABASE_URL=postgresql://user:password@host:5432/pfic_tool
SECRET_KEY=your-32-character-random-secret-key
```

Then run migrations:

```bash
cd backend
alembic upgrade head
python -m api.db.seed_static
```

Deploy on Railway or Render by pointing to the `backend/` directory with `uvicorn api.main:app`.

---

## Project structure

```
pfic-tool/
├── start.sh                        # Start both servers
├── backend/
│   ├── requirements.txt
│   ├── pfic_engine/
│   │   ├── core/
│   │   │   ├── tax_constants.py    # §6621 rates, max tax rates, §7503 deadlines
│   │   │   ├── date_utils.py
│   │   │   └── decimal_utils.py
│   │   ├── section_1291/
│   │   │   ├── excess_dist.py      # 125% test
│   │   │   ├── daily_allocation.py # Per-day ratable allocation
│   │   │   ├── interest.py         # §6622 daily compound interest
│   │   │   └── deferred_tax.py     # Per-year tax at historical rate
│   │   ├── lot/
│   │   │   ├── fifo.py             # FIFO lot matching
│   │   │   └── lot_tracker.py
│   │   ├── output/
│   │   │   ├── pdf_generator.py    # Form 8621 Part V workpaper
│   │   │   ├── line16a_statement.py
│   │   │   └── excel_workpaper.py
│   │   └── verification/
│   │       └── cross_check.py
│   ├── api/
│   │   ├── main.py                 # FastAPI app
│   │   ├── auth.py                 # JWT register/login
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── clients.py
│   │       ├── holdings.py
│   │       ├── transactions.py     # CRUD + CSV import
│   │       ├── calculations.py     # Engine trigger
│   │       └── exports.py          # PDF / Excel download
│   └── tests/                      # 71 tests
└── frontend/
    └── src/
        ├── api.ts                  # Typed API client
        ├── App.tsx                 # Router
        └── pages/
            ├── Login.tsx
            ├── Dashboard.tsx
            ├── ClientDetail.tsx
            └── PFICWorkspace.tsx   # 5-step wizard
```

---

## Disclaimer

This tool is for tax calculation assistance only and does not constitute tax advice. All computed figures must be reviewed by a qualified tax professional before filing. The taxpayer and signing preparer remain responsible for the accuracy of all filed returns.
