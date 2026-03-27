# IntelliStock Dashboard - New Modules Integration Guide

## Overview

You now have **8 new enterprise-grade modules** successfully created that add powerful features to your dashboard:

| Module | Purpose | Status |
|--------|---------|--------|
| **validators.py** | Data validation & error handling | ✅ Complete |
| **performance.py** | Caching, pagination & optimization | ✅ Complete |
| **alerts.py** | Real-time alerts & notifications | ✅ Complete |
| **advanced_forecast.py** | ML-based forecasting with confidence intervals | ✅ Complete |
| **reporting.py** | Excel export & scheduled reports | ✅ Complete |
| **visualization.py** | Enhanced interactive charts | ✅ Complete |
| **scenario_analysis.py** | What-if analysis & scenario comparison | ✅ Complete |
| **enhanced_recommendations.py** | ML recommendations, A/B testing, feedback loops | ✅ Complete |

## Quick Start - Top 3 Integration Tasks

### 1. **Add Validation to Forms** (Easy - 15 min)
Add input validation to product forms for real-time error feedback:

```python
from backend.validators import DataValidator

# In your form:
if st.button("Add Product"):
    is_valid, message = DataValidator.validate_product(
        product_id, product_name, selling_price
    )
    if is_valid:
        # Add to database
        st.success("✅ Product added!")
    else:
        st.error(f"❌ {message}")
```

### 2. **Display Alerts Dashboard** (Medium - 20 min)
Add alert monitoring to your main dashboard:

```python
from backend.alerts import AlertManager

alert_mgr = AlertManager()
alerts = alert_mgr.get_open_alerts()

col1, col2, col3 = st.columns(3)
with col1:
    critical = len([a for a in alerts if a['severity'] == 4])
    st.metric("🔴 Critical", critical)
with col2:
    high = len([a for a in alerts if a['severity'] == 3])
    st.metric("🟠 High", high)
with col3:
    st.metric("📊 Total", len(alerts))
```

### 3. **Add Excel Export** (Easy - 10 min)
Allow users to download reports:

```python
from backend.reporting import ReportGenerator

if st.button("📥 Export Inventory Report"):
    report_bytes = ReportGenerator.generate_inventory_report(products_df)
    if report_bytes:
        st.download_button(
            label="Download Excel Report",
            data=report_bytes,
            file_name=f"inventory_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
```

## Module Details & APIs

### 1. validators.py - Data Validation Framework

**Key Classes:**
- `DataValidator` - Static methods for all validation

**Main Methods:**
```python
# Validate single product
is_valid, message = DataValidator.validate_product(
    product_id=1, 
    product_name="Widget", 
    selling_price=100
)

# Validate price changes
is_valid, message = DataValidator.validate_price_change(
    old_price=100,
    new_price=120,
    max_change_pct=30
)

# Validate discount
is_valid, message = DataValidator.validate_discount_change(
    product_id=1,
    discount_pct=15,
    min_margin=10
)

# Validate entire dataframe
is_valid, errors = DataValidator.validate_dataframe(df)
# Returns: (bool, [list of error rows])

# Email validation
is_valid, message = DataValidator.validate_email("user@example.com")

# String sanitization
clean_str = DataValidator.sanitize_string("Product <Name>")
```

**Returns:** `Tuple[bool, str]` - (success, message)

---

### 2. performance.py - Caching & Optimization

**Key Classes:**
- `Cache` - In-memory caching with TTL
- `Paginator` - Pagination helper
- `QueryOptimizer` - Query optimization

**Usage:**

```python
# Initialize cache
cache = Cache(ttl_seconds=3600)  # 1 hour

# Use cache
cache.set('products', products_df)
products = cache.get('products')
cache.clear()

# Decorator for automatic caching
from backend.performance import cached

@cached(ttl_seconds=3600)
def expensive_calculation():
    return result

# Pagination
paginator = Paginator(page_size=20)
page_data = paginator.paginate_dataframe(df, page_num=1)
# Returns: {'data': df_page, 'total_pages': 5, 'page_size': 20}

# Query optimization
optimizer = QueryOptimizer()
top_10 = optimizer.get_top_products(df, category='Electronics', n=10)
low_stock = optimizer.get_low_stock_products(df, threshold=20)
```

---

### 3. alerts.py - Real-time Alerts System

**Key Classes:**
- `AlertManager` - Create and manage alerts
- `EmailNotifier` - Send email notifications

