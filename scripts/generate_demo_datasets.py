import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set seed for reproducible demo datasets
np.random.seed(42)
random.seed(42)

OUT_DIR = r"C:\Users\HP\.gemini\antigravity\scratch\InsightX\data\samples"
os.makedirs(OUT_DIR, exist_ok=True)

print(f"Generating realistic sample datasets in {OUT_DIR}...")

# --------------------------------------------------------------------------
# 1. E-COMMERCE WITH EMBEDDED ROOT CAUSE
# --------------------------------------------------------------------------
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
        # Hidden Root Cause Period: Days 90 to 140
        is_crisis_period = (90 <= day_offset <= 140)
        
        # Base daily orders ~15-25 orders per day
        daily_order_count = np.random.randint(18, 28)
        
        for _ in range(daily_order_count):
            order_id = f"ORD-{order_counter}"
            order_counter += 1
            customer_id = f"CUST-{np.random.randint(1000, 1500)}"
            segment = random.choice(customer_segments)
            region = random.choice(regions)
            category = random.choice(list(categories.keys()))
            product_name, base_price, unit_cost = random.choice(categories[category])
            product_id = f"PRD-{abs(hash(product_name)) % 1000:03d}"
            
            quantity = np.random.randint(1, 5)
            discount = round(random.choice([0.0, 0.05, 0.10, 0.15]), 2)
            unit_sale_price = base_price * (1 - discount)
            
            carrier = random.choice(carriers)
            
            # Normal baseline delivery delay: 1 to 3 days
            delivery_delay_days = max(0, int(np.random.normal(1.8, 0.8)))
            customer_complaint = 1 if (np.random.random() < 0.04) else 0
            order_cancelled = 1 if (np.random.random() < 0.03) else 0
            
            # --- INJECT HIDDEN ROOT CAUSE: South region logistics breakdown in Electronics ---
            if is_crisis_period and region == "South":
                if category == "Electronics":
                    # Severe carrier bottleneck
                    delivery_delay_days = int(np.random.normal(7.5, 2.2))
                    delivery_delay_days = max(4, delivery_delay_days)
                    # Complaints surge dramatically due to delay
                    customer_complaint = 1 if (np.random.random() < 0.45) else 0
                    # Cancellations surge
                    order_cancelled = 1 if (np.random.random() < 0.35) else 0
                else:
                    delivery_delay_days = int(np.random.normal(4.0, 1.5))
                    customer_complaint = 1 if (np.random.random() < 0.18) else 0
                    order_cancelled = 1 if (np.random.random() < 0.12) else 0
            
            if order_cancelled == 1:
                revenue = 0.0
                profit = -round(unit_cost * 0.15 * quantity, 2) # Restocking / return loss
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
    
    # Introduce real-world imperfections for data profiler & cleaner
    # 1. A few missing values in shipping_carrier and customer_segment
    mask_carrier = np.random.random(len(df)) < 0.02
    df.loc[mask_carrier, "shipping_carrier"] = None
    
    mask_segment = np.random.random(len(df)) < 0.015
    df.loc[mask_segment, "customer_segment"] = None
    
    # 2. Duplicate rows (simulate re-submission)
    dup_indices = np.random.choice(len(df), size=12, replace=False)
    duplicates = df.iloc[dup_indices].copy()
    df = pd.concat([df, duplicates], ignore_index=True)
    
    # 3. A couple of outlier order quantities to test IQR detection
    df.loc[np.random.choice(len(df), size=3), "quantity"] = 85
    
    file_path = os.path.join(OUT_DIR, "ecommerce_sales_with_hidden_root_cause.csv")
    df.to_csv(file_path, index=False)
    print(f"-> E-commerce dataset created: {len(df)} rows, 18 columns -> {file_path}")

