# IntelliStock - Page-Wise & Project Workflow

---

## 📊 PAGE 1: DASHBOARD

### Purpose
Real-time overview of selected product with KPIs, inventory status, price recommendations, and AI insights.

### Page Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ USER LOADS DASHBOARD PAGE                                       │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 1. PRODUCT SELECTION                                            │
│    ├─ Load all product names from database                      │
│    ├─ Display searchable dropdown                               │
│    └─ User selects product                                      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. LOAD PRODUCT DATA                                            │
│    ├─ Query PostgreSQL for product details                      │
│    ├─ Get: price, stock, discount, sales, rating               │
│    └─ Fall back to CSV if DB unavailable                        │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. CALCULATE KPIs (5 Main Metrics)                              │
│    ├─ Total Revenue = monthly_sales × final_price              │
│    ├─ Units Sold (30d) = monthly_sales                         │
│    ├─ Avg Unit Price = selling_price - discount                │
│    ├─ Inventory Turnover = sales / stock                       │
│    └─ Data Health Score = % complete data fields                │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. CLASSIFY PRODUCT (Badges)                                    │
│    ├─ Value Classification (A/B/C)                              │
│    │  ├─ A: High revenue & profit                               │
│    │  ├─ B: Medium value                                        │
│    │  └─ C: Low priority                                        │
│    ├─ Demand Pattern (X/Y/Z)                                    │
│    │  ├─ X: Consistent demand                                   │
│    │  ├─ Y: Growing demand                                      │
│    │  └─ Z: Declining/irregular                                 │
│    ├─ Seasonality Detection                                     │
│    │  ├─ SEASONAL: Holiday peaks                                │
│    │  ├─ FESTIVE: Festival-driven                               │
│    │  └─ REGULAR: Consistent year-round                         │
│    └─ AI Prediction                                             │
│       └─ ML confidence score on pattern                         │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. AI DISCOUNT RECOMMENDATION                                   │
│    ├─ User selects: Optimize for [Profit / Revenue]            │
│    ├─ Discount Service calculates:                              │
│    │  ├─ Demand elasticity                                      │
│    │  ├─ Price sensitivity                                      │
│    │  ├─ Festival/seasonal factors                              │
│    │  └─ Current stock levels                                   │
│    ├─ Returns: Recommended discount + confidence                │
│    ├─ Projections:                                              │
│    │  ├─ Expected units sold                                    │
│    │  ├─ Expected revenue                                       │
│    │  └─ Expected profit                                        │
│    └─ Shows alternate objective comparison                      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. DISPLAY OVERVIEW SECTION                                     │
│    ├─ Product name with badges                                  │
│    ├─ Current Price: ₹XXX                                       │
│    ├─ Units in Stock: XXX                                       │
│    ├─ Current Discount: X%                                      │
│    ├─ Income (this month): ₹XXX, +X%                            │
│    └─ Performance progress bar                                  │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. DISPLAY STOCK INFO CHART                                     │
│    ├─ Current stock bar                                         │
│    ├─ Reorder point (safe level)                                │
│    ├─ Maximum stock threshold                                   │
│    ├─ Minimum stock (danger zone)                               │
│    └─ Visual bar chart with color coding                        │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. CATEGORY REVENUE ANALYSIS                                    │
│    ├─ Get all products in category                              │
│    ├─ Calculate category revenue breakdown                      │
│    ├─ Display donut chart (category-wise)                       │
│    ├─ Show category breakdown table                             │
│    │  ├─ Category name                                          │
│    │  ├─ Product count                                          │
│    │  ├─ Total revenue                                          │
│    │  ├─ Avg profit margin                                      │
│    │  └─ Trend (+/-%)                                           │
│    └─ Top 3 performers highlighted                              │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. DEMAND PATTERN CLASSIFICATION TABLE                          │
│    ├─ Query all products                                        │
│    ├─ Categorize into:                                          │
│    │  ├─ Steady Demand (X pattern)                              │
│    │  ├─ Growing Demand (Y pattern)                             │
│    │  └─ Declining/Irregular (Z pattern)                        │
│    ├─ Display with stats:                                       │
│    │  ├─ Product name                                           │
│    │  ├─ Pattern                                                │
│    │  ├─ Current stock                                          │
│    │  ├─ Reorder status                                         │
│    │  └─ Last action                                            │
│    └─ Scrollable table (1000+ rows supported)                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 10. AI RECOMMENDATIONS SIDEBAR                                  │
│    ├─ Get ML recommendations for product                        │
│    ├─ Display action cards:                                     │
│    │  ├─ Price Action (↑ increase / ↓ decrease)                 │
│    │  ├─ Stock Action (↑ reorder / ↓ reduce)                    │
│    │  ├─ Promotion Action (seasonal offer)                      │
│    │  └─ Alert (if anomaly detected)                            │
│    └─ Each with confidence score                                │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ PAGE RENDERED TO USER                                           │
│ ✅ KPIs displayed                                                │
│ ✅ Charts rendered                                               │
│ ✅ Tables loaded                                                │
│ ✅ Recommendations shown                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Dashboard Data Sources
```
Product Selection → Database → 
├─ product_name
├─ selling_price
├─ cost_price
├─ discount
├─ stock
├─ monthly_sales
├─ category
├─ demand_level
├─ rating
└─ supplier_lead_time

Calculations:
├─ DashboardService.get_dashboard_data()
├─ InventoryService.calculate_inventory_status()
├─ InventoryService.inventory_turnover()
├─ PricingService.calculate_final_price()
└─ DiscountService.ai_recommend_discount()
```

---

## 📦 PAGE 2: INVENTORY

### Purpose
Complete inventory management with stock status, low stock alerts, product bulk operations, and AI forecasts.