**Alert Types:**
- `LOW_STOCK` - Below threshold
- `STOCKOUT` - Zero stock
- `PRICE_CHANGE` - Significant price change
- `HIGH_DEMAND` - Unusual sales spike
- `EXCESS_INVENTORY` - Over-stocked
- `REORDER_DUE` - Time to reorder
- `QUALITY_ISSUE` - Quality concerns

**Severity Levels:** LOW(1), MEDIUM(2), HIGH(3), CRITICAL(4)

**Usage:**

```python
from backend.alerts import AlertManager

alert_mgr = AlertManager()

# Create alert
alert_mgr.create_alert(
    alert_type='LOW_STOCK',
    product_id=1,
    product_name='Widget',
    current_value=15,
    threshold=20,
    severity=3
)

# Check conditions
alerts = alert_mgr.check_low_stock(df, threshold=20)
alerts = alert_mgr.check_stockout_risk(df, lead_time_days=7)
alerts = alert_mgr.check_price_anomalies(df, threshold_pct=10)
alerts = alert_mgr.check_high_demand(df, threshold_pct=20)

# Get alerts
open_alerts = alert_mgr.get_open_alerts()
critical_alerts = [a for a in open_alerts if a['severity'] == 4]

# Resolve alert
alert_mgr.resolve_alert(alert_id)

# Send emails
notifier = EmailNotifier(
    smtp_server="smtp.gmail.com",
    sender_email="your-email@gmail.com",
    sender_password="your-password"
)
notifier.send_alert_email(
    recipient="manager@example.com",
    alert=alert
)
```

---

### 4. advanced_forecast.py - Advanced Forecasting

**Key Classes:**
- `AdvancedForecaster` - Multiple forecasting models

**Models:**
1. **Exponential Smoothing** - Smooth trends
2. **ARIMA-like** - Using differencing
3. **Random Forest** - ML-based
4. **Ensemble** - Weighted combination

**Usage:**

```python
from backend.advanced_forecast import AdvancedForecaster

forecaster = AdvancedForecaster()

# Simple forecast
forecast_data = forecaster.exponential_smoothing_forecast(
    historical_data=[100, 105, 110, 108, ...],
    periods=30,
    alpha=0.3
)
# Returns: {'forecast': [...], 'upper_ci': [...], 'lower_ci': [...]}

# Ensemble forecast (best accuracy)
forecast_data = forecaster.forecast_with_intervals(
    historical_data=revenue_history,
    periods=30,
    confidence=0.95
)
# Returns dict with multiple model predictions and confidence intervals

# Seasonal decomposition
trends, seasonal, residual = forecaster.decompose_seasonal(
    time_series=df,
    period=12  # 12 months
)

# Save forecast for later
forecaster.save_forecast(
    product_id=1,
    forecast_data=forecast_data,
    model_name='ensemble'
)
```

---

### 5. reporting.py - Excel Reports & Scheduling

**Key Classes:**
- `ReportGenerator` - Generate Excel, CSV reports
- `ScheduledReportConfig` - Schedule reports

**Usage:**

```python
from backend.reporting import ReportGenerator, ScheduledReportConfig

# Generate Excel report
report_bytes = ReportGenerator.generate_inventory_report(
    df=products_df,
    include_charts=True
)

if report_bytes:
    st.download_button(
        label="Download Excel",
        data=report_bytes,
        file_name="inventory_report.xlsx"
    )

# Export to CSV
ReportGenerator.export_to_csv(df, "products.csv")

# Performance report
perf_report = ReportGenerator.generate_performance_report(
    df=products_df,
    discount_history=discounts,
    price_history=prices
)

# Schedule report
ScheduledReportConfig.create_schedule(
    report_type='inventory',
    frequency='weekly',  # 'daily', 'weekly', 'monthly'
    recipients=['manager@example.com'],
    include_pdf=False
)

# Get schedules
schedules = ScheduledReportConfig.get_schedules()
```

---

### 6. visualization.py - Enhanced Charts

**Key Classes:**
- `VisualizationFactory` - Create interactive charts

**Available Charts:**

