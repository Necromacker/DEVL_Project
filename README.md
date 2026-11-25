# 🥗 Branch Food Waste & Procurement Planner (Pune Multi-Branch Network)

A streamlined, production-grade web application for multi-branch restaurant groups across Pune to normalize messy point-of-sale orders and purchase logs, track food waste, detect portion shrinkage & unexplained stock variances, and automate replenishment procurement.

Built to mirror the Neo-Brutalist / Modern Playful aesthetic from the reference designs (pastel yellow `#FFE57F`, lavender `#D7B7FD`, neon lime `#CCFF00`, bold 2.5px solid black borders, chunky display typography, segmented capsule pill bar charts, and **separate modular vanilla CSS files for each page without Tailwind**).

---

## ⚡ Quick Start

### 1. Backend Setup & Run
```bash
# In the root directory
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Run pytest unit tests (unit conversions, reconciliation, anomaly detection)
PYTHONPATH=. pytest backend/tests

# Launch FastAPI backend (automatically seeds Pune branches x 90 days if empty)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup & Run
```bash
cd frontend
npm install
npm run build   # Compiles production bundle to frontend/dist (served directly by FastAPI at http://localhost:8000)

# Or run Vite dev server with hot reload:
npm run dev     # Available at http://localhost:5173
```

Visit the app at **http://localhost:8000** (or http://localhost:5173).

---

## 🏙️ Pune Branch Network

The application simulates and audits 6 prominent Pune restaurant localities:
1. **Koregaon Park (B01)** — North Main Road, Pune (120 seats)
2. **Kothrud (B02)** — Paud Road, Pune (85 seats)
3. **Viman Nagar (B03)** — Phoenix Marketcity Area, Pune (140 seats)
4. **Baner (B04)** — Balewadi High Street, Pune (95 seats)
5. **FC Road (B05)** — Deccan Gymkhana, Pune (110 seats)
6. **Wakad (B06)** — Dutt Mandir Chowk, Pune (160 seats)

---

## 🏗️ Architecture & Styling

- **Backend**: Python (FastAPI, Pandas, RapidFuzz, SQLAlchemy, Pydantic, Pytest)
- **Frontend**: React 19, Recharts, Vite, custom inline SVG icons, Unsplash food thumbnails
- **Currency**: Indian Rupee (`₹` / INR) with commercial restaurant pricing benchmarks
- **Human-Friendly Unit Scaling**: Automatically converts unwieldy gram/milliliter numbers (e.g. `14,00,000 g` $\rightarrow$ `1,400 kg`; `50,000 ml` $\rightarrow$ `50 L`) and rounds all quantities, currency amounts, and percentages to **clean whole numbers without decimals**.
- **Top Main Navbar**: Horizontal header featuring Logo + Brand at left, 4 central navigation tabs in the middle, and notification bell & chart actions at the rightmost.
- **Separate Modular CSS Files (No Tailwind)**:
  - `styles/index.css`: Color variables, neo-brutalist cards, buttons, badges, tables
  - `styles/App.css`: Top navbar, responsive layout, button styling
  - `styles/Overview.css`: Revenue/Expenses/Sales KPI cards, segmented pill chart, recent orders
  - `styles/BranchView.css`: Branch balance sheet, category pills
  - `styles/ProcurementPlanner.css`: Forecasted demand, pack size inputs, order total
  - `styles/ReviewQueue.css`: Human-readable diagnostics, severity scores, status tabs
- **Database**: SQLite (`backend/data/planner.db`)
- **Seeded Benchmark CSVs**: Preserved in `backend/data/`:
  - `pos_orders.csv` (5,400 records)
  - `recipes.csv` (35 BOM records)
  - `purchases.csv` (855 transactions)
  - `inventory_counts.csv` (924 weekly counts)
  - `waste_logs.csv` (1,023 logged waste incidents)

---

## 🔍 Planted Operational Anomalies

The 90-day benchmark dataset contains 3 deliberate, realistic restaurant operational anomalies:

1. **Koregaon Park (Branch B01) — Chicken Over-Portioning**:
   - Kitchen staff serves ~290g instead of the 220g specified in the recipe BOM.
   - Result: Unexplained chicken variance of **+32%**, diagnosed in Audit Alerts as *"Portion Creep"*.
2. **Viman Nagar (Branch B03) — Dairy Cooler Spoilage**:
   - Walk-in cooler compressor temperature fluctuations cause Heavy Cream & Mozzarella spoilage.
   - Result: Waste rate is **18%** of purchases vs group normal of **1.5%**, diagnosed in Audit Alerts as *"Cooler Spoilage"*.
3. **FC Road (Branch B05) — Inventory Count Typo**:
   - On Day 56 (Week 8), Ground Beef closing count was entered as **150 kg instead of 18 kg** (8.5x transcription jump).
   - Result: Flagged as a *"Suspicious Count Typo"*.

---

## 📐 Formulas & Core Logic

### 1. Unit Normalization & Packaging (`normalizer.py`)
- Standardizes supplier units to base dimensions: Mass $\rightarrow$ **g**, Volume $\rightarrow$ **ml**, Count $\rightarrow$ **pcs**.
- Regex parser unpacks composite supplier packaging:
  - `"case of 4 x 2.5kg"` $\rightarrow 10,000\text{ g}$
  - `"crate of 20 lb"` $\rightarrow 9,072\text{ g}$
  - `"tub of 4 l"` $\rightarrow 4,000\text{ ml}$
- Density table handles volume-to-mass conversions (Olive Oil: $0.92\text{ g/ml}$, Cream: $1.01\text{ g/ml}$).
- Auto-scales display units: $\ge 1,000\text{ g} \rightarrow \text{kg}$, $\ge 1,000\text{ ml} \rightarrow \text{L}$.

### 2. Ingredient Normalization & Fuzzy Matching
- Exact alias lookup $\rightarrow$ canonical ingredient ID.
- RapidFuzz token set/sort matching handles raw supplier naming variants (`"Murgh Boneless"`, `"tomatoes fresh"`, `"paneer mozzarella"`).

### 3. Recipe Explosion (Theoretical Usage)
$$\text{Theoretical Usage} = \sum_{\text{Orders}} \left( \text{Quantity Sold} \times \frac{\text{Recipe BOM Quantity}}{\text{Yield \%} / 100} \right)$$
- Items without complete recipe BOMs are marked `"Not Estimable"` and are **never guessed**.

### 4. Stock Reconciliation Formula (`reconciliation.py`)
$$\text{Actual Usage} = \text{Opening Stock} + \text{Purchases} - \text{Closing Stock}$$
$$\text{Unexplained Variance} = \text{Actual Usage} - \text{Theoretical Usage} - \text{Logged Waste}$$

### 5. Procurement Planning & Pack Size Rounding (`forecasting.py`)
1. **Sales Forecast**: 14-day day-of-week moving average captures Friday/Saturday peak restaurant seasonality.
2. **Projected Ingredient Demand**: Converted via recipe BOMs with trim loss adjustments.
3. **Safety Stock Buffer**: $\text{Daily Burn} \times \text{Safety Days} \times (1 + \text{Historical Waste Rate})$.
4. **Commercial Pack Rounding**:
   $$\text{Net Demand} = \text{Projected 7-Day Demand} + \text{Safety Buffer} - \text{Current Stock}$$
   $$\text{Suggested Packs} = \left\lceil \frac{\text{Net Demand}}{\text{Pack Size Base}} \right\rceil$$

---

## 🖥️ Streamlined Application Pages

1. **Overview**:
   - Clean KPI cards for **Revenue**, **Expenses**, and **Sales** in matching neo-brutalist card styling (whole numbers, no decimals).
   - Day-of-week segmented capsule bar chart displaying weekly consumption rhythm.
   - Recent orders list with food thumbnails.
   - Pune branch manager cards (Koregaon Park, Viman Nagar).
   - Pune Branch Performance Ranking table with 1-click order planning shortcut.
2. **Branch Balance**:
   - Locality selector and category filter buttons (`All`, `Meat & Poultry`, `Produce`, `Dairy`, `Dry Goods`).
   - Summary cards: Total Spend, Logged Waste Cost, and Unexplained Variance Cost in ₹.
   - Clean inventory table: `Canonical Ingredient`, `Category`, `Opening`, `Purchases`, `Closing`, `Actual Usage`, `Theoretical`, `Waste`, `Unexplained Var`, and `Status` (with scaled `kg`/`L` units and whole numbers).
3. **Procurement**:
   - Projected Order Total in ₹ with save quantities button.
   - Order table displaying Current Stock, Daily Burn, Days of Supply, 7-Day Demand, Safety Buffer, Commercial Pack Size, and Order Packs.
   - Inline pack quantity inputs that update total order spend live.
   - 1-click CSV order sheet export.
4. **Audit Alerts (Review Queue)**:
   - Filter by status tabs: `ALL`, `OPEN`, `INVESTIGATING`, `RESOLVED`.
   - Severity scores (0-100) and plain-language diagnostic explanations for the 3 planted anomalies.
   - Inline team notes editor and status action buttons.
