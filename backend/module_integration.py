"""
Module Integration Summary and Health Check Tool
"""
import os
import sys
from datetime import datetime
from typing import Dict, List

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# Simple ANSI color support for terminal output. Falls back to plain text
# on environments without ANSI support (older Windows shells).
COLORS = {
    'reset': '\033[0m',
    'bold': '\033[1m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
}

def _supports_color() -> bool:
    # Basic detection: modern Windows terminals set WT_SESSION or terminal programs
    if os.name == 'nt':
        return bool(os.environ.get('WT_SESSION') or os.environ.get('ANSICON') or os.environ.get('TERM'))
    return True


def color_text(text: str, color_name: str) -> str:
    if not _supports_color():
        return text
    prefix = COLORS.get(color_name, '')
    reset = COLORS['reset']
    return f"{prefix}{text}{reset}"

class ModuleHealthCheck:
    """Check health and integration status of new modules"""
    
    REQUIRED_MODULES = {
        'validators.py': 'Data Validation Framework',
        'performance.py': 'Performance Optimization & Caching',
        'alerts.py': 'Real-time Alerts System',
        'advanced_forecast.py': 'Advanced Forecasting',
        'reporting.py': 'Excel Reports & Scheduling',
        'visualization.py': 'Enhanced Data Visualization',
        'scenario_analysis.py': 'Scenario Analysis & What-if',
        'enhanced_recommendations.py': 'ML-Based Recommendations'
    }
    
    @staticmethod
    def check_module_existence() -> Dict:
        """Check if all required modules exist"""
        status = {}
        
        for module_name, description in ModuleHealthCheck.REQUIRED_MODULES.items():
            filepath = os.path.join(BACKEND_DIR, module_name)
            exists = os.path.exists(filepath)
            status[module_name] = {
                'description': description,
                'exists': exists,
                'path': filepath,
                'size_kb': os.path.getsize(filepath) / 1024 if exists else 0
            }
        
        return status
    
    @staticmethod
    def check_imports_in_app() -> Dict:
        """Check if modules are imported in app.py"""
        app_path = os.path.join(os.path.dirname(BACKEND_DIR), 'backend', 'streamlit_app', 'app.py')
        
        imports = {}
        try:
            with open(app_path, 'r') as f:
                content = f.read()
                
            for module_name in ModuleHealthCheck.REQUIRED_MODULES.keys():
                module_basename = module_name.replace('.py', '')
                import_statement = f"from backend.{module_basename}"
                is_imported = import_statement in content
                imports[module_name] = {
                    'imported': is_imported,
                    'import_statement': import_statement
                }
        except Exception as e:
            imports['error'] = str(e)
        
        return imports
    
    @staticmethod
    def generate_health_report() -> str:
        """Generate comprehensive health report"""
        report = []
        report.append(color_text("=" * 70, 'cyan'))
        report.append(color_text("INTELLISTOCK DASHBOARD - NEW MODULES HEALTH CHECK", 'bold'))
        report.append(color_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 'blue'))
        report.append(color_text("=" * 70, 'cyan'))
        
        # Module Existence Check
        report.append("\n" + color_text("📦 MODULE EXISTENCE CHECK:", 'magenta'))
        report.append("-" * 70)
        
        module_status = ModuleHealthCheck.check_module_existence()
        all_exist = True
        
        for module_name, status in module_status.items():
            if status['exists']:
                symbol = color_text("✅", 'green')
                size = color_text(f"({status['size_kb']:.1f} KB)", 'blue')
                name = color_text(module_name, 'bold')
                desc = status['description']
            else:
                symbol = color_text("❌", 'red')
                size = ""
                name = color_text(module_name, 'red')
                desc = color_text(status['description'], 'yellow')

            report.append(f"{symbol} {name:<30} - {desc:<35} {size}")
            all_exist = all_exist and status['exists']
        
        # Import Check
        report.append("\n" + color_text("📥 INTEGRATION CHECK (app.py imports):", 'magenta'))
        report.append("-" * 70)
        
        imports = ModuleHealthCheck.check_imports_in_app()
        if 'error' not in imports:
            for module_name, import_status in imports.items():
                if import_status['imported']:
                    symbol = color_text("✅", 'green')
                    name = color_text(module_name, 'bold')
                else:
                    symbol = color_text("⚠️", 'yellow')
                    name = color_text(module_name, 'yellow')

                report.append(f"{symbol} {name:<30} - {import_status['import_statement']}")
        else:
            report.append(f"⚠️  Error reading app.py: {imports['error']}")
        
        # Summary
        report.append("\n" + color_text("=" * 70, 'cyan'))
        report.append(color_text("📊 SUMMARY:", 'bold'))
        report.append(color_text("=" * 70, 'cyan'))
        
        total_modules = len(ModuleHealthCheck.REQUIRED_MODULES)
        existing_modules = sum(1 for s in module_status.values() if s['exists'])
        integrated_modules = sum(1 for imp in imports.values() if isinstance(imp, dict) and imp.get('imported', False))
        
        report.append(color_text(f"Total New Modules:      {total_modules}", 'blue'))
        report.append(color_text(f"Modules Created:        {existing_modules}/{total_modules}", 'green' if existing_modules==total_modules else 'yellow'))
        report.append(color_text(f"Modules Integrated:     {integrated_modules}/{total_modules}", 'green' if integrated_modules==total_modules else 'yellow'))
        report.append(color_text(f"Creation Progress:      {(existing_modules/total_modules*100):.0f}%", 'magenta'))
        report.append(color_text(f"Integration Progress:   {(integrated_modules/total_modules*100):.0f}%", 'magenta'))
        
        # Next Steps
        report.append("\n" + color_text("=" * 70, 'cyan'))
        report.append(color_text("🎯 NEXT STEPS:", 'bold'))
        report.append(color_text("=" * 70, 'cyan'))
        
        if existing_modules < total_modules:
            report.append(f"1. Create remaining {total_modules - existing_modules} modules")
        
        if integrated_modules < existing_modules:
            report.append(f"2. Integrate {existing_modules - integrated_modules} modules into app.py")
            report.append("   - Add imports at top of file")
            report.append("   - Add UI components to relevant pages")
            report.append("   - Wire up callbacks and state management")
        
        report.append("3. Test each module integration")
        report.append("4. Add error handling and logging")
        report.append("5. Create user documentation")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    @staticmethod
    def print_module_api_summary() -> str:
        """Print summary of available APIs in each module"""
        summary = []
        summary.append("\n" + "=" * 70)
        summary.append("📚 MODULE API SUMMARY")
        summary.append("=" * 70)
        
        apis = {
            'validators.py': [
                'DataValidator.validate_product()',
                'DataValidator.validate_discount_change()',
                'DataValidator.validate_price_change()',
                'DataValidator.validate_reorder()',
                'DataValidator.validate_dataframe()',
                'DataValidator.sanitize_string()',
                'DataValidator.validate_email()'
            ],
            'performance.py': [
                'Cache.set() / get() / clear()',
                '@cached decorator for function caching',
                'Paginator.paginate() / paginate_dataframe()',
                'QueryOptimizer.optimize_product_filters()',
                'QueryOptimizer.get_top_products()',
                'QueryOptimizer.get_low_stock_products()'
            ],
            'alerts.py': [
                'AlertManager.create_alert()',
                'AlertManager.check_low_stock()',
                'AlertManager.check_stockout_risk()',
                'AlertManager.check_price_anomalies()',
                'AlertManager.check_high_demand()',
                'AlertManager.resolve_alert()',
                'AlertManager.get_open_alerts()',
                'EmailNotifier.send_alert_email()',
                'EmailNotifier.send_batch_alerts()'
            ],
            'advanced_forecast.py': [
                'AdvancedForecaster.decompose_seasonal()',
                'AdvancedForecaster.exponential_smoothing_forecast()',
                'AdvancedForecaster.arima_simple_forecast()',
                'AdvancedForecaster.machine_learning_forecast()',
                'AdvancedForecaster.ensemble_forecast()',
                'AdvancedForecaster.forecast_with_intervals()',
                'AdvancedForecaster.save_forecast()'
            ],
            'reporting.py': [
                'ReportGenerator.generate_inventory_report()',
                'ReportGenerator.export_to_csv()',
                'ReportGenerator.generate_performance_report()',
                'ReportGenerator.save_report()',
                'ReportGenerator.get_recent_reports()',
                'ScheduledReportConfig.create_schedule()',
                'ScheduledReportConfig.get_schedules()'
            ],
            'visualization.py': [
                'VisualizationFactory.create_inventory_status_pie()',
                'VisualizationFactory.create_revenue_forecast_line()',
                'VisualizationFactory.create_stock_turnover_heatmap()',
                'VisualizationFactory.create_margin_distribution_box()',
                'VisualizationFactory.create_stock_velocity_scatter()',
                'VisualizationFactory.create_cumulative_revenue_area()',
                'VisualizationFactory.create_price_range_histogram()',
                'VisualizationFactory.create_comparison_bars()',
                'VisualizationFactory.create_funnel_chart()'
            ],
            'scenario_analysis.py': [
                'Scenario.apply_price_change()',
                'Scenario.apply_discount()',
                'Scenario.apply_stock_change()',
                'Scenario.apply_cost_change()',
                'ScenarioAnalyzer.calculate_scenario_impact()',
                'ScenarioAnalyzer.create_comparison_summary()',
                'ScenarioAnalyzer.roi_calculation()',
                'ScenarioAnalyzer.sensitivity_analysis()',
                'ScenarioManager.save_scenario()',
                'ScenarioManager.load_scenario()',
                'ScenarioManager.list_scenarios()',
                'ScenarioManager.delete_scenario()'
            ],
            'enhanced_recommendations.py': [
                'MLRecommender.train_recommendation_model()',
                'MLRecommender.get_price_optimization()',
                'MLRecommender.get_cross_sell_recommendations()',
                'MLRecommender.get_bundle_recommendations()',
                'ABTesting.create_test()',
                'ABTesting.record_interaction()',
                'ABTesting.get_test_results()',
                'FeedbackLoop.record_feedback()',
                'FeedbackLoop.get_recommendation_effectiveness()'
            ]
        }
        
        for module, methods in apis.items():
            summary.append(f"\n{module}:")
            summary.append("-" * 70)
            for method in methods:
                summary.append(f"  • {method}")
        
        summary.append("\n" + "=" * 70)
        return "\n".join(summary)
    
    @staticmethod
    def print_integration_guide() -> str:
        """Print guide for integrating modules into app.py"""
        guide = []
        guide.append("\n" + "=" * 70)
        guide.append("🔗 INTEGRATION GUIDE - How to wire modules into app.py")
        guide.append("=" * 70)
        
        guide.append("\n1. ADD IMPORTS (at top of app.py):")
        guide.append("-" * 70)
        guide.append("""
from backend.validators import DataValidator
from backend.performance import Cache, Paginator, QueryOptimizer
from backend.alerts import AlertManager, EmailNotifier
from backend.advanced_forecast import AdvancedForecaster
from backend.reporting import ReportGenerator, ScheduledReportConfig
from backend.visualization import VisualizationFactory
from backend.scenario_analysis import Scenario, ScenarioAnalyzer, ScenarioManager
from backend.enhanced_recommendations import MLRecommender, ABTesting, FeedbackLoop
""")
        
        guide.append("\n2. INITIALIZE SINGLETONS (in main app flow):")
        guide.append("-" * 70)
        guide.append("""
# In Streamlit app initialization
if 'cache' not in st.session_state:
    st.session_state.cache = Cache()
if 'recommender' not in st.session_state:
    st.session_state.recommender = MLRecommender()
if 'alert_manager' not in st.session_state:
    st.session_state.alert_manager = AlertManager()
""")
        
        guide.append("\n3. USE IN FORMS (Example: Product Validation):")
        guide.append("-" * 70)
        guide.append("""
product_id = st.number_input("Product ID")
product_name = st.text_input("Product Name")
selling_price = st.number_input("Selling Price")

# Validate on submit
if st.button("Add Product"):
    is_valid, message = DataValidator.validate_product(
        product_id, product_name, selling_price
    )
    if is_valid:
        # Add product to database
        st.success("Product added successfully!")
    else:
        st.error(f"Validation error: {message}")
""")
        
        guide.append("\n4. USE IN DASHBOARDS (Example: Display Alerts):")
        guide.append("-" * 70)
        guide.append("""
with st.container():
    col1, col2, col3 = st.columns(3)
    alerts = st.session_state.alert_manager.get_open_alerts()
    
    with col1:
        st.metric("Critical Alerts", len([a for a in alerts if a['severity'] == 4]))
    with col2:
        st.metric("High Priority", len([a for a in alerts if a['severity'] == 3]))
    with col3:
        st.metric("Total Alerts", len(alerts))
    
    if alerts:
        st.dataframe(pd.DataFrame(alerts))
""")
        
        guide.append("\n5. USE IN REPORTING (Example: Export):")
        guide.append("-" * 70)
        guide.append("""
if st.button("Export Inventory Report"):
    report_bytes = ReportGenerator.generate_inventory_report(products_df)
    st.download_button(
        label="Download Excel Report",
        data=report_bytes,
        file_name="inventory_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
""")
        
        guide.append("\n" + "=" * 70)
        return "\n".join(guide)


if __name__ == "__main__":
    print(ModuleHealthCheck.generate_health_report())
    print(ModuleHealthCheck.print_module_api_summary())
    print(ModuleHealthCheck.print_integration_guide())