```python
from backend.visualization import VisualizationFactory

# Pie chart - inventory status
fig = VisualizationFactory.create_inventory_status_pie(df)
st.plotly_chart(fig)

# Line chart - forecasts with confidence intervals
fig = VisualizationFactory.create_revenue_forecast_line(
    dates=date_list,
    actual_revenue=actual,
    forecast_revenue=forecast,
    confidence_upper=upper_ci,
    confidence_lower=lower_ci
)

# Heatmap - stock turnover
fig = VisualizationFactory.create_stock_turnover_heatmap(df)

# Box plot - margin distribution
fig = VisualizationFactory.create_margin_distribution_box(df)

# Scatter - stock vs sales
fig = VisualizationFactory.create_stock_velocity_scatter(df)

# Area chart - cumulative revenue
fig = VisualizationFactory.create_cumulative_revenue_area(df, top_n=10)

# Histogram - price distribution
fig = VisualizationFactory.create_price_range_histogram(df)

# Comparison bars
fig = VisualizationFactory.create_comparison_bars(
    categories=['Q1', 'Q2', 'Q3'],
    values1=[100, 120, 110],
    values2=[80, 95, 105],
    label1='2023',
    label2='2024',
    title='Quarterly Revenue'
)

# Funnel chart
fig = VisualizationFactory.create_funnel_chart(
    stages=['Leads', 'Contacts', 'Opportunities', 'Won'],
    values=[1000, 500, 200, 80]
)
```

---

### 7. scenario_analysis.py - What-if Analysis

**Key Classes:**
- `Scenario` - Define scenario
- `ScenarioAnalyzer` - Calculate impact
- `ScenarioManager` - Persist scenarios

**Usage:**

```python
from backend.scenario_analysis import Scenario, ScenarioAnalyzer, ScenarioManager

# Create scenario
scenario = Scenario(
    name="Q1 2024 Plan",
    description="10% price increase, focus on Electronics"
)

# Apply changes
scenario.apply_price_change(product_id=1, new_price=110)
scenario.apply_discount(product_id=2, discount_pct=15)
scenario.apply_stock_change(product_id=3, new_stock=500)

# Calculate impact
scenario_df, impact = ScenarioAnalyzer.calculate_scenario_impact(
    base_df=products_df,
    scenario=scenario
)
# Returns: (modified_df, {'revenue_change': X, 'profit_change': Y, ...})

# Compare scenarios
comparison = ScenarioAnalyzer.create_comparison_summary(
    base_df=products_df,
    scenarios=[scenario1, scenario2, scenario3]
)
# Returns: DataFrame with all metrics comparison

# ROI calculation
roi = ScenarioAnalyzer.roi_calculation(
    investment=50000,
    revenue_increase=2000,
    cost_increase=500,
    time_period_months=12
)
# Returns: {'roi_percent': X, 'payback_months': Y, ...}

# Sensitivity analysis
sensitivity = ScenarioAnalyzer.sensitivity_analysis(
    base_df=products_df,
    variable='price',  # 'price', 'cost', 'demand'
    min_change=-20,
    max_change=20,
    steps=5
)

# Save scenario
ScenarioManager.save_scenario(scenario)

# Load scenario
loaded = ScenarioManager.load_scenario(scenario.id)

# List scenarios
scenarios = ScenarioManager.list_scenarios()
```

---

### 8. enhanced_recommendations.py - ML Recommendations

**Key Classes:**
- `MLRecommender` - ML-based suggestions
- `ABTesting` - A/B test framework
- `FeedbackLoop` - Learn from feedback

**Usage:**

```python
from backend.enhanced_recommendations import MLRecommender, ABTesting, FeedbackLoop

# Train model
recommender = MLRecommender()
recommender.train_recommendation_model(products_df)

# Get price optimization
price_recs = recommender.get_price_optimization(products_df)
# Returns: {
#   'recommendations': [
#     {
#       'product_id': 1,
#       'type': 'PRICE_INCREASE',
#       'suggested_price': 110,
#       'confidence': 0.75,
#       ...
#     }
#   ]
# }

# Get cross-sell recommendations
cross_sells = recommender.get_cross_sell_recommendations(
    product_id=1,
    df=products_df
)

# Get bundle recommendations
bundles = recommender.get_bundle_recommendations(products_df)

# A/B Testing
ab_test = ABTesting()

ab_test.create_test(
    test_name="pricing_strategy_2024",
    variant_a={'name': 'Original Price', 'price': 100},
    variant_b={'name': 'Discounted 10%', 'price': 90},
    product_ids=[1, 2, 3]
)

# Record interactions
ab_test.record_interaction('pricing_strategy_2024', 'A', 'view')
ab_test.record_interaction('pricing_strategy_2024', 'A', 'conversion')

# Get results
results = ab_test.get_test_results('pricing_strategy_2024')
# Returns: {
#   'variant_a': {'conversion_rate': 5.2, ...},
#   'variant_b': {'conversion_rate': 7.1, ...},
#   'winner': 'B',
#   'improvement_pct': 36.5
# }

# Feedback loop
feedback = FeedbackLoop()

feedback.record_feedback(
    recommendation_id='rec_123',
    product_id=1,
    action='applied',
    result='positive'
)

effectiveness = feedback.get_recommendation_effectiveness()
# Returns: {
#   'total_recommendations': 100,
#   'applied_percentage': 45,
#   'positive_rate': 82,
#   'effectiveness_score': 36.9
# }
```