### Page Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ USER LOADS INVENTORY PAGE                                       │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 1. LOAD INVENTORY SUMMARY                                       │
│    ├─ Total Products: Count all in database                     │
│    ├─ Total Units: Sum all stock levels                         │
│    ├─ Inventory Value: Sum(stock × cost_price)                  │
│    ├─ Low Stock Count: Count where stock < reorder_point        │
│    ├─ Stockout Risk: Count where stock < 1 week supply          │
│    └─ Display as KPI metrics                                    │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. CATEGORY FILTER                                              │
│    ├─ Get all unique categories                                 │
│    ├─ Display multi-select dropdown                             │
│    ├─ User selects categories to view                           │
│    └─ Filter dataset accordingly                                │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. DISPLAY INVENTORY TABLE                                      │
│    ├─ Columns: Product | Category | Stock | Reorder Pt | Status│
│    ├─ Add columns: Price | Value | Days Supply | Alert          │
│    ├─ Sort by: Product name / Stock level / Category            │
│    ├─ Color code rows:                                          │
│    │  ├─ 🔴 Red: Stockout risk                                   │
│    │  ├─ 🟡 Yellow: Low stock                                    │
│    │  └─ 🟢 Green: Good stock                                    │
│    ├─ Pagination: 20 items per page                             │
│    └─ Search: Filter by product name                            │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. LOW STOCK ALERTS SECTION                                     │
│    ├─ Query AlertManager for low stock alerts                   │
│    ├─ Display alert cards:                                      │
│    │  ├─ Product name                                           │
│    │  ├─ Current stock                                          │
│    │  ├─ Safe reorder point                                     │
│    │  ├─ Recommended reorder quantity                           │
│    │  ├─ Days to stockout                                       │
│    │  └─ Estimated lead time                                    │
│    ├─ Alert severity color                                      │
│    └─ "Acknowledge Alert" button                                │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. MANAGE PRODUCT SECTION                                       │
│    ├─ Expandable form to:                                       │
│    │  ├─ SELECT: Choose product from dropdown                   │
│    │  ├─ UPDATE: Change stock level                             │
│    │  ├─ REASON: Reason for change (restock/damage/return)      │
│    │  ├─ NOTE: Additional notes                                 │
│    │  └─ SUBMIT: Save to database                               │
│    ├─ Validations:                                              │
│    │  ├─ Stock can't be negative                                │
│    │  ├─ Reason is required                                     │
│    │  └─ Maximum stock limit enforced                           │
│    └─ Success/error feedback                                    │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. BULK DISCOUNT APPLICATION                                    │
│    ├─ User selects:                                             │
│    │  ├─ Category to apply discount to                          │
│    │  ├─ Discount percentage (0-50%)                            │
│    │  ├─ Start date                                             │
│    │  └─ End date (optional)                                    │
│    ├─ Calculate impact:                                         │
│    │  ├─ Products affected                                      │
│    │  ├─ New prices                                             │
│    │  ├─ Revenue impact                                         │
│    │  └─ Margin preservation check                              │
│    ├─ Display preview                                           │
│    ├─ User confirms                                             │
│    └─ Apply discount:                                           │
│       ├─ Update database                                        │
│       ├─ Log to discount_audit table                            │
│       ├─ Send notification                                      │
│       └─ Show success message                                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. AI STOCK FORECAST (Expander)                                 │
│    ├─ User selects product                                      │
│    ├─ Select forecast period (30/60/90 days)                    │
│    ├─ Model choice: Auto (best) / Manual select                 │
│    ├─ Run forecast:                                             │
│    │  ├─ Get historical data                                    │
│    │  ├─ Clean/normalize data                                   │
│    │  ├─ Run 4 ML models                                        │
│    │  │  ├─ Exponential Smoothing                               │
│    │  │  ├─ ARIMA                                               │
│    │  │  ├─ Random Forest                                       │
│    │  │  └─ Ensemble (weighted)                                 │
│    │  └─ Generate confidence intervals                          │
│    ├─ Display:                                                  │
│    │  ├─ Line chart (actual vs forecast)                        │
│    │  ├─ Confidence bands (95%)                                 │
│    │  ├─ Predicted min/max stock                                │
│    │  ├─ Risk indicator                                         │
│    │  └─ Recommendation (reorder now? / wait?)                  │
│    └─ Save forecast to database                                 │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ PAGE RENDERED TO USER                                           │
│ ✅ Summary metrics                                               │
│ ✅ Inventory table                                               │
│ ✅ Low stock alerts                                              │
│ ✅ Management controls                                          │
│ ✅ Bulk operations                                               │
│ ✅ Forecasts                                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Inventory Data Sources
```
Database Tables:
├─ Products (all fields)
├─ Reorders (pending orders)
└─ Discount_Audit (history)

Services:
├─ InventoryService
│  ├─ calculate_inventory_status()
│  ├─ calculate_reorder_point()
│  └─ predict_stock_series()
├─ AlertManager
│  └─ check_low_stock()
└─ AdvancedForecaster
   └─ forecast_with_intervals()
```

---

## 📉 PAGE 3: STOCKOUTS & LOST SALES

### Purpose
Track stockout incidents, analyze lost sales impact, and generate recovery plans.

### Page Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ USER LOADS STOCKOUTS & LOST SALES PAGE                          │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 1. DATE RANGE SELECTION                                         │
│    ├─ Default: Last 30 days                                     │
│    ├─ Presets: 7d, 30d, 90d, Custom                             │
│    ├─ Allow custom start/end date                               │
│    └─ Filter all subsequent data by range                       │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. CALCULATE STOCKOUT METRICS                                   │
│    ├─ Total Stockout Events: Count incidents in period          │
│    ├─ Total Units Lost: Sum of unfulfilled demand               │
│    ├─ Total Revenue Lost: Sum(unfulfilled units × price)        │
│    ├─ Avg Recovery Time: Days to restock                        │
│    ├─ Stockout % by Category: Calculate per category            │
│    └─ Display as 4 KPI cards                                    │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. LOST SALES ACCOUNTABILITY TABLE                              │
│    ├─ Query reorders table for stockouts                        │
│    ├─ Columns:                                                  │
│    │  ├─ Date                                                   │
│    │  ├─ Product                                                │
│    │  ├─ Unfulfilled Qty                                        │
│    │  ├─ Unit Price                                             │
│    │  ├─ Revenue Lost                                           │
│    │  ├─ Days Delayed                                           │
│    │  ├─ Responsible Person                                     │
│    │  └─ Status (Recovered/Pending)                             │
│    ├─ Sort by: Revenue Lost (descending)                        │
│    ├─ Highlight top 10 worst incidents                          │
│    └─ Export to CSV button                                      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. TREND ANALYSIS CHART                                         │
│    ├─ Dual-axis chart:                                          │
│    │  ├─ Left axis: Lost Sales (bar chart)                      │
│    │  └─ Right axis: Stockout % (line chart)                    │
│    ├─ X-axis: Days in selected period                           │
│    ├─ Show: Daily trend + 7-day moving average                  │
│    ├─ Color zones:                                              │
│    │  ├─ Green: < 5% stockouts                                  │
│    │  ├─ Yellow: 5-15% stockouts                                │
│    │  └─ Red: > 15% stockouts                                   │
│    └─ Highlight worst days                                      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. CATEGORY-WISE LOST SALES BREAKDOWN                           │
│    ├─ Group by category                                         │
│    ├─ Display table:                                            │
│    │  ├─ Category                                               │
│    │  ├─ Stockout Events                                        │
│    │  ├─ Units Lost                                             │
│    │  ├─ Revenue Lost                                           │
│    │  ├─ % of Category Revenue                                  │
│    │  └─ Top Problem Product                                    │
│    ├─ Pie chart visualization                                   │
│    └─ Categories sorted by impact                               │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. STOCK OUT DETAILS TABLE                                      │
│    ├─ Show all stockout incidents in detail                     │
│    ├─ Columns:                                                  │
│    │  ├─ Product                                                │
│    │  ├─ Category                                               │
│    │  ├─ Stockout Date                                          │
│    │  ├─ Duration (days)                                        │
│    │  ├─ Demand Lost                                            │
│    │  ├─ Revenue Impact                                         │
│    │  ├─ Root Cause (supply delay/demand surge/forecast error)  │
│    │  ├─ Restock Date                                           │
│    │  └─ Recovery Action                                        │
│    ├─ Sortable & filterable                                     │
│    ├─ Color severity bands                                      │
│    └─ Pagination (20 per page)                                  │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. RECOVERY & RECOMMENDATIONS                                   │
│    ├─ For each incident:                                        │
│    │  ├─ Show recommended action                                │
│    │  ├─ Adjust reorder point (20% increase)                    │
│    │  ├─ Increase safety stock                                  │
│    │  ├─ Faster forecast update frequency                       │
│    │  └─ Alternative supplier recommendation                    │
│    ├─ Implement recommendations button                          │
│    ├─ Update database if accepted                               │
│    └─ Log changes to audit trail                                │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. EXPORT & REPORT                                              │
│    ├─ Download options:                                         │
│    │  ├─ CSV: Full incident list                                │
│    │  ├─ CSV: Category summary                                  │
│    │  ├─ Excel: Formatted report with charts                    │
│    │  └─ PDF: Executive summary                                 │
│    └─ Include date range & comparison YoY                       │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ PAGE RENDERED TO USER                                           │
│ ✅ KPI metrics                                                   │
│ ✅ Accountability table                                          │
│ ✅ Trend charts                                                  │
│ ✅ Category breakdown                                            │
│ ✅ Incident details                                              │
│ ✅ Recovery recommendations                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Stockouts Data Sources
```
Database:
├─ Reorders (for unfulfilled orders)
├─ Products (for pricing)
└─ Price_Audit (for historical analysis)

Calculations:
├─ Revenue Lost = unfulfilled_qty × price
├─ Stockout % = (days_stocked_out / period) × 100
├─ Category Impact = sum by category
└─ Trend Analysis = daily aggregations
```

