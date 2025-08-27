# MarketPulse Development Schedule

## 📅 Kế hoạch phát triển hệ thống MarketPulse (15 ngày)

### 🎯 **Phase 1: Core Backend Development (Ngày 1-6)**

#### **Ngày 1-2: Data Collection Core**

**Mục tiêu:** Xây dựng module thu thập dữ liệu từ Yahoo Finance

**Tasks:**
- [ ] Cài đặt dependencies: `yfinance`, `apscheduler`
- [ ] Tạo file `collectors/yahoo_collector.py`
- [ ] Implement class `YahooCollector` với các method:
  - `fetch_ticker_data(symbol)` - Lấy dữ liệu từ Yahoo Finance
  - `save_to_db(price_data)` - Lưu vào MySQL database
- [ ] Test kết nối Yahoo Finance API
- [ ] Test lưu dữ liệu vào database

**Deliverables:**
```python
# collectors/yahoo_collector.py
class YahooCollector:
    def fetch_ticker_data(self, symbol: str) -> dict
    def save_to_db(self, price_data: dict) -> bool
```

**Thời gian ước tính:** 16 giờ

---

#### **Ngày 3-4: Collector Agent Service**

**Mục tiêu:** Tạo background service để thu thập dữ liệu định kỳ

**Tasks:**
- [ ] Tạo file `collectors/collector_agent.py`
- [ ] Implement class `CollectorAgent` với APScheduler:
  - `start_collection(tickers)` - Bắt đầu thu thập
  - `stop_collection()` - Dừng thu thập
  - `collect_data()` - Job chạy mỗi phút
- [ ] Xử lý lỗi và logging
- [ ] Test chạy background job

**Deliverables:**
```python
# collectors/collector_agent.py
class CollectorAgent:
    def start_collection(self, tickers: list) -> bool
    def stop_collection() -> bool
    def collect_data() -> None  # Job chạy mỗi phút
```

**Thời gian ước tính:** 16 giờ

---

#### **Ngày 5-6: REST API Endpoints**

**Mục tiêu:** Tạo API endpoints để điều khiển collector

**Tasks:**
- [ ] Tạo file `app/api/tickers.py`
- [ ] Implement API endpoints:
  - `POST /api/tickers/start-collection` - Bắt đầu thu thập
  - `POST /api/tickers/stop-collection` - Dừng thu thập
  - `GET /api/tickers/status` - Trạng thái collector
- [ ] Tích hợp với collector agent
- [ ] Test APIs với Postman/curl

**Deliverables:**
```python
# app/api/tickers.py
@router.post("/start-collection")
@router.post("/stop-collection") 
@router.get("/status")
```

**Thời gian ước tính:** 16 giờ

---

### 🎯 **Phase 2: Query System Development (Ngày 7-8)**

#### **Ngày 7-8: Query APIs**

**Mục tiêu:** Tạo APIs để truy vấn dữ liệu

**Tasks:**
- [ ] Tạo file `app/api/prices.py`
- [ ] Implement query endpoints:
  - `GET /api/prices/latest` - Giá mới nhất
  - `GET /api/prices/history` - Lịch sử giá
  - `GET /api/prices/summary` - Tổng quan ticker
- [ ] Xử lý query parameters (tickers, time range)
- [ ] Optimize database queries
- [ ] Test performance với data lớn

**Deliverables:**
```python
# app/api/prices.py  
@router.get("/latest")
@router.get("/history")
@router.get("/summary")
```

**Thời gian ước tính:** 16 giờ

---

### 🎯 **Phase 3: Web Interface Development (Ngày 9-13)**

#### **Ngày 9-10: HTML Templates & Static Files**

**Mục tiêu:** Tạo giao diện web cơ bản

**Tasks:**
- [ ] Setup Jinja2 templates
- [ ] Tạo `app/templates/` directory
- [ ] Implement templates:
  - `index.html` - Main Controller Page
  - `collector.html` - Ticker Collector Interface
  - `query.html` - Query Menu Interface
- [ ] Tạo CSS styles cơ bản
- [ ] Setup static files serving

**Deliverables:**
```
app/templates/
├── index.html      # Main navigation
├── collector.html  # Collector interface  
└── query.html      # Query interface
```

**Thời gian ước tính:** 16 giờ

