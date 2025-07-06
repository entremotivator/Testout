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
from plotly.subplots import make_subplots

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

# Voice options for assistants
VOICE_OPTIONS = {
    "alloy": "Alloy - Balanced and clear",
    "echo": "Echo - Warm and engaging",
    "fable": "Fable - Expressive and dynamic",
    "onyx": "Onyx - Deep and authoritative",
    "nova": "Nova - Bright and energetic",
    "shimmer": "Shimmer - Gentle and soothing"
}

# Model options
MODEL_OPTIONS = {
    "gpt-4": "GPT-4 - Most capable",
    "gpt-3.5-turbo": "GPT-3.5 Turbo - Fast and efficient",
    "gpt-4-turbo": "GPT-4 Turbo - Latest and fastest"
}

# Order status options
ORDER_STATUSES = [
    "Pending",
    "Processing", 
    "Shipped",
    "Delivered",
    "Completed",
    "Cancelled",
    "Refunded",
    "On Hold"
]

# Customer status options
CUSTOMER_STATUSES = [
    "Hot Lead",
    "Warm Lead", 
    "Cold Lead",
    "Customer",
    "Inactive",
    "Churned"
]

# Demo customers data
DEMO_CUSTOMERS = [
    {
        "id": "cust_001",
        "name": "John Smith",
        "email": "john.smith@email.com",
        "phone": "+1234567890",
        "company": "Tech Solutions Inc",
        "position": "CEO",
        "lead_score": 85,
        "status": "Hot Lead",
        "last_contact": "2024-01-15",
        "notes": "Interested in enterprise solution",
        "orders": [
            {"id": "ORD-001", "date": "2024-01-10", "amount": 5000, "status": "Completed", "product": "Enterprise Package"},
            {"id": "ORD-002", "date": "2024-01-20", "amount": 2500, "status": "Processing", "product": "Add-on Services"}
        ],
        "total_value": 7500,
        "tags": ["Enterprise", "High Value", "Decision Maker"]
    },
    {
        "id": "cust_002",
        "name": "Sarah Johnson",
        "email": "sarah.j@businesscorp.com",
        "phone": "+1234567891",
        "company": "Business Corp",
        "position": "Marketing Director",
        "lead_score": 72,
        "status": "Warm Lead",
        "last_contact": "2024-01-12",
        "notes": "Needs marketing automation tools",
        "orders": [
            {"id": "ORD-003", "date": "2024-01-05", "amount": 1200, "status": "Completed", "product": "Marketing Suite"}
        ],
        "total_value": 1200,
        "tags": ["Marketing", "Mid-Market", "Repeat Customer"]
    },
    {
        "id": "cust_003",
        "name": "Michael Brown",
        "email": "m.brown@startup.io",
        "phone": "+1234567892",
        "company": "Startup Innovations",
        "position": "Founder",
        "lead_score": 90,
        "status": "Hot Lead",
        "last_contact": "2024-01-18",
        "notes": "Fast-growing startup, budget approved",
        "orders": [],
        "total_value": 0,
        "tags": ["Startup", "High Potential", "New Customer"]
    },
    {
        "id": "cust_004",
        "name": "Emily Davis",
        "email": "emily.davis@retailplus.com",
        "phone": "+1234567893",
        "company": "Retail Plus",
        "position": "Operations Manager",
        "lead_score": 65,
        "status": "Cold Lead",
        "last_contact": "2024-01-08",
        "notes": "Interested but budget constraints",
        "orders": [
            {"id": "ORD-004", "date": "2023-12-15", "amount": 800, "status": "Completed", "product": "Basic Package"}
        ],
        "total_value": 800,
        "tags": ["Retail", "Budget Conscious", "Small Business"]
    },
    {
        "id": "cust_005",
        "name": "David Wilson",
        "email": "d.wilson@manufacturing.com",
        "phone": "+1234567894",
        "company": "Wilson Manufacturing",
        "position": "Plant Manager",
        "lead_score": 78,
        "status": "Warm Lead",
        "last_contact": "2024-01-14",
        "notes": "Looking for automation solutions",
        "orders": [
            {"id": "ORD-005", "date": "2024-01-12", "amount": 3500, "status": "Shipped", "product": "Automation Tools"}
        ],
        "total_value": 3500,
        "tags": ["Manufacturing", "Automation", "Industrial"]
    }
]

# Initialize session state
if 'call_results' not in st.session_state:
    st.session_state.call_results = []
