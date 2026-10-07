import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

OUT_DIR = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\data\samples"
os.makedirs(OUT_DIR, exist_ok=True)

def generate_ecommerce_dataset():
    start_date = datetime(2024, 1, 1)
    num_days = 180
    records = []
    
    regions = ["North", "South", "East", "West"]
    categories = {
        "Electronics": [
            ("Apex Gaming Laptop", 1200.0, 300.0),
            ("SoundPulse Wireless Headphone", 150.0, 50.0),
            ("UltraVision 4K Monitor", 400.0, 110.0),
            ("SmartSync Fitness Tracker", 90.0, 35.0)
        ],
        "Furniture": [
            ("ErgoPro Executive Desk", 450.0, 120.0),
            ("LumbarComfort Mesh Chair", 220.0, 65.0),
            ("Nordic Solid Oak Bookshelf", 310.0, 85.0)
        ],
        "Office Supplies": [
            ("HeavyDuty Metal Stapler", 25.0, 10.0),
            ("Premium Recycled Paper (Box)", 45.0, 14.0),
            ("Gel Ink Pen Multi-Pack", 18.0, 6.0)
        ]
    }
    customer_segments = ["Consumer", "Corporate", "Small Business"]
    carriers = ["ExpressLogistics", "SwiftFreight", "ApexGlobal", "StandardMail"]
    
    order_counter = 10001
    
    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        # Period 1 (Baseline): Days 0 to 89
        # Period 2 (Crisis Period): Days 90 to 140 (April 1 to May 20)
        is_crisis_period = (90 <= day_offset <= 140)
        
        for region in regions:
            # Daily orders per region
            daily_order_count = np.random.randint(5, 9)
            
            # During crisis, South region orders also decrease as word spreads of delays
            if is_crisis_period and region == "South":
                daily_order_count = max(2, int(daily_order_count * 0.75))
            
            for _ in range(daily_order_count):
                order_id = f"ORD-{order_counter}"
                order_counter += 1
                customer_id = f"CUST-{np.random.randint(1000, 1500)}"
                segment = random.choice(customer_segments)
                category = random.choice(list(categories.keys()))
                product_name, base_price, unit_cost = random.choice(categories[category])
                product_id = f"PRD-{abs(hash(product_name)) % 1000:03d}"
                
                quantity = np.random.randint(1, 4)
                discount = round(random.choice([0.0, 0.05, 0.10, 0.15]), 2)
                unit_sale_price = base_price * (1 - discount)
                carrier = random.choice(carriers)
                
                # Baseline
                delivery_delay_days = max(0, int(np.random.normal(1.5, 0.7)))
                customer_complaint = 1 if (np.random.random() < 0.03) else 0
                order_cancelled = 1 if (np.random.random() < 0.02) else 0
                
                # Crisis injection in South region
                if is_crisis_period and region == "South":
                    if category == "Electronics":
                        delivery_delay_days = max(4, int(np.random.normal(7.8, 1.8)))
                        customer_complaint = 1 if (np.random.random() < 0.52) else 0
                        order_cancelled = 1 if (np.random.random() < 0.46) else 0
                    else:
                        delivery_delay_days = max(2, int(np.random.normal(4.2, 1.2)))
                        customer_complaint = 1 if (np.random.random() < 0.22) else 0
                        order_cancelled = 1 if (np.random.random() < 0.18) else 0
                
                if order_cancelled == 1:
                    revenue = 0.0
                    profit = -round(unit_cost * 0.20 * quantity, 2)
                    delivery_status = "Cancelled"
                else:
                    revenue = round(unit_sale_price * quantity, 2)
                    profit = round((unit_sale_price - unit_cost) * quantity, 2)
                    delivery_status = "Delayed" if delivery_delay_days >= 5 else ("On-Time" if delivery_delay_days <= 2 else "Normal")
                
                records.append({
                    "order_id": order_id,
                    "order_date": current_date.strftime("%Y-%m-%d"),
                    "customer_id": customer_id,
                    "customer_segment": segment,
                    "region": region,
                    "product_id": product_id,
                    "product_category": category,
                    "product_name": product_name,
                    "quantity": quantity,
                    "unit_price": base_price,
                    "discount": discount,
                    "revenue": revenue,
                    "profit": profit,
                    "shipping_carrier": carrier,
                    "delivery_delay_days": delivery_delay_days,
                    "delivery_status": delivery_status,
                    "customer_complaint": customer_complaint,
                    "order_cancelled": order_cancelled
                })
                
    df = pd.DataFrame(records)
    
    # Missing values injection
    mask_carrier = np.random.random(len(df)) < 0.02
    df.loc[mask_carrier, "shipping_carrier"] = None
    mask_segment = np.random.random(len(df)) < 0.015
    df.loc[mask_segment, "customer_segment"] = None
    
    # Duplicate rows
    dup_indices = np.random.choice(len(df), size=10, replace=False)
    df = pd.concat([df, df.iloc[dup_indices].copy()], ignore_index=True)
    
    # 2 outlier quantities
    df.loc[np.random.choice(len(df), size=2), "quantity"] = 75
    
    file_path = os.path.join(OUT_DIR, "ecommerce_sales_with_hidden_root_cause.csv")
    df.to_csv(file_path, index=False)
    print(f"-> Updated E-commerce dataset: {len(df)} rows -> {file_path}")

generate_ecommerce_dataset()