---

## 🤖 PAGE 4: AI DECISION SUPPORT

### Purpose
ML-powered forecasting, model comparison, and actionable insights for inventory decisions.

### Page Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ USER LOADS AI DECISION SUPPORT PAGE                             │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 1. PRODUCT & PARAMETER SELECTION                                │
│    ├─ Select Product from dropdown                              │
│    ├─ Select Historical Period:                                 │
│    │  ├─ Last 6 months / 12 months / 24 months                  │
│    │  └─ More historical = more accurate forecast               │
│    ├─ Select Forecast Horizon:                                  │
│    │  ├─ 30 days (short term)                                   │
│    │  ├─ 60 days (medium term)                                  │
│    │  └─ 90 days (long term)                                    │
│    └─ User clicks "Analyze"                                     │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. RETRIEVE HISTORICAL DATA                                     │
│    ├─ Query product sales history                               │
│    ├─ Get monthly_sales from database                           │
│    ├─ Normalize data:                                           │
│    │  ├─ Handle missing values                                  │
│    │  ├─ Remove outliers                                        │
│    │  └─ Validate timestamp continuity                          │
│    └─ Prepare time series data                                  │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. RUN 4 FORECASTING MODELS (Parallel)                          │
│                                                                 │
│ Model 1: EXPONENTIAL SMOOTHING                                  │
│ ├─ Smooth parameter: α = 0.3                                    │
│ ├─ Advantage: Fast, simple                                      │
│ ├─ Best for: Stable demand                                      │
│ └─ Output: Point forecast + error                               │
│                                                                 │
│ Model 2: ARIMA-LIKE (Differencing)                              │
│ ├─ Parameters: p=1, d=1, q=1                                    │
│ ├─ Advantage: Handles seasonality                               │
│ ├─ Best for: Trending demand                                    │
│ └─ Output: Point forecast + confidence                          │
│                                                                 │
│ Model 3: RANDOM FOREST (ML)                                     │
│ ├─ Features: Lag(1), Lag(2), Lag(3), Trend, Seasonality        │
│ ├─ Advantage: Non-linear patterns                               │
│ ├─ Best for: Complex relationships                              │
│ └─ Output: Point forecast + uncertainty                         │
│                                                                 │
│ Model 4: ENSEMBLE (Weighted Average)                            │
│ ├─ Weights: 0.25 ES + 0.25 ARIMA + 0.5 RF                       │
│ ├─ Advantage: Best accuracy, lower bias                         │
│ ├─ Best for: Production use                                     │
│ └─ Output: Point forecast + 95% CI                              │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. CALCULATE CONFIDENCE INTERVALS                               │
│    ├─ For each model:                                           │
│    │  ├─ Upper bound (95th percentile)                          │
│    │  ├─ Point estimate (mean)                                  │
│    │  └─ Lower bound (5th percentile)                           │
│    ├─ Confidence bands are model-specific                       │
│    ├─ Ensemble uses average uncertainty                         │
│    └─ Wider bands = lower confidence                            │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. SEASONAL DECOMPOSITION                                       │
│    ├─ Extract components:                                       │
│    │  ├─ Trend: Long-term direction                             │
│    │  ├─ Seasonal: Repeating pattern (12-month cycle)           │
│    │  └─ Residual: Irregular fluctuations                       │
│    ├─ Display decomposition chart                               │
│    ├─ Show: 4-panel plot (original, trend, seasonal, residual)  │
│    └─ Identify: Strength of seasonality                         │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. DISPLAY MODEL COMPARISON                                     │
│    ├─ 4-Panel Chart:                                            │
│    │  ├─ Panel 1: Exponential Smoothing forecast                │
│    │  ├─ Panel 2: ARIMA forecast                                │
│    │  ├─ Panel 3: Random Forest forecast                        │
│    │  └─ Panel 4: Ensemble (best) forecast                      │
│    ├─ Each shows:                                               │
│    │  ├─ Historical actual data (blue line)                     │
│    │  ├─ Forecast (red line)                                    │
│    │  ├─ 95% confidence bands (light)                           │
│    │  └─ Accuracy metrics                                       │
│    └─ Interactive Plotly charts                                 │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. DISPLAY ACCURACY METRICS                                     │
│    ├─ For each model:                                           │
│    │  ├─ MAPE (Mean Absolute % Error): % deviation              │
│    │  ├─ RMSE (Root Mean Sq Error): Absolute error              │
│    │  ├─ MAE (Mean Absolute Error): Average deviation           │
│    │  └─ R² Score: Fit quality (0-1)                            │
│    ├─ Rank models by MAPE                                       │
│    ├─ Highlight: Ensemble typically best                        │
│    └─ Show: Model selection recommendation                      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. ACTIONABLE RECOMMENDATIONS                                   │
│    ├─ Based on forecast:                                        │
│    │  ├─ If trending up: "Increase reorder point by 20%"        │
│    │  ├─ If trending down: "Reduce safety stock"                │
│    │  ├─ If high variance: "Increase reorder frequency"         │
│    │  └─ If seasonal: "Plan for peak/trough periods"            │
│    ├─ Stock level recommendations:                              │
│    │  ├─ Current safe stock: XXX units                          │
│    │  ├─ Recommended reorder: XXX units                         │
│    │  ├─ Lead time adjusted quantity: XXX units                 │
│    │  └─ Next reorder date: YYYY-MM-DD                          │
│    ├─ Action priority: High/Medium/Low                          │
│    └─ Confidence: % (from ensemble)                             │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. IMPLEMENT RECOMMENDATION                                     │
│    ├─ User clicks "Apply Recommendation"                        │
│    ├─ System:                                                   │
│    │  ├─ Updates reorder point in Products table                │
│    │  ├─ Logs change to audit table                             │
│    │  ├─ Saves forecast to database                             │
│    │  └─ Invalidates cache                                      │
│    ├─ Show confirmation                                         │
│    └─ Dashboard updates automatically                           │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ PAGE RENDERED TO USER                                           │
│ ✅ Parameter controls                                            │
│ ✅ 4-model comparison charts                                     │
│ ✅ Seasonal decomposition                                        │
│ ✅ Accuracy metrics                                              │
│ ✅ Actionable recommendations                                    │
│ ✅ One-click implementation                                      │
└─────────────────────────────────────────────────────────────────┘
```

### AI Decision Support Data Sources
```
Historical Data:
├─ monthly_sales (from Products table)
├─ Date range (user-selected)
└─ Normalized time series