---

## Integration Checklist

### Phase 1: Core Setup (5 min)
- [ ] Copy all 8 .py files to `backend/` folder
- [ ] Add imports to `app.py`
- [ ] Initialize session state variables

### Phase 2: Form Validation (15 min)
- [ ] Add DataValidator to "Add Product" form
- [ ] Add price change validation
- [ ] Add discount validation
- [ ] Display error messages

### Phase 3: Alerts Dashboard (20 min)
- [ ] Add AlertManager to main page
- [ ] Display alert metrics (counts by severity)
- [ ] Show alert list with filters
- [ ] Add resolve/dismiss functionality

### Phase 4: Reports & Export (10 min)
- [ ] Add Excel export button
- [ ] Add CSV export option
- [ ] Create performance report UI
- [ ] Add schedule creation form

### Phase 5: Visualizations (20 min)
- [ ] Replace existing charts with enhanced versions
- [ ] Add new chart types
- [ ] Add interactivity (drill-down)
- [ ] Add date range filters

### Phase 6: Scenarios & Analysis (25 min)
- [ ] Create scenario builder UI
- [ ] Add "What-if" analysis page
- [ ] Show comparison table
- [ ] Display ROI calculations
- [ ] Add sensitivity analysis

### Phase 7: Forecasting & Recommendations (20 min)
- [ ] Train ML model on startup
- [ ] Display price optimization recommendations
- [ ] Show forecast charts with confidence intervals
- [ ] Create A/B testing dashboard
- [ ] Display recommendation effectiveness

**Total Integration Time: ~2 hours** (for full integration)

---

## Environment Setup

### Python Dependencies
```bash
pip install openpyxl  # For Excel export
pip install scikit-learn  # For ML models
```

### Email Notifications (Optional)
Set environment variables:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password  # Use app-specific password for Gmail
```

---

## Quick Integration Script

```python
# Add this to app.py imports section:

from backend.validators import DataValidator
from backend.performance import Cache, Paginator, QueryOptimizer
from backend.alerts import AlertManager, EmailNotifier
from backend.advanced_forecast import AdvancedForecaster
from backend.reporting import ReportGenerator, ScheduledReportConfig
from backend.visualization import VisualizationFactory
from backend.scenario_analysis import Scenario, ScenarioAnalyzer, ScenarioManager
from backend.enhanced_recommendations import MLRecommender, ABTesting, FeedbackLoop

# Initialize in your Streamlit app:
if 'initialized' not in st.session_state:
    st.session_state.cache = Cache()
    st.session_state.alert_manager = AlertManager()
    st.session_state.recommender = MLRecommender()
    st.session_state.ab_testing = ABTesting()
    st.session_state.feedback_loop = FeedbackLoop()
    st.session_state.initialized = True
```

---

## Support & Troubleshooting

**Module Import Errors:**
```python
# Check if module is accessible
import sys
sys.path.append('/path/to/workspace')
from backend.validators import DataValidator
```

**Performance Issues:**
- Use Cache with appropriate TTL
- Use Paginator for large datasets
- Use QueryOptimizer for filtering

**Email Not Sending:**
- Verify SMTP credentials
- Check sender_password (use app-specific password for Gmail)
- Verify recipient email addresses

**Forecasting Accuracy:**
- Ensure you have at least 24 historical data points
- Use ensemble method for better accuracy
- Retrain model periodically with new data

---

## Next Steps

1. **Start with validation** - Add to your forms first
2. **Add alerts** - Display on dashboard
3. **Enable exports** - Let users download reports
4. **Enhance visualizations** - Replace existing charts
5. **Add scenarios** - Create what-if analysis page
6. **Deploy forecasting** - Add forecast comparison UI
7. **Enable recommendations** - Show pricing/cross-sell suggestions

All modules are production-ready and tested. Happy integrating! 🚀
