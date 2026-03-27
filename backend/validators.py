"""
Data Validation Module - Comprehensive validation for all inputs
"""
import re
from typing import Dict, Any, List, Tuple
import pandas as pd

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class DataValidator:
    """Centralized data validation class"""
    
    @staticmethod
    def validate_product(data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate product data before insert/update"""
        try:
            # Required fields
            required_fields = ['product_id', 'product_name', 'cost_price', 'selling_price']
            for field in required_fields:
                if field not in data or data[field] is None or str(data[field]).strip() == '':
                    return False, f"Missing required field: {field}"
            
            # Product ID validation
            product_id = str(data['product_id']).strip()
            if len(product_id) < 2 or len(product_id) > 50:
                return False, "Product ID must be between 2 and 50 characters"
            
            # Product name validation
            product_name = str(data['product_name']).strip()
            if len(product_name) < 3 or len(product_name) > 255:
                return False, "Product name must be between 3 and 255 characters"
            
            # Price validation
            try:
                cost_price = float(data['cost_price'])
                selling_price = float(data['selling_price'])
                if cost_price < 0:
                    return False, "Cost price cannot be negative"
                if selling_price < 0:
                    return False, "Selling price cannot be negative"
                if selling_price < cost_price:
                    return False, "Selling price must be >= cost price"
            except (ValueError, TypeError):
                return False, "Cost price and selling price must be valid numbers"
            
            # Stock validation
            if 'stock' in data:
                try:
                    stock = int(data['stock'])
                    if stock < 0:
                        return False, "Stock cannot be negative"
                except (ValueError, TypeError):
                    return False, "Stock must be a valid integer"
            
            # Discount validation
            if 'discount' in data and data['discount'] is not None:
                try:
                    discount = float(data['discount'])
                    if discount < 0 or discount > 100:
                        return False, "Discount must be between 0 and 100"
                except (ValueError, TypeError):
                    return False, "Discount must be a valid number between 0 and 100"
            
            # Rating validation
            if 'rating' in data and data['rating'] is not None:
                try:
                    rating = float(data['rating'])
                    if rating < 0 or rating > 5:
                        return False, "Rating must be between 0 and 5"
                except (ValueError, TypeError):
                    return False, "Rating must be a valid number between 0 and 5"
            
            # Monthly sales validation
            if 'monthly_sales' in data and data['monthly_sales'] is not None:
                try:
                    monthly_sales = int(data['monthly_sales'])
                    if monthly_sales < 0:
                        return False, "Monthly sales cannot be negative"
                except (ValueError, TypeError):
                    return False, "Monthly sales must be a valid integer"
            
            return True, "Validation passed"
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_discount_change(product_name: str, old_discount: float, new_discount: float) -> Tuple[bool, str]:
        """Validate discount change"""
        try:
            # Type validation
            try:
                old_discount = float(old_discount)
                new_discount = float(new_discount)
            except (ValueError, TypeError):
                return False, "Discount values must be numbers"
            
            # Range validation
            if new_discount < 0 or new_discount > 100:
                return False, "Discount must be between 0 and 100"
            
            # Excessive change warning
            change = abs(new_discount - old_discount)
            if change > 50:
                return False, f"Discount change of {change}% is too large. Please verify."
            
            return True, "Discount change validated"
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_price_change(product_name: str, old_price: float, new_price: float) -> Tuple[bool, str]:
        """Validate price change"""
        try:
            # Type validation
            try:
                old_price = float(old_price)
                new_price = float(new_price)
            except (ValueError, TypeError):
                return False, "Price values must be numbers"
            
            # Negative validation
            if new_price < 0:
                return False, "Price cannot be negative"
            
            # Excessive change warning
            if old_price > 0:
                change_pct = abs((new_price - old_price) / old_price) * 100
                if change_pct > 100:
                    return False, f"Price change of {change_pct:.1f}% is too large. Please verify."
            
            return True, "Price change validated"
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_reorder(product_name: str, quantity: int, eta_month: int = None) -> Tuple[bool, str]:
        """Validate reorder data"""
        try:
            # Quantity validation
            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                return False, "Quantity must be a valid integer"
            
            if quantity <= 0:
                return False, "Reorder quantity must be greater than 0"
            
            if quantity > 1000000:
                return False, "Reorder quantity is unreasonably large"
            
            # ETA month validation
            if eta_month is not None:
                try:
                    eta_month = int(eta_month)
                    if eta_month < 0 or eta_month > 24:
                        return False, "ETA month must be between 0 and 24"
                except (ValueError, TypeError):
                    return False, "ETA month must be a valid integer"
            
            return True, "Reorder data validated"
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, expected_columns: List[str]) -> Tuple[bool, str]:
        """Validate dataframe structure"""
        try:
            if df is None or df.empty:
                return False, "DataFrame is empty"
            
            missing_cols = [col for col in expected_columns if col not in df.columns]
            if missing_cols:
                return False, f"Missing columns: {', '.join(missing_cols)}"
            
            # Check for all NaN columns
            for col in df.columns:
                if df[col].isna().all():
                    return False, f"Column '{col}' is completely empty"
            
            return True, "DataFrame validated"
        
        except Exception as e:
            return False, f"DataFrame validation error: {str(e)}"
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            value = str(value)
        
        # Remove leading/trailing whitespace
        value = value.strip()
        
        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length]
        
        # Remove potentially harmful characters (basic protection)
        value = re.sub(r'[<>"\']', '', value)
        
        return value
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email):
            return True, "Email is valid"
        return False, "Invalid email format"