Forecasting Models:
├─ AdvancedForecaster
│  ├─ exponential_smoothing_forecast()
│  ├─ arima_like_forecast()
│  ├─ random_forest_forecast()
│  └─ ensemble_forecast_with_intervals()
└─ Seasonal decomposition

Recommendations:
└─ Based on trend + confidence
```

---

## ⚙️ PAGE 5: MANAGEMENT

### Purpose
System administration, user management, settings, and health monitoring.

### Page Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ USER LOADS MANAGEMENT PAGE                                      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 1. SYSTEM HEALTH CHECK                                          │
│    ├─ Run module_integration.get_system_health()                │
│    ├─ Check all 8 modules:                                      │
│    │  ├─ ✓ Validators (response time, error rate)               │
│    │  ├─ ✓ Performance (cache hits, TTL status)                 │
│    │  ├─ ✓ Alerts (pending alerts, last check)                  │
│    │  ├─ ✓ Forecasting (last update, model accuracy)            │
│    │  ├─ ✓ Reporting (last report, queue)                       │
│    │  ├─ ✓ Visualization (charts available, render time)        │
│    │  ├─ ✓ Scenario Analysis (saved scenarios, compute time)    │
│    │  └─ ✓ Recommender (predictions, feedback processed)        │
│    ├─ Display status dashboard:                                 │
│    │  ├─ Green: All OK                                          │
│    │  ├─ Yellow: Degraded                                       │
│    │  └─ Red: Error                                             │
│    └─ Show last check timestamp                                 │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. USER MANAGEMENT                                              │
│    ├─ Current user profile:                                     │
│    │  ├─ Name: David Thompson                                   │
│    │  ├─ Role: Logistics Manager                                │
│    │  ├─ Last login: Today at HH:MM                              │
│    │  └─ Permissions: Full inventory management                 │
│    ├─ Add user form:                                            │
│    │  ├─ Email                                                  │
│    │  ├─ Full Name                                              │
│    │  ├─ Role (dropdown)                                        │
│    │  └─ Permissions (multi-select)                             │
│    ├─ User list:                                                │
│    │  ├─ Active users                                           │
│    │  ├─ Last activity                                          │
│    │  └─ Delete/Edit buttons                                    │
│    └─ Access control:                                           │
│       ├─ Admin: Full system access                              │
│       ├─ Manager: Inventory + Pricing                           │
│       └─ Viewer: Read-only dashboard                            │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. ALERT CONFIGURATION                                          │
│    ├─ Low Stock Alert:                                          │
│    │  ├─ Threshold %: 20% of max stock (editable)               │
│    │  ├─ Email recipients: (add/remove)                         │
│    │  └─ Frequency: Daily / Weekly / Real-time                  │
│    ├─ Stockout Risk Alert:                                      │
│    │  ├─ Days ahead: 7 (editable)                               │
│    │  └─ Recipients & frequency                                 │
│    ├─ Price Anomaly Alert:                                      │
│    │  ├─ Change %: 20% (editable)                               │
│    │  └─ Recipients & frequency                                 │
│    ├─ High Demand Alert:                                        │
│    │  ├─ Sales threshold: 50% above avg (editable)              │
│    │  └─ Recipients & frequency                                 │
│    └─ Save settings button                                      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. PERFORMANCE SETTINGS                                         │
│    ├─ Cache Configuration:                                      │
│    │  ├─ TTL (hours): 1        (adjustable)                     │
│    │  ├─ Max items: 10000      (adjustable)                     │
│    │  └─ Clear cache button    (manual)                         │
│    ├─ Forecast Settings:                                        │
│    │  ├─ Default model: Ensemble                                │
│    │  ├─ Confidence level: 95%                                  │
│    │  ├─ Re-forecast every (days): 7                            │
│    │  └─ Historical data period: 12 months                      │
│    ├─ Reorder Point Rules:                                      │
│    │  ├─ Safety stock %: 20%   (of avg sales)                   │
│    │  ├─ Lead time days: 7                                      │
│    │  └─ Max stock multiplier: 4x                               │
│    └─ Pagination:                                               │
│       ├─ Page size: 20 (editable)                               │
│       └─ Cache paginated results: Yes/No                        │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. DATABASE SETTINGS                                            │
│    ├─ Connection Status:                                        │
│    │  ├─ PostgreSQL: Connected (5432)                           │
│    │  └─ Last check: 2 minutes ago                              │
│    ├─ Database Size:                                            │
│    │  ├─ Total size: XXX MB                                     │
│    │  ├─ Products table: XXX MB                                 │
│    │  └─ Backup status: Last 2026-02-28 10:00                   │
│    ├─ Maintenance:                                              │
│    │  ├─ Run vacuum (cleanup): Button                           │
│    │  ├─ Rebuild indexes: Button                                │
│    │  └─ Export backup: Button                                  │
│    └─ Connection pool:                                          │
│       ├─ Active connections: 5/10                               │
│       └─ Queue length: 0                                        │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. LOGGING & AUDIT                                              │
│    ├─ Error Log:                                                │
│    │  ├─ Last 100 errors (if any)                               │
│    │  ├─ Timestamp, module, message                             │
│    │  └─ Download full log button                               │
│    ├─ Audit Trail:                                              │
│    │  ├─ User actions (create, update, delete)                  │
│    │  ├─ Timestamp & user                                       │
│    │  └─ Download audit CSV button                              │
│    └─ Performance Metrics:                                      │
│       ├─ Average response time: XXX ms                          │
│       ├─ Cache hit ratio: XX%                                   │
│       ├─ Query execution times                                  │
│       └─ API endpoint stats                                     │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. DATA QUALITY REPORT                                          │
│    ├─ Data completeness:                                        │
│    │  ├─ Products: 98% complete                                 │
│    │  ├─ Prices: 100% complete                                  │
│    │  ├─ Stock levels: 100% complete                            │
│    │  └─ Sales data: 95% complete                               │
│    ├─ Data anomalies:                                           │
│    │  ├─ Products with no sales: X                              │
│    │  ├─ Zero/negative prices: X                                │
│    │  ├─ Negative stock: X                                      │
│    │  └─ Duplicate products: X                                  │
│    ├─ Actions:                                                  │
│    │  ├─ Flag suspicious records                                │
│    │  ├─ Auto-clean data button                                 │
│    │  └─ Manual review list                                     │
│    └─ Schedule automatic validation                             │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ PAGE RENDERED TO USER                                           │
│ ✅ System health dashboard                                       │
│ ✅ User management                                               │
│ ✅ Alert configuration                                           │
│ ✅ Performance settings                                          │
│ ✅ Database status                                               │
│ ✅ Logging & audit                                               │
│ ✅ Data quality report                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💵 PAGE 6: PRICING

### Purpose
Price optimization, demand elasticity analysis, discount recommendations, and revenue impact calculations.

### Page Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ USER LOADS PRICING PAGE                                         │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 1. LOAD PRICING SUMMARY                                         │
│    ├─ Today's KPIs:                                             │
│    │  ├─ Total Revenue (today): ₹XXX                            │
│    │  ├─ Avg Product Price: ₹XXX                                │
│    │  ├─ Avg Discount Applied: X%                               │
│    │  └─ Margin %: XX.X%                                        │
│    ├─ Trend vs Yesterday: +/- X%                                │
│    └─ Display as 4 KPI cards                                    │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. PRODUCT SELECTOR                                             │
│    ├─ Filter by:                                                │
│    │  ├─ Category (multi-select)                                │
│    │  ├─ Price range (min-max slider)                           │
│    │  ├─ Demand pattern (X/Y/Z)                                 │
│    │  └─ Value class (A/B/C)                                    │
│    ├─ Sort by:                                                  │
│    │  ├─ Price (asc/desc)                                       │
│    │  ├─ Demand (high/low)                                      │
│    │  ├─ Margin (high/low)                                      │
│    │  └─ Revenue (high/low)                                     │
│    └─ Selected products listed below                            │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. DEMAND ELASTICITY ANALYSIS                                   │
│    ├─ For selected products:                                    │
│    │  ├─ Get historical price points (price_audit)              │
│    │  ├─ Get corresponding sales (monthly_sales)                │
│    │  ├─ Calculate elasticity:                                  │
│    │  │  Elasticity = (ΔQty / Δ Price) × (Avg Price / Avg Qty)  │
│    │  ├─ Classify:                                              │
│    │  │  ├─ Elastic: > 1 (price sensitive)                      │
│    │  │  ├─ Unit elastic: = 1                                   │
│    │  │  └─ Inelastic: < 1 (price insensitive)                  │
│    │  └─ Chart: Price vs Sales points                           │
│    └─ Display elasticity scatter plot                           │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. COMPETITIVE PRICING ANALYSIS                                 │
│    ├─ For each product category:                                │
│    │  ├─ Your average price                                     │
│    │  ├─ Market average (from industry data)                    │
│    │  ├─ Price difference: +/- X%                               │
│    │  ├─ Competitor position: Higher/Lower/Same                 │
│    │  └─ Recommendation: Increase/Decrease/Maintain             │
│    ├─ Display as:                                               │
│    │  ├─ Comparison bars (Your price vs Market)                 │
│    │  ├─ Positioning matrix (Price vs Quality)                  │
│    │  └─ Table with details per category                        │
│    └─ Action buttons: "Increase Price" / "Keep" / "Decrease"    │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. DISCOUNT RECOMMENDATION ENGINE                               │
│    ├─ User selects product(s)                                   │
│    ├─ System suggests discounts:                                │
│    │  ├─ For profit optimization: X%                            │
│    │  ├─ For revenue maximization: Y%                           │
│    │  ├─ For market share: Z%                                   │
│    │  ├─ For seasonal peak: W%                                  │
│    │  ├─ For clearance (low stock): V%                          │
│    │  └─ For competitive match: U%                              │
│    ├─ For each option show:                                     │
│    │  ├─ Expected units sold                                    │
│    │  ├─ Expected revenue                                       │
│    │  ├─ Expected profit                                        │
│    │  ├─ Break-even check                                       │
│    │  └─ Margin impact                                          │
│    └─ User selects one option                                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. PRICE HISTORY CHART                                          │
│    ├─ For selected product:                                     │
│    │  ├─ Line chart: Price over time (last 12 months)           │
│    │  ├─ Mark discount periods (shaded regions)                 │
│    │  ├─ Overlay: Sales volume (bars)                           │
│    │  ├─ Show: Price elasticity at each point                   │
│    │  ├─ Overlay: COGS (cost price)                             │
│    │  └─ Highlight: Profit margin band                          │
│    └─ Interactive Plotly chart                                  │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. BULK PRICING OPERATIONS                                      │
│    ├─ Select products (or category)                             │
│    ├─ Operation type:                                           │
│    │  ├─ Percentage increase: +5%                               │
│    │  ├─ Percentage decrease: -10%                              │
│    │  ├─ Set fixed price: ₹XXX                                  │
│    │  └─ Apply formula: (COGS × 1.5)                            │
│    ├─ Constraints:                                              │
│    │  ├─ Minimum price: ₹XXX (cost enforced)                    │
│    │  ├─ Maximum price: ₹XXX (optional cap)                     │
│    │  ├─ Minimum margin: X%                                     │
│    │  └─ No discount >X%                                        │
│    ├─ Preview impact:                                           │
│    │  ├─ Before & after prices                                  │
│    │  ├─ Revenue impact estimates                               │
│    │  ├─ Products affected                                      │
│    │  └─ Margin changes                                         │
│    ├─ Validate & apply                                          │
│    └─ Update database + audit log                               │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. REVENUE IMPACT CALCULATOR                                    │
│    ├─ Scenario inputs:                                          │
│    │  ├─ New price: ₹XXX                                        │
│    │  ├─ Expected % demand change: +X%                          │
│    │  ├─ Discount %: X%                                         │
│    │  └─ Time period: 30 days                                   │
│    ├─ Calculate impact:                                         │
│    │  ├─ Current: Qty × Current Price = Revenue₁                │
│    │  ├─ New: (Qty × Elasticity) × New Price = Revenue₂         │
│    │  ├─ Difference: Revenue₂ - Revenue₁                        │
│    │  ├─ Profit impact after cogs                               │
│    │  └─ Breakeven point                                        │
│    ├─ Show:                                                     │
│    │  ├─ Waterfall chart (before → after)                       │
│    │  ├─ Sensitivity analysis (price elasticity)                │
│    │  └─ "What-if" scenario comparison                          │
│    └─ Save scenario for later                                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. PRICING RULES & POLICIES                                     │
│    ├─ Display current rules:                                    │
│    │  ├─ Minimum margin by category: X%                         │
│    │  ├─ Maximum discount: X%                                   │
│    │  ├─ Price match competitors: Yes/No                        │
│    │  ├─ Dynamic pricing: On/Off                                │
│    │  └─ Seasonal pricing: On/Off                               │
│    ├─ Edit rules:                                               │
│    │  ├─ Update any rule                                        │
│    │  ├─ Set effective date                                     │
│    │  ├─ Preview impact                                         │
│    │  └─ Apply & audit log                                      │
│    └─ Historical rule changes                                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ PAGE RENDERED TO USER                                           │
│ ✅ Pricing KPIs                                                  │
│ ✅ Demand elasticity charts                                      │
│ ✅ Competitive analysis                                          │
│ ✅ Discount recommendations                                      │
│ ✅ Price history visualization                                   │
│ ✅ Bulk operations                                               │
│ ✅ Revenue impact calculator                                     │
│ ✅ Pricing policies                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 PAGE 7: REPORTS

### Purpose
Generate, download, and schedule reports for data analysis and decision support.

### Page Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ USER LOADS REPORTS PAGE                                         │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 1. REPORT TYPE SELECTION                                        │
│    ├─ Choose report type:                                       │
│    │  ├─ Inventory Report                                       │
│    │  ├─ Sales Report                                           │
│    │  ├─ Performance Report                                     │
│    │  ├─ Discount Impact Report                                 │
│    │  ├─ Lost Sales Report                                      │
│    │  ├─ Forecast Report                                        │
│    │  ├─ KPI Summary                                            │
│    │  └─ Custom Report Builder                                  │
│    └─ User selects one                                          │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. FILTER & PARAMETERS                                          │
│    ├─ Date range:                                               │
│    │  ├─ Start date (picker)                                    │
│    │  ├─ End date (picker)                                      │
│    │  └─ Presets: Last 7/30/90 days, YTD, Custom                │
│    ├─ Category filter:                                          │
│    │  ├─ Multi-select (all / select specific)                   │
│    │  └─ Include all = single report                            │
│    ├─ Product filter:                                           │
│    │  ├─ All / Top 10 / Bottom 10 / Custom list                 │
│    │  └─ Optional for all report types                          │
│    ├─ Performance level (for KPI reports):                      │
│    │  ├─ Executive summary (high-level)                         │
│    │  ├─ Detailed (line items)                                  │
│    │  └─ Granular (every transaction)                           │
│    └─ User configures filters                                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. GENERATE REPORT                                              │
│    ├─ Click "Generate Report"                                   │
│    ├─ System calls ReportGenerator:                             │
│    │  ├─ Fetch filtered data (database)                         │
│    │  ├─ Calculate metrics                                      │
│    │  ├─ Format data                                            │
│    │  ├─ Create charts (if applicable)                          │
│    │  └─ Build workbook                                         │
│    ├─ Progress indicator (% complete)                           │
│    └─ Report ready notification                                 │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. PREVIEW REPORT                                               │
│    ├─ Report preview panel:                                     │
│    │  ├─ Summary section (KPIs, dates, filters applied)         │
│    │  ├─ Table preview (first 20 rows)                          │
│    │  ├─ Chart preview (if charts included)                     │
│    │  ├─ Page count indicator                                   │
│    │  └─ Data quality check                                     │
│    ├─ Options:                                                  │
│    │  ├─ Adjust filters & regenerate                            │
│    │  ├─ Change visualizations                                  │
│    │  └─ Proceed to export                                      │
│    └─ User reviews                                              │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. EXPORT OPTIONS                                               │
│    ├─ Format selection:                                         │
│    │  ├─ Excel (.xlsx)                                          │
│    │  │  ├─ Multi-sheet workbook                                │
│    │  │  ├─ Formatted cells (colors, borders)                   │
│    │  │  ├─ Embedded charts                                     │
│    │  │  ├─ Frozen headers                                      │
│    │  │  └─ Easy to share & print                               │
│    │  ├─ CSV (.csv)                                             │
│    │  │  ├─ Comma-separated values                              │
│    │  │  ├─ No formatting                                       │
│    │  │  ├─ Easy import to other tools                          │
│    │  │  └─ Large file support                                  │
│    │  └─ PDF (.pdf)                                             │
│    │     ├─ Print-ready format                                  │
│    │     ├─ No editing                                          │
│    │     └─ Professional look                                   │
│    ├─ Additional options:                                       │
│    │  ├─ Include company logo: Yes/No                           │
│    │  ├─ Add timestamp: Yes/No                                  │
│    │  ├─ Include summary page: Yes/No                           │
│    │  └─ Watermark: None / Draft / Confidential                 │
│    └─ User selects format                                       │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. DOWNLOAD REPORT                                              │
│    ├─ Generate file in selected format                          │
│    ├─ File naming: {reporttype}_{date}_{user}                   │
│    ├─ Show download button                                      │
│    ├─ File size indicator                                       │
│    ├─ Direct browser download (no server storage needed)        │
│    └─ Success message with details                              │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. EMAIL REPORT (Optional)                                      │
│    ├─ Checkbox: "Email report"                                  │
│    ├─ Recipients: (comma-separated emails)                      │
│    ├─ Subject: (auto-filled, editable)                          │
│    ├─ Message: (optional custom message)                        │
│    ├─ Click "Send Email"                                        │
│    ├─ System:                                                   │
│    │  ├─ Generates report file                                  │
│    │  ├─ Attaches to email                                      │
│    │  ├─ Sends via SMTP                                         │
│    │  └─ Logs action                                            │
│    └─ Confirmation: "Email sent to..."                          │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. SCHEDULE AUTOMATED REPORTS                                   │
│    ├─ Setup scheduled report:                                   │
│    │  ├─ Report type (select)                                   │
│    │  ├─ Schedule: Daily / Weekly / Monthly                     │
│    │  ├─ Run time: HH:MM (e.g., 08:00 AM)                       │
│    │  ├─ Recipients: (email list)                               │
│    │  ├─ Format: Excel / CSV / PDF                              │
│    │  ├─ Filters to apply (category, period, etc.)              │
│    │  ├─ Effective date:  From YYYY-MM-DD                       │
│    │  └─ End date: (optional, leave blank for ongoing)          │
│    ├─ Create schedule button                                    │
│    ├─ System:                                                   │
│    │  ├─ Saves config to database                               │
│    │  ├─ Adds to scheduler queue                                │
│    │  └─ Runs at scheduled times                                │
│    ├─ View scheduled reports:                                   │
│    │  ├─ List of active schedules                               │
│    │  ├─ Next run time                                          │
│    │  ├─ Edit/Pause/Delete buttons                              │
│    │  └─ View last sent report                                  │
│    └─ Confirmation: "Schedule created"                          │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. REPORT HISTORY                                               │
│    ├─ View previously generated reports:                        │
│    │  ├─ Report type                                            │
│    │  ├─ Generation date/time                                   │
│    │  ├─ Generated by (user)                                    │
│    │  ├─ File size                                              │
│    │  ├─ Download button                                        │
│    │  └─ Delete button (archive old reports)                    │
│    ├─ Filter history:                                           │
│    │  ├─ By report type                                         │
│    │  ├─ By date range                                          │
│    │  └─ By user who generated                                  │
│    ├─ Export all history (CSV)                                  │
│    └─ Pagination: 10 per page                                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│ PAGE RENDERED TO USER                                           │
│ ✅ Report type selector                                          │
│ ✅ Filter configuration                                          │
│ ✅ Preview panel                                                 │
│ ✅ Export options                                                │
│ ✅ Download/Email buttons                                        │
│ ✅ Schedule management                                           │
│ ✅ Report history                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

---

# 🎯 OVERALL PROJECT WORKFLOW

## Complete End-to-End System Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                    INTELLISTOCK SYSTEM - COMPLETE WORKFLOW             │
│                                                                        │
│                        ↓ START: USER SESSION ↓                         │
└────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────────┐
                              │ USER LOGS IN     │
                              │ (David Thompson) │
                              │ Logistics Mgr    │
                              └────────┬─────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: APPLICATION INITIALIZATION                                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  1. Load Streamlit App (app.py)                                       │
│     ├─ Set page config (wide layout, 📦 icon)                         │
│     ├─ Initialize session state:                                      │
│     │  ├─ Cache = Cache(ttl=3600s)                                   │
│     │  ├─ AlertManager = AlertManager()                              │
│     │  └─ Recommender = MLRecommender()                              │
│     └─ Load CSS styling (custom dashboard)                           │
│                                                                        │
│  2. Load Product Data                                                 │
│     ├─ Try: Query PostgreSQL database                                 │
│     │  ├─ products.py (using SQLAlchemy ORM)                          │
│     │  ├─ reorders.py                                                 │
│     │  ├─ discount_audit.py                                           │
│     │  └─ price_audit.py                                              │
│     └─ Fallback: Load CSV files if DB unavailable                    │
│                  ├─ products.csv                                       │
│                  ├─ reorders.csv                                       │
│                  ├─ ai_recommendations.csv                             │
│                  └─ discount_audit.csv                                 │
│                                                                        │
│  3. Validate Data (validators.py)                                     │
│     ├─ Check all products loaded correctly                            │
│     ├─ Validate data types & ranges                                   │
│     ├─ Sanitize strings                                               │
│     ├─ Check for missing critical fields                              │
│     └─ Log any validation issues                                      │
│                                                                        │
│  4. Initialize Core Services                                          │
│     ├─ DashboardService                                               │
│     ├─ InventoryService                                               │
│     ├─ DiscountService                                                │
│     ├─ AIService                                                      │
│     ├─ OrderService                                                   │
│     └─ PricingService                                                 │
│                                                                        │
│  ✅ Application Ready                                                  │
└────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: REQUEST ROUTING (User Navigation)                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Sidebar Navigation:                                                  │
│  ┌─ Dashboard ──────────┐                                             │
│  ├─ Inventory ─────────┤                                              │
│  ├─ Stockouts & Sales ─┤                                              │
│  ├─ AI Decision ───────┤  ← User clicks page                         │
│  ├─ Management ────────┤                                              │
│  ├─ Pricing ───────────┤                                              │
│  └─ Reports ──────────┘                                               │
│                                                                        │
│  Router (if menu == "Dashboard"):                                     │
│    └─→ Execute Page 1 Workflow                                        │
│                                                                        │
│  Router (if menu == "Inventory"):                                     │
│    └─→ Execute Page 2 Workflow                                        │
│                                                                        │
│  [... etc for all 7 pages]                                            │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: PAGE EXECUTION (One of 7 Pages)                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  A. DASHBOARD PAGE                                                    │
│     ├─→ Get product selection from sidebar                            │
│     ├─→ Query database for product details                            │
│     ├─→ Calculate 5 KPIs                                              │
│     ├─→ Classify product (ABC, XYZ, Seasonal)                         │
│     ├─→ Get AI discount recommendation                                │
│     ├─→ Render overview, charts, tables                               │
│     └─→ Display to user                                               │
│                                                                        │
│  B. INVENTORY PAGE                                                    │
│     ├─→ Load inventory summary metrics                                │
│     ├─→ Apply category filters                                        │
│     ├─→ Display inventory table with status                           │
│     ├─→ Show low stock alerts                                         │
│     ├─→ Allow product management                                      │
│     ├─→ Process bulk discount if applied                              │
│     ├─→ Generate AI stock forecast on demand                          │
│     └─→ Display to user                                               │
│                                                                        │
│  [... Pages 3-7 similar pattern]                                      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: USER ACTION (Form Submit / Button Click)                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Possible User Actions:                                              │
│  ├─ Update product stock                                              │
│  ├─ Apply discount to product(s)                                      │
│  ├─ Change product price                                              │
│  ├─ Generate forecast                                                 │
│  ├─ Create reorder                                                    │
│  ├─ Export report                                                     │
│  ├─ Acknowledge alert                                                 │
│  ├─ Schedule report                                                   │
│  └─ Update settings                                                   │
│                                                                        │
│  User submits form...                                                 │
└────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: INPUT VALIDATION                                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  validators.py checks:                                                │
│  ├─ validate_product()          → Is product valid?                   │
│  ├─ validate_price_change()     → Price change ≤ 30%?                 │
│  ├─ validate_discount_change()  → Margin preserved > 10%?             │
│  ├─ validate_dataframe()        → DataFrame integrity?                │
│  ├─ sanitize_string()           → Clean input strings                 │
│  └─ validate_email()            → Email format OK?                    │
│                                                                        │
│  If VALID:  ✅ Proceed to Phase 6                                     │
│  If INVALID: ❌ Show error & return to form                           │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 6: DATABASE OPERATION                                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  PostgreSQL (Docker Container):                                       │
│  ├─ INSERT: New product, reorder, audit record                        │
│  ├─ UPDATE: Stock level, price, discount                              │
│  ├─ SELECT: Query for reports, charts, forecasts                      │
│  ├─ DELETE: Remove products (soft delete to audit)                    │
│  └─ TRANSACTION: Multi-step operations (atomic)                       │
│                                                                        │
│  Audit Trail (automatic):                                            │
│  ├─ discount_audit: All discount changes                              │
│  ├─ price_audit: All price changes                                    │
│  ├─ reorders: All order changes                                       │
│  └─ Logs: Timestamps + user info                                      │
│                                                                        │
│  Database Updated ✅                                                   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 7: CACHE INVALIDATION                                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  performance.py Cache:                                                │
│  ├─ Old cache entry invalidated                                       │
│  ├─ New data queried from DB                                          │
│  ├─ Results recached with TTL                                         │
│  ├─ Related caches cleared                                            │
│  │  ├─ Dashboard KPIs (affected product)                              │
│  │  ├─ Inventory summary (total units may change)                     │
│  │  ├─ Category totals                                                │
│  │  └─ Forecast cache (if applicable)                                 │
│  └─ Future queries use new data                                       │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 8: ENHANCEMENT MODULES (Auto-Triggered)                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  1. ALERTS (alerts.py)                                                │
│     ├─ check_low_stock(df, threshold)                                 │
│     ├─ check_stockout_risk(df, days=7)                                │
│     ├─ check_price_anomalies(df)                                      │
│     ├─ check_high_demand(df)                                          │
│     └─ Send notifications if alerts triggered                         │
│                                                                        │
│  2. PERFORMANCE (performance.py)                                      │
│     ├─ Cache updated result                                           │
│     ├─ Optimize subsequent queries                                    │
│     └─ Paginate if > 1000 records                                     │
│                                                                        │
│  3. ADVANCED FORECAST (advanced_forecast.py) [Optional]               │
│     ├─ If product stock changed significantly                         │
│     ├─ Re-run 4 models:                                               │
│     │  ├─ Exponential Smoothing                                       │
│     │  ├─ ARIMA                                                       │
│     │  ├─ Random Forest                                               │
│     │  └─ Ensemble (best)                                             │
│     └─ Update forecast in DB                                          │
│                                                                        │
│  4. ML RECOMMENDER (enhanced_recommendations.py) [Optional]           │
│     ├─ Generate new recommendations                                   │
│     ├─ A/B test variant performance                                   │
│     ├─ Update feedback loop                                           │
│     └─ Next recommendation improves                                   │
│                                                                        │
│  5. VISUALIZATION (visualization.py) [Real-time]                      │
│     ├─ Prepare chart data                                             │
│     ├─ Use new values for live charts                                 │
│     └─ Charts auto-update on page refresh                             │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 9: REPORTING & ANALYTICS (On-Demand)                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  User requests Report:                                                │
│  ├─ ReportGenerator (reporting.py):                                   │
│  │  ├─ Generate inventory report (Excel)                              │
│  │  ├─ Generate performance report (CSV)                              │
│  │  ├─ Generate lost sales report (with charts)                       │
│  │  └─ Include KPI summaries                                          │
│  │                                                                    │
│  ├─ VisualizationFactory (visualization.py):                          │
│  │  ├─ Create revenue forecast chart (line + CI)                      │
│  │  ├─ Create category pie chart                                      │
│  │  ├─ Create stock turnover heatmap                                  │
│  │  ├─ Create margin distribution box                                 │
│  │  └─ Create 9+ more chart types                                     │
│  │                                                                    │
│  └─ Package into file (Excel/CSV/PDF)                                 │
│                                                                        │
│  Report Options:                                                      │
│  ├─ Download to user's computer                                       │
│  ├─ Email report attachment                                           │
│  └─ Schedule for automatic sending                                    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 10: PAGE RENDERING (to Browser)                                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Streamlit renders:                                                   │
│  ├─ HTML structure                                                    │
│  ├─ CSS styling (dashboard.css + inline)                              │
│  ├─ Interactive elements:                                             │
│  │  ├─ Dropdowns (product selector)                                   │
│  │  ├─ Sliders (discount %)                                           │
│  │  ├─ Date pickers                                                   │
│  │  ├─ Buttons (submit, export, etc.)                                 │
│  │  ├─ Text inputs (for notes)                                        │
│  │  └─ Multi-select (categories, filters)                             │
│  ├─ Data visualizations:                                              │
│  │  ├─ Plotly interactive charts                                      │
│  │  ├─ Pandas DataFrames (tables)                                     │
│  │  └─ KPI metric cards                                               │
│  └─ Success/Error messages                                            │
│                                                                        │
│  Browser receives & displays UI                                       │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 11: USER INTERACTION (Continuous Loop)                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  User can now:                                                        │
│  ├─ [View dashboard] → See updated KPIs & insights                    │
│  ├─ [Apply discount] → Proceed to Phase 5-9 again                     │
│  ├─ [Export report] → Download data                                   │
│  ├─ [Navigate to different page] → Proceed to Phase 2                 │
│  ├─ [Acknowledge alert] → Mark resolved & update DB                   │
│  ├─ [View charts] → Interact with Plotly visualizations               │
│  ├─ [Apply recommendation] → Auto-implement suggestion                │
│  └─ [Schedule report] → Set up automation                             │
│                                                                        │
│  Each action loops back to Phase 4-11                                 │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 12: MONITORING & BACKGROUND TASKS                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Continuous (Every 5-60 minutes):                                     │
│  ├─ Alert system wakes up:                                            │
│  │  ├─ check_low_stock()                                              │
│  │  ├─ check_stockout_risk()                                          │
│  │  ├─ check_price_anomalies()                                        │
│  │  └─ check_high_demand()                                            │
│  ├─ Creates new alerts if conditions met                              │
│  ├─ Sends notifications (email/dashboard)                             │
│  └─ Logs alerts to database                                           │
│                                                                        │
│  Daily (Scheduled):                                                   │
│  ├─ Forecast models retrain (optional)                                │
│  ├─ Scheduled reports generate and email                              │
│  ├─ Cache TTL refreshes                                               │
│  ├─ Backup database                                                   │
│  └─ Clean up old logs                                                 │
│                                                                        │
│  On-Demand (module_integration.py):                                   │
│  ├─ Health check: All 8 modules operational?                          │
│  ├─ Response times acceptable?                                        │
│  ├─ Database connection stable?                                       │
│  ├─ Cache hit rate good?                                              │
│  └─ Report errors to admin                                            │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 13: SESSION END (User Logout)                                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ├─ Clear session state                                               │
│  ├─ Close database connections                                        │
│  ├─ Invalidate cache entries (optional)                               │
│  ├─ Log out user                                                      │
│  └─ Redirect to login page                                            │
│                                                                        │
│  System ready for next user session                                   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Architecture

```
OUTER LOOP (User Session):
  1. User logs in
  2. App initializes
  3. User navigates (phases 2-11 repeat)
  4. User logs out

