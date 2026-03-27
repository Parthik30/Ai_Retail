"""
Advanced Forecasting Module - Multiple models with confidence intervals and ensemble
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import json
import os
from datetime import datetime, timedelta

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FORECASTS_DIR = os.path.join(BACKEND_DIR, "data", "forecasts")
os.makedirs(FORECASTS_DIR, exist_ok=True)


class AdvancedForecaster:
    """Advanced forecasting with multiple models and ensemble methods"""
    
    @staticmethod
    def decompose_seasonal(series: np.ndarray, period: int = 12) -> Dict:
        """
        Simple seasonal decomposition
        Returns trend and seasonal components
        """
        if len(series) < 2 * period:
            return {'trend': series, 'seasonal': np.zeros(len(series))}
        
        try:
            # Calculate moving average for trend
            trend = np.convolve(series, np.ones(period)/period, mode='same')
            
            # Calculate seasonal component
            seasonal = np.zeros(len(series))
            for i in range(period):
                indices = np.arange(i, len(series), period)
                if len(indices) > 0:
                    seasonal[indices] = np.mean(series[indices] - trend[indices])
            
            return {
                'trend': trend,
                'seasonal': seasonal,
                'residual': series - trend - seasonal
            }
        except Exception:
            return {'trend': series, 'seasonal': np.zeros(len(series))}
    
    @staticmethod
    def exponential_smoothing_forecast(
        series: np.ndarray,
        periods: int = 12,
        alpha: float = 0.3,
        beta: float = 0.1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Exponential smoothing with trend
        Returns forecast and confidence interval
        """
        try:
            # Initialize
            level = series[0]
            trend = (series[1] - series[0]) if len(series) > 1 else 0
            
            forecast = np.zeros(periods)
            
            for t in range(periods):
                forecast[t] = level + trend
                
                # Update level and trend for next period
                if t + 1 < len(series):
                    level = alpha * series[t + 1] + (1 - alpha) * (level + trend)
                    trend = beta * (level - series[t]) + (1 - beta) * trend
            
            # Confidence intervals (95%)
            residuals = series - np.concatenate([series[:-1], [forecast[0]]])
            std_error = np.std(residuals)
            ci = 1.96 * std_error  # 95% confidence
            
            upper_ci = forecast + ci
            lower_ci = forecast - ci
            
            return forecast, np.column_stack([lower_ci, forecast, upper_ci])
        
        except Exception:
            return np.zeros(periods), np.zeros((periods, 3))
    
    @staticmethod
    def arima_simple_forecast(series: np.ndarray, periods: int = 12) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simplified ARIMA-like forecasting using differencing
        """
        try:
            # First differencing
            if len(series) < 2:
                return np.full(periods, series[-1]), np.zeros((periods, 3))
            
            diff = np.diff(series)
            
            # Use last differences as pattern
            avg_diff = np.mean(diff[-6:]) if len(diff) >= 6 else np.mean(diff)
            
            forecast = np.zeros(periods)
            last_value = series[-1]
            
            for t in range(periods):
                last_value = last_value + avg_diff
                forecast[t] = last_value
            
            # Add noise for confidence interval
            std_error = np.std(diff)
            ci = 1.96 * std_error
            
            upper_ci = forecast + ci
            lower_ci = forecast - ci
            
            return forecast, np.column_stack([lower_ci, forecast, upper_ci])
        
        except Exception:
            return np.zeros(periods), np.zeros((periods, 3))
    
    @staticmethod
    def machine_learning_forecast(series: np.ndarray, periods: int = 12) -> Tuple[np.ndarray, np.ndarray]:
        """
        ML-based forecast using random forest regression
        """
        try:
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.preprocessing import StandardScaler
            
            if len(series) < 10:
                return np.full(periods, np.mean(series)), np.zeros((periods, 3))
            
            # Create lag features
            X, y = [], []
            lag = 3
            
            for i in range(lag, len(series)):
                X.append(series[i-lag:i])
                y.append(series[i])
            
            if len(y) < 5:
                return np.full(periods, np.mean(series)), np.zeros((periods, 3))
            
            X = np.array(X)
            y = np.array(y)
            
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # Forecast
            forecast = np.zeros(periods)
            last_features = series[-lag:]
            
            for t in range(periods):
                pred = model.predict([last_features])[0]
                forecast[t] = max(0, pred)  # No negative forecasts
                last_features = np.append(last_features[1:], pred)
            
            # Confidence interval from residuals
            residuals = y - model.predict(X)
            std_error = np.std(residuals)
            ci = 1.96 * std_error
            
            upper_ci = forecast + ci
            lower_ci = forecast - ci
            
            return forecast, np.column_stack([lower_ci, forecast, upper_ci])
        
        except Exception:
            return np.full(periods, np.mean(series)), np.zeros((periods, 3))
    
    @staticmethod
    def ensemble_forecast(series: np.ndarray, periods: int = 12) -> Dict:
        """
        Ensemble forecast combining multiple models with weighted average
        """
        try:
            # Get forecasts from different models
            es_forecast, es_ci = AdvancedForecaster.exponential_smoothing_forecast(series, periods)
            ar_forecast, ar_ci = AdvancedForecaster.arima_simple_forecast(series, periods)
            ml_forecast, ml_ci = AdvancedForecaster.machine_learning_forecast(series, periods)
            
            # Weighted ensemble (ML gets more weight)
            weights = {'es': 0.2, 'ar': 0.2, 'ml': 0.6}
            
            ensemble_forecast = (
                weights['es'] * es_forecast +
                weights['ar'] * ar_forecast +
                weights['ml'] * ml_forecast
            )
            
            # Ensemble confidence intervals
            ensemble_upper = (
                weights['es'] * es_ci[:, 0] +
                weights['ar'] * ar_ci[:, 0] +
                weights['ml'] * ml_ci[:, 0]
            )
            ensemble_lower = (
                weights['es'] * es_ci[:, 2] +
                weights['ar'] * ar_ci[:, 2] +
                weights['ml'] * ml_ci[:, 2]
            )
            
            return {
                'forecast': ensemble_forecast,
                'models': {
                    'exponential_smoothing': {
                        'forecast': es_forecast,
                        'confidence_interval': es_ci,
                        'weight': weights['es']
                    },
                    'arima': {
                        'forecast': ar_forecast,
                        'confidence_interval': ar_ci,
                        'weight': weights['ar']
                    },
                    'random_forest': {
                        'forecast': ml_forecast,
                        'confidence_interval': ml_ci,
                        'weight': weights['ml']
                    }
                },
                'confidence_interval': {
                    'lower': ensemble_lower,
                    'forecast': ensemble_forecast,
                    'upper': ensemble_upper
                }
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def forecast_with_intervals(series: List[float], periods: int = 12) -> Dict:
        """
        Complete forecast with confidence intervals and model performance
        """
        series_array = np.array(series)
        
        # Decompose
        decomposition = AdvancedForecaster.decompose_seasonal(series_array)
        
        # Ensemble forecast
        ensemble = AdvancedForecaster.ensemble_forecast(series_array, periods)
        
        if 'error' in ensemble:
            return {'error': ensemble['error']}
        
        return {
            'forecast': {
                'values': ensemble['forecast'].tolist(),
                'lower_ci': ensemble['confidence_interval']['lower'].tolist(),
                'upper_ci': ensemble['confidence_interval']['upper'].tolist()
            },
            'decomposition': {
                'trend': decomposition['trend'].tolist(),
                'seasonal': decomposition['seasonal'].tolist()
            },
            'models': {k: {
                'forecast': v['forecast'].tolist(),
                'weight': v['weight']
            } for k, v in ensemble['models'].items()},
            'metrics': {
                'forecast_length': periods,
                'history_length': len(series),
                'generated_at': datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def save_forecast(product_name: str, forecast_data: Dict) -> bool:
        """Save forecast to file for later analysis"""
        try:
            filename = os.path.join(
                FORECASTS_DIR,
                f"{product_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(filename, 'w') as f:
                json.dump(forecast_data, f, indent=2)
            return True
        except Exception:
            return False
