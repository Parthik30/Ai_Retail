"""
Scenario Analysis Module - What-if analysis, save/compare scenarios, budget planning
"""
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple


BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
SCENARIOS_DIR = os.path.join(BACKEND_DIR, "data", "scenarios")
os.makedirs(SCENARIOS_DIR, exist_ok=True)


class Scenario:
    """Represents a business scenario with alternative parameters"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.modifications: Dict = {}
        self.results: Dict = {}
        self.id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def apply_price_change(self, product_id: int, new_price: float):
        """Apply price change to scenario"""
        if 'price_changes' not in self.modifications:
            self.modifications['price_changes'] = {}
        self.modifications['price_changes'][product_id] = new_price
    
    def apply_discount(self, product_id: int, discount_pct: float):
        """Apply discount to scenario"""
        if 'discounts' not in self.modifications:
            self.modifications['discounts'] = {}
        self.modifications['discounts'][product_id] = discount_pct
    
    def apply_stock_change(self, product_id: int, new_stock: int):
        """Apply stock level change to scenario"""
        if 'stock_changes' not in self.modifications:
            self.modifications['stock_changes'] = {}
        self.modifications['stock_changes'][product_id] = new_stock
    
    def apply_cost_change(self, product_id: int, new_cost: float):
        """Apply cost change to scenario"""
        if 'cost_changes' not in self.modifications:
            self.modifications['cost_changes'] = {}
        self.modifications['cost_changes'][product_id] = new_cost
    
    def to_dict(self) -> Dict:
        """Convert scenario to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'modifications': self.modifications,
            'results': self.results
        }


