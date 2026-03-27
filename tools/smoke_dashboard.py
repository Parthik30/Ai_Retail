import sys
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
from backend.services import dashboard_service as ds

print('classification head:')
print(ds.get_demand_pattern_classification().head(3))
print('\nget_dashboard_data for Laptop Dell i5:')
print(ds.get_dashboard_data('Laptop Dell i5'))
