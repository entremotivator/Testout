import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional
import time
import base64
from io import BytesIO
import os
import sqlite3
import uuid
import plotly.express as px
import plotly.graph_objects as go

# Configure the page
st.set_page_config(
    page_title="Vapi Outbound Calling Pro Enhanced",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
def init_database():
    """Initialize SQLite database for storing call data."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    # Create calls table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            type TEXT,
            assistant_name TEXT,
            assistant_id TEXT,
            customer_phone TEXT,
            customer_name TEXT,
            customer_email TEXT,
            call_id TEXT,
            status TEXT,
            notes TEXT,
            transcript TEXT,
            recording_url TEXT,
            recording_path TEXT,
            duration INTEGER,
            cost REAL,
            created_at TEXT
        )
    ''')
    
    # Create customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            company TEXT,
            position TEXT,
            lead_score INTEGER,
            status TEXT,
            last_contact TEXT,
            notes TEXT,
            total_value REAL,
            tags TEXT,
            created_at TEXT,
            updated_at TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            country TEXT,
            website TEXT,
            industry TEXT,
            company_size TEXT,
            annual_revenue REAL,
            source TEXT,
            assigned_to TEXT
        )
    ''')
    
    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            customer_id TEXT,
            order_date TEXT,
            amount REAL,
            status TEXT,
            product TEXT,
            quantity INTEGER,
            discount REAL,
            tax REAL,
            shipping REAL,
            total REAL,
            notes TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # Create customer interactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_interactions (
            id TEXT PRIMARY KEY,
            customer_id TEXT,
            interaction_type TEXT,
            interaction_date TEXT,
            notes TEXT,
            outcome TEXT,
            next_action TEXT,
            created_by TEXT,
            created_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_database()

# Static configuration
STATIC_PHONE_NUMBER_ID = "431f1dc9-4888-41e6-933c-4fa2e97d34d6"

# Predefined assistants
ASSISTANTS = {
    "Agent CEO": "bf161516-6d88-490c-972e-274098a6b51a",
    "Agent Social": "bf161516-6d88-490c-972e-274098a6b51a",
    "Agent Mindset": "4fe7083e-2f28-4502-b6bf-4ae6ea71a8f4",
    "Agent Blogger": "f8ef1ad5-5281-42f1-ae69-f94ff7acb453",
    "Agent Grant": "7673e69d-170b-4319-bdf4-e74e5370e98a",
    "Agent Prayer Ai": "339cdad6-9989-4bb6-98ed-bd15521707d1",
    "Agent Metrics": "4820eab2-adaf-4f17-a8a0-30cab3e3f007",
    "Agent Researcher": "f05c182f-d3d1-4a17-9c79-52442a9171b8",
    "Agent Investor": "1008771d-86ca-472a-a125-7a7e10100297",
    "Agent Newsroom": "76f1d6e5-cab4-45b8-9aeb-d3e6f3c0c019",
    "STREAMLIT agent": "538258da-0dda-473d-8ef8-5427251f3ad5",
    "Html/ Css Agent": "14b94e2f-299b-4e75-a445-a4f5feacc522",
    "Businesses Plan": "87d59105-723b-427e-a18d-da99fbf28608",
    "Ecom Agent": "d56551f8-0447-468a-872b-eaa9f830993d",
    "Agent Health": "7b2b8b86-5caa-4f28-8c6b-e7d3d0404f06",
    "Cinch Closer": "232f3d9c-18b3-4963-bdd9-e7de3be156ae",
    "DISC Agent": "41fe59e1-829f-4936-8ee5-eef2bb1287fe",
    "Biz Plan Agent": "87d59105-723b-427e-a18d-da99fbf28608",
    "Invoice Agent": "88862739-c227-4bfc-b90a-5f450a823e23",
    "Agent Clone": "88862739-c227-4bfc-b90a-5f450a823e23",
    "Agent Doctor": "9d1cccc6-3193-4694-a9f7-853198ee4082",
    "Agent Multi Lig": "8f045bce-08bc-4477-8d3d-05f233a44df3",
    "Agent Real Estate": "d982667e-d931-477c-9708-c183ba0aa964",
    "Businesses Launcher": "dffb2e5c-7d59-462b-a8aa-48746ea70cb1"
}

# Order status options
ORDER_STATUSES = [
    "Pending", "Processing", "Shipped", "Delivered", "Completed", "Cancelled", "Refunded", "On Hold"
]

# Customer status options
CUSTOMER_STATUSES = [
    "Hot Lead", "Warm Lead", "Cold Lead", "Customer", "Inactive", "Churned"
]

# Demo customers data (25 customers)
DEMO_CUSTOMERS = [
    {
        "id": "cust_001", "name": "John Smith", "email": "john.smith@email.com", "phone": "+1234567890",
        "company": "Tech Solutions Inc", "position": "CEO", "lead_score": 85, "status": "Hot Lead",
        "last_contact": "2024-01-15", "notes": "Interested in enterprise solution",
        "orders": [
            {"id": "ORD-001", "date": "2024-01-10", "amount": 5000, "status": "Completed", "product": "Enterprise Package"},
            {"id": "ORD-002", "date": "2024-01-20", "amount": 2500, "status": "Processing", "product": "Add-on Services"}
        ],
        "total_value": 7500, "tags": ["Enterprise", "High Value", "Decision Maker"]
    },
    {
        "id": "cust_002", "name": "Sarah Johnson", "email": "sarah.j@businesscorp.com", "phone": "+1234567891",
        "company": "Business Corp", "position": "Marketing Director", "lead_score": 72, "status": "Warm Lead",
        "last_contact": "2024-01-12", "notes": "Needs marketing automation tools",
        "orders": [
            {"id": "ORD-003", "date": "2024-01-05", "amount": 1200, "status": "Completed", "product": "Marketing Suite"}
        ],
        "total_value": 1200, "tags": ["Marketing", "Mid-Market", "Repeat Customer"]
    },
    {
        "id": "cust_003", "name": "Michael Brown", "email": "m.brown@startup.io", "phone": "+1234567892",
        "company": "Startup Innovations", "position": "Founder", "lead_score": 90, "status": "Hot Lead",
        "last_contact": "2024-01-18", "notes": "Fast-growing startup, budget approved",
        "orders": [], "total_value": 0, "tags": ["Startup", "High Potential", "New Customer"]
    },
    {
        "id": "cust_004", "name": "Emily Davis", "email": "emily.davis@retailplus.com", "phone": "+1234567893",
        "company": "Retail Plus", "position": "Operations Manager", "lead_score": 65, "status": "Cold Lead",
        "last_contact": "2024-01-08", "notes": "Interested but budget constraints",
        "orders": [
            {"id": "ORD-004", "date": "2023-12-15", "amount": 800, "status": "Completed", "product": "Basic Package"}
        ],
        "total_value": 800, "tags": ["Retail", "Budget Conscious", "Small Business"]
    },
    {
        "id": "cust_005", "name": "David Wilson", "email": "d.wilson@manufacturing.com", "phone": "+1234567894",
        "company": "Wilson Manufacturing", "position": "Plant Manager", "lead_score": 78, "status": "Warm Lead",
        "last_contact": "2024-01-14", "notes": "Looking for automation solutions",
        "orders": [
            {"id": "ORD-005", "date": "2024-01-12", "amount": 3500, "status": "Shipped", "product": "Automation Tools"}
        ],
        "total_value": 3500, "tags": ["Manufacturing", "Automation", "Industrial"]
    },
    {
        "id": "cust_006", "name": "Lisa Anderson", "email": "lisa.a@healthcareplus.org", "phone": "+1234567895",
        "company": "Healthcare Plus", "position": "IT Director", "lead_score": 82, "status": "Hot Lead",
        "last_contact": "2024-01-16", "notes": "HIPAA compliance requirements",
        "orders": [
            {"id": "ORD-006", "date": "2024-01-08", "amount": 4200, "status": "Processing", "product": "Healthcare Suite"}
        ],
        "total_value": 4200, "tags": ["Healthcare", "Compliance", "Security"]
    },
    {
        "id": "cust_007", "name": "Robert Taylor", "email": "r.taylor@financefirm.com", "phone": "+1234567896",
        "company": "Taylor Finance", "position": "CFO", "lead_score": 88, "status": "Hot Lead",
        "last_contact": "2024-01-17", "notes": "Needs financial reporting tools",
        "orders": [
            {"id": "ORD-007", "date": "2024-01-15", "amount": 6000, "status": "Completed", "product": "Financial Suite"},
            {"id": "ORD-008", "date": "2024-01-18", "amount": 1500, "status": "Pending", "product": "Reporting Add-on"}
        ],
        "total_value": 7500, "tags": ["Finance", "High Value", "Enterprise"]
    },
    {
        "id": "cust_008", "name": "Jennifer Martinez", "email": "j.martinez@educationtech.edu", "phone": "+1234567897",
        "company": "Education Tech Institute", "position": "Technology Coordinator", "lead_score": 70, "status": "Warm Lead",
        "last_contact": "2024-01-11", "notes": "Educational discount applicable",
        "orders": [
            {"id": "ORD-009", "date": "2024-01-10", "amount": 2000, "status": "Completed", "product": "Education Package"}
        ],
        "total_value": 2000, "tags": ["Education", "Non-Profit", "Discount"]
    },
    {
        "id": "cust_009", "name": "Christopher Lee", "email": "c.lee@realestate.com", "phone": "+1234567898",
        "company": "Prime Real Estate", "position": "Broker", "lead_score": 75, "status": "Warm Lead",
        "last_contact": "2024-01-13", "notes": "Seasonal business, peak in spring",
        "orders": [
            {"id": "ORD-010", "date": "2024-01-05", "amount": 1800, "status": "Completed", "product": "CRM Package"}
        ],
        "total_value": 1800, "tags": ["Real Estate", "Seasonal", "CRM"]
    },
    {
        "id": "cust_010", "name": "Amanda White", "email": "a.white@consulting.biz", "phone": "+1234567899",
        "company": "White Consulting", "position": "Principal Consultant", "lead_score": 80, "status": "Hot Lead",
        "last_contact": "2024-01-19", "notes": "Multi-client deployment needed",
        "orders": [
            {"id": "ORD-011", "date": "2024-01-16", "amount": 3200, "status": "Processing", "product": "Consulting Suite"}
        ],
        "total_value": 3200, "tags": ["Consulting", "Multi-Client", "Professional Services"]
    },
    {
        "id": "cust_011", "name": "James Garcia", "email": "j.garcia@logistics.net", "phone": "+1234567800",
        "company": "Garcia Logistics", "position": "Operations Director", "lead_score": 73, "status": "Warm Lead",
        "last_contact": "2024-01-10", "notes": "Supply chain optimization focus",
        "orders": [
            {"id": "ORD-012", "date": "2024-01-08", "amount": 2800, "status": "Shipped", "product": "Logistics Suite"}
        ],
        "total_value": 2800, "tags": ["Logistics", "Supply Chain", "Operations"]
    },
    {
        "id": "cust_012", "name": "Michelle Thompson", "email": "m.thompson@restaurant.com", "phone": "+1234567801",
        "company": "Thompson's Restaurant Group", "position": "General Manager", "lead_score": 68, "status": "Cold Lead",
        "last_contact": "2024-01-07", "notes": "Multiple locations, needs unified system",
        "orders": [
            {"id": "ORD-013", "date": "2023-12-20", "amount": 1500, "status": "Completed", "product": "Restaurant POS"}
        ],
        "total_value": 1500, "tags": ["Restaurant", "Multi-Location", "POS"]
    },
    {
        "id": "cust_013", "name": "Kevin Rodriguez", "email": "k.rodriguez@autoparts.com", "phone": "+1234567802",
        "company": "Rodriguez Auto Parts", "position": "Owner", "lead_score": 76, "status": "Warm Lead",
        "last_contact": "2024-01-15", "notes": "Inventory management priority",
        "orders": [
            {"id": "ORD-014", "date": "2024-01-12", "amount": 2200, "status": "Processing", "product": "Inventory System"}
        ],
        "total_value": 2200, "tags": ["Automotive", "Inventory", "Small Business"]
    },
    {
        "id": "cust_014", "name": "Nicole Clark", "email": "n.clark@lawfirm.legal", "phone": "+1234567803",
        "company": "Clark & Associates Law", "position": "Managing Partner", "lead_score": 85, "status": "Hot Lead",
        "last_contact": "2024-01-18", "notes": "Document management and billing focus",
        "orders": [
            {"id": "ORD-015", "date": "2024-01-14", "amount": 4500, "status": "Completed", "product": "Legal Suite"}
        ],
        "total_value": 4500, "tags": ["Legal", "Document Management", "Professional"]
    },
    {
        "id": "cust_015", "name": "Daniel Lewis", "email": "d.lewis@construction.build", "phone": "+1234567804",
        "company": "Lewis Construction", "position": "Project Manager", "lead_score": 71, "status": "Warm Lead",
        "last_contact": "2024-01-12", "notes": "Project tracking and scheduling needs",
        "orders": [
            {"id": "ORD-016", "date": "2024-01-09", "amount": 3100, "status": "Shipped", "product": "Project Management Suite"}
        ],
        "total_value": 3100, "tags": ["Construction", "Project Management", "Scheduling"]
    },
    {
        "id": "cust_016", "name": "Rachel Walker", "email": "r.walker@fitness.gym", "phone": "+1234567805",
        "company": "Walker Fitness Centers", "position": "Franchise Owner", "lead_score": 69, "status": "Cold Lead",
        "last_contact": "2024-01-09", "notes": "Member management and billing",
        "orders": [
            {"id": "ORD-017", "date": "2024-01-06", "amount": 1900, "status": "Completed", "product": "Fitness Management"}
        ],
        "total_value": 1900, "tags": ["Fitness", "Membership", "Franchise"]
    },
    {
        "id": "cust_017", "name": "Steven Hall", "email": "s.hall@insurance.protect", "phone": "+1234567806",
        "company": "Hall Insurance Agency", "position": "Agency Owner", "lead_score": 77, "status": "Warm Lead",
        "last_contact": "2024-01-16", "notes": "Client management and policy tracking",
        "orders": [
            {"id": "ORD-018", "date": "2024-01-13", "amount": 2600, "status": "Processing", "product": "Insurance CRM"}
        ],
        "total_value": 2600, "tags": ["Insurance", "Client Management", "Policy Tracking"]
    },
    {
        "id": "cust_018", "name": "Karen Young", "email": "k.young@veterinary.care", "phone": "+1234567807",
        "company": "Young Veterinary Clinic", "position": "Practice Manager", "lead_score": 74, "status": "Warm Lead",
        "last_contact": "2024-01-14", "notes": "Patient records and appointment scheduling",
        "orders": [
            {"id": "ORD-019", "date": "2024-01-11", "amount": 2300, "status": "Completed", "product": "Veterinary Suite"}
        ],
        "total_value": 2300, "tags": ["Veterinary", "Healthcare", "Appointments"]
    },
    {
        "id": "cust_019", "name": "Brian King", "email": "b.king@photography.studio", "phone": "+1234567808",
        "company": "King Photography Studio", "position": "Owner/Photographer", "lead_score": 66, "status": "Cold Lead",
        "last_contact": "2024-01-08", "notes": "Client galleries and booking system",
        "orders": [
            {"id": "ORD-020", "date": "2023-12-28", "amount": 1100, "status": "Completed", "product": "Photography Suite"}
        ],
        "total_value": 1100, "tags": ["Photography", "Creative", "Booking"]
    },
    {
        "id": "cust_020", "name": "Angela Wright", "email": "a.wright@accounting.numbers", "phone": "+1234567809",
        "company": "Wright Accounting Services", "position": "CPA", "lead_score": 81, "status": "Hot Lead",
        "last_contact": "2024-01-17", "notes": "Tax season preparation, client portal needed",
        "orders": [
            {"id": "ORD-021", "date": "2024-01-15", "amount": 3800, "status": "Processing", "product": "Accounting Suite"}
        ],
        "total_value": 3800, "tags": ["Accounting", "Tax", "Client Portal"]
    },
    {
        "id": "cust_021", "name": "Gregory Green", "email": "g.green@landscaping.earth", "phone": "+1234567810",
        "company": "Green Landscaping Co", "position": "Business Owner", "lead_score": 70, "status": "Warm Lead",
        "last_contact": "2024-01-13", "notes": "Seasonal business, route optimization",
        "orders": [
            {"id": "ORD-022", "date": "2024-01-10", "amount": 1700, "status": "Shipped", "product": "Field Service Suite"}
        ],
        "total_value": 1700, "tags": ["Landscaping", "Seasonal", "Field Service"]
    },
    {
        "id": "cust_022", "name": "Stephanie Adams", "email": "s.adams@dental.smile", "phone": "+1234567811",
        "company": "Adams Dental Practice", "position": "Office Manager", "lead_score": 79, "status": "Warm Lead",
        "last_contact": "2024-01-16", "notes": "Patient scheduling and insurance billing",
        "orders": [
            {"id": "ORD-023", "date": "2024-01-12", "amount": 2900, "status": "Processing", "product": "Dental Practice Suite"}
        ],
        "total_value": 2900, "tags": ["Dental", "Healthcare", "Insurance"]
    },
    {
        "id": "cust_023", "name": "Timothy Baker", "email": "t.baker@bakery.fresh", "phone": "+1234567812",
        "company": "Baker's Fresh Bakery", "position": "Owner", "lead_score": 63, "status": "Cold Lead",
        "last_contact": "2024-01-09", "notes": "Inventory and ordering system needed",
        "orders": [
            {"id": "ORD-024", "date": "2024-01-07", "amount": 1300, "status": "Completed", "product": "Retail POS"}
        ],
        "total_value": 1300, "tags": ["Food Service", "Retail", "Inventory"]
    },
    {
        "id": "cust_024", "name": "Melissa Nelson", "email": "m.nelson@spa.relax", "phone": "+1234567813",
        "company": "Nelson Day Spa", "position": "Spa Director", "lead_score": 72, "status": "Warm Lead",
        "last_contact": "2024-01-15", "notes": "Appointment booking and customer management",
        "orders": [
            {"id": "ORD-025", "date": "2024-01-13", "amount": 2100, "status": "Processing", "product": "Spa Management Suite"}
        ],
        "total_value": 2100, "tags": ["Spa", "Wellness", "Appointments"]
    },
    {
        "id": "cust_025", "name": "Anthony Carter", "email": "a.carter@security.safe", "phone": "+1234567814",
        "company": "Carter Security Solutions", "position": "Security Director", "lead_score": 84, "status": "Hot Lead",
        "last_contact": "2024-01-18", "notes": "Enterprise security monitoring system",
        "orders": [
            {"id": "ORD-026", "date": "2024-01-16", "amount": 5500, "status": "Processing", "product": "Security Suite"}
        ],
        "total_value": 5500, "tags": ["Security", "Enterprise", "Monitoring"]
    }
]

# Initialize session state
def init_session_state():
    """Initialize all session state variables with unique identifiers."""
    session_vars = {
        'current_page': "📊 Dashboard",
        'api_key': "",
        'selected_customer_for_call': None,
        'show_add_customer': False,
        'editing_customer': None,
        'viewing_customer_orders': None,
        'viewing_customer_interactions': None,
        'viewing_transcript': None,
        'viewing_recording': None,
        'call_monitoring': {},
        'call_results': []
    }
    
    for var, default_value in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default_value

# Utility functions
def save_call_to_db(call_data):
    """Save call data to database."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO calls 
        (id, timestamp, type, assistant_name, assistant_id, customer_phone, 
         customer_name, customer_email, call_id, status, notes, transcript, 
         recording_url, recording_path, duration, cost, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        call_data.get('id', str(uuid.uuid4())),
        call_data.get('timestamp'),
        call_data.get('type'),
        call_data.get('assistant_name'),
        call_data.get('assistant_id'),
        call_data.get('customer_phone'),
        call_data.get('customer_name'),
        call_data.get('customer_email'),
        call_data.get('call_id'),
        call_data.get('status'),
        call_data.get('notes'),
        call_data.get('transcript'),
        call_data.get('recording_url'),
        call_data.get('recording_path'),
        call_data.get('duration'),
        call_data.get('cost'),
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()

def get_calls_from_db(limit=None):
    """Retrieve calls from database."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    query = 'SELECT * FROM calls ORDER BY created_at DESC'
    if limit:
        query += f' LIMIT {limit}'
    
    cursor.execute(query)
    calls = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'timestamp', 'type', 'assistant_name', 'assistant_id', 
               'customer_phone', 'customer_name', 'customer_email', 'call_id', 
               'status', 'notes', 'transcript', 'recording_url', 'recording_path', 
               'duration', 'cost', 'created_at']
    
    return [dict(zip(columns, call)) for call in calls]

def get_customers_from_db(search_term=None, status_filter=None, limit=None):
    """Retrieve customers from database with optional filtering."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    query = 'SELECT * FROM customers'
    params = []
    conditions = []
    
    if search_term:
        conditions.append('(name LIKE ? OR email LIKE ? OR company LIKE ? OR phone LIKE ?)')
        search_pattern = f'%{search_term}%'
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
    
    if status_filter and status_filter != "All":
        conditions.append('status = ?')
        params.append(status_filter)
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' ORDER BY updated_at DESC'
    
    if limit:
        query += f' LIMIT {limit}'
    
    cursor.execute(query, params)
    customers = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'name', 'email', 'phone', 'company', 'position', 'lead_score', 
               'status', 'last_contact', 'notes', 'total_value', 'tags', 'created_at', 
               'updated_at', 'address', 'city', 'state', 'zip_code', 'country', 
               'website', 'industry', 'company_size', 'annual_revenue', 'source', 'assigned_to']
    
    return [dict(zip(columns, customer)) for customer in customers]

def get_customer_orders(customer_id):
    """Get orders for a specific customer."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM orders WHERE customer_id = ? ORDER BY order_date DESC', (customer_id,))
    orders = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'customer_id', 'order_date', 'amount', 'status', 'product', 
               'quantity', 'discount', 'tax', 'shipping', 'total', 'notes', 
               'created_at', 'updated_at']
    
    return [dict(zip(columns, order)) for order in orders]

def load_demo_customers():
    """Load demo customers into the database."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    for customer in DEMO_CUSTOMERS:
        # Insert customer
        cursor.execute('''
            INSERT OR REPLACE INTO customers 
            (id, name, email, phone, company, position, lead_score, status, 
             last_contact, notes, total_value, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer['id'],
            customer['name'],
            customer['email'],
            customer['phone'],
            customer['company'],
            customer['position'],
            customer['lead_score'],
            customer['status'],
            customer['last_contact'],
            customer['notes'],
            customer['total_value'],
            ','.join(customer['tags']),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # Insert orders
        for order in customer['orders']:
            cursor.execute('''
                INSERT OR REPLACE INTO orders 
                (id, customer_id, order_date, amount, status, product, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order['id'],
                customer['id'],
                order['date'],
                order['amount'],
                order['status'],
                order['product'],
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
    
    conn.commit()
    conn.close()

def validate_phone_number(phone: str) -> bool:
    """Basic phone number validation."""
    try:
        phone_str = str(phone).strip()
        phone_str = ''.join(char for char in phone_str if char.isprintable())
        
        clean_phone = phone_str.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace(".", "")
        
        if clean_phone.startswith("+") and len(clean_phone) >= 10 and len(clean_phone) <= 18:
            if clean_phone[1:].isdigit():
                return True
        return False
    except Exception:
        return False

def make_vapi_call(
    api_key: str,
    assistant_id: str,
    customers: List[Dict],
    schedule_plan: Optional[Dict] = None,
    base_url: str = "https://api.vapi.ai"
) -> Dict:
    """Make a call to the Vapi API for outbound calling."""
    
    url = f"{base_url}/call"
    
    try:
        api_key = str(api_key).strip()
        assistant_id = str(assistant_id).strip()
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        payload = {
            "assistantId": assistant_id,
            "phoneNumberId": STATIC_PHONE_NUMBER_ID,
        }
        
        # Clean customer phone numbers
        clean_customers = []
        for customer in customers:
            clean_customer = {}
            for key, value in customer.items():
                if isinstance(value, str):
                    clean_value = ''.join(char for char in value if char.isprintable()).strip()
                    clean_customer[key] = clean_value
                else:
                    clean_customer[key] = value
            clean_customers.append(clean_customer)
        
        # Add customers (single or multiple)
        if len(clean_customers) == 1:
            payload["customer"] = clean_customers[0]
        else:
            payload["customers"] = clean_customers
        
        # Add schedule plan if provided
        if schedule_plan:
            payload["schedulePlan"] = schedule_plan
        
        json_payload = json.dumps(payload, ensure_ascii=False)
        
        response = requests.post(
            url, 
            headers=headers, 
            data=json_payload.encode('utf-8'),
            timeout=30
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_api_connection(api_key: str) -> Dict:
    """Test the API connection by making a simple request."""
    try:
        url = "https://api.vapi.ai/assistant"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_details = response.json()
                error_msg += f" - {error_details.get('message', 'Unknown error')}"
            except:
                error_msg += f" - {response.text[:200]}"
            return {"success": False, "error": error_msg, "status_code": response.status_code}
        
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout", "status_code": None}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error", "status_code": None}
    except Exception as e:
        return {"success": False, "error": str(e), "status_code": None}

# Navigation
def render_navigation():
    """Render the navigation sidebar with unique keys."""
    with st.sidebar:
        st.title("📞 Vapi Pro Enhanced")
        
        # API Key input with unique key
        api_key = st.text_input(
            "🔑 Vapi API Key", 
            type="password",
            value=st.session_state.api_key,
            help="Your Vapi API key",
            key="nav_sidebar_api_key_input_unique_001"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
        
        # API Connection Status
        if api_key:
            if st.button("🔍 Test Connection", key="nav_sidebar_test_connection_btn_unique_002"):
                with st.spinner("Testing..."):
                    result = test_api_connection(api_key)
                    if result["success"]:
                        st.success("✅ Connected!")
                    else:
                        st.error(f"❌ {result['error']}")
        
        st.divider()
        
        # Navigation menu with unique key
        pages = [
            "📊 Dashboard",
            "📞 Make Calls", 
            "👥 CRM Dashboard",
            "👥 CRM Manager",
            "📋 Call History",
            "📝 Transcripts",
            "🎵 Recordings",
            "🤖 Assistant Manager",
            "📈 Analytics",
            "⚙️ Settings"
        ]
        
        selected_page = st.radio("Navigation", pages, key="nav_sidebar_page_radio_unique_003")
        
        # Update current page
        if selected_page != st.session_state.current_page:
            st.session_state.current_page = selected_page
        
        st.divider()
        
        # Quick stats
        if api_key:
            calls = get_calls_from_db(limit=10)
            customers = get_customers_from_db(limit=10)
            
            st.metric("Recent Calls", len(calls))
            st.metric("Total Customers", len(customers))
            
            if calls:
                completed_calls = len([c for c in calls if c['status'] == 'completed'])
                st.metric("Success Rate", f"{(completed_calls/len(calls)*100):.1f}%")

def render_dashboard():
    """Render the dashboard page with unique keys."""
    st.title("📊 Dashboard")
    st.markdown("Welcome to your Vapi Outbound Calling dashboard")
    
    # Get analytics data
    calls = get_calls_from_db()
    customers = get_customers_from_db()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Calls", len(calls))
    
    with col2:
        completed_calls = len([c for c in calls if c['status'] == 'completed'])
        st.metric("Successful Calls", completed_calls)
    
    with col3:
        success_rate = (completed_calls / len(calls) * 100) if calls else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col4:
        st.metric("Total Customers", len(customers))
    
    # Recent calls
    st.subheader("📞 Recent Calls")
    recent_calls = get_calls_from_db(limit=5)
    
    if recent_calls:
        for i, call in enumerate(recent_calls):
            with st.expander(f"📞 {call['customer_phone']} - {call['status'].upper()}", key=f"dashboard_call_expander_unique_{i}_004"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Assistant:** {call['assistant_name']}")
                    st.write(f"**Customer:** {call['customer_phone']}")
                    if call['customer_name']:
                        st.write(f"**Name:** {call['customer_name']}")
                with col2:
                    st.write(f"**Status:** {call['status']}")
                    st.write(f"**Date:** {call['timestamp'][:16] if call['timestamp'] else 'N/A'}")
                    if call['duration']:
                        st.write(f"**Duration:** {call['duration']}s")
    else:
        st.info("No calls made yet. Start by making your first call!")
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📞 Make Single Call", type="primary", key="dashboard_make_call_btn_unique_005"):
            st.session_state.current_page = "📞 Make Calls"
            st.rerun()
    
    with col2:
        if st.button("📋 View Call History", key="dashboard_call_history_btn_unique_006"):
            st.session_state.current_page = "📋 Call History"
            st.rerun()
    
    with col3:
        if st.button("👥 Manage CRM", key="dashboard_crm_btn_unique_007"):
            st.session_state.current_page = "👥 CRM Dashboard"
            st.rerun()

def render_make_calls():
    """Render the make calls page with unique keys."""
    st.title("📞 Make Calls")
    st.markdown("Enhanced outbound calling with CRM integration")
    
    # Check if customer was selected from CRM
    selected_customer = st.session_state.get('selected_customer_for_call')
    
    if selected_customer:
        st.info(f"📋 Selected customer: {selected_customer['name']} ({selected_customer['phone']})")
        if st.button("❌ Clear Selection", key="make_calls_clear_selection_btn_unique_008"):
            st.session_state.selected_customer_for_call = None
            st.rerun()
    
    # Call type selection
    col1, col2 = st.columns(2)
    
    with col1:
        call_type = st.radio(
            "Select calling mode:",
            ["Single Call", "Bulk Calls"],
            help="Choose your calling approach",
            key="make_calls_type_radio_unique_009"
        )
    
    with col2:
        # Assistant selection
        assistant_name = st.selectbox(
            "Choose Assistant",
            options=list(ASSISTANTS.keys()),
            help="Select from your pre-configured assistants",
            key="make_calls_assistant_select_unique_010"
        )
        assistant_id = ASSISTANTS[assistant_name]
    
    # Single Call
    if call_type == "Single Call":
        st.subheader("📱 Single Call")
        
        # Use selected customer or manual input
        if selected_customer:
            customer_number = selected_customer['phone']
            customer_name = selected_customer['name']
            customer_email = selected_customer['email']
            st.write(f"**Calling:** {customer_name} at {customer_number}")
        else:
            customer_number = st.text_input("Customer Phone Number", placeholder="+1234567890", key="make_calls_phone_input_unique_011")
            customer_name = st.text_input("Customer Name", placeholder="John Doe", key="make_calls_name_input_unique_012")
            customer_email = st.text_input("Customer Email", placeholder="john@example.com", key="make_calls_email_input_unique_013")
        
        customer_notes = st.text_area("Call Notes", placeholder="Purpose of call, talking points...", key="make_calls_notes_textarea_unique_014")
        
        if st.button("📞 Make Call", type="primary", disabled=not all([st.session_state.api_key, customer_number]), key="make_calls_submit_btn_unique_015"):
            if not validate_phone_number(customer_number):
                st.error("Please enter a valid phone number with country code")
            else:
                # Prepare customer data
                customer_data = {"number": customer_number}
                if customer_name:
                    customer_data["name"] = customer_name
                if customer_email:
                    customer_data["email"] = customer_email
                
                customers = [customer_data]
                
                # Make the call
                with st.spinner("Making call..."):
                    result = make_vapi_call(
                        api_key=st.session_state.api_key,
                        assistant_id=assistant_id,
                        customers=customers
                    )
                
                if result["success"]:
                    st.success("Call initiated successfully!")
                    call_data = result["data"]
                    
                    if isinstance(call_data, dict) and "id" in call_data:
                        call_id = call_data["id"]
                        st.info(f"**Call ID:** `{call_id}`")
                        
                        # Save to database
                        call_record = {
                            'id': str(uuid.uuid4()),
                            'timestamp': datetime.now().isoformat(),
                            'type': 'Single Call',
                            'assistant_name': assistant_name,
                            'assistant_id': assistant_id,
                            'customer_phone': customer_number,
                            'customer_name': customer_name,
                            'customer_email': customer_email,
                            'call_id': call_id,
                            'status': 'initiated',
                            'notes': customer_notes
                        }
                        
                        save_call_to_db(call_record)
                        st.json(call_data)
                    else:
                        st.json(call_data)
                else:
                    st.error(f"Call failed: {result['error']}")
    
    # Bulk Calls
    else:
        st.subheader("📞 Bulk Calls")
        
        bulk_input_method = st.radio(
            "Input method:",
            ["Text Input", "Upload CSV", "Select from CRM"],
            horizontal=True,
            key="make_calls_bulk_method_radio_unique_016"
        )
        
        customer_numbers = []
        
        if bulk_input_method == "Text Input":
            bulk_numbers_text = st.text_area(
                "Phone Numbers (one per line)",
                placeholder="+1234567890\n+0987654321\n+1122334455",
                height=150,
                key="make_calls_bulk_text_area_unique_017"
            )
            
            if bulk_numbers_text:
                lines = bulk_numbers_text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and validate_phone_number(line):
                        customer_numbers.append(line)
                st.info(f"Found {len(customer_numbers)} valid phone numbers")
        
        elif bulk_input_method == "Upload CSV":
            uploaded_file = st.file_uploader("Upload CSV file", type=['csv'], key="make_calls_csv_upload_unique_018")
            
            if uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.write("Preview:")
                    st.dataframe(df.head())
                    
                    phone_column = None
                    for col in ['phone', 'number', 'phone_number', 'Phone', 'Number']:
                        if col in df.columns:
                            phone_column = col
                            break
                    
                    if phone_column:
                        for phone in df[phone_column].dropna():
                            phone_str = str(phone).strip()
                            if validate_phone_number(phone_str):
                                customer_numbers.append(phone_str)
                        
                        st.info(f"Found {len(customer_numbers)} valid phone numbers")
                    else:
                        st.error("No phone column found")
                
                except Exception as e:
                    st.error(f"Error reading CSV: {str(e)}")
        
        elif bulk_input_method == "Select from CRM":
            customers = get_customers_from_db()
            
            if customers:
                st.write("Select customers to call:")
                
                # Filter options
                col1, col2 = st.columns(2)
                with col1:
                    status_filter = st.multiselect("Filter by Status", CUSTOMER_STATUSES, key="make_calls_crm_status_filter_unique_019")
                with col2:
                    min_score = st.slider("Minimum Lead Score", 0, 100, 0, key="make_calls_crm_score_slider_unique_020")
                
                # Filter customers
                filtered_customers = customers
                if status_filter:
                    filtered_customers = [c for c in filtered_customers if c['status'] in status_filter]
                if min_score > 0:
                    filtered_customers = [c for c in filtered_customers if (c['lead_score'] or 0) >= min_score]
                
                # Customer selection
                selected_customers = []
                for i, customer in enumerate(filtered_customers[:20]):  # Limit to 20 for performance
                    if st.checkbox(f"{customer['name']} - {customer['phone']} ({customer['status']})", 
                                 key=f"make_calls_crm_customer_checkbox_unique_{i}_021"):
                        selected_customers.append(customer)
                
                customer_numbers = [c['phone'] for c in selected_customers]
                st.info(f"Selected {len(customer_numbers)} customers")
            else:
                st.warning("No customers found in CRM")
        
        # Bulk call execution
        if customer_numbers and st.button("📞 Make Bulk Calls", type="primary", key="make_calls_bulk_submit_btn_unique_022"):
            customers = [{"number": num} for num in customer_numbers]
            
            with st.spinner(f"Making {len(customers)} calls..."):
                result = make_vapi_call(
                    api_key=st.session_state.api_key,
                    assistant_id=assistant_id,
                    customers=customers
                )
            
            if result["success"]:
                st.success(f"Bulk calls initiated for {len(customers)} numbers!")
                call_data = result["data"]
                
                # Save bulk call record
                call_record = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.now().isoformat(),
                    'type': 'Bulk Calls',
                    'assistant_name': assistant_name,
                    'assistant_id': assistant_id,
                    'customer_phone': f"{len(customers)} numbers",
                    'call_id': str(call_data) if isinstance(call_data, list) else call_data.get('id', ''),
                    'status': 'initiated',
                    'notes': f"Bulk call to {len(customers)} customers"
                }
                
                save_call_to_db(call_record)
                st.json(call_data)
            else:
                st.error(f"Bulk calls failed: {result['error']}")

def render_crm_dashboard():
    """Render the CRM dashboard page with unique keys."""
    st.title("👥 CRM Dashboard")
    st.markdown("Manage your customers, orders, and relationships")
    
    # Load demo customers if database is empty
    customers = get_customers_from_db(limit=5)
    if not customers:
        if st.button("🎯 Load 25 Demo Customers", key="crm_dashboard_load_demo_btn_unique_023"):
            load_demo_customers()
            st.success("Demo customers loaded successfully!")
            st.rerun()
    
    # CRM Overview metrics
    all_customers = get_customers_from_db()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Customers", len(all_customers))
    
    with col2:
        hot_leads = len([c for c in all_customers if c['status'] == 'Hot Lead'])
        st.metric("Hot Leads", hot_leads)
    
    with col3:
        total_value = sum([c['total_value'] or 0 for c in all_customers])
        st.metric("Total Customer Value", f"${total_value:,.2f}")
    
    with col4:
        avg_score = sum([c['lead_score'] or 0 for c in all_customers]) / len(all_customers) if all_customers else 0
        st.metric("Avg Lead Score", f"{avg_score:.1f}")
    
    # Customer status distribution
    if all_customers:
        st.subheader("📊 Customer Status Distribution")
        status_counts = {}
        for customer in all_customers:
            status = customer['status'] or 'Unknown'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        fig = px.pie(
            values=list(status_counts.values()),
            names=list(status_counts.keys()),
            title="Customer Status Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent customers and quick actions
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🆕 Recent Customers")
        recent_customers = get_customers_from_db(limit=5)
        
        for i, customer in enumerate(recent_customers):
            with st.expander(f"👤 {customer['name']} - {customer['company']}", key=f"crm_dashboard_customer_expander_unique_{i}_024"):
                st.write(f"**Status:** {customer['status']}")
                st.write(f"**Lead Score:** {customer['lead_score']}/100")
                st.write(f"**Phone:** {customer['phone']}")
                st.write(f"**Total Value:** ${customer['total_value'] or 0:,.2f}")
                
                if st.button(f"📞 Call {customer['name']}", key=f"crm_dashboard_call_customer_btn_unique_{i}_025"):
                    st.session_state.selected_customer_for_call = customer
                    st.session_state.current_page = "📞 Make Calls"
                    st.rerun()
    
    with col2:
        st.subheader("🚀 Quick Actions")
        
        if st.button("➕ Add New Customer", type="primary", key="crm_dashboard_add_customer_btn_unique_026"):
            st.session_state.show_add_customer = True
        
        if st.button("📋 View All Customers", key="crm_dashboard_view_all_btn_unique_027"):
            st.session_state.current_page = "👥 CRM Manager"
            st.rerun()
        
        if st.button("📊 Customer Analytics", key="crm_dashboard_analytics_btn_unique_028"):
            st.session_state.current_page = "📈 Analytics"
            st.rerun()
        
        if st.button("📤 Export Customers", key="crm_dashboard_export_btn_unique_029"):
            customers_df = pd.DataFrame(all_customers)
            csv_data = customers_df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv_data,
                file_name=f"customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="crm_dashboard_download_btn_unique_030"
            )
    
    # Add customer form
    if st.session_state.get('show_add_customer', False):
        st.subheader("➕ Add New Customer")
        
        with st.form("add_customer_form_unique_031"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Customer Name*", key="add_customer_name_input_unique_032")
                email = st.text_input("Email*", key="add_customer_email_input_unique_033")
                phone = st.text_input("Phone*", key="add_customer_phone_input_unique_034")
                company = st.text_input("Company", key="add_customer_company_input_unique_035")
                position = st.text_input("Position", key="add_customer_position_input_unique_036")
            
            with col2:
                status = st.selectbox("Status", CUSTOMER_STATUSES, key="add_customer_status_select_unique_037")
                lead_score = st.slider("Lead Score", 0, 100, 50, key="add_customer_score_slider_unique_038")
                tags = st.text_input("Tags (comma-separated)", key="add_customer_tags_input_unique_039")
                notes = st.text_area("Notes", key="add_customer_notes_textarea_unique_040")
            
            submitted = st.form_submit_button("Add Customer", key="add_customer_submit_btn_unique_041")
            
            if submitted and name and email and phone:
                customer_data = {
                    'id': str(uuid.uuid4()),
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'company': company,
                    'position': position,
                    'lead_score': lead_score,
                    'status': status,
                    'notes': notes,
                    'tags': tags,
                    'total_value': 0,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                # Save to database
                conn = sqlite3.connect('vapi_calls.db')
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO customers 
                    (id, name, email, phone, company, position, lead_score, status, 
                     notes, tags, total_value, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    customer_data['id'], customer_data['name'], customer_data['email'],
                    customer_data['phone'], customer_data['company'], customer_data['position'],
                    customer_data['lead_score'], customer_data['status'], customer_data['notes'],
                    customer_data['tags'], customer_data['total_value'], 
                    customer_data['created_at'], customer_data['updated_at']
                ))
                
                conn.commit()
                conn.close()
                
                st.success(f"Customer {name} added successfully!")
                st.session_state.show_add_customer = False
                st.rerun()

def render_crm_manager():
    """Render the full CRM management page with unique keys."""
    st.title("👥 CRM Manager")
    st.markdown("Complete customer relationship management")
    
    # Search and filter controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search customers", placeholder="Name, email, company, or phone", key="crm_manager_search_input_unique_042")
    
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All"] + CUSTOMER_STATUSES, key="crm_manager_status_filter_unique_043")
        if status_filter == "All":
            status_filter = None
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Updated", "Name", "Lead Score", "Total Value"], key="crm_manager_sort_select_unique_044")
    
    # Get filtered customers
    customers = get_customers_from_db(search_term=search_term, status_filter=status_filter)
    
    # Sort customers
    if sort_by == "Name":
        customers.sort(key=lambda x: x['name'] or '')
    elif sort_by == "Lead Score":
        customers.sort(key=lambda x: x['lead_score'] or 0, reverse=True)
    elif sort_by == "Total Value":
        customers.sort(key=lambda x: x['total_value'] or 0, reverse=True)
    
    st.write(f"Found {len(customers)} customers")
    
    # Customer list with actions
    for i, customer in enumerate(customers):
        with st.expander(f"👤 {customer['name']} - {customer['company']} ({customer['status']})", key=f"crm_manager_customer_expander_unique_{i}_045"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**Email:** {customer['email']}")
                st.write(f"**Phone:** {customer['phone']}")
                st.write(f"**Position:** {customer['position']}")
                st.write(f"**Lead Score:** {customer['lead_score']}/100")
                st.write(f"**Total Value:** ${customer['total_value'] or 0:,.2f}")
                if customer['notes']:
                    st.write(f"**Notes:** {customer['notes']}")
                if customer['tags']:
                    st.write(f"**Tags:** {customer['tags']}")
            
            with col2:
                # Customer orders
                orders = get_customer_orders(customer['id'])
                st.write(f"**Orders:** {len(orders)}")
                
                if orders:
                    for j, order in enumerate(orders[:3]):  # Show last 3 orders
                        status_color = {
                            'Completed': '🟢',
                            'Processing': '🟡', 
                            'Pending': '🟠',
                            'Cancelled': '🔴'
                        }.get(order['status'], '⚪')
                        
                        st.write(f"{status_color} {order['id']}: ${order['amount']:,.2f} ({order['status']})")
            
            with col3:
                # Action buttons
                if st.button(f"📞 Call", key=f"crm_manager_call_btn_unique_{i}_046"):
                    st.session_state.selected_customer_for_call = customer
                    st.session_state.current_page = "📞 Make Calls"
                    st.rerun()
                
                if st.button(f"✏️ Edit", key=f"crm_manager_edit_btn_unique_{i}_047"):
                    st.session_state.editing_customer = customer
                
                if st.button(f"📋 Orders", key=f"crm_manager_orders_btn_unique_{i}_048"):
                    st.session_state.viewing_customer_orders = customer['id']

def render_call_history():
    """Render the call history page with unique keys."""
    st.title("📋 Call History")
    st.markdown("Complete call history with advanced filtering and export options")
    
    # Get calls
    calls = get_calls_from_db()
    
    # Display summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Calls", len(calls))
    
    with col2:
        completed = len([c for c in calls if c['status'] == 'completed'])
        st.metric("Completed", completed)
    
    with col3:
        success_rate = (completed / len(calls) * 100) if calls else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col4:
        total_duration = sum([c['duration'] or 0 for c in calls])
        st.metric("Total Duration", f"{total_duration}s")
    
    # Export options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Export CSV", key="call_history_export_csv_btn_unique_049"):
            if calls:
                df = pd.DataFrame(calls)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="💾 Download CSV",
                    data=csv_data,
                    file_name=f"call_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="call_history_download_csv_btn_unique_050"
                )
    
    with col2:
        if st.button("📊 Export Excel", key="call_history_export_excel_btn_unique_051"):
            if calls:
                df = pd.DataFrame(calls)
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_data = excel_buffer.getvalue()
                st.download_button(
                    label="💾 Download Excel",
                    data=excel_data,
                    file_name=f"call_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="call_history_download_excel_btn_unique_052"
                )
    
    with col3:
        if st.button("📋 Copy to Clipboard", key="call_history_copy_btn_unique_053"):
            if calls:
                df = pd.DataFrame(calls)
                st.code(df.to_string(index=False))
    
    # Call history table
    if calls:
        st.subheader("📞 Call Records")
        
        for i, call in enumerate(calls):
            with st.expander(f"📞 {call['customer_phone']} - {call['status'].upper()}", key=f"call_history_call_expander_unique_{i}_054"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Type:** {call['type']}")
                    st.write(f"**Assistant:** {call['assistant_name']}")
                    st.write(f"**Customer:** {call['customer_phone']}")
                    if call['customer_name']:
                        st.write(f"**Name:** {call['customer_name']}")
                
                with col2:
                    st.write(f"**Status:** {call['status']}")
                    st.write(f"**Call ID:** {call['call_id']}")
                    if call['duration']:
                        st.write(f"**Duration:** {call['duration']}s")
                    if call['cost']:
                        st.write(f"**Cost:** ${call['cost']:.4f}")
                
                with col3:
                    if call['transcript']:
                        if st.button(f"📝 View Transcript", key=f"call_history_transcript_btn_unique_{i}_055"):
                            st.session_state.viewing_transcript = call['id']
                            st.session_state.current_page = "📝 Transcripts"
                            st.rerun()
                    
                    if call['recording_path']:
                        if st.button(f"🎵 Play Recording", key=f"call_history_recording_btn_unique_{i}_056"):
                            st.session_state.viewing_recording = call['id']
                            st.session_state.current_page = "🎵 Recordings"
                            st.rerun()
                
                if call['notes']:
                    st.write(f"**Notes:** {call['notes']}")
    else:
        st.info("No calls found.")

def render_transcripts():
    """Render the transcripts page with unique keys."""
    st.title("📝 Transcripts")
    st.markdown("View, search, and manage call transcripts")
    
    # Check if viewing specific transcript
    viewing_transcript_id = st.session_state.get('viewing_transcript')
    
    if viewing_transcript_id:
        # Display specific transcript
        calls = get_calls_from_db()
        call = next((c for c in calls if c['id'] == viewing_transcript_id), None)
        
        if call and call['transcript']:
            st.subheader(f"📝 Transcript: {call['customer_phone']}")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Call Date:** {call['timestamp'][:16] if call['timestamp'] else 'N/A'}")
                st.write(f"**Assistant:** {call['assistant_name']}")
                st.write(f"**Customer:** {call['customer_phone']}")
                if call['customer_name']:
                    st.write(f"**Name:** {call['customer_name']}")
                st.write(f"**Duration:** {call['duration'] or 0}s")
            
            with col2:
                # Export options
                if st.button("📥 Export TXT", key="transcripts_export_txt_btn_unique_057"):
                    transcript_data = f"""Call Transcript
Date: {call['timestamp'][:16] if call['timestamp'] else 'N/A'}
Assistant: {call['assistant_name']}
Customer: {call['customer_phone']}
Duration: {call['duration'] or 0}s

Transcript:
{call['transcript']}
"""
                    st.download_button(
                        label="💾 Download TXT",
                        data=transcript_data,
                        file_name=f"transcript_{call['call_id'][:8]}.txt",
                        mime="text/plain",
                        key="transcripts_download_txt_btn_unique_058"
                    )
                
                if st.button("📋 Copy Text", key="transcripts_copy_btn_unique_059"):
                    st.code(call['transcript'])
                
                if st.button("⬅️ Back to List", key="transcripts_back_btn_unique_060"):
                    st.session_state.viewing_transcript = None
                    st.rerun()
            
            # Display transcript
            st.subheader("📄 Transcript Content")
            st.text_area("", value=call['transcript'], height=400, disabled=True, key="transcripts_content_textarea_unique_061")
            
            # Transcript analysis
            st.subheader("🔍 Quick Analysis")
            
            transcript_text = call['transcript'].lower()
            word_count = len(call['transcript'].split())
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Word Count", word_count)
            
            with col2:
                # Simple sentiment analysis
                positive_words = ['yes', 'great', 'good', 'excellent', 'interested', 'perfect']
                negative_words = ['no', 'not', 'bad', 'terrible', 'uninterested', 'busy']
                
                positive_count = sum(transcript_text.count(word) for word in positive_words)
                negative_count = sum(transcript_text.count(word) for word in negative_words)
                
                sentiment = "Positive" if positive_count > negative_count else "Negative" if negative_count > positive_count else "Neutral"
                st.metric("Sentiment", sentiment)
            
            with col3:
                # Extract phone numbers or emails mentioned
                import re
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', call['transcript'])
                st.metric("Emails Mentioned", len(emails))
        
        else:
            st.error("Transcript not found or not available")
            if st.button("⬅️ Back to List", key="transcripts_back_error_btn_unique_062"):
                st.session_state.viewing_transcript = None
                st.rerun()
    
    else:
        # Display transcript list
        calls_with_transcripts = [c for c in get_calls_from_db() if c['transcript']]
        
        # Search functionality
        search_term = st.text_input("🔍 Search transcripts", placeholder="Enter keywords to search...", key="transcripts_search_input_unique_063")
        
        if search_term:
            calls_with_transcripts = [c for c in calls_with_transcripts 
                                    if search_term.lower() in c['transcript'].lower()]
        
        # Display summary
        st.write(f"Found {len(calls_with_transcripts)} transcripts")
        
        if calls_with_transcripts:
            # Bulk export
            if st.button("📥 Export All Transcripts", key="transcripts_export_all_btn_unique_064"):
                all_transcripts = ""
                for call in calls_with_transcripts:
                    all_transcripts += f"""
=== Call {call['call_id'][:8]} ===
Date: {call['timestamp'][:16] if call['timestamp'] else 'N/A'}
Customer: {call['customer_phone']}
Assistant: {call['assistant_name']}
Duration: {call['duration'] or 0}s

{call['transcript']}

{'='*50}

"""
                
                st.download_button(
                    label="💾 Download All Transcripts",
                    data=all_transcripts,
                    file_name=f"all_transcripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="transcripts_download_all_btn_unique_065"
                )
            
            # Transcript list
            for i, call in enumerate(calls_with_transcripts):
                with st.expander(f"📝 {call['customer_phone']} - {call['timestamp'][:16] if call['timestamp'] else 'N/A'}", key=f"transcripts_call_expander_unique_{i}_066"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Show first 200 characters of transcript
                        preview = call['transcript'][:200] + "..." if len(call['transcript']) > 200 else call['transcript']
                        st.write(f"**Preview:** {preview}")
                        st.write(f"**Assistant:** {call['assistant_name']}")
                        st.write(f"**Duration:** {call['duration'] or 0}s")
                    
                    with col2:
                        if st.button("👁️ View Full", key=f"transcripts_view_full_btn_unique_{i}_067"):
                            st.session_state.viewing_transcript = call['id']
                            st.rerun()
                        
                        if st.button("📥 Export", key=f"transcripts_export_single_btn_unique_{i}_068"):
                            transcript_data = f"""Call Transcript
Date: {call['timestamp'][:16] if call['timestamp'] else 'N/A'}
Customer: {call['customer_phone']}
Assistant: {call['assistant_name']}
Duration: {call['duration'] or 0}s

{call['transcript']}
"""
                            st.download_button(
                                label="💾 Download",
                                data=transcript_data,
                                file_name=f"transcript_{call['call_id'][:8]}.txt",
                                mime="text/plain",
                                key=f"transcripts_download_single_btn_unique_{i}_069"
                            )
        else:
            st.info("No transcripts found. Transcripts will appear here after calls are completed.")

def render_recordings():
    """Render the recordings page with MP3 playback and unique keys."""
    st.title("🎵 Recordings")
    st.markdown("Listen to and manage call recordings")
    
    # Check if viewing specific recording
    viewing_recording_id = st.session_state.get('viewing_recording')
    
    if viewing_recording_id:
        # Display specific recording
        calls = get_calls_from_db()
        call = next((c for c in calls if c['id'] == viewing_recording_id), None)
        
        if call:
            st.subheader(f"🎵 Recording: {call['customer_phone']}")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Call Date:** {call['timestamp'][:16] if call['timestamp'] else 'N/A'}")
                st.write(f"**Assistant:** {call['assistant_name']}")
                st.write(f"**Customer:** {call['customer_phone']}")
                if call['customer_name']:
                    st.write(f"**Name:** {call['customer_name']}")
                st.write(f"**Duration:** {call['duration'] or 0}s")
            
            with col2:
                if st.button("⬅️ Back to List", key="recordings_back_btn_unique_070"):
                    st.session_state.viewing_recording = None
                    st.rerun()
            
            # Recording playback
            if call['recording_path'] and os.path.exists(call['recording_path']):
                st.subheader("🎧 Audio Player")
                
                # Read audio file
                try:
                    with open(call['recording_path'], 'rb') as audio_file:
                        audio_bytes = audio_file.read()
                    
                    # Display audio player
                    st.audio(audio_bytes, format='audio/mp3')
                    
                    # Download option
                    st.download_button(
                        label="💾 Download Recording",
                        data=audio_bytes,
                        file_name=f"recording_{call['call_id'][:8]}.mp3",
                        mime="audio/mpeg",
                        key="recordings_download_btn_unique_071"
                    )
                except Exception as e:
                    st.error(f"Error loading audio file: {str(e)}")
                
            elif call['recording_url']:
                st.subheader("📥 Download Recording")
                st.write("Recording is available for download from Vapi servers.")
                st.info("Recording download from Vapi servers will be implemented in a future version.")
            else:
                st.warning("No recording available for this call.")
        
        else:
            st.error("Call not found")
            if st.button("⬅️ Back to List", key="recordings_back_error_btn_unique_072"):
                st.session_state.viewing_recording = None
                st.rerun()
    
    else:
        # Display recordings list
        calls_with_recordings = [c for c in get_calls_from_db() 
                               if c['recording_url'] or c['recording_path']]
        
        st.write(f"Found {len(calls_with_recordings)} recordings")
        
        if calls_with_recordings:
            # Recordings list
            for i, call in enumerate(calls_with_recordings):
                with st.expander(f"🎵 {call['customer_phone']} - {call['timestamp'][:16] if call['timestamp'] else 'N/A'}", key=f"recordings_call_expander_unique_{i}_073"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Assistant:** {call['assistant_name']}")
                        st.write(f"**Duration:** {call['duration'] or 0}s")
                        st.write(f"**Status:** {'Downloaded' if call['recording_path'] else 'Available'}")
                    
                    with col2:
                        if call['recording_path'] and os.path.exists(call['recording_path']):
                            # Quick play option
                            try:
                                with open(call['recording_path'], 'rb') as audio_file:
                                    audio_bytes = audio_file.read()
                                st.audio(audio_bytes, format='audio/mp3')
                            except Exception as e:
                                st.error(f"Error loading audio: {str(e)}")
                    
                    with col3:
                        if st.button("🎧 Open Player", key=f"recordings_open_player_btn_unique_{i}_074"):
                            st.session_state.viewing_recording = call['id']
                            st.rerun()
                        
                        if call['recording_path'] and os.path.exists(call['recording_path']):
                            try:
                                with open(call['recording_path'], 'rb') as audio_file:
                                    audio_bytes = audio_file.read()
                                
                                st.download_button(
                                    label="💾 Download",
                                    data=audio_bytes,
                                    file_name=f"recording_{call['call_id'][:8]}.mp3",
                                    mime="audio/mpeg",
                                    key=f"recordings_download_single_btn_unique_{i}_075"
                                )
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
        else:
            st.info("No recordings found. Recordings will appear here after calls are completed.")

def render_assistant_manager():
    """Render the assistant manager page with unique keys."""
    st.title("🤖 Assistant Manager")
    st.markdown("Create and manage your AI assistants")
    
    # Display predefined assistants
    st.subheader("📋 Your Assistants")
    
    for i, (name, assistant_id) in enumerate(ASSISTANTS.items()):
        with st.expander(f"🤖 {name}", key=f"assistant_manager_expander_unique_{i}_076"):
            st.code(f"ID: {assistant_id}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📞 Test Call", key=f"assistant_manager_test_btn_unique_{i}_077"):
                    st.info("Test call feature coming soon!")
            
            with col2:
                if st.button(f"✏️ Edit", key=f"assistant_manager_edit_btn_unique_{i}_078"):
                    st.info("Edit feature coming soon!")

def render_analytics():
    """Render the analytics page with unique keys."""
    st.title("📈 Analytics")
    st.markdown("Comprehensive insights into your calling performance")
    
    # Get data
    calls = get_calls_from_db()
    customers = get_customers_from_db()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Calls", len(calls))
    
    with col2:
        completed_calls = len([c for c in calls if c['status'] == 'completed'])
        success_rate = (completed_calls / len(calls) * 100) if calls else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        total_duration = sum([c['duration'] or 0 for c in calls])
        avg_duration = total_duration / len(calls) if calls else 0
        st.metric("Avg Duration", f"{avg_duration:.1f}s")
    
    with col4:
        st.metric("Total Customers", len(customers))
    
    # Assistant performance
    if calls:
        st.subheader("🤖 Assistant Performance")
        
        assistant_stats = {}
        for call in calls:
            assistant = call['assistant_name']
            if assistant not in assistant_stats:
                assistant_stats[assistant] = {'total': 0, 'completed': 0, 'duration': 0}
            
            assistant_stats[assistant]['total'] += 1
            if call['status'] == 'completed':
                assistant_stats[assistant]['completed'] += 1
            assistant_stats[assistant]['duration'] += call['duration'] or 0
        
        # Create assistant performance dataframe
        assistant_data = []
        for assistant, stats in assistant_stats.items():
            success_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            avg_duration = stats['duration'] / stats['total'] if stats['total'] > 0 else 0
            
            assistant_data.append({
                'Assistant': assistant,
                'Total Calls': stats['total'],
                'Success Rate': f"{success_rate:.1f}%",
                'Avg Duration': f"{avg_duration:.1f}s"
            })
        
        df_assistants = pd.DataFrame(assistant_data)
        st.dataframe(df_assistants, use_container_width=True)
    
    # Customer insights
    if customers:
        st.subheader("👥 Customer Insights")
        
        # Customer status distribution
        status_counts = {}
        for customer in customers:
            status = customer['status'] or 'Unknown'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            fig = px.pie(values=list(status_counts.values()), names=list(status_counts.keys()), 
                        title="Customer Status Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        # Top customers by value
        top_customers = sorted(customers, key=lambda x: x['total_value'] or 0, reverse=True)[:10]
        
        if top_customers:
            st.subheader("💎 Top Customers by Value")
            top_customer_data = [{
                'Name': c['name'],
                'Company': c['company'],
                'Total Value': f"${c['total_value'] or 0:,.2f}",
                'Status': c['status']
            } for c in top_customers]
            
            df_top_customers = pd.DataFrame(top_customer_data)
            st.dataframe(df_top_customers, use_container_width=True)

def render_settings():
    """Render the settings page with unique keys."""
    st.title("⚙️ Settings")
    st.markdown("Configure your Vapi application settings")
    
    # API Settings
    st.subheader("🔑 API Configuration")
    
    with st.expander("API Settings"):
        current_api_key = st.session_state.api_key
        new_api_key = st.text_input("Vapi API Key", value=current_api_key, type="password", key="settings_api_key_input_unique_079")
        
        if new_api_key != current_api_key:
            st.session_state.api_key = new_api_key
            st.success("API key updated!")
        
        # Test connection
        if st.button("🔍 Test API Connection", key="settings_test_connection_btn_unique_080"):
            if new_api_key:
                with st.spinner("Testing connection..."):
                    result = test_api_connection(new_api_key)
                    if result["success"]:
                        st.success("✅ API connection successful!")
                    else:
                        st.error(f"❌ Connection failed: {result['error']}")
            else:
                st.warning("Please enter an API key first")
    
    # Phone Number Settings
    st.subheader("📱 Phone Number Configuration")
    
    with st.expander("Phone Number Settings"):
        st.info(f"Current Phone Number ID: {STATIC_PHONE_NUMBER_ID}")
        st.write("This is the phone number used for all outbound calls.")
    
    # Database Settings
    st.subheader("🗄️ Database Management")
    
    with st.expander("Database Operations"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Reset Demo Data", key="settings_reset_demo_btn_unique_081"):
                load_demo_customers()
                st.success("Demo customers reloaded!")
        
        with col2:
            if st.button("📥 Export Database", key="settings_export_db_btn_unique_082"):
                # Export all data
                calls = get_calls_from_db()
                customers = get_customers_from_db()
                
                export_data = {
                    'calls': calls,
                    'customers': customers,
                    'export_date': datetime.now().isoformat()
                }
                
                json_data = json.dumps(export_data, indent=2)
                st.download_button(
                    label="💾 Download Database Export",
                    data=json_data,
                    file_name=f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="settings_download_db_btn_unique_083"
                )
        
        with col3:
            if st.button("⚠️ Clear All Data", key="settings_clear_data_btn_unique_084"):
                if st.checkbox("I understand this will delete all data", key="settings_confirm_clear_checkbox_unique_085"):
                    conn = sqlite3.connect('vapi_calls.db')
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM calls')
                    cursor.execute('DELETE FROM customers')
                    cursor.execute('DELETE FROM orders')
                    cursor.execute('DELETE FROM customer_interactions')
                    conn.commit()
                    conn.close()
                    st.success("All data cleared!")
    
    # System Information
    st.subheader("ℹ️ System Information")
    
    with st.expander("System Info"):
        st.write(f"**Application Version:** 3.0.0 Enhanced Fixed")
        st.write(f"**Database:** SQLite")
        st.write(f"**Total Calls:** {len(get_calls_from_db())}")
        st.write(f"**Total Customers:** {len(get_customers_from_db())}")
        st.write(f"**Available Assistants:** {len(ASSISTANTS)}")
        
        # Database file size
        try:
            db_size = os.path.getsize('vapi_calls.db')
            st.write(f"**Database Size:** {db_size / 1024:.2f} KB")
        except:
            st.write("**Database Size:** Unknown")

# Main function with proper routing
def main():
    """Main application function with complete routing and unique keys."""
    init_session_state()
    render_navigation()
    
    # Route to appropriate page
    page = st.session_state.current_page
    
    if "Dashboard" in page and "CRM" not in page:
        render_dashboard()
    elif "CRM Dashboard" in page:
        render_crm_dashboard()
    elif "CRM Manager" in page:
        render_crm_manager()
    elif "Make Calls" in page:
        render_make_calls()
    elif "Call History" in page:
        render_call_history()
    elif "Transcripts" in page:
        render_transcripts()
    elif "Recordings" in page:
        render_recordings()
    elif "Assistant Manager" in page:
        render_assistant_manager()
    elif "Analytics" in page:
        render_analytics()
    elif "Settings" in page:
        render_settings()

if __name__ == "__main__":
    main()