class ScenarioAnalyzer:
    """Analyze and compare scenarios"""
    
    @staticmethod
    def calculate_scenario_impact(
        base_df: pd.DataFrame,
        scenario: Scenario
    ) -> Tuple[pd.DataFrame, Dict]:
        """Calculate impact of scenario on dataframe"""
        try:
            df = base_df.copy()
            impact = {
                'revenue_change': 0,
                'profit_change': 0,
                'stock_value_change': 0,
                'margin_change': 0
            }
            
            # Apply price changes
            if 'price_changes' in scenario.modifications:
                for prod_id, new_price in scenario.modifications['price_changes'].items():
                    mask = df['product_id'] == prod_id
                    old_revenue = (df.loc[mask, 'selling_price'] * df.loc[mask, 'monthly_sales']).sum()
                    df.loc[mask, 'selling_price'] = new_price
                    new_revenue = (new_price * df.loc[mask, 'monthly_sales']).sum()
                    impact['revenue_change'] += new_revenue - old_revenue
            
            # Apply discounts
            if 'discounts' in scenario.modifications:
                for prod_id, discount_pct in scenario.modifications['discounts'].items():
                    mask = df['product_id'] == prod_id
                    old_revenue = (df.loc[mask, 'selling_price'] * df.loc[mask, 'monthly_sales']).sum()
                    discounted_price = df.loc[mask, 'selling_price'] * (1 - discount_pct / 100)
                    df.loc[mask, 'selling_price'] = discounted_price
                    new_revenue = (discounted_price * df.loc[mask, 'monthly_sales']).sum()
                    impact['revenue_change'] += new_revenue - old_revenue
            
            # Apply stock changes
            if 'stock_changes' in scenario.modifications:
                for prod_id, new_stock in scenario.modifications['stock_changes'].items():
                    mask = df['product_id'] == prod_id
                    old_stock_value = (df.loc[mask, 'stock'] * df.loc[mask, 'cost_price']).sum()
                    df.loc[mask, 'stock'] = new_stock
                    new_stock_value = (new_stock * df.loc[mask, 'cost_price']).sum()
                    impact['stock_value_change'] += new_stock_value - old_stock_value
            
            # Apply cost changes
            if 'cost_changes' in scenario.modifications:
                for prod_id, new_cost in scenario.modifications['cost_changes'].items():
                    mask = df['product_id'] == prod_id
                    old_cost = (df.loc[mask, 'cost_price']).sum()
                    df.loc[mask, 'cost_price'] = new_cost
                    new_cost = (new_cost).sum()
                    impact['profit_change'] += old_cost - new_cost  # Negative cost = positive profit
            
            # Calculate profit impact
            df['profit'] = (df['selling_price'] - df['cost_price']) * df['monthly_sales']
            total_profit = df['profit'].sum()
            impact['profit_change'] = total_profit
            
            # Calculate margin
            df['margin_pct'] = ((df['selling_price'] - df['cost_price']) / df['selling_price'] * 100)
            impact['margin_change'] = df['margin_pct'].mean()
            
            return df, impact
        except Exception as e:
            print(f"Error calculating scenario impact: {e}")
            return base_df, {}
    
    @staticmethod
    def create_comparison_summary(
        base_df: pd.DataFrame,
        scenarios: List[Scenario]
    ) -> pd.DataFrame:
        """Create comparison summary of multiple scenarios"""
        try:
            comparison = []
            
            # Base metrics
            base_revenue = (base_df['selling_price'] * base_df['monthly_sales']).sum()
            base_profit = ((base_df['selling_price'] - base_df['cost_price']) * base_df['monthly_sales']).sum()
            base_margin = ((base_df['selling_price'] - base_df['cost_price']) / base_df['selling_price'] * 100).mean()
            base_stock_value = (base_df['stock'] * base_df['cost_price']).sum()
            
            comparison.append({
                'Scenario': 'Base Case',
                'Total Revenue': base_revenue,
                'Total Profit': base_profit,
                'Avg Margin %': base_margin,
                'Stock Value': base_stock_value,
                'Revenue Change %': 0,
                'Profit Change %': 0
            })
            
            # Scenario metrics
            for scenario in scenarios:
                scenario_df, impact = ScenarioAnalyzer.calculate_scenario_impact(base_df, scenario)
                
                scenario_revenue = (scenario_df['selling_price'] * scenario_df['monthly_sales']).sum()
                scenario_profit = ((scenario_df['selling_price'] - scenario_df['cost_price']) * scenario_df['monthly_sales']).sum()
                scenario_margin = ((scenario_df['selling_price'] - scenario_df['cost_price']) / scenario_df['selling_price'] * 100).mean()
                scenario_stock_value = (scenario_df['stock'] * scenario_df['cost_price']).sum()
                
                revenue_change_pct = ((scenario_revenue - base_revenue) / base_revenue * 100) if base_revenue != 0 else 0
                profit_change_pct = ((scenario_profit - base_profit) / base_profit * 100) if base_profit != 0 else 0
                
                comparison.append({
                    'Scenario': scenario.name,
                    'Total Revenue': scenario_revenue,
                    'Total Profit': scenario_profit,
                    'Avg Margin %': scenario_margin,
                    'Stock Value': scenario_stock_value,
                    'Revenue Change %': revenue_change_pct,
                    'Profit Change %': profit_change_pct
                })
            
            return pd.DataFrame(comparison)
        except Exception as e:
            print(f"Error creating comparison: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def roi_calculation(
        investment: float,
        revenue_increase: float,
        cost_increase: float,
        time_period_months: int = 12
    ) -> Dict:
        """Calculate ROI for a scenario"""
        try:
            net_benefit = (revenue_increase - cost_increase) * time_period_months
            roi_pct = (net_benefit / investment * 100) if investment != 0 else 0
            payback_months = (investment / (revenue_increase - cost_increase)) if (revenue_increase - cost_increase) != 0 else float('inf')
            
            return {
                'investment': investment,
                'net_benefit_12m': net_benefit,
                'roi_percent': roi_pct,
                'payback_months': payback_months,
                'break_even': payback_months <= time_period_months
            }
        except Exception as e:
            print(f"Error calculating ROI: {e}")
            return {}
    
    @staticmethod
    def sensitivity_analysis(
        base_df: pd.DataFrame,
        variable: str,  # 'price', 'cost', 'demand'
        min_change: float = -20,
        max_change: float = 20,
        steps: int = 5
    ) -> pd.DataFrame:
        """Perform sensitivity analysis on a variable"""
        try:
            results = []
            step_size = (max_change - min_change) / steps
            
            for i in range(steps + 1):
                change_pct = min_change + (i * step_size)
                scenario = Scenario(f"Sensitivity: {variable} {change_pct:+.1f}%", "")
                
                # Apply changes based on variable
                if variable == 'price':
                    for prod_id in base_df['product_id'].unique():
                        old_price = base_df[base_df['product_id'] == prod_id]['selling_price'].iloc[0]
                        new_price = old_price * (1 + change_pct / 100)
                        scenario.apply_price_change(prod_id, new_price)
                
                elif variable == 'cost':
                    for prod_id in base_df['product_id'].unique():
                        old_cost = base_df[base_df['product_id'] == prod_id]['cost_price'].iloc[0]
                        new_cost = old_cost * (1 + change_pct / 100)
                        scenario.apply_cost_change(prod_id, new_cost)
                
                elif variable == 'demand':
                    for prod_id in base_df['product_id'].unique():
                        # Demand affects revenue
                        pass
                
                scenario_df, impact = ScenarioAnalyzer.calculate_scenario_impact(base_df, scenario)
                revenue = (scenario_df['selling_price'] * scenario_df['monthly_sales']).sum()
                profit = ((scenario_df['selling_price'] - scenario_df['cost_price']) * scenario_df['monthly_sales']).sum()
                
                results.append({
                    'Change %': change_pct,
                    'Revenue': revenue,
                    'Profit': profit,
                    'Margin %': ((scenario_df['selling_price'] - scenario_df['cost_price']) / scenario_df['selling_price'] * 100).mean()
                })
            
            return pd.DataFrame(results)
        except Exception as e:
            print(f"Error in sensitivity analysis: {e}")
            return pd.DataFrame()