# --------------------------------------------------------------------------
# 2. SAAS MARKETING FUNNEL DATASET
# --------------------------------------------------------------------------
def generate_saas_marketing_dataset():
    start_date = datetime(2024, 1, 1)
    num_days = 120
    channels = ["Google Search Ads", "LinkedIn B2B", "Meta Retargeting", "Organic SEO", "Partner Referral"]
    records = []
    
    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        # Simulated marketing push in month 2
        is_push = (30 <= day_offset <= 60)
        
        for ch in channels:
            if ch == "Google Search Ads":
                spend = round(np.random.uniform(800, 1500) * (1.5 if is_push else 1.0), 2)
                impressions = int(spend * np.random.uniform(18, 25))
                ctr = round(np.random.uniform(0.028, 0.045), 4)
            elif ch == "LinkedIn B2B":
                spend = round(np.random.uniform(1200, 2200) * (1.3 if is_push else 1.0), 2)
                impressions = int(spend * np.random.uniform(8, 14))
                ctr = round(np.random.uniform(0.015, 0.028), 4)
            elif ch == "Meta Retargeting":
                spend = round(np.random.uniform(400, 800), 2)
                impressions = int(spend * np.random.uniform(30, 45))
                ctr = round(np.random.uniform(0.022, 0.038), 4)
            elif ch == "Organic SEO":
                spend = 250.0 # Fixed content creation allocation
                impressions = int(np.random.uniform(12000, 20000))
                ctr = round(np.random.uniform(0.035, 0.055), 4)
            else: # Partner Referral
                spend = round(np.random.uniform(300, 600), 2)
                impressions = int(spend * np.random.uniform(10, 18))
                ctr = round(np.random.uniform(0.040, 0.070), 4)
            
            clicks = max(1, int(impressions * ctr))
            cpc = round(spend / clicks, 2)
            lead_conversion_rate = np.random.uniform(0.06, 0.14)
            leads = max(1, int(clicks * lead_conversion_rate))
            cpl = round(spend / leads, 2)
            
            sale_conversion_rate = np.random.uniform(0.10, 0.22)
            converted_customers = max(0, int(leads * sale_conversion_rate))
            
            avg_contract_value = np.random.choice([150.0, 300.0, 650.0, 1200.0])
            mrr_generated = round(converted_customers * avg_contract_value, 2)
            roi = round((mrr_generated - spend) / spend, 3) if spend > 0 else 1.0
            
            records.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "channel": ch,
                "ad_spend": spend,
                "impressions": impressions,
                "clicks": clicks,
                "ctr": ctr,
                "cost_per_click": cpc,
                "leads": leads,
                "cost_per_lead": cpl,
                "converted_customers": converted_customers,
                "mrr_generated": mrr_generated,
                "roi": roi
            })
            
    df = pd.DataFrame(records)
    file_path = os.path.join(OUT_DIR, "saas_marketing_funnel.csv")
    df.to_csv(file_path, index=False)
    print(f"-> SaaS Marketing dataset created: {len(df)} rows, 12 columns -> {file_path}")

# --------------------------------------------------------------------------
# 3. HEALTHCARE PATIENT FLOW DATASET
# --------------------------------------------------------------------------
def generate_healthcare_dataset():
    start_date = datetime(2024, 1, 1)
    num_days = 90
    departments = ["Emergency", "Cardiology", "Orthopedics", "Pediatrics", "General Surgery"]
    admission_types = ["Emergency", "Urgent", "Elective"]
    records = []
    
    adm_counter = 5001
    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        daily_patients = np.random.randint(20, 35)
        
        for _ in range(daily_patients):
            adm_id = f"ADM-{adm_counter}"
            adm_counter += 1
            patient_id = f"PAT-{np.random.randint(10000, 99999)}"
            age = int(np.random.normal(52, 18))
            age = max(1, min(95, age))
            gender = random.choice(["Male", "Female"])
            dept = random.choice(departments)
            adm_type = random.choice(admission_types)
            
            # Emergency triage wait time depends on department load
            if dept == "Emergency":
                wait_time_minutes = max(5, int(np.random.normal(65, 30)))
                los = max(1, int(np.random.exponential(2.5)))
                cost = round(wait_time_minutes * 15.0 + los * 1100.0 + np.random.uniform(500, 2000), 2)
            elif dept == "Cardiology":
                wait_time_minutes = max(15, int(np.random.normal(45, 15)))
                los = max(2, int(np.random.exponential(5.0)))
                cost = round(los * 2400.0 + np.random.uniform(4000, 12000), 2)
            else:
                wait_time_minutes = max(10, int(np.random.normal(30, 12)))
                los = max(1, int(np.random.exponential(3.0)))
                cost = round(los * 1400.0 + np.random.uniform(1500, 5000), 2)
                
            satisfaction = min(10, max(1, int(np.random.normal(8.0 - (wait_time_minutes / 40.0), 1.2))))
            readmission_30d = 1 if (np.random.random() < (0.20 if los > 6 else 0.08)) else 0
            
            records.append({
                "admission_id": adm_id,
                "admission_date": current_date.strftime("%Y-%m-%d"),
                "patient_id": patient_id,
                "age": age,
                "gender": gender,
                "department": dept,
                "admission_type": adm_type,
                "wait_time_minutes": wait_time_minutes,
                "length_of_stay_days": los,
                "treatment_cost": cost,
                "satisfaction_score": satisfaction,
                "readmission_30d": readmission_30d
            })
            
    df = pd.DataFrame(records)
    file_path = os.path.join(OUT_DIR, "healthcare_patient_flow.csv")
    df.to_csv(file_path, index=False)
    print(f"-> Healthcare Patient Flow dataset created: {len(df)} rows, 12 columns -> {file_path}")

if __name__ == "__main__":
    generate_ecommerce_dataset()
    generate_saas_marketing_dataset()
    generate_healthcare_dataset()
    print("All demo datasets generated successfully!")
