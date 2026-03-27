"""
Performance Optimization Module - Caching, pagination, and query optimization
"""
import hashlib
import time
from typing import Any, Dict, List, Optional
import pandas as pd
from functools import wraps
import pickle
import os

class Cache:
    """Simple in-memory cache with TTL (Time To Live)"""
    
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
        self.ttl = {}  # Time to live in seconds
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set cache value with TTL"""
        self.cache[key] = value
        self.timestamps[key] = time.time()
        self.ttl[key] = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value if not expired"""
        if key not in self.cache:
            return None
        
        age = time.time() - self.timestamps[key]
        if age > self.ttl.get(key, 3600):
            # Expired
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        return self.cache[key]
    
    def invalidate(self, key: str):
        """Remove cache entry"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.timestamps.clear()
    
    def get_hash_key(self, *args, **kwargs) -> str:
        """Generate hash key for caching"""
        key_str = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_str.encode()).hexdigest()


# Global cache instance
_cache = Cache()


def cached(ttl: int = 3600):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _cache.get_hash_key(func.__name__, *args, **kwargs)
            result = _cache.get(cache_key)
            
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl=ttl)
            return result
        
        return wrapper
    return decorator


class Paginator:
    """Pagination helper for large datasets"""
    
    @staticmethod
    def paginate(data: List[Dict], page: int = 1, per_page: int = 20) -> Dict:
        """Paginate a list of items"""
        if page < 1:
            page = 1
        
        total_items = len(data)
        total_pages = (total_items + per_page - 1) // per_page
        
        # Validate page number
        if page > total_pages and total_pages > 0:
            page = total_pages
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        items = data[start_idx:end_idx]
        
        return {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    
    @staticmethod
    def paginate_dataframe(df: pd.DataFrame, page: int = 1, per_page: int = 20) -> Dict:
        """Paginate a DataFrame"""
        if df is None or df.empty:
            return {
                'data': df,
                'page': 1,
                'per_page': per_page,
                'total_items': 0,
                'total_pages': 0,
                'has_next': False,
                'has_prev': False
            }
        
        total_items = len(df)
        total_pages = (total_items + per_page - 1) // per_page
        
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        return {
            'data': df.iloc[start_idx:end_idx],
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }


class QueryOptimizer:
    """Database query optimization helpers"""
    
    @staticmethod
    def optimize_product_filters(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
        """Apply multiple filters efficiently"""
        result = df.copy()
        
        # Category filter
        if 'category' in filters and filters['category'] != 'All':
            result = result[result['category'] == filters['category']]
        
        # Stock status filter
        if 'stock_status' in filters:
            status = filters['stock_status']
            if status == 'low':
                result = result[result['stock'] < 20]
            elif status == 'medium':
                result = result[(result['stock'] >= 20) & (result['stock'] <= 100)]
            elif status == 'high':
                result = result[result['stock'] > 100]
        
        # Demand level filter
        if 'demand_level' in filters and filters['demand_level'] != 'All':
            result = result[result['demand_level'] == filters['demand_level']]
        
        # Price range filter
        if 'min_price' in filters and 'max_price' in filters:
            min_price = float(filters['min_price'])
            max_price = float(filters['max_price'])
            result = result[(result['selling_price'] >= min_price) & (result['selling_price'] <= max_price)]
        
        # Rating filter
        if 'min_rating' in filters:
            min_rating = float(filters['min_rating'])
            result = result[result['rating'] >= min_rating]
        
        # Search filter
        if 'search' in filters and filters['search']:
            search_term = str(filters['search']).lower()
            result = result[
                result['product_name'].str.lower().str.contains(search_term, na=False) |
                result['product_id'].str.lower().str.contains(search_term, na=False)
            ]
        
        return result
    
    @staticmethod
    def get_top_products(df: pd.DataFrame, metric: str = 'monthly_sales', top_n: int = 10) -> pd.DataFrame:
        """Get top products by specified metric"""
        if df is None or df.empty:
            return df
        
        valid_metrics = ['monthly_sales', 'revenue', 'stock', 'rating']
        if metric == 'revenue' and 'selling_price' in df.columns:
            df_copy = df.copy()
            df_copy['revenue'] = df_copy['selling_price'] * df_copy['monthly_sales']
            return df_copy.nlargest(top_n, 'revenue')
        elif metric in valid_metrics:
            return df.nlargest(top_n, metric)
        
        return df.head(top_n)
    
    @staticmethod
    def get_low_stock_products(df: pd.DataFrame, threshold: int = 20) -> pd.DataFrame:
        """Efficiently get low stock products"""
        if df is None or df.empty:
            return df
        
        return df[df['stock'] < threshold].sort_values('stock')


def clear_cache():
    """Clear all cached data"""
    _cache.clear()


def invalidate_product_cache():
    """Invalidate product-related cache entries"""
    for key in list(_cache.cache.keys()):
        if 'product' in key.lower():
            _cache.invalidate(key)