---

#### **Ngày 11-12: JavaScript & Interactive Features**

**Mục tiêu:** Thêm tính năng tương tác với JavaScript

**Tasks:**
- [ ] Implement AJAX calls cho collector controls
- [ ] Real-time status updates
- [ ] Form validation cho ticker input
- [ ] Error handling và user feedback
- [ ] Auto-refresh cho query results
- [ ] Navigation giữa các pages

**Deliverables:**
```javascript
// Static file với functions:
- startCollection()
- stopCollection() 
- updateStatus()
- queryPrices()
```

**Thời gian ước tính:** 16 giờ

---

#### **Ngày 13: UI/UX Improvements**

**Mục tiêu:** Cải thiện giao diện người dùng

**Tasks:**
- [ ] Responsive design cho mobile
- [ ] Loading indicators
- [ ] Data tables với sorting
- [ ] Charts cho price history (optional)
- [ ] User-friendly error messages
- [ ] Accessibility improvements

**Thời gian ước tính:** 8 giờ

---

### 🎯 **Phase 4: Integration & Testing (Ngày 14-15)**

#### **Ngày 14: System Integration**

**Mục tiêu:** Tích hợp tất cả components

**Tasks:**
- [ ] Update `app/api/main.py` với tất cả routers
- [ ] Integrate templates với FastAPI
- [ ] Configure static files serving
- [ ] Environment configuration
- [ ] Docker setup refinement
- [ ] End-to-end testing

**Deliverables:**
```python
# app/api/main.py - Complete FastAPI app
app.include_router(tickers.router)
app.include_router(prices.router)
# Template routes
# Static file mounting
```

**Thời gian ước tính:** 8 giờ

---

#### **Ngày 15: Final Testing & Documentation**

**Mục tiêu:** Testing toàn diện và tài liệu

**Tasks:**
- [ ] Functional testing tất cả workflows
- [ ] Performance testing với multiple tickers
- [ ] Error scenario testing
- [ ] Update README.md với usage instructions
- [ ] API documentation
- [ ] Deployment testing với Docker

**Test Scenarios:**
1. Start collector với multiple tickers
2. Query real-time data
3. Stop/restart collector
4. Database persistence testing
5. Error handling testing

**Thời gian ước tính:** 8 giờ

---

## 📊 **Tổng quan Timeline**

| Phase | Ngày | Nội dung chính | Thời gian (giờ) |
|-------|------|---------------|----------------|
| **Phase 1** | 1-6 | Backend Core, APIs | 48 |
| **Phase 2** | 7-8 | Query System | 16 |
| **Phase 3** | 9-13 | Web Interface | 40 |
| **Phase 4** | 14-15 | Integration & Testing | 16 |
| **Total** | 15 days | Complete System | 120 |

---

## 🛠️ **Dependencies cần cài đặt**

```bash
# Core dependencies
pip install yfinance apscheduler jinja2 python-multipart

# Development dependencies  
pip install pytest pytest-asyncio httpx

# Optional dependencies
pip install plotly  # For charts
pip install redis   # For caching
```

---

## 📋 **Checklist hoàn thành**

### Core Features
- [ ] Yahoo Finance data collection
- [ ] Background scheduled collection
- [ ] Start/Stop collector controls
- [ ] Real-time price queries
- [ ] Historical data queries
- [ ] Web interface với navigation

### Technical Requirements
- [ ] FastAPI backend
- [ ] MySQL database integration
- [ ] Docker containerization
- [ ] Error handling & logging
- [ ] API documentation
- [ ] Unit tests

### User Experience
- [ ] Intuitive web interface
- [ ] Real-time status updates
- [ ] Data visualization
- [ ] Mobile responsive design
- [ ] User feedback mechanisms

---

## 🚀 **Post-Launch Enhancements**

**Phase 5: Advanced Features (Optional)**
- WebSocket real-time updates
- Data export functionality
- Advanced charting
- Alert notifications
- Multi-timeframe analysis
- Portfolio tracking

**Thời gian ước tính:** 1-2 tuần thêm

---

## 📞 **Support & Maintenance**

- Code review và refactoring
- Performance optimization
- Security updates
- Bug fixes và improvements
- Feature requests từ users

**Thời gian ước tính:** Ongoing
