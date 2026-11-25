# 🥗 Branch Food Waste & Procurement Planner

A comprehensive, production-grade web application for multi-branch restaurant groups to normalize disparate ingredients, track food waste, detect portion shrinkage & unexplained variances, and automate replenishment procurement.

Built to mirror the Neo-Brutalist / Modern Playful aesthetic from the reference designs (pastel yellow `#FFE57F`, lavender `#D7B7FD`, neon lime `#CCFF00`, bold 2.5px solid black borders, chunky display typography, and vertical segmented capsule pill bar charts).

---

## ⚡ Quick Start

### 1. Backend Setup & Run
```bash
# In the root directory
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Run pytest unit tests (unit conversions, reconciliation, anomalies)
PYTHONPATH=. pytest backend/tests

# Launch FastAPI backend (automatically seeds 6 branches x 90 days if database is empty)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup & Run
```bash
cd frontend
npm install
npm run build   # Builds production bundle to frontend/dist (auto-served by FastAPI at http://localhost:8000)

# Or run Vite dev server with hot reload:
npm run dev     # Available at http://localhost:5173
```

Visit the app at **http://localhost:8000** (or http://localhost:5173).

---

## 🏗️ Architecture & Tech Stack

- **Backend**: Python (FastAPI, Pandas, RapidFuzz, SQLAlchemy, Pydantic, Pytest)
- **Frontend**: React 19, Recharts, Vite
- **Styling**: Separate modular vanilla CSS files for every page and component (**no Tailwind**, matching the user specification):
  - `styles/index.css`: Global variables, neo-brutalist cards, buttons, badges, tables
  - `styles/App.css`: Responsive sidebar, sticky header, mobile drawer
  - `styles/Overview.css`: KPI cards, segmented capsule chart, recent items list
  - `styles/BranchView.css`: Branch reconciliation balance sheet, category pills
  - `styles/MenuItemReview.css`: Recipe BOM viewer, margin & estimability audits
  - `styles/ProcurementPlanner.css`: Forecasted demand, pack size rounding, inline edits
  - `styles/ReviewQueue.css`: Human-readable diagnostics, severity scores, status tabs
  - `styles/DataQuality.css`: Alias mapping resolver, missing recipe alerts
  - `styles/DataUploadSettings.css`: CSV exporter/uploader, threshold configuration
- **Database**: SQLite (`backend/data/planner.db`)
- **CSV Storage**: 5 benchmark datasets saved in `backend/data/`:
  - `pos_orders.csv` (5,400 orders)
  - `recipes.csv` (36 BOM rows)
  - `purchases.csv` (874 transactions)
  - `inventory_counts.csv` (1,008 weekly counts)
  - `waste_logs.csv` (1,097 logged waste incidents)

---

## 🧪 Planted Anomalies & Where to Find Them

The 90-day synthetic dataset contains 3 deliberate, realistic operational anomalies:

1. **Downtown Bistro (Branch B01) — Chicken Over-Portioning**:
   - Kitchen staff serves ~290g instead of the 220g specified in the recipe BOM.
   - Result: Unexplained chicken variance is **+32%**, yielding a peer Z-score of **+2.7σ**.
   - Found in: **Review Queue** & **Branch View (B01)** labeled *"Portion Creep"*.
2. **Westside Grill (Branch B03) — High Dairy Spoilage**:
   - Walk-in cooler compressor temperature fluctuations cause Heavy Cream & Mozzarella spoilage.
   - Result: Waste rate is **18%** of purchases vs peer group median of **1.5%**.
   - Found in: **Review Queue** & **Branch View (B03)** labeled *"Cooler Spoilage"*.
3. **Eastside Kitchen (Branch B05) — Bad Inventory Count (Typo)**:
   - On Day 56 (Week 8), Ground Beef closing count was keyed as **150 kg instead of 18 kg** (8.5x jump).
   - Result: Triggers a high-severity alert for impossible stock surge followed by correction.
   - Found in: **Data Quality > Suspicious Counts** & **Review Queue**.

---

## 📐 Formulas & Core Logic

### 1. Unit Normalization & Pack Parsing (`normalizer.py`)
- Standardizes all supplier packaging into base physical dimensions:
  - Mass $\rightarrow$ **grams (g)**
  - Volume $\rightarrow$ **milliliters (ml)**
  - Count $\rightarrow$ **each**
- Regex parser handles composite descriptions:
  - `"case of 12 x 500g"` $\rightarrow 6,000\text{ g}$
  - `"crate of 20 lb"` $\rightarrow 9,071.85\text{ g}$
  - `"tub of 4 l"` $\rightarrow 4,000\text{ ml}$
- Density table handles volume-to-mass conversions (e.g., Olive Oil density $0.92\text{ g/ml}$, Cream $1.01\text{ g/ml}$).

### 2. Ingredient Normalization & Fuzzy Matching
- Exact alias lookup $\rightarrow$ canonical ID with 100% confidence.
- RapidFuzz token set & sort matching for dirty strings (e.g., `"tomatoes fresh"`, `"Murgh Boneless"`, `"chk breast"`).
- Scores $< 80\%$ routed to the **Data Quality Resolution Queue**.

### 3. Recipe Explosion (Theoretical Usage)
$$\text{Theoretical Usage} = \sum_{\text{Orders}} \left( \text{Quantity Sold} \times \frac{\text{Recipe BOM Quantity}}{\text{Yield \%} / 100} \right)$$
- Items without recipe BOMs (e.g., *Chef Special Risotto*) are strictly marked `"Not Estimable"` and are **never guessed**.

### 4. Stock Reconciliation Formula (`reconciliation.py`)
$$\text{Actual Usage} = \text{Opening Stock} + \text{Purchases} - \text{Closing Stock}$$
$$\text{Unexplained Variance} = \text{Actual Usage} - \text{Theoretical Usage} - \text{Logged Waste}$$
$$\text{Variance \%} = \frac{\text{Unexplained Variance}}{\text{Theoretical Usage}} \times 100$$

### 5. Review Flag Transparent Scoring
- **Peer Z-Score**: $Z = \frac{\text{Variance \%} - \mu_{\text{group}}}{\sigma_{\text{group}}}$. Flagged if $Z > 2.0$.
- **High Waste**: Flagged if branch waste rate $> 1.5\times$ group median.
- **Severity Score (0-100)**: Transparent weighted composite based on dollar variance, percentage deviation, and recurrence.

### 6. Procurement Planning & Pack Size Rounding (`forecasting.py`)
1. **Sales Forecast**: 14-day day-of-week moving average captures Friday/Saturday peak seasonality.
2. **Projected Ingredient Demand**: Converted via BOM with trim loss adjustments.
3. **Safety Stock Buffer**: $\text{Daily Burn} \times \text{Safety Days} \times (1 + \text{Historical Waste Rate})$.
4. **Pack Rounding**:
   $$\text{Net Demand} = \text{Projected 7-Day Demand} + \text{Safety Buffer} - \text{Current Stock}$$
   $$\text{Suggested Packs} = \left\lceil \frac{\text{Net Demand}}{\text{Pack Size Base}} \right\rceil$$

---

## 🖥️ Application Pages

1. **Overview**:
   - Total Purchases, Logged Waste, Unexplained Variance, and Gross Sales KPI cards.
   - Segmented vertical capsule bar chart displaying day-of-week consumption rhythm.
   - Ranked branch performance table with food cost %, waste %, and variance.
2. **Branch View**:
   - Single-branch drilldown with category filters (Meat, Produce, Dairy, Dry Goods).
   - Balance sheet showing Opening, Purchases, Closing, Actual, Theoretical, Waste, and Z-Score.
3. **Menu Item Review**:
   - Food margin analysis, unit sales, and BOM drawer with portion weights and yield %.
   - Identifies items with missing recipes or zero quantities.
4. **Procurement Planner**:
   - Automated order suggestion rounded to commercial pack sizes.
   - Interactive quantity inputs with real-time order cost recalculation.
   - 1-click CSV order sheet export.
5. **Review Queue**:
   - Open, Investigating, and Resolved status tabs.
   - Plain-language diagnoses and team notes editor.
6. **Data Quality**:
   - Low-confidence alias matcher with dropdown confirmation.
   - Missing recipe alerts and suspicious inventory count audits.
7. **Settings & Upload**:
   - Download or upload CSV datasets.
   - Tune variance thresholds, dollar limits, and Z-score cutoffs.
   - 1-click synthetic benchmark regeneration.