class ScenarioManager:
    """Manage scenario persistence"""
    
    @staticmethod
    def save_scenario(scenario: Scenario) -> bool:
        """Save scenario to file"""
        try:
            filepath = os.path.join(SCENARIOS_DIR, f"{scenario.id}.json")
            with open(filepath, 'w') as f:
                json.dump(scenario.to_dict(), f, indent=2)
            return True
        except Exception:
            return False
    
    @staticmethod
    def load_scenario(scenario_id: str) -> Optional[Scenario]:
        """Load scenario from file"""
        try:
            filepath = os.path.join(SCENARIOS_DIR, f"{scenario_id}.json")
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            scenario = Scenario(data['name'], data['description'])
            scenario.id = data['id']
            scenario.created_at = datetime.fromisoformat(data['created_at'])
            scenario.modifications = data['modifications']
            scenario.results = data['results']
            
            return scenario
        except Exception:
            return None
    
    @staticmethod
    def list_scenarios() -> List[Dict]:
        """List all saved scenarios"""
        try:
            scenarios = []
            for f in os.listdir(SCENARIOS_DIR):
                if f.endswith('.json'):
                    filepath = os.path.join(SCENARIOS_DIR, f)
                    with open(filepath, 'r') as file:
                        data = json.load(file)
                        scenarios.append({
                            'id': data['id'],
                            'name': data['name'],
                            'description': data['description'],
                            'created_at': data['created_at']
                        })
            
            scenarios.sort(key=lambda x: x['created_at'], reverse=True)
            return scenarios
        except Exception:
            return []
    
    @staticmethod
    def delete_scenario(scenario_id: str) -> bool:
        """Delete scenario from file"""
        try:
            filepath = os.path.join(SCENARIOS_DIR, f"{scenario_id}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception:
            return False