if 'call_monitoring' not in st.session_state:
    st.session_state.call_monitoring = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

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
    
    # Convert to list of dictionaries
    columns = ['id', 'timestamp', 'type', 'assistant_name', 'assistant_id', 
               'customer_phone', 'customer_name', 'customer_email', 'call_id', 
               'status', 'notes', 'transcript', 'recording_url', 'recording_path', 
               'duration', 'cost', 'created_at']
    
    return [dict(zip(columns, call)) for call in calls]

def get_call_analytics():
    """Get call analytics data."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    # Get daily stats
    cursor.execute('''
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as total_calls,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_calls,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_calls,
            AVG(duration) as avg_duration,
            SUM(cost) as total_cost
        FROM calls 
        WHERE created_at >= date('now', '-30 days')
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    ''')
    
    daily_stats = cursor.fetchall()
    
    # Get overall stats
    cursor.execute('''
        SELECT 
            COUNT(*) as total_calls,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_calls,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_calls,
            AVG(duration) as avg_duration,
            SUM(cost) as total_cost,
            COUNT(DISTINCT assistant_name) as unique_assistants
        FROM calls
    ''')
    
    overall_stats = cursor.fetchone()
    conn.close()
    
    return daily_stats, overall_stats

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
    
    if status_filter:
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
    
    # Convert to list of dictionaries
    columns = ['id', 'name', 'email', 'phone', 'company', 'position', 'lead_score', 
               'status', 'last_contact', 'notes', 'total_value', 'tags', 'created_at', 
               'updated_at', 'address', 'city', 'state', 'zip_code', 'country', 
               'website', 'industry', 'company_size', 'annual_revenue', 'source', 'assigned_to']
    
    return [dict(zip(columns, customer)) for customer in customers]

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

# Navigation
def render_navigation():
    """Render the navigation sidebar."""
    with st.sidebar:
        st.title("📞 Vapi Pro Enhanced")
        
        # API Key input with unique key
        api_key = st.text_input(
            "🔑 Vapi API Key", 
            type="password",
            value=st.session_state.api_key,
            help="Your Vapi API key",
            key="sidebar_api_key"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
        
        # API Connection Status
        if api_key:
            if st.button("🔍 Test Connection", key="sidebar_test_connection"):
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
        
        selected_page = st.radio("Navigation", pages, key="sidebar_nav_radio")
        
        # Update current page
        if selected_page != st.session_state.current_page:
            st.session_state.current_page = selected_page
        
        st.divider()
        
        # Quick stats including CRM
        if api_key:
            calls = get_calls_from_db(limit=10)
            customers = get_customers_from_db(limit=10)
            
            st.metric("Recent Calls", len(calls))
            st.metric("Total Customers", len(customers))
            
            if calls:
                completed_calls = len([c for c in calls if c['status'] == 'completed'])
                st.metric("Success Rate", f"{(completed_calls/len(calls)*100):.1f}%")

def render_dashboard():
    """Render the dashboard page."""
    st.title("📊 Dashboard")
    st.markdown("Welcome to your Vapi Outbound Calling dashboard")
    
    # Get analytics data
    daily_stats, overall_stats = get_call_analytics()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    if overall_stats:
        with col1:
            st.metric("Total Calls", overall_stats[0] or 0)
        with col2:
            st.metric("Successful Calls", overall_stats[1] or 0)
        with col3:
            success_rate = (overall_stats[1] / overall_stats[0] * 100) if overall_stats[0] > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col4:
            st.metric("Total Cost", f"${overall_stats[4] or 0:.2f}")
    
    # Recent activity
    st.subheader("📈 Recent Activity")
    
    if daily_stats:
        # Create daily activity chart
        df_daily = pd.DataFrame(daily_stats, columns=['date', 'total_calls', 'successful_calls', 'failed_calls', 'avg_duration', 'total_cost'])
        
        fig = px.line(df_daily, x='date', y='total_calls', title='Daily Call Volume')
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent calls
    st.subheader("📞 Recent Calls")
    recent_calls = get_calls_from_db(limit=5)
    
    if recent_calls:
        for i, call in enumerate(recent_calls):
            with st.expander(f"📞 {call['customer_phone']} - {call['status'].upper()}", key=f"dashboard_call_{i}"):
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
        if st.button("📞 Make Single Call", type="primary", key="dashboard_make_call"):
            st.session_state.current_page = "📞 Make Calls"
            st.rerun()
    
    with col2:
        if st.button("📋 View Call History", key="dashboard_call_history"):
            st.session_state.current_page = "📋 Call History"
            st.rerun()
    
    with col3:
        if st.button("🤖 Manage Assistants", key="dashboard_assistants"):
            st.session_state.current_page = "🤖 Assistant Manager"
            st.rerun()

def render_make_calls():
    """Render the make calls page."""
    st.title("📞 Make Calls")
    st.markdown("Enhanced outbound calling with CRM integration")
    
    # Check if customer was selected from CRM
    selected_customer = st.session_state.get('selected_customer_for_call')
    
    if selected_customer:
        st.info(f"📋 Selected customer: {selected_customer['name']} ({selected_customer['phone']})")
        if st.button("❌ Clear Selection", key="clear_customer_selection"):
            st.session_state.selected_customer_for_call = None
            st.rerun()
    
    # Call type selection
    col1, col2 = st.columns(2)
    
    with col1:
        call_type = st.radio(
            "Select calling mode:",
            ["Single Call", "Bulk Calls"],
            help="Choose your calling approach",
            key="call_type_selection"
        )
    
    with col2:
        # Assistant selection
        assistant_name = st.selectbox(
            "Choose Assistant",
            options=list(ASSISTANTS.keys()),
            help="Select from your pre-configured assistants",
            key="assistant_selection"
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
            customer_number = st.text_input("Customer Phone Number", placeholder="+1234567890", key="single_call_phone")
            customer_name = st.text_input("Customer Name", placeholder="John Doe", key="single_call_name")
            customer_email = st.text_input("Customer Email", placeholder="john@example.com", key="single_call_email")
        
        customer_notes = st.text_area("Call Notes", placeholder="Purpose of call, talking points...", key="single_call_notes")
        
        if st.button("📞 Make Call", type="primary", disabled=not all([st.session_state.api_key, customer_number]), key="make_single_call"):
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
            ["Text Input", "Upload CSV"],
            horizontal=True,
            key="bulk_input_method"
        )
        
        customer_numbers = []
        
        if bulk_input_method == "Text Input":
            bulk_numbers_text = st.text_area(
                "Phone Numbers (one per line)",
                placeholder="+1234567890\n+0987654321\n+1122334455",
                height=150,
                key="bulk_numbers_text"
            )
            
            if bulk_numbers_text:
                lines = bulk_numbers_text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and validate_phone_number(line):
                        customer_numbers.append(line)
                st.info(f"Found {len(customer_numbers)} valid phone numbers")
        
        elif bulk_input_method == "Upload CSV":
            uploaded_file = st.file_uploader("Upload CSV file", type=['csv'], key="bulk_csv_upload")
            
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
        
        # Bulk call execution
        if customer_numbers and st.button("📞 Make Bulk Calls", type="primary", key="make_bulk_calls"):
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
    """Render the CRM dashboard page."""
    st.title("👥 CRM Dashboard")
    st.markdown("Manage your customers, orders, and relationships")
    
    # Load demo customers if database is empty
    customers = get_customers_from_db(limit=5)
    if not customers:
        if st.button("🎯 Load Demo Customers", key="load_demo_customers"):
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
    
    # Recent customers and quick actions
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🆕 Recent Customers")
        recent_customers = get_customers_from_db(limit=5)
        
        for i, customer in enumerate(recent_customers):
            with st.expander(f"👤 {customer['name']} - {customer['company']}", key=f"crm_customer_{i}"):
                st.write(f"**Status:** {customer['status']}")
                st.write(f"**Lead Score:** {customer['lead_score']}/100")
                st.write(f"**Phone:** {customer['phone']}")
                st.write(f"**Total Value:** ${customer['total_value'] or 0:,.2f}")
                
                if st.button(f"📞 Call {customer['name']}", key=f"call_customer_{i}"):
                    st.session_state.selected_customer_for_call = customer
                    st.session_state.current_page = "📞 Make Calls"
                    st.rerun()
    
    with col2:
        st.subheader("🚀 Quick Actions")
        
        if st.button("➕ Add New Customer", type="primary", key="add_new_customer"):
            st.session_state.show_add_customer = True
        
        if st.button("📋 View All Customers", key="view_all_customers"):
            st.session_state.current_page = "👥 CRM Manager"
            st.rerun()

def render_call_history():
    """Render the call history page."""
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
    
    # Call history table
    if calls:
        st.subheader("📞 Call Records")
        
        for i, call in enumerate(calls):
            with st.expander(f"📞 {call['customer_phone']} - {call['status'].upper()}", key=f"call_history_{i}"):
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
                        if st.button(f"📝 View Transcript", key=f"transcript_{i}"):
                            st.session_state.viewing_transcript = call['id']
                            st.session_state.current_page = "📝 Transcripts"
                            st.rerun()
                    
                    if call['recording_path']:
                        if st.button(f"🎵 Play Recording", key=f"recording_{i}"):
                            st.session_state.viewing_recording = call['id']
                            st.session_state.current_page = "🎵 Recordings"
                            st.rerun()
                
                if call['notes']:
                    st.write(f"**Notes:** {call['notes']}")
    else:
        st.info("No calls found.")

def render_transcripts():
    """Render the transcripts page."""
    st.title("📝 Transcripts")
    st.markdown("View, search, and manage call transcripts")
    
    # Get calls with transcripts
    calls_with_transcripts = [c for c in get_calls_from_db() if c['transcript']]
    
    st.write(f"Found {len(calls_with_transcripts)} transcripts")
    
    if calls_with_transcripts:
        for i, call in enumerate(calls_with_transcripts):
            with st.expander(f"📝 {call['customer_phone']} - {call['timestamp'][:16] if call['timestamp'] else 'N/A'}", key=f"transcript_{i}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Show first 200 characters of transcript
                    preview = call['transcript'][:200] + "..." if len(call['transcript']) > 200 else call['transcript']
                    st.write(f"**Preview:** {preview}")
                    st.write(f"**Assistant:** {call['assistant_name']}")
                    st.write(f"**Duration:** {call['duration'] or 0}s")
                
                with col2:
                    if st.button("👁️ View Full", key=f"view_transcript_{i}"):
                        st.text_area("Full Transcript", value=call['transcript'], height=300, key=f"full_transcript_{i}")
    else:
        st.info("No transcripts found.")

def render_recordings():
    """Render the recordings page."""
    st.title("🎵 Recordings")
    st.markdown("Listen to and manage call recordings")
    
    # Get calls with recordings
    calls_with_recordings = [c for c in get_calls_from_db() 
                           if c['recording_url'] or c['recording_path']]
    
    st.write(f"Found {len(calls_with_recordings)} recordings")
    
    if calls_with_recordings:
        for i, call in enumerate(calls_with_recordings):
            with st.expander(f"🎵 {call['customer_phone']} - {call['timestamp'][:16] if call['timestamp'] else 'N/A'}", key=f"recording_{i}"):
                col1, col2 = st.columns([2, 1])
                
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
    else:
        st.info("No recordings found.")

def render_assistant_manager():
    """Render the assistant manager page."""
    st.title("🤖 Assistant Manager")
    st.markdown("Create and manage your AI assistants")
    
    # Display predefined assistants
    st.subheader("📋 Your Assistants")
    
    for i, (name, assistant_id) in enumerate(ASSISTANTS.items()):
        with st.expander(f"🤖 {name}", key=f"assistant_{i}"):
            st.code(f"ID: {assistant_id}")

def render_analytics():
    """Render the analytics page."""
    st.title("📈 Analytics")
    st.markdown("Comprehensive insights into your calling performance")
    
    # Get analytics data
    daily_stats, overall_stats = get_call_analytics()
    calls = get_calls_from_db()
    customers = get_customers_from_db()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    if overall_stats:
        with col1:
            st.metric("Total Calls", overall_stats[0] or 0)
        with col2:
            st.metric("Success Rate", f"{(overall_stats[1] / overall_stats[0] * 100) if overall_stats[0] > 0 else 0:.1f}%")
        with col3:
            st.metric("Avg Duration", f"{overall_stats[3] or 0:.1f}s")
        with col4:
            st.metric("Total Cost", f"${overall_stats[4] or 0:.2f}")
    
    # Charts and visualizations
    if daily_stats:
        df_daily = pd.DataFrame(daily_stats, columns=['date', 'total_calls', 'successful_calls', 'failed_calls', 'avg_duration', 'total_cost'])
        
        # Call volume over time
        st.subheader("📊 Call Volume Over Time")
        fig = px.line(df_daily, x='date', y='total_calls', title='Daily Call Volume')
        st.plotly_chart(fig, use_container_width=True)

def render_settings():
    """Render the settings page."""
    st.title("⚙️ Settings")
    st.markdown("Configure your Vapi application settings")
    
    # API Settings
    st.subheader("🔑 API Configuration")
    
    with st.expander("API Settings"):
        current_api_key = st.session_state.api_key
        new_api_key = st.text_input("Vapi API Key", value=current_api_key, type="password", key="settings_api_key")
        
        if new_api_key != current_api_key:
            st.session_state.api_key = new_api_key
            st.success("API key updated!")

# Main function with proper routing
def main():
    """Main application function with complete routing."""
    render_navigation()
    
    # Route to appropriate page
    page = st.session_state.current_page
    
    if "Dashboard" in page and "CRM" not in page:
        render_dashboard()
    elif "CRM Dashboard" in page:
        render_crm_dashboard()
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



