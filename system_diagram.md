# MarketPulse System Diagram (Textual Representation)

## 1. Main Controller Page
- Options:
  - **Go to Tickers Collector Main**
  - **Go to Query Menu**

---

## 2. Tickers Collector Main
- Input: **Enter Tickers** (user enters ticker symbols)
- Buttons: **Start / Stop Collector Agent**
- Navigation:
  - **Back to Main Controller Page**
  - **Go to Query Menu**

---

## 3. Query Menu
- Input: **Enter Tickers** (ticker symbols to query)
- Output: **Display Current Table** (fetch from DB)
- Navigation:
  - **Back to Main Controller Page**
  - **Go to Tickers Collector Main**

---

## 4. Collector Agent
- Triggered by: **Start button** from Tickers Collector Main
- Reads: **Tickers Input** (selected tickers)
- Behavior:
  - Loop: **Every 1 minute**
  - **Get ticker info** from **Yahoo Finance (yfinance)**
  - **Write ticker info** into **Local MySQL Database**
- Stopped by: **Stop button** from Tickers Collector Main

---

## 5. Database
- **Local MySQL**
- Stores records containing:
  - Symbol (ticker)
  - Date, Time (timestamp)
  - Price data (Open, High, Low, Close, Volume, …)

---

## Workflow
1. User opens **Main Controller Page**.
2. If selecting **Tickers Collector**:
   - Enter tickers
   - Press **Start** → Collector Agent runs (fetch every minute, save to DB)
   - Press **Stop** → Collector Agent stops
3. If selecting **Query Menu**:
   - Enter tickers
   - System queries MySQL
   - Displays data table
4. User can navigate between **Collector** ↔ **Query** ↔ **Main**
