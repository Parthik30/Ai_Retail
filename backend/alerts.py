"""
Alerts and Notifications System - Real-time alerts for inventory and pricing
"""
import os
import csv
import datetime
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ALERTS_DIR = os.path.join(BACKEND_DIR, "data", "alerts")
ALERTS_FILE = os.path.join(ALERTS_DIR, "alerts.csv")
ALERT_LOG = os.path.join(ALERTS_DIR, "alert_log.json")

# Ensure alerts directory exists
os.makedirs(ALERTS_DIR, exist_ok=True)


class AlertManager:
    """Manage alerts and notifications"""
    
    ALERT_TYPES = {
        'LOW_STOCK': 'Low Stock Alert',
        'STOCKOUT': 'Stockout Alert',
        'PRICE_CHANGE': 'Price Change Alert',
        'HIGH_DEMAND': 'High Demand Alert',
        'EXCESS_INVENTORY': 'Excess Inventory Alert',
        'REORDER_DUE': 'Reorder Due Alert',
        'QUALITY_ISSUE': 'Quality Issue Alert'
    }
    
    SEVERITY_LEVELS = {
        'LOW': 1,
        'MEDIUM': 2,
        'HIGH': 3,
        'CRITICAL': 4
    }
    
    @staticmethod
    def _ensure_alert_file():
        """Ensure alert file exists"""
        if not os.path.exists(ALERTS_FILE):
            with open(ALERTS_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'id', 'timestamp', 'product', 'alert_type', 'severity',
                    'message', 'threshold_value', 'actual_value', 'status',
                    'assigned_to', 'resolved_at'
                ])
    
    @staticmethod
    def create_alert(
        product: str,
        alert_type: str,
        severity: str,
        message: str,
        threshold_value: float = None,
        actual_value: float = None,
        assigned_to: str = 'admin'
    ) -> bool:
        """Create a new alert"""
        try:
            AlertManager._ensure_alert_file()
            
            alert_id = int(datetime.datetime.now().timestamp() * 1000)
            timestamp = datetime.datetime.now().isoformat()
            
            with open(ALERTS_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    alert_id, timestamp, product, alert_type, severity,
                    message, threshold_value or '', actual_value or '',
                    'OPEN', assigned_to, ''
                ])
            
            # Log alert
            AlertManager._log_alert({
                'id': alert_id,
                'product': product,
                'type': alert_type,
                'severity': severity,
                'created_at': timestamp
            })
            
            return True
        except Exception as e:
            print(f"Error creating alert: {e}")
            return False
    
    @staticmethod
    def check_low_stock(df, threshold: int = 20) -> List[Dict]:
        """Check for low stock alerts"""
        alerts = []
        if df is None or df.empty:
            return alerts
        
        low_stock = df[df['stock'] < threshold]
        
        for _, row in low_stock.iterrows():
            if int(row['stock']) < threshold:
                product = row['product_name']
                stock = int(row['stock'])
                monthly_sales = float(row.get('monthly_sales', 0))
                
                # Calculate days of stock remaining
                if monthly_sales > 0:
                    days_remaining = (stock / monthly_sales) * 30
                    severity = 'CRITICAL' if days_remaining < 7 else 'HIGH'
                else:
                    severity = 'MEDIUM'
                
                message = f"Stock level ({stock}) is below threshold ({threshold})"
                
                alerts.append({
                    'product': product,
                    'type': 'LOW_STOCK',
                    'severity': severity,
                    'message': message,
                    'threshold': threshold,
                    'actual': stock
                })
        
        return alerts
    
    @staticmethod
    def check_stockout_risk(df, risk_data: Dict) -> List[Dict]:
        """Check for stockout risk"""
        alerts = []
        if df is None or df.empty:
            return alerts
        
        for product, risk_info in risk_data.items():
            if risk_info.get('risk_score', 0) >= 70:  # Critical risk
                message = f"Product has high stockout risk (score: {risk_info['risk_score']})"
                alerts.append({
                    'product': product,
                    'type': 'STOCKOUT',
                    'severity': 'CRITICAL',
                    'message': message,
                    'threshold': 70,
                    'actual': risk_info['risk_score']
                })
        
        return alerts
    
    @staticmethod
    def check_price_anomalies(old_price: float, new_price: float, product: str) -> Optional[Dict]:
        """Check for unusual price changes"""
        if old_price == 0:
            return None
        
        change_pct = abs((new_price - old_price) / old_price) * 100
        
        if change_pct > 50:  # More than 50% change
            return {
                'product': product,
                'type': 'PRICE_CHANGE',
                'severity': 'HIGH',
                'message': f"Unusual price change detected ({change_pct:.1f}%)",
                'threshold': 50,
                'actual': change_pct
            }
        
        return None
    
    @staticmethod
    def check_high_demand(df) -> List[Dict]:
        """Check for unusually high demand"""
        alerts = []
        if df is None or df.empty:
            return alerts
        
        # Get products with sales > 75th percentile
        q75 = df['monthly_sales'].quantile(0.75)
        high_demand = df[df['monthly_sales'] > q75]
        
        for _, row in high_demand.iterrows():
            if row['monthly_sales'] > q75:
                stock = int(row['stock'])
                monthly_sales = float(row['monthly_sales'])
                
                # If stock ratio is low
                if stock < monthly_sales * 0.5:
                    alerts.append({
                        'product': row['product_name'],
                        'type': 'HIGH_DEMAND',
                        'severity': 'MEDIUM',
                        'message': f"High demand with low stock ratio",
                        'threshold': q75,
                        'actual': monthly_sales
                    })
        
        return alerts
    
    @staticmethod
    def resolve_alert(alert_id: int) -> bool:
        """Mark alert as resolved"""
        try:
            alerts = []
            with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['id'] == str(alert_id):
                        row['status'] = 'RESOLVED'
                        row['resolved_at'] = datetime.datetime.now().isoformat()
                    alerts.append(row)
            
            with open(ALERTS_FILE, 'w', newline='', encoding='utf-8') as f:
                if alerts:
                    writer = csv.DictWriter(f, fieldnames=alerts[0].keys())
                    writer.writeheader()
                    writer.writerows(alerts)
            
            return True
        except Exception as e:
            print(f"Error resolving alert: {e}")
            return False
    
    @staticmethod
    def get_open_alerts(limit: int = 50) -> List[Dict]:
        """Get all open alerts"""
        try:
            AlertManager._ensure_alert_file()
            alerts = []
            
            with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('status') == 'OPEN':
                        alerts.append(row)
            
            return alerts[-limit:]  # Return most recent
        except Exception:
            return []
    
    @staticmethod
    def _log_alert(alert_data: Dict):
        """Log alert to JSON log file"""
        try:
            logs = []
            if os.path.exists(ALERT_LOG):
                with open(ALERT_LOG, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            
            logs.append(alert_data)
            
            with open(ALERT_LOG, 'w', encoding='utf-8') as f:
                json.dump(logs[-1000:], f, indent=2)  # Keep last 1000 logs
        except Exception:
            pass


class EmailNotifier:
    """Send email notifications"""
    
    def __init__(self, smtp_server: str = 'smtp.gmail.com', smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = os.environ.get('ALERT_EMAIL_SENDER')
        self.sender_password = os.environ.get('ALERT_EMAIL_PASSWORD')
    
    def send_alert_email(
        self,
        recipient: str,
        subject: str,
        alert_type: str,
        product: str,
        message: str,
        severity: str
    ) -> bool:
        """Send alert email"""
        try:
            if not self.sender_email or not self.sender_password:
                print("Email credentials not configured")
                return False
            
            # Create HTML email
            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>IntelliStock Alert - {alert_type}</h2>
                    <hr/>
                    <p><strong>Severity:</strong> {severity}</p>
                    <p><strong>Product:</strong> {product}</p>
                    <p><strong>Message:</strong> {message}</p>
                    <hr/>
                    <p>Please log in to your IntelliStock dashboard to review and take action.</p>
                    <p style="color: #999; font-size: 12px;">
                        This is an automated alert from IntelliStock Inventory Management System
                    </p>
                </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{severity}] {subject}"
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def send_batch_alerts(self, recipient: str, alerts: List[Dict]) -> int:
        """Send multiple alerts in one email"""
        try:
            if not alerts:
                return 0
            
            # Group by severity
            alerts_by_severity = {}
            for alert in alerts:
                severity = alert.get('severity', 'MEDIUM')
                if severity not in alerts_by_severity:
                    alerts_by_severity[severity] = []
                alerts_by_severity[severity].append(alert)
            
            # Create HTML
            alert_html = ""
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                if severity in alerts_by_severity:
                    alert_html += f"<h3>{severity} Alerts ({len(alerts_by_severity[severity])})</h3>"
                    for alert in alerts_by_severity[severity]:
                        alert_html += f"""
                        <div style="border-left: 4px solid #ff6b6b; padding: 10px; margin: 10px 0;">
                            <p><strong>{alert.get('product')}</strong></p>
                            <p>{alert.get('message')}</p>
                            <p style="font-size: 12px; color: #666;">{alert.get('type')}</p>
                        </div>
                        """
            
            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>IntelliStock Daily Alert Summary</h2>
                    <p>Total Alerts: {len(alerts)}</p>
                    <hr/>
                    {alert_html}
                    <hr/>
                    <p style="color: #999; font-size: 12px;">
                        This is an automated alert from IntelliStock Inventory Management System
                    </p>
                </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"IntelliStock Daily Alert Summary - {len(alerts)} alert(s)"
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return len(alerts)
        
        except Exception as e:
            print(f"Error sending batch alerts: {e}")
            return 0
