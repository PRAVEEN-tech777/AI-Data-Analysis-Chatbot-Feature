"""
Demo Data Generator for Excel-based Database


Creates sample customer and order data with regions and quality metrics.
"""


import pandas as pd
import random
from datetime import datetime, timedelta


# Set seed for reproducibility
random.seed(42)


# Generate Customers
regions = ['North', 'South', 'East', 'West', 'Central']
customer_segments = ['Enterprise', 'SMB', 'Startup', 'Individual']


customers = []
for i in range(1, 101):
    customers.append({
        'customer_id': i,
        'customer_name': f'Customer_{i}',
        'region': random.choice(regions),
        'segment': random.choice(customer_segments),
        'signup_date': (datetime(2023, 1, 1) + timedelta(days=random.randint(0, 600))).strftime('%Y-%m-%d'),
        'credit_limit': random.choice([5000, 10000, 25000, 50000, 100000]),
        'status': random.choice(['Active', 'Active', 'Active', 'Inactive'])
    })


df_customers = pd.DataFrame(customers)


# Generate Orders
qualities = ['Premium', 'Standard', 'Basic']
statuses = ['Completed', 'Pending', 'Shipped', 'Cancelled']


orders = []
order_id = 1
for customer_id in range(1, 101):
    # Each customer has 1-15 orders
    num_orders = random.randint(1, 15)
    for _ in range(num_orders):
        order_date = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 700))
        orders.append({
            'order_id': order_id,
            'customer_id': customer_id,
            'order_date': order_date.strftime('%Y-%m-%d'),
            'product_category': random.choice(['Electronics', 'Clothing', 'Food', 'Books', 'Home']),
            'quantity': random.randint(1, 20),
            'unit_price': round(random.uniform(10, 500), 2),
            'total_amount': 0,  # Will calculate
            'quality_rating': random.choice(qualities),
            'status': random.choice(statuses),
            'delivery_days': random.randint(1, 30) if random.random() > 0.2 else None
        })
        orders[-1]['total_amount'] = round(orders[-1]['quantity'] * orders[-1]['unit_price'], 2)
        order_id += 1


df_orders = pd.DataFrame(orders)


# Save to Excel with multiple sheets
with pd.ExcelWriter('demo_database.xlsx', engine='openpyxl') as writer:
    df_customers.to_excel(writer, sheet_name='customers', index=False)
    df_orders.to_excel(writer, sheet_name='orders', index=False)


print(f"✅ Created demo database with:")
print(f"   - {len(df_customers)} customers")
print(f"   - {len(df_orders)} orders")
print(f"   - Saved to: demo_database.xlsx")


# Display sample data
print("\n📊 Sample Customers:")
print(df_customers.head())
print("\n📊 Sample Orders:")
print(df_orders.head())



