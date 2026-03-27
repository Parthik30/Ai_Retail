"""
Enhanced Data Visualization Module - Interactive charts, drill-down, date range selection
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class VisualizationFactory:
    """Factory for creating enhanced interactive visualizations"""
    
    @staticmethod
    def create_inventory_status_pie(df: pd.DataFrame) -> go.Figure:
        """Create pie chart for inventory status"""
        if df is None or df.empty:
            return go.Figure()
        
        try:
            # Categorize inventory
            status_counts = {
                'Optimal (20-100)': len(df[(df['stock'] >= 20) & (df['stock'] <= 100)]),
                'High (>100)': len(df[df['stock'] > 100]),
                'Low (<20)': len(df[df['stock'] < 20])
            }
            
            fig = go.Figure(data=[go.Pie(
                labels=list(status_counts.keys()),
                values=list(status_counts.values()),
                marker=dict(colors=['#22C55E', '#FFA500', '#FF6B6B']),
                hovertemplate='<b>%{label}</b><br>Count: %{value}<extra></extra>'
            )])
            
            fig.update_layout(
                title='Inventory Status Distribution',
                height=400,
                showlegend=True,
                hovermode='closest'
            )
            
            return fig
        except Exception as e:
            print(f"Error creating pie chart: {e}")
            return go.Figure()
    
    @staticmethod
    def create_revenue_forecast_line(
        dates: List[datetime],
        actual_revenue: List[float],
        forecast_revenue: List[float],
        confidence_upper: List[float],
        confidence_lower: List[float]
    ) -> go.Figure:
        """Create revenue forecast line chart with confidence intervals"""
        try:
            # Prepare data
            forecast_dates = dates[-len(forecast_revenue):] if forecast_revenue else []
            
            fig = go.Figure()
            
            # Actual revenue
            fig.add_trace(go.Scatter(
                x=dates[:len(actual_revenue)],
                y=actual_revenue,
                name='Actual Revenue',
                mode='lines+markers',
                line=dict(color='#22C55E', width=2),
                marker=dict(size=6)
            ))
            
            # Forecast
            if forecast_revenue:
                fig.add_trace(go.Scatter(
                    x=forecast_dates,
                    y=forecast_revenue,
                    name='Forecast',
                    mode='lines+markers',
                    line=dict(color='#3B82F6', width=2, dash='dash'),
                    marker=dict(size=6)
                ))
                
                # Confidence interval
                fig.add_trace(go.Scatter(
                    x=forecast_dates + forecast_dates[::-1],
                    y=confidence_upper + confidence_lower[::-1],
                    fill='toself',
                    fillcolor='rgba(59, 130, 246, 0.2)',
                    line=dict(color='rgba(59, 130, 246, 0)'),
                    hoverinfo='skip',
                    name='95% Confidence Interval',
                    showlegend=True
                ))
            
            fig.update_layout(
                title='Revenue Forecast with Confidence Intervals',
                xaxis_title='Date',
                yaxis_title='Revenue (₹)',
                hovermode='x unified',
                height=500,
                template='plotly_white',
                legend=dict(x=0, y=1, bgcolor='rgba(255,255,255,0.8)')
            )
            
            return fig
        except Exception as e:
            print(f"Error creating forecast chart: {e}")
            return go.Figure()
    
    @staticmethod
    def create_stock_turnover_heatmap(df: pd.DataFrame, period_days: int = 30) -> go.Figure:
        """Create heatmap of stock turnover by category"""
        if df is None or df.empty:
            return go.Figure()
        
        try:
            # Calculate turnover ratio: monthly_sales / avg_stock
            df_copy = df.copy()
            df_copy['turnover_ratio'] = (df_copy['monthly_sales'] / (df_copy['stock'] + 1)).round(2)
            df_copy['stock_value'] = (df_copy['stock'] * df_copy['cost_price']).round(0)
            
            # Create pivot table
            pivot = pd.pivot_table(
                df_copy,
                values='turnover_ratio',
                index='category',
                aggfunc='mean'
            ).sort_values(ascending=False)
            
            fig = go.Figure(data=go.Heatmap(
                z=pivot.values.flatten(),
                y=pivot.index,
                colorscale='RdYlGn',
                text=pivot.values.round(2),
                texttemplate='%{text:.2f}',
                hovertemplate='Category: %{y}<br>Turnover Ratio: %{z:.2f}<extra></extra>'
            ))
            
            fig.update_layout(
                title='Stock Turnover Ratio by Category',
                yaxis_title='Category',
                xaxis_title='Turnover Ratio',
                height=400,
                coloraxis_colorbar=dict(title='Ratio')
            )
            
            return fig
        except Exception as e:
            print(f"Error creating heatmap: {e}")
            return go.Figure()
    
    @staticmethod
    def create_margin_distribution_box(df: pd.DataFrame) -> go.Figure:
        """Create box plot of profit margins by category"""
        if df is None or df.empty:
            return go.Figure()
        
        try:
            df_copy = df.copy()
            df_copy['margin_pct'] = ((df_copy['selling_price'] - df_copy['cost_price']) / df_copy['cost_price'] * 100).round(1)
            
            fig = go.Figure()
            
            categories = df_copy['category'].unique()
            for category in sorted(categories):
                category_data = df_copy[df_copy['category'] == category]['margin_pct']
                fig.add_trace(go.Box(
                    y=category_data,
                    name=category,
                    boxmean='sd'
                ))
            
            fig.update_layout(
                title='Profit Margin Distribution by Category',
                yaxis_title='Margin (%)',
                xaxis_title='Category',
                height=500,
                hovermode='closest'
            )
            
            return fig
        except Exception as e:
            print(f"Error creating box plot: {e}")
            return go.Figure()
    
    @staticmethod
    def create_stock_velocity_scatter(df: pd.DataFrame) -> go.Figure:
        """Create scatter plot of stock levels vs sales velocity"""
        if df is None or df.empty:
            return go.Figure()
        
        try:
            df_copy = df.copy()
            df_copy['velocity'] = df_copy['monthly_sales'] / (df_copy['stock'] + 1)
            
            fig = px.scatter(
                df_copy,
                x='stock',
                y='monthly_sales',
                size='selling_price',
                color='category',
                hover_name='product_name',
                hover_data={'stock': ':.0f', 'monthly_sales': ':.0f', 'selling_price': '₹.2f'},
                title='Stock vs Sales Velocity',
                labels={'stock': 'Current Stock', 'monthly_sales': 'Monthly Sales'},
                height=500
            )
            
            fig.update_traces(marker=dict(line=dict(width=0.5, color='DarkSlateGrey')))
            
            return fig
        except Exception as e:
            print(f"Error creating scatter plot: {e}")
            return go.Figure()
    
    @staticmethod
    def create_cumulative_revenue_area(
        df: pd.DataFrame,
        top_n: int = 10
    ) -> go.Figure:
        """Create area chart showing cumulative revenue contribution"""
        if df is None or df.empty:
            return go.Figure()
        
        try:
            df_copy = df.copy()
            df_copy['revenue'] = df_copy['selling_price'] * df_copy['monthly_sales']
            
            top_products = df_copy.nlargest(top_n, 'revenue').sort_values('revenue', ascending=False)
            cumulative = top_products['revenue'].cumsum()
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=top_products['product_name'],
                y=cumulative,
                fill='tozeroy',
                name='Cumulative Revenue',
                line=dict(color='#06B6D4', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title=f'Top {top_n} Products - Cumulative Revenue Contribution',
                xaxis_title='Product',
                yaxis_title='Cumulative Revenue (₹)',
                height=400,
                hovermode='x unified'
            )
            
            fig.update_xaxes(tickangle=45)
            
            return fig
        except Exception as e:
            print(f"Error creating area chart: {e}")
            return go.Figure()
    
    @staticmethod
    def create_price_range_histogram(df: pd.DataFrame) -> go.Figure:
        """Create histogram of product price ranges"""
        if df is None or df.empty:
            return go.Figure()
        
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=df['selling_price'],
                nbinsx=15,
                name='Price Distribution',
                marker_color='#3B82F6',
                hovertemplate='Price Range: ₹%{x}<br>Count: %{y}<extra></extra>'
            ))
            
            fig.update_layout(
                title='Product Price Distribution',
                xaxis_title='Selling Price (₹)',
                yaxis_title='Number of Products',
                height=400,
                hovermode='x unified'
            )
            
            return fig
        except Exception as e:
            print(f"Error creating histogram: {e}")
            return go.Figure()
    
    @staticmethod
    def create_comparison_bars(
        categories: List[str],
        values1: List[float],
        values2: List[float],
        label1: str,
        label2: str,
        title: str
    ) -> go.Figure:
        """Create grouped bar chart for comparison"""
        try:
            fig = go.Figure(data=[
                go.Bar(name=label1, x=categories, y=values1, marker_color='#22C55E'),
                go.Bar(name=label2, x=categories, y=values2, marker_color='#3B82F6')
            ])
            
            fig.update_layout(
                title=title,
                barmode='group',
                height=400,
                hovermode='x unified',
                xaxis_tickangle=-45
            )
            
            return fig
        except Exception as e:
            print(f"Error creating comparison chart: {e}")
            return go.Figure()
    
    @staticmethod
    def create_funnel_chart(stages: List[str], values: List[int]) -> go.Figure:
        """Create funnel chart for sales pipeline"""
        try:
            fig = go.Figure(go.Funnel(
                y=stages,
                x=values,
                textposition='inside',
                textinfo='value+percent initial',
                marker=dict(color=['#22C55E', '#3B82F6', '#06B6D4', '#FFA500', '#FF6B6B']),
                hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
            ))
            
            fig.update_layout(
                title='Sales Funnel Analysis',
                height=400
            )
            
            return fig
        except Exception as e:
            print(f"Error creating funnel chart: {e}")
            return go.Figure()