INNER LOOP (Per Action - Phases 4-11):
  Form Input
    ↓
  Validation (validators)
    ↓
  Database Operation
    ↓
  Cache Invalidation (performance)
    ↓
  Enhancement Modules (alerts, forecast, viz)
    ↓
  Page Render (streamlit)
    ↓
  User Views Results
    ↓
  (Loop back for next action)

BACKGROUND TASKS (Continuous):
  Every 5 mins:   Alerts check
  Every 15 mins:  Cache refresh
  Daily:          Forecast retrain
  Daily:          Report generation
  Scheduled:      User-configured tasks
```

---

## 🎛️ System State Management

```
Session State (Per User):
├─ cache: Cache object (TTL-based)
├─ alert_manager: AlertManager instance
├─ recommender: MLRecommender instance
├─ selected_product: Current product
├─ current_page: Active page
└─ user_filters: Applied filters

Database State (Persistent):
├─ Products table (current inventory)
├─ Reorders table (pending orders)
├─ Discount_audit (change history)
├─ Price_audit (change history)
└─ Alerts table (alert records)

Cache State (Temporary):
├─ KPI calculations (1 hour TTL)
├─ Forecasts (24 hour TTL)
├─ Dashboard data (30 min TTL)
└─ Paginated queries (1 hour TTL)
```

---

## ✅ Checklist: System Workflow Complete

- [x] **Phase 1:** App initialization
- [x] **Phase 2:** Request routing (navigation)
- [x] **Phase 3:** Page execution (7 pages covered)
- [x] **Phase 4:** User action handling
- [x] **Phase 5:** Input validation
- [x] **Phase 6:** Database operations
- [x] **Phase 7:** Cache management
- [x] **Phase 8:** Enhancement modules
- [x] **Phase 9:** Reporting & analytics
- [x] **Phase 10:** UI rendering
- [x] **Phase 11:** User interaction loop
- [x] **Phase 12:** Background monitoring
- [x] **Phase 13:** Session management

---

**System Status:** ✅ **100% Complete & Fully Operational**

**Generated:** February 28, 2026
