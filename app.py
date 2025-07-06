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
    
    # Create assistants table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assistants (
            id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            model TEXT,
            voice TEXT,
            first_message TEXT,
            system_message TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Create analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id TEXT PRIMARY KEY,
            date TEXT,
            total_calls INTEGER,
            successful_calls INTEGER,
            failed_calls INTEGER,
            total_duration INTEGER,
            total_cost REAL,
            avg_duration REAL
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_database()

# Static configuration
STATIC_PHONE_NUMBER_ID = "431f1dc9-4888-41e6-933c-4fa2e97d34d6"

# Predefined assistants (expanded)
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

def get_assistants_from_api(api_key: str) -> Dict:
    """Get all assistants from Vapi API."""
    try:
        url = "https://api.vapi.ai/assistant"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_assistant(api_key: str, assistant_data: Dict) -> Dict:
    """Create a new assistant via Vapi API."""
    try:
        url = "https://api.vapi.ai/assistant"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        response = requests.post(url, headers=headers, json=assistant_data, timeout=30)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_assistant(api_key: str, assistant_id: str, assistant_data: Dict) -> Dict:
    """Update an existing assistant via Vapi API."""
    try:
        url = f"https://api.vapi.ai/assistant/{assistant_id}"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        response = requests.patch(url, headers=headers, json=assistant_data, timeout=30)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_phone_numbers(api_key: str) -> Dict:
    """Get all phone numbers from Vapi API."""
    try:
        url = "https://api.vapi.ai/phone-number"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_call_details(api_key: str, call_id: str) -> Dict:
    """Get detailed call information including transcript and recording."""
    try:
        url = f"https://api.vapi.ai/call/{call_id}"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def download_call_recording(api_key: str, recording_url: str, call_id: str) -> Dict:
    """Download call recording from URL and save locally."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
        }
        
        response = requests.get(recording_url, headers=headers, timeout=60)
        response.raise_for_status()
        
        # Create recordings directory if it doesn't exist
        os.makedirs("recordings", exist_ok=True)
        
        # Save recording locally
        filename = f"recordings/call_{call_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        return {"success": True, "data": response.content, "filename": filename}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

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

def parse_bulk_numbers(text: str) -> List[str]:
    """Parse bulk phone numbers from text input."""
    try:
        clean_text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\r', '\t'])
        lines = clean_text.strip().split('\n')
        numbers = []
        
        for line in lines:
            line = line.strip()
            if line:
                clean_line = ''.join(char for char in line if char.isprintable()).strip()
                if clean_line and validate_phone_number(clean_line):
                    numbers.append(clean_line)
        return numbers
    except Exception:
        return []

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
        
        # API Key input
        api_key = st.text_input(
            "🔑 Vapi API Key", 
            type="password",
            value=st.session_state.api_key,
            help="Your Vapi API key"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
        
        # API Connection Status
        if api_key:
            if st.button("🔍 Test Connection"):
                with st.spinner("Testing..."):
                    result = test_api_connection(api_key)
                    if result["success"]:
                        st.success("✅ Connected!")
                    else:
                        st.error(f"❌ {result['error']}")
        
        st.divider()
        
        # Navigation menu
        pages = [
            "📊 Dashboard",
            "📞 Make Calls", 
            "📋 Call History",
            "📝 Transcripts",
            "🎵 Recordings",
            "🤖 Assistant Manager",
            "📈 Analytics",
            "⚙️ Settings"
        ]
        
        selected_page = st.radio("Navigation", pages, key="nav_radio")
        
        # Update current page
        if selected_page != st.session_state.current_page:
            st.session_state.current_page = selected_page
        
        st.divider()
        
        # Quick stats
        if api_key:
            calls = get_calls_from_db(limit=10)
            st.metric("Recent Calls", len(calls))
            
            if calls:
                completed_calls = len([c for c in calls if c['status'] == 'completed'])
                st.metric("Success Rate", f"{(completed_calls/len(calls)*100):.1f}%")

# Page routing
def main():
    """Main application function."""
    render_navigation()
    
    # Route to appropriate page
    page = st.session_state.current_page
    
    if "Dashboard" in page:
        render_dashboard()
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
        
        # Success rate chart
        df_daily['success_rate'] = (df_daily['successful_calls'] / df_daily['total_calls'] * 100).fillna(0)
        fig2 = px.bar(df_daily, x='date', y='success_rate', title='Daily Success Rate (%)')
        st.plotly_chart(fig2, use_container_width=True)
    
    # Recent calls
    st.subheader("📞 Recent Calls")
    recent_calls = get_calls_from_db(limit=5)
    
    if recent_calls:
        for call in recent_calls:
            with st.expander(f"📞 {call['customer_phone']} - {call['status'].upper()}"):
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
        if st.button("📞 Make Single Call", type="primary"):
            st.session_state.current_page = "📞 Make Calls"
            st.rerun()
    
    with col2:
        if st.button("📋 View Call History"):
            st.session_state.current_page = "📋 Call History"
            st.rerun()
    
    with col3:
        if st.button("🤖 Manage Assistants"):
            st.session_state.current_page = "🤖 Assistant Manager"
            st.rerun()

if __name__ == "__main__":
    main()



# CRM and Customer Management Features

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
    },
    {
        "id": "cust_006",
        "name": "Lisa Anderson",
        "email": "lisa.a@healthcareplus.org",
        "phone": "+1234567895",
        "company": "Healthcare Plus",
        "position": "IT Director",
        "lead_score": 82,
        "status": "Hot Lead",
        "last_contact": "2024-01-16",
        "notes": "HIPAA compliance requirements",
        "orders": [
            {"id": "ORD-006", "date": "2024-01-08", "amount": 4200, "status": "Processing", "product": "Healthcare Suite"}
        ],
        "total_value": 4200,
        "tags": ["Healthcare", "Compliance", "Security"]
    },
    {
        "id": "cust_007",
        "name": "Robert Taylor",
        "email": "r.taylor@financefirm.com",
        "phone": "+1234567896",
        "company": "Taylor Finance",
        "position": "CFO",
        "lead_score": 88,
        "status": "Hot Lead",
        "last_contact": "2024-01-17",
        "notes": "Needs financial reporting tools",
        "orders": [
            {"id": "ORD-007", "date": "2024-01-15", "amount": 6000, "status": "Completed", "product": "Financial Suite"},
            {"id": "ORD-008", "date": "2024-01-18", "amount": 1500, "status": "Pending", "product": "Reporting Add-on"}
        ],
        "total_value": 7500,
        "tags": ["Finance", "High Value", "Enterprise"]
    },
    {
        "id": "cust_008",
        "name": "Jennifer Martinez",
        "email": "j.martinez@educationtech.edu",
        "phone": "+1234567897",
        "company": "Education Tech Institute",
        "position": "Technology Coordinator",
        "lead_score": 70,
        "status": "Warm Lead",
        "last_contact": "2024-01-11",
        "notes": "Educational discount applicable",
        "orders": [
            {"id": "ORD-009", "date": "2024-01-10", "amount": 2000, "status": "Completed", "product": "Education Package"}
        ],
        "total_value": 2000,
        "tags": ["Education", "Non-Profit", "Discount"]
    },
    {
        "id": "cust_009",
        "name": "Christopher Lee",
        "email": "c.lee@realestate.com",
        "phone": "+1234567898",
        "company": "Prime Real Estate",
        "position": "Broker",
        "lead_score": 75,
        "status": "Warm Lead",
        "last_contact": "2024-01-13",
        "notes": "Seasonal business, peak in spring",
        "orders": [
            {"id": "ORD-010", "date": "2024-01-05", "amount": 1800, "status": "Completed", "product": "CRM Package"}
        ],
        "total_value": 1800,
        "tags": ["Real Estate", "Seasonal", "CRM"]
    },
    {
        "id": "cust_010",
        "name": "Amanda White",
        "email": "a.white@consulting.biz",
        "phone": "+1234567899",
        "company": "White Consulting",
        "position": "Principal Consultant",
        "lead_score": 80,
        "status": "Hot Lead",
        "last_contact": "2024-01-19",
        "notes": "Multi-client deployment needed",
        "orders": [
            {"id": "ORD-011", "date": "2024-01-16", "amount": 3200, "status": "Processing", "product": "Consulting Suite"}
        ],
        "total_value": 3200,
        "tags": ["Consulting", "Multi-Client", "Professional Services"]
    },
    {
        "id": "cust_011",
        "name": "James Garcia",
        "email": "j.garcia@logistics.net",
        "phone": "+1234567800",
        "company": "Garcia Logistics",
        "position": "Operations Director",
        "lead_score": 73,
        "status": "Warm Lead",
        "last_contact": "2024-01-10",
        "notes": "Supply chain optimization focus",
        "orders": [
            {"id": "ORD-012", "date": "2024-01-08", "amount": 2800, "status": "Shipped", "product": "Logistics Suite"}
        ],
        "total_value": 2800,
        "tags": ["Logistics", "Supply Chain", "Operations"]
    },
    {
        "id": "cust_012",
        "name": "Michelle Thompson",
        "email": "m.thompson@restaurant.com",
        "phone": "+1234567801",
        "company": "Thompson's Restaurant Group",
        "position": "General Manager",
        "lead_score": 68,
        "status": "Cold Lead",
        "last_contact": "2024-01-07",
        "notes": "Multiple locations, needs unified system",
        "orders": [
            {"id": "ORD-013", "date": "2023-12-20", "amount": 1500, "status": "Completed", "product": "Restaurant POS"}
        ],
        "total_value": 1500,
        "tags": ["Restaurant", "Multi-Location", "POS"]
    },
    {
        "id": "cust_013",
        "name": "Kevin Rodriguez",
        "email": "k.rodriguez@autoparts.com",
        "phone": "+1234567802",
        "company": "Rodriguez Auto Parts",
        "position": "Owner",
        "lead_score": 76,
        "status": "Warm Lead",
        "last_contact": "2024-01-15",
        "notes": "Inventory management priority",
        "orders": [
            {"id": "ORD-014", "date": "2024-01-12", "amount": 2200, "status": "Processing", "product": "Inventory System"}
        ],
        "total_value": 2200,
        "tags": ["Automotive", "Inventory", "Small Business"]
    },
    {
        "id": "cust_014",
        "name": "Nicole Clark",
        "email": "n.clark@lawfirm.legal",
        "phone": "+1234567803",
        "company": "Clark & Associates Law",
        "position": "Managing Partner",
        "lead_score": 85,
        "status": "Hot Lead",
        "last_contact": "2024-01-18",
        "notes": "Document management and billing focus",
        "orders": [
            {"id": "ORD-015", "date": "2024-01-14", "amount": 4500, "status": "Completed", "product": "Legal Suite"}
        ],
        "total_value": 4500,
        "tags": ["Legal", "Document Management", "Professional"]
    },
    {
        "id": "cust_015",
        "name": "Daniel Lewis",
        "email": "d.lewis@construction.build",
        "phone": "+1234567804",
        "company": "Lewis Construction",
        "position": "Project Manager",
        "lead_score": 71,
        "status": "Warm Lead",
        "last_contact": "2024-01-12",
        "notes": "Project tracking and scheduling needs",
        "orders": [
            {"id": "ORD-016", "date": "2024-01-09", "amount": 3100, "status": "Shipped", "product": "Project Management Suite"}
        ],
        "total_value": 3100,
        "tags": ["Construction", "Project Management", "Scheduling"]
    },
    {
        "id": "cust_016",
        "name": "Rachel Walker",
        "email": "r.walker@fitness.gym",
        "phone": "+1234567805",
        "company": "Walker Fitness Centers",
        "position": "Franchise Owner",
        "lead_score": 69,
        "status": "Cold Lead",
        "last_contact": "2024-01-09",
        "notes": "Member management and billing",
        "orders": [
            {"id": "ORD-017", "date": "2024-01-06", "amount": 1900, "status": "Completed", "product": "Fitness Management"}
        ],
        "total_value": 1900,
        "tags": ["Fitness", "Membership", "Franchise"]
    },
    {
        "id": "cust_017",
        "name": "Steven Hall",
        "email": "s.hall@insurance.protect",
        "phone": "+1234567806",
        "company": "Hall Insurance Agency",
        "position": "Agency Owner",
        "lead_score": 77,
        "status": "Warm Lead",
        "last_contact": "2024-01-16",
        "notes": "Client management and policy tracking",
        "orders": [
            {"id": "ORD-018", "date": "2024-01-13", "amount": 2600, "status": "Processing", "product": "Insurance CRM"}
        ],
        "total_value": 2600,
        "tags": ["Insurance", "Client Management", "Policy Tracking"]
    },
    {
        "id": "cust_018",
        "name": "Karen Young",
        "email": "k.young@veterinary.care",
        "phone": "+1234567807",
        "company": "Young Veterinary Clinic",
        "position": "Practice Manager",
        "lead_score": 74,
        "status": "Warm Lead",
        "last_contact": "2024-01-14",
        "notes": "Patient records and appointment scheduling",
        "orders": [
            {"id": "ORD-019", "date": "2024-01-11", "amount": 2300, "status": "Completed", "product": "Veterinary Suite"}
        ],
        "total_value": 2300,
        "tags": ["Veterinary", "Healthcare", "Appointments"]
    },
    {
        "id": "cust_019",
        "name": "Brian King",
        "email": "b.king@photography.studio",
        "phone": "+1234567808",
        "company": "King Photography Studio",
        "position": "Owner/Photographer",
        "lead_score": 66,
        "status": "Cold Lead",
        "last_contact": "2024-01-08",
        "notes": "Client galleries and booking system",
        "orders": [
            {"id": "ORD-020", "date": "2023-12-28", "amount": 1100, "status": "Completed", "product": "Photography Suite"}
        ],
        "total_value": 1100,
        "tags": ["Photography", "Creative", "Booking"]
    },
    {
        "id": "cust_020",
        "name": "Angela Wright",
        "email": "a.wright@accounting.numbers",
        "phone": "+1234567809",
        "company": "Wright Accounting Services",
        "position": "CPA",
        "lead_score": 81,
        "status": "Hot Lead",
        "last_contact": "2024-01-17",
        "notes": "Tax season preparation, client portal needed",
        "orders": [
            {"id": "ORD-021", "date": "2024-01-15", "amount": 3800, "status": "Processing", "product": "Accounting Suite"}
        ],
        "total_value": 3800,
        "tags": ["Accounting", "Tax", "Client Portal"]
    },
    {
        "id": "cust_021",
        "name": "Gregory Green",
        "email": "g.green@landscaping.earth",
        "phone": "+1234567810",
        "company": "Green Landscaping Co",
        "position": "Business Owner",
        "lead_score": 70,
        "status": "Warm Lead",
        "last_contact": "2024-01-13",
        "notes": "Seasonal business, route optimization",
        "orders": [
            {"id": "ORD-022", "date": "2024-01-10", "amount": 1700, "status": "Shipped", "product": "Field Service Suite"}
        ],
        "total_value": 1700,
        "tags": ["Landscaping", "Seasonal", "Field Service"]
    },
    {
        "id": "cust_022",
        "name": "Stephanie Adams",
        "email": "s.adams@dental.smile",
        "phone": "+1234567811",
        "company": "Adams Dental Practice",
        "position": "Office Manager",
        "lead_score": 79,
        "status": "Warm Lead",
        "last_contact": "2024-01-16",
        "notes": "Patient scheduling and insurance billing",
        "orders": [
            {"id": "ORD-023", "date": "2024-01-12", "amount": 2900, "status": "Processing", "product": "Dental Practice Suite"}
        ],
        "total_value": 2900,
        "tags": ["Dental", "Healthcare", "Insurance"]
    },
    {
        "id": "cust_023",
        "name": "Timothy Baker",
        "email": "t.baker@bakery.fresh",
        "phone": "+1234567812",
        "company": "Baker's Fresh Bakery",
        "position": "Owner",
        "lead_score": 63,
        "status": "Cold Lead",
        "last_contact": "2024-01-09",
        "notes": "Inventory and ordering system needed",
        "orders": [
            {"id": "ORD-024", "date": "2024-01-07", "amount": 1300, "status": "Completed", "product": "Retail POS"}
        ],
        "total_value": 1300,
        "tags": ["Food Service", "Retail", "Inventory"]
    },
    {
        "id": "cust_024",
        "name": "Melissa Nelson",
        "email": "m.nelson@spa.relax",
        "phone": "+1234567813",
        "company": "Nelson Day Spa",
        "position": "Spa Director",
        "lead_score": 72,
        "status": "Warm Lead",
        "last_contact": "2024-01-15",
        "notes": "Appointment booking and customer management",
        "orders": [
            {"id": "ORD-025", "date": "2024-01-13", "amount": 2100, "status": "Processing", "product": "Spa Management Suite"}
        ],
        "total_value": 2100,
        "tags": ["Spa", "Wellness", "Appointments"]
    },
    {
        "id": "cust_025",
        "name": "Anthony Carter",
        "email": "a.carter@security.safe",
        "phone": "+1234567814",
        "company": "Carter Security Solutions",
        "position": "Security Director",
        "lead_score": 84,
        "status": "Hot Lead",
        "last_contact": "2024-01-18",
        "notes": "Enterprise security monitoring system",
        "orders": [
            {"id": "ORD-026", "date": "2024-01-16", "amount": 5500, "status": "Processing", "product": "Security Suite"}
        ],
        "total_value": 5500,
        "tags": ["Security", "Enterprise", "Monitoring"]
    }
]

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

# Enhanced database initialization for CRM
def init_crm_database():
    """Initialize CRM database tables."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
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

# Initialize CRM database
init_crm_database()

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

def update_customer(customer_id, customer_data):
    """Update customer information."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    # Build update query dynamically
    fields = []
    values = []
    
    for key, value in customer_data.items():
        if key != 'id':
            fields.append(f'{key} = ?')
            values.append(value)
    
    fields.append('updated_at = ?')
    values.append(datetime.now().isoformat())
    values.append(customer_id)
    
    query = f'UPDATE customers SET {", ".join(fields)} WHERE id = ?'
    cursor.execute(query, values)
    
    conn.commit()
    conn.close()

def add_customer_interaction(customer_id, interaction_data):
    """Add a customer interaction record."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    interaction_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO customer_interactions 
        (id, customer_id, interaction_type, interaction_date, notes, outcome, next_action, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        interaction_id,
        customer_id,
        interaction_data.get('type'),
        interaction_data.get('date'),
        interaction_data.get('notes'),
        interaction_data.get('outcome'),
        interaction_data.get('next_action'),
        interaction_data.get('created_by'),
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()
    return interaction_id

def get_customer_interactions(customer_id):
    """Get interactions for a specific customer."""
    conn = sqlite3.connect('vapi_calls.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM customer_interactions 
        WHERE customer_id = ? 
        ORDER BY interaction_date DESC
    ''', (customer_id,))
    
    interactions = cursor.fetchall()
    conn.close()
    
    columns = ['id', 'customer_id', 'interaction_type', 'interaction_date', 
               'notes', 'outcome', 'next_action', 'created_by', 'created_at']
    
    return [dict(zip(columns, interaction)) for interaction in interactions]

def export_customers_to_csv():
    """Export customers to CSV format."""
    customers = get_customers_from_db()
    if not customers:
        return ""
    
    df = pd.DataFrame(customers)
    return df.to_csv(index=False)

def import_customers_from_csv(csv_data):
    """Import customers from CSV data."""
    try:
        df = pd.read_csv(BytesIO(csv_data.encode()))
        
        conn = sqlite3.connect('vapi_calls.db')
        cursor = conn.cursor()
        
        imported_count = 0
        for _, row in df.iterrows():
            customer_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO customers 
                (id, name, email, phone, company, position, lead_score, status, 
                 notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer_id,
                row.get('name', ''),
                row.get('email', ''),
                row.get('phone', ''),
                row.get('company', ''),
                row.get('position', ''),
                row.get('lead_score', 0),
                row.get('status', 'Cold Lead'),
                row.get('notes', ''),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            imported_count += 1
        
        conn.commit()
        conn.close()
        
        return {"success": True, "count": imported_count}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

# Google Sheets integration functions
def create_google_sheets_template():
    """Create a Google Sheets template URL for customer data."""
    # This would typically involve Google Sheets API, but for demo purposes,
    # we'll provide a template structure
    template_data = {
        "spreadsheet_id": "demo_template",
        "template_url": "https://docs.google.com/spreadsheets/d/your-sheet-id/edit",
        "columns": [
            "name", "email", "phone", "company", "position", 
            "lead_score", "status", "notes", "tags"
        ],
        "instructions": [
            "1. Copy this template to your Google Drive",
            "2. Fill in customer information",
            "3. Export as CSV and upload to the CRM",
            "4. Or use the Google Sheets API integration (coming soon)"
        ]
    }
    return template_data

def render_crm_dashboard():
    """Render the CRM dashboard page."""
    st.title("👥 CRM Dashboard")
    st.markdown("Manage your customers, orders, and relationships")
    
    # Load demo customers if database is empty
    customers = get_customers_from_db(limit=5)
    if not customers:
        if st.button("🎯 Load Demo Customers"):
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
        
        for customer in recent_customers:
            with st.expander(f"👤 {customer['name']} - {customer['company']}"):
                st.write(f"**Status:** {customer['status']}")
                st.write(f"**Lead Score:** {customer['lead_score']}/100")
                st.write(f"**Phone:** {customer['phone']}")
                st.write(f"**Total Value:** ${customer['total_value'] or 0:,.2f}")
                
                if st.button(f"📞 Call {customer['name']}", key=f"call_{customer['id']}"):
                    st.session_state.selected_customer_for_call = customer
                    st.session_state.current_page = "📞 Make Calls"
                    st.rerun()
    
    with col2:
        st.subheader("🚀 Quick Actions")
        
        if st.button("➕ Add New Customer", type="primary"):
            st.session_state.show_add_customer = True
        
        if st.button("📋 View All Customers"):
            st.session_state.current_page = "👥 CRM Manager"
            st.rerun()
        
        if st.button("📊 Customer Analytics"):
            st.session_state.current_page = "📈 Analytics"
            st.rerun()
        
        if st.button("📤 Export Customers"):
            csv_data = export_customers_to_csv()
            if csv_data:
                st.download_button(
                    label="💾 Download CSV",
                    data=csv_data,
                    file_name=f"customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    # Add customer form
    if st.session_state.get('show_add_customer', False):
        st.subheader("➕ Add New Customer")
        
        with st.form("add_customer_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Customer Name*")
                email = st.text_input("Email*")
                phone = st.text_input("Phone*")
                company = st.text_input("Company")
                position = st.text_input("Position")
            
            with col2:
                status = st.selectbox("Status", CUSTOMER_STATUSES)
                lead_score = st.slider("Lead Score", 0, 100, 50)
                tags = st.text_input("Tags (comma-separated)")
                notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("Add Customer")
            
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
    """Render the full CRM management page."""
    st.title("👥 CRM Manager")
    st.markdown("Complete customer relationship management")
    
    # Search and filter controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search customers", placeholder="Name, email, company, or phone")
    
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All"] + CUSTOMER_STATUSES)
        if status_filter == "All":
            status_filter = None
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Updated", "Name", "Lead Score", "Total Value"])
    
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
    for customer in customers:
        with st.expander(f"👤 {customer['name']} - {customer['company']} ({customer['status']})"):
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
                    for order in orders[:3]:  # Show last 3 orders
                        status_color = {
                            'Completed': '🟢',
                            'Processing': '🟡', 
                            'Pending': '🟠',
                            'Cancelled': '🔴'
                        }.get(order['status'], '⚪')
                        
                        st.write(f"{status_color} {order['id']}: ${order['amount']:,.2f} ({order['status']})")
            
            with col3:
                # Action buttons
                if st.button(f"📞 Call", key=f"call_{customer['id']}"):
                    st.session_state.selected_customer_for_call = customer
                    st.session_state.current_page = "📞 Make Calls"
                    st.rerun()
                
                if st.button(f"✏️ Edit", key=f"edit_{customer['id']}"):
                    st.session_state.editing_customer = customer
                
                if st.button(f"📋 Orders", key=f"orders_{customer['id']}"):
                    st.session_state.viewing_customer_orders = customer['id']
                
                if st.button(f"💬 Interactions", key=f"interactions_{customer['id']}"):
                    st.session_state.viewing_customer_interactions = customer['id']
    
    # Customer editing form
    if st.session_state.get('editing_customer'):
        customer = st.session_state.editing_customer
        st.subheader(f"✏️ Edit Customer: {customer['name']}")
        
        with st.form("edit_customer_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Name", value=customer['name'])
                email = st.text_input("Email", value=customer['email'])
                phone = st.text_input("Phone", value=customer['phone'])
                company = st.text_input("Company", value=customer['company'] or '')
                position = st.text_input("Position", value=customer['position'] or '')
            
            with col2:
                status = st.selectbox("Status", CUSTOMER_STATUSES, 
                                    index=CUSTOMER_STATUSES.index(customer['status']) if customer['status'] in CUSTOMER_STATUSES else 0)
                lead_score = st.slider("Lead Score", 0, 100, customer['lead_score'] or 50)
                tags = st.text_input("Tags", value=customer['tags'] or '')
                notes = st.text_area("Notes", value=customer['notes'] or '')
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save Changes"):
                    update_data = {
                        'name': name,
                        'email': email,
                        'phone': phone,
                        'company': company,
                        'position': position,
                        'status': status,
                        'lead_score': lead_score,
                        'tags': tags,
                        'notes': notes
                    }
                    
                    update_customer(customer['id'], update_data)
                    st.success("Customer updated successfully!")
                    st.session_state.editing_customer = None
                    st.rerun()
            
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.editing_customer = None
                    st.rerun()
    
    # Customer orders view
    if st.session_state.get('viewing_customer_orders'):
        customer_id = st.session_state.viewing_customer_orders
        customer = next((c for c in customers if c['id'] == customer_id), None)
        
        if customer:
            st.subheader(f"📋 Orders for {customer['name']}")
            orders = get_customer_orders(customer_id)
            
            if orders:
                # Orders summary
                total_orders = len(orders)
                total_value = sum([o['amount'] for o in orders])
                completed_orders = len([o for o in orders if o['status'] == 'Completed'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Orders", total_orders)
                with col2:
                    st.metric("Total Value", f"${total_value:,.2f}")
                with col3:
                    st.metric("Completed", completed_orders)
                
                # Orders table
                df_orders = pd.DataFrame(orders)
                st.dataframe(df_orders[['id', 'order_date', 'product', 'amount', 'status']], use_container_width=True)
                
                # Add new order form
                with st.expander("➕ Add New Order"):
                    with st.form("add_order_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            product = st.text_input("Product/Service")
                            amount = st.number_input("Amount", min_value=0.0, step=0.01)
                            status = st.selectbox("Status", ORDER_STATUSES)
                        
                        with col2:
                            order_date = st.date_input("Order Date", datetime.now().date())
                            quantity = st.number_input("Quantity", min_value=1, value=1)
                            order_notes = st.text_area("Order Notes")
                        
                        if st.form_submit_button("Add Order"):
                            order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            
                            conn = sqlite3.connect('vapi_calls.db')
                            cursor = conn.cursor()
                            
                            cursor.execute('''
                                INSERT INTO orders 
                                (id, customer_id, order_date, amount, status, product, quantity, notes, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                order_id, customer_id, order_date.isoformat(), amount, status, 
                                product, quantity, order_notes, datetime.now().isoformat(), datetime.now().isoformat()
                            ))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success("Order added successfully!")
                            st.rerun()
            else:
                st.info("No orders found for this customer.")
            
            if st.button("⬅️ Back to Customers"):
                st.session_state.viewing_customer_orders = None
                st.rerun()
    
    # Customer interactions view
    if st.session_state.get('viewing_customer_interactions'):
        customer_id = st.session_state.viewing_customer_interactions
        customer = next((c for c in customers if c['id'] == customer_id), None)
        
        if customer:
            st.subheader(f"💬 Interactions for {customer['name']}")
            interactions = get_customer_interactions(customer_id)
            
            # Add new interaction form
            with st.expander("➕ Add New Interaction"):
                with st.form("add_interaction_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        interaction_type = st.selectbox("Type", ["Call", "Email", "Meeting", "Demo", "Follow-up", "Other"])
                        interaction_date = st.date_input("Date", datetime.now().date())
                        outcome = st.selectbox("Outcome", ["Positive", "Neutral", "Negative", "No Response"])
                    
                    with col2:
                        notes = st.text_area("Notes")
                        next_action = st.text_input("Next Action")
                        created_by = st.text_input("Created By", value="System User")
                    
                    if st.form_submit_button("Add Interaction"):
                        interaction_data = {
                            'type': interaction_type,
                            'date': interaction_date.isoformat(),
                            'notes': notes,
                            'outcome': outcome,
                            'next_action': next_action,
                            'created_by': created_by
                        }
                        
                        add_customer_interaction(customer_id, interaction_data)
                        st.success("Interaction added successfully!")
                        st.rerun()
            
            # Display interactions
            if interactions:
                for interaction in interactions:
                    with st.expander(f"{interaction['interaction_type']} - {interaction['interaction_date']} ({interaction['outcome']})"):
                        st.write(f"**Notes:** {interaction['notes']}")
                        if interaction['next_action']:
                            st.write(f"**Next Action:** {interaction['next_action']}")
                        st.write(f"**Created by:** {interaction['created_by']}")
                        st.write(f"**Date:** {interaction['created_at'][:16]}")
            else:
                st.info("No interactions recorded for this customer.")
            
            if st.button("⬅️ Back to Customers"):
                st.session_state.viewing_customer_interactions = None
                st.rerun()

# Update the navigation to include CRM pages
def render_navigation():
    """Render the navigation sidebar with CRM features."""
    with st.sidebar:
        st.title("📞 Vapi Pro Enhanced")
        
        # API Key input
        api_key = st.text_input(
            "🔑 Vapi API Key", 
            type="password",
            value=st.session_state.api_key,
            help="Your Vapi API key"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
        
        # API Connection Status
        if api_key:
            if st.button("🔍 Test Connection"):
                with st.spinner("Testing..."):
                    result = test_api_connection(api_key)
                    if result["success"]:
                        st.success("✅ Connected!")
                    else:
                        st.error(f"❌ {result['error']}")
        
        st.divider()
        
        # Navigation menu with CRM
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
        
        selected_page = st.radio("Navigation", pages, key="nav_radio")
        
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

# Update the main function to include CRM routing
def main():
    """Main application function with CRM support."""
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



def render_make_calls():
    """Render the enhanced make calls page with CRM integration."""
    st.title("📞 Make Calls")
    st.markdown("Enhanced outbound calling with CRM integration")
    
    # Check if customer was selected from CRM
    selected_customer = st.session_state.get('selected_customer_for_call')
    
    if selected_customer:
        st.info(f"📋 Selected customer: {selected_customer['name']} ({selected_customer['phone']})")
        if st.button("❌ Clear Selection"):
            st.session_state.selected_customer_for_call = None
            st.rerun()
    
    # Call type selection
    col1, col2 = st.columns(2)
    
    with col1:
        call_type = st.radio(
            "Select calling mode:",
            ["Single Call", "Bulk Calls", "CRM Campaign"],
            help="Choose your calling approach"
        )
    
    with col2:
        # Assistant selection
        assistant_name = st.selectbox(
            "Choose Assistant",
            options=list(ASSISTANTS.keys()),
            help="Select from your pre-configured assistants"
        )
        assistant_id = ASSISTANTS[assistant_name]
    
    # Scheduling options
    with st.expander("⏰ Scheduling Options"):
        schedule_call = st.checkbox("Schedule call for later")
        
        if schedule_call:
            col1, col2 = st.columns(2)
            with col1:
                earliest_date = st.date_input("Earliest Date", datetime.now().date())
                earliest_time = st.time_input("Earliest Time", datetime.now().time())
            with col2:
                latest_date = st.date_input("Latest Date", datetime.now().date())
                latest_time = st.time_input("Latest Time", (datetime.now() + timedelta(hours=1)).time())
    
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
            customer_number = st.text_input("Customer Phone Number", placeholder="+1234567890")
            customer_name = st.text_input("Customer Name", placeholder="John Doe")
            customer_email = st.text_input("Customer Email", placeholder="john@example.com")
        
        customer_notes = st.text_area("Call Notes", placeholder="Purpose of call, talking points...")
        
        if st.button("📞 Make Call", type="primary", disabled=not all([st.session_state.api_key, customer_number])):
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
                
                # Prepare schedule plan
                schedule_plan = None
                if schedule_call:
                    earliest_datetime = datetime.combine(earliest_date, earliest_time)
                    schedule_plan = {"earliestAt": earliest_datetime.isoformat() + "Z"}
                    if latest_date and latest_time:
                        latest_datetime = datetime.combine(latest_date, latest_time)
                        schedule_plan["latestAt"] = latest_datetime.isoformat() + "Z"
                
                # Make the call
                with st.spinner("Making call..."):
                    result = make_vapi_call(
                        api_key=st.session_state.api_key,
                        assistant_id=assistant_id,
                        customers=customers,
                        schedule_plan=schedule_plan
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
                        
                        # Update customer interaction if from CRM
                        if selected_customer:
                            interaction_data = {
                                'type': 'Call',
                                'date': datetime.now().date().isoformat(),
                                'notes': f"Outbound call made using {assistant_name}. Call ID: {call_id}",
                                'outcome': 'Initiated',
                                'next_action': 'Follow up after call completion',
                                'created_by': 'Vapi System'
                            }
                            add_customer_interaction(selected_customer['id'], interaction_data)
                        
                        st.json(call_data)
                        
                        # Start monitoring
                        st.session_state.call_monitoring[call_id] = {
                            "api_key": st.session_state.api_key,
                            "start_time": datetime.now(),
                            "customer": customer_number,
                            "assistant": assistant_name
                        }
                    else:
                        st.json(call_data)
                else:
                    st.error(f"Call failed: {result['error']}")
    
    # Bulk Calls
    elif call_type == "Bulk Calls":
        st.subheader("📞 Bulk Calls")
        
        bulk_input_method = st.radio(
            "Input method:",
            ["Text Input", "Upload CSV", "Select from CRM"],
            horizontal=True
        )
        
        customer_numbers = []
        
        if bulk_input_method == "Text Input":
            bulk_numbers_text = st.text_area(
                "Phone Numbers (one per line)",
                placeholder="+1234567890\n+0987654321\n+1122334455",
                height=150
            )
            
            if bulk_numbers_text:
                customer_numbers = parse_bulk_numbers(bulk_numbers_text)
                st.info(f"Found {len(customer_numbers)} valid phone numbers")
        
        elif bulk_input_method == "Upload CSV":
            uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
            
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
                    status_filter = st.multiselect("Filter by Status", CUSTOMER_STATUSES)
                with col2:
                    min_score = st.slider("Minimum Lead Score", 0, 100, 0)
                
                # Filter customers
                filtered_customers = customers
                if status_filter:
                    filtered_customers = [c for c in filtered_customers if c['status'] in status_filter]
                if min_score > 0:
                    filtered_customers = [c for c in filtered_customers if (c['lead_score'] or 0) >= min_score]
                
                # Customer selection
                selected_customers = []
                for customer in filtered_customers[:20]:  # Limit to 20 for performance
                    if st.checkbox(f"{customer['name']} - {customer['phone']} ({customer['status']})", 
                                 key=f"bulk_customer_{customer['id']}"):
                        selected_customers.append(customer)
                
                customer_numbers = [c['phone'] for c in selected_customers]
                st.info(f"Selected {len(customer_numbers)} customers")
            else:
                st.warning("No customers found in CRM")
        
        # Bulk call execution
        if customer_numbers and st.button("📞 Make Bulk Calls", type="primary"):
            customers = [{"number": num} for num in customer_numbers]
            
            schedule_plan = None
            if schedule_call:
                earliest_datetime = datetime.combine(earliest_date, earliest_time)
                schedule_plan = {"earliestAt": earliest_datetime.isoformat() + "Z"}
            
            with st.spinner(f"Making {len(customers)} calls..."):
                result = make_vapi_call(
                    api_key=st.session_state.api_key,
                    assistant_id=assistant_id,
                    customers=customers,
                    schedule_plan=schedule_plan
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
    
    # CRM Campaign
    elif call_type == "CRM Campaign":
        st.subheader("🎯 CRM Campaign")
        
        # Campaign settings
        campaign_name = st.text_input("Campaign Name", placeholder="Q1 Follow-up Campaign")
        
        # Target criteria
        col1, col2 = st.columns(2)
        with col1:
            target_statuses = st.multiselect("Target Customer Status", CUSTOMER_STATUSES, default=["Hot Lead", "Warm Lead"])
            min_lead_score = st.slider("Minimum Lead Score", 0, 100, 70)
        
        with col2:
            days_since_contact = st.number_input("Days since last contact", min_value=0, value=7)
            max_customers = st.number_input("Max customers to call", min_value=1, value=50)
        
        # Preview campaign targets
        if st.button("🔍 Preview Campaign Targets"):
            customers = get_customers_from_db()
            
            # Filter customers based on criteria
            target_customers = []
            for customer in customers:
                if customer['status'] in target_statuses:
                    if (customer['lead_score'] or 0) >= min_lead_score:
                        if customer['last_contact']:
                            last_contact = datetime.fromisoformat(customer['last_contact'])
                            days_diff = (datetime.now() - last_contact).days
                            if days_diff >= days_since_contact:
                                target_customers.append(customer)
                        else:
                            target_customers.append(customer)
            
            target_customers = target_customers[:max_customers]
            
            st.write(f"**Campaign Targets:** {len(target_customers)} customers")
            
            if target_customers:
                df_targets = pd.DataFrame(target_customers)
                st.dataframe(df_targets[['name', 'company', 'phone', 'status', 'lead_score', 'last_contact']])
                
                if st.button("🚀 Launch Campaign", type="primary"):
                    customer_numbers = [c['phone'] for c in target_customers]
                    customers = [{"number": num} for num in customer_numbers]
                    
                    with st.spinner(f"Launching campaign for {len(customers)} customers..."):
                        result = make_vapi_call(
                            api_key=st.session_state.api_key,
                            assistant_id=assistant_id,
                            customers=customers
                        )
                    
                    if result["success"]:
                        st.success(f"Campaign '{campaign_name}' launched successfully!")
                        
                        # Save campaign record
                        call_record = {
                            'id': str(uuid.uuid4()),
                            'timestamp': datetime.now().isoformat(),
                            'type': 'CRM Campaign',
                            'assistant_name': assistant_name,
                            'assistant_id': assistant_id,
                            'customer_phone': f"{len(customers)} campaign targets",
                            'call_id': str(result["data"]),
                            'status': 'initiated',
                            'notes': f"Campaign: {campaign_name}"
                        }
                        
                        save_call_to_db(call_record)
                        
                        # Update customer interactions
                        for customer in target_customers:
                            interaction_data = {
                                'type': 'Campaign Call',
                                'date': datetime.now().date().isoformat(),
                                'notes': f"Included in campaign: {campaign_name}",
                                'outcome': 'Initiated',
                                'next_action': 'Monitor campaign results',
                                'created_by': 'Campaign System'
                            }
                            add_customer_interaction(customer['id'], interaction_data)
                        
                        st.json(result["data"])
                    else:
                        st.error(f"Campaign failed: {result['error']}")
            else:
                st.warning("No customers match the campaign criteria")

def render_call_history():
    """Render the call history page with enhanced filtering and export."""
    st.title("📋 Call History")
    st.markdown("Complete call history with advanced filtering and export options")
    
    # Filter controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        date_filter = st.selectbox("Date Range", ["All Time", "Today", "Last 7 Days", "Last 30 Days", "Custom"])
    
    with col2:
        status_filter = st.selectbox("Status", ["All", "initiated", "completed", "failed", "in-progress"])
    
    with col3:
        type_filter = st.selectbox("Call Type", ["All", "Single Call", "Bulk Calls", "CRM Campaign"])
    
    with col4:
        assistant_filter = st.selectbox("Assistant", ["All"] + list(ASSISTANTS.keys()))
    
    # Custom date range
    if date_filter == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
    
    # Get filtered calls
    calls = get_calls_from_db()
    
    # Apply filters
    filtered_calls = calls
    
    if date_filter != "All Time":
        now = datetime.now()
        if date_filter == "Today":
            start_date = now.date()
            end_date = now.date()
        elif date_filter == "Last 7 Days":
            start_date = (now - timedelta(days=7)).date()
            end_date = now.date()
        elif date_filter == "Last 30 Days":
            start_date = (now - timedelta(days=30)).date()
            end_date = now.date()
        
        if date_filter != "Custom":
            filtered_calls = [c for c in filtered_calls if c['timestamp'] and 
                            start_date <= datetime.fromisoformat(c['timestamp']).date() <= end_date]
    
    if status_filter != "All":
        filtered_calls = [c for c in filtered_calls if c['status'] == status_filter]
    
    if type_filter != "All":
        filtered_calls = [c for c in filtered_calls if c['type'] == type_filter]
    
    if assistant_filter != "All":
        filtered_calls = [c for c in filtered_calls if c['assistant_name'] == assistant_filter]
    
    # Display summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Calls", len(filtered_calls))
    
    with col2:
        completed = len([c for c in filtered_calls if c['status'] == 'completed'])
        st.metric("Completed", completed)
    
    with col3:
        success_rate = (completed / len(filtered_calls) * 100) if filtered_calls else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col4:
        total_duration = sum([c['duration'] or 0 for c in filtered_calls])
        st.metric("Total Duration", f"{total_duration}s")
    
    # Export options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Export CSV"):
            if filtered_calls:
                df = pd.DataFrame(filtered_calls)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="💾 Download CSV",
                    data=csv_data,
                    file_name=f"call_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    with col2:
        if st.button("📊 Export Excel"):
            if filtered_calls:
                df = pd.DataFrame(filtered_calls)
                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_data = excel_buffer.getvalue()
                st.download_button(
                    label="💾 Download Excel",
                    data=excel_data,
                    file_name=f"call_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col3:
        if st.button("📋 Copy to Clipboard"):
            if filtered_calls:
                df = pd.DataFrame(filtered_calls)
                st.code(df.to_string(index=False))
    
    # Call history table
    if filtered_calls:
        st.subheader("📞 Call Records")
        
        for call in filtered_calls:
            with st.expander(f"📞 {call['customer_phone']} - {call['status'].upper()} ({call['timestamp'][:16] if call['timestamp'] else 'N/A'})"):
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
                        if st.button(f"📝 View Transcript", key=f"transcript_{call['id']}"):
                            st.session_state.viewing_transcript = call['id']
                            st.session_state.current_page = "📝 Transcripts"
                            st.rerun()
                    
                    if call['recording_path']:
                        if st.button(f"🎵 Play Recording", key=f"recording_{call['id']}"):
                            st.session_state.viewing_recording = call['id']
                            st.session_state.current_page = "🎵 Recordings"
                            st.rerun()
                    
                    if call['call_id'] and st.button(f"🔄 Refresh Status", key=f"refresh_{call['id']}"):
                        with st.spinner("Updating call status..."):
                            result = get_call_details(st.session_state.api_key, call['call_id'])
                            if result["success"]:
                                call_data = result["data"]
                                # Update database with latest info
                                update_data = {
                                    'status': call_data.get('status', call['status']),
                                    'transcript': call_data.get('transcript', call['transcript']),
                                    'recording_url': call_data.get('recordingUrl', call['recording_url']),
                                    'duration': call_data.get('duration', call['duration']),
                                    'cost': call_data.get('cost', call['cost'])
                                }
                                
                                conn = sqlite3.connect('vapi_calls.db')
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE calls SET status=?, transcript=?, recording_url=?, duration=?, cost=?
                                    WHERE id=?
                                ''', (update_data['status'], update_data['transcript'], 
                                         update_data['recording_url'], update_data['duration'], 
                                         update_data['cost'], call['id']))
                                conn.commit()
                                conn.close()
                                
                                st.success("Call status updated!")
                                st.rerun()
                            else:
                                st.error(f"Failed to update: {result['error']}")
                
                if call['notes']:
                    st.write(f"**Notes:** {call['notes']}")
    else:
        st.info("No calls found matching the selected filters.")

def render_transcripts():
    """Render the transcripts page with search and export."""
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
                if st.button("📥 Export TXT"):
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
                        mime="text/plain"
                    )
                
                if st.button("📋 Copy Text"):
                    st.code(call['transcript'])
                
                if st.button("⬅️ Back to List"):
                    st.session_state.viewing_transcript = None
                    st.rerun()
            
            # Display transcript
            st.subheader("📄 Transcript Content")
            st.text_area("", value=call['transcript'], height=400, disabled=True)
            
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
            
            # Key phrases extraction (simple)
            st.subheader("🔑 Key Phrases")
            words = call['transcript'].lower().split()
            word_freq = {}
            for word in words:
                if len(word) > 4:  # Only words longer than 4 characters
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top 10 most frequent words
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            if top_words:
                col1, col2 = st.columns(2)
                with col1:
                    for word, count in top_words[:5]:
                        st.write(f"• {word}: {count} times")
                with col2:
                    for word, count in top_words[5:10]:
                        st.write(f"• {word}: {count} times")
        
        else:
            st.error("Transcript not found or not available")
            if st.button("⬅️ Back to List"):
                st.session_state.viewing_transcript = None
                st.rerun()
    
    else:
        # Display transcript list
        calls_with_transcripts = [c for c in get_calls_from_db() if c['transcript']]
        
        # Search functionality
        search_term = st.text_input("🔍 Search transcripts", placeholder="Enter keywords to search...")
        
        if search_term:
            calls_with_transcripts = [c for c in calls_with_transcripts 
                                    if search_term.lower() in c['transcript'].lower()]
        
        # Display summary
        st.write(f"Found {len(calls_with_transcripts)} transcripts")
        
        if calls_with_transcripts:
            # Bulk export
            if st.button("📥 Export All Transcripts"):
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
                    mime="text/plain"
                )
            
            # Transcript list
            for call in calls_with_transcripts:
                with st.expander(f"📝 {call['customer_phone']} - {call['timestamp'][:16] if call['timestamp'] else 'N/A'}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Show first 200 characters of transcript
                        preview = call['transcript'][:200] + "..." if len(call['transcript']) > 200 else call['transcript']
                        st.write(f"**Preview:** {preview}")
                        st.write(f"**Assistant:** {call['assistant_name']}")
                        st.write(f"**Duration:** {call['duration'] or 0}s")
                    
                    with col2:
                        if st.button("👁️ View Full", key=f"view_transcript_{call['id']}"):
                            st.session_state.viewing_transcript = call['id']
                            st.rerun()
                        
                        if st.button("📥 Export", key=f"export_transcript_{call['id']}"):
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
                                key=f"download_transcript_{call['id']}"
                            )
        else:
            st.info("No transcripts found. Transcripts will appear here after calls are completed.")

def render_recordings():
    """Render the recordings page with MP3 playback."""
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
                if st.button("⬅️ Back to List"):
                    st.session_state.viewing_recording = None
                    st.rerun()
            
            # Recording playback
            if call['recording_path'] and os.path.exists(call['recording_path']):
                st.subheader("🎧 Audio Player")
                
                # Read audio file
                with open(call['recording_path'], 'rb') as audio_file:
                    audio_bytes = audio_file.read()
                
                # Display audio player
                st.audio(audio_bytes, format='audio/mp3')
                
                # Download option
                st.download_button(
                    label="💾 Download Recording",
                    data=audio_bytes,
                    file_name=f"recording_{call['call_id'][:8]}.mp3",
                    mime="audio/mpeg"
                )
                
            elif call['recording_url']:
                st.subheader("📥 Download Recording")
                st.write("Recording is available for download from Vapi servers.")
                
                if st.button("📥 Download from Vapi"):
                    with st.spinner("Downloading recording..."):
                        result = download_call_recording(
                            st.session_state.api_key, 
                            call['recording_url'], 
                            call['call_id']
                        )
                        
                        if result["success"]:
                            # Update database with local path
                            conn = sqlite3.connect('vapi_calls.db')
                            cursor = conn.cursor()
                            cursor.execute(
                                'UPDATE calls SET recording_path=? WHERE id=?',
                                (result["filename"], call['id'])
                            )
                            conn.commit()
                            conn.close()
                            
                            st.success("Recording downloaded successfully!")
                            
                            # Display audio player
                            st.audio(result["data"], format='audio/mp3')
                            
                            # Download button
                            st.download_button(
                                label="💾 Save Recording",
                                data=result["data"],
                                file_name=f"recording_{call['call_id'][:8]}.mp3",
                                mime="audio/mpeg"
                            )
                        else:
                            st.error(f"Failed to download: {result['error']}")
            else:
                st.warning("No recording available for this call.")
        
        else:
            st.error("Call not found")
            if st.button("⬅️ Back to List"):
                st.session_state.viewing_recording = None
                st.rerun()
    
    else:
        # Display recordings list
        calls_with_recordings = [c for c in get_calls_from_db() 
                               if c['recording_url'] or c['recording_path']]
        
        st.write(f"Found {len(calls_with_recordings)} recordings")
        
        if calls_with_recordings:
            # Bulk download option
            if st.button("📥 Download All Recordings"):
                st.info("Bulk download will be implemented in a future version.")
            
            # Recordings list
            for call in calls_with_recordings:
                with st.expander(f"🎵 {call['customer_phone']} - {call['timestamp'][:16] if call['timestamp'] else 'N/A'}"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Assistant:** {call['assistant_name']}")
                        st.write(f"**Duration:** {call['duration'] or 0}s")
                        st.write(f"**Status:** {'Downloaded' if call['recording_path'] else 'Available'}")
                    
                    with col2:
                        if call['recording_path'] and os.path.exists(call['recording_path']):
                            # Quick play option
                            with open(call['recording_path'], 'rb') as audio_file:
                                audio_bytes = audio_file.read()
                            st.audio(audio_bytes, format='audio/mp3')
                    
                    with col3:
                        if st.button("🎧 Open Player", key=f"play_{call['id']}"):
                            st.session_state.viewing_recording = call['id']
                            st.rerun()
                        
                        if call['recording_path'] and os.path.exists(call['recording_path']):
                            with open(call['recording_path'], 'rb') as audio_file:
                                audio_bytes = audio_file.read()
                            
                            st.download_button(
                                label="💾 Download",
                                data=audio_bytes,
                                file_name=f"recording_{call['call_id'][:8]}.mp3",
                                mime="audio/mpeg",
                                key=f"download_{call['id']}"
                            )
        else:
            st.info("No recordings found. Recordings will appear here after calls are completed.")

def render_assistant_manager():
    """Render the assistant manager page."""
    st.title("🤖 Assistant Manager")
    st.markdown("Create and manage your AI assistants")
    
    # Get assistants from API
    if st.session_state.api_key:
        if st.button("🔄 Refresh Assistants"):
            with st.spinner("Loading assistants..."):
                result = get_assistants_from_api(st.session_state.api_key)
                if result["success"]:
                    st.session_state.api_assistants = result["data"]
                    st.success("Assistants loaded successfully!")
                else:
                    st.error(f"Failed to load assistants: {result['error']}")
    
    # Tabs for different assistant management functions
    tab1, tab2, tab3 = st.tabs(["📋 My Assistants", "➕ Create Assistant", "⚙️ Assistant Settings"])
    
    with tab1:
        st.subheader("📋 Your Assistants")
        
        # Display predefined assistants
        st.write("**Predefined Assistants:**")
        for name, assistant_id in ASSISTANTS.items():
            with st.expander(f"🤖 {name}"):
                st.code(f"ID: {assistant_id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"📞 Test Call", key=f"test_{assistant_id}"):
                        st.info("Test call feature coming soon!")
                
                with col2:
                    if st.button(f"✏️ Edit", key=f"edit_{assistant_id}"):
                        st.info("Edit feature coming soon!")
        
        # Display API assistants if available
        if st.session_state.get('api_assistants'):
            st.write("**API Assistants:**")
            for assistant in st.session_state.api_assistants:
                with st.expander(f"🤖 {assistant.get('name', 'Unnamed')}"):
                    st.json(assistant)
    
    with tab2:
        st.subheader("➕ Create New Assistant")
        
        with st.form("create_assistant_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                assistant_name = st.text_input("Assistant Name*")
                model = st.selectbox("Model", list(MODEL_OPTIONS.keys()))
                voice = st.selectbox("Voice", list(VOICE_OPTIONS.keys()))
                
            with col2:
                first_message = st.text_area("First Message", 
                    placeholder="Hello! How can I help you today?")
                
            system_message = st.text_area("System Message", 
                placeholder="You are a helpful AI assistant...", height=150)
            
            # Advanced settings
            with st.expander("🔧 Advanced Settings"):
                col1, col2 = st.columns(2)
                
                with col1:
                    temperature = st.slider("Temperature", 0.0, 2.0, 1.0, 0.1)
                    max_tokens = st.number_input("Max Tokens", 100, 4000, 1000)
                
                with col2:
                    silence_timeout = st.number_input("Silence Timeout (ms)", 1000, 10000, 3000)
                    response_delay = st.number_input("Response Delay (ms)", 0, 2000, 500)
            
            submitted = st.form_submit_button("🚀 Create Assistant")
            
            if submitted and assistant_name and st.session_state.api_key:
                assistant_data = {
                    "name": assistant_name,
                    "model": {
                        "provider": "openai",
                        "model": model,
                        "temperature": temperature,
                        "maxTokens": max_tokens
                    },
                    "voice": {
                        "provider": "openai",
                        "voiceId": voice
                    },
                    "firstMessage": first_message,
                    "systemMessage": system_message,
                    "silenceTimeoutSeconds": silence_timeout / 1000,
                    "responseDelaySeconds": response_delay / 1000
                }
                
                with st.spinner("Creating assistant..."):
                    result = create_assistant(st.session_state.api_key, assistant_data)
                    
                    if result["success"]:
                        st.success(f"Assistant '{assistant_name}' created successfully!")
                        st.json(result["data"])
                        
                        # Add to local assistants list
                        new_assistant_id = result["data"].get("id")
                        if new_assistant_id:
                            ASSISTANTS[assistant_name] = new_assistant_id
                    else:
                        st.error(f"Failed to create assistant: {result['error']}")
    
    with tab3:
        st.subheader("⚙️ Assistant Settings")
        
        # Voice samples
        st.write("**Voice Samples:**")
        for voice_id, voice_name in VOICE_OPTIONS.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{voice_name}**")
            with col2:
                if st.button(f"🔊 Preview", key=f"preview_{voice_id}"):
                    st.info("Voice preview feature coming soon!")
        
        # Model comparison
        st.write("**Model Comparison:**")
        model_data = [
            {"Model": "GPT-4", "Speed": "Slow", "Quality": "Excellent", "Cost": "High"},
            {"Model": "GPT-4 Turbo", "Speed": "Fast", "Quality": "Excellent", "Cost": "Medium"},
            {"Model": "GPT-3.5 Turbo", "Speed": "Very Fast", "Quality": "Good", "Cost": "Low"}
        ]
        
        df_models = pd.DataFrame(model_data)
        st.dataframe(df_models, use_container_width=True)

def render_analytics():
    """Render the analytics page with comprehensive insights."""
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
        
        # Success rate trend
        st.subheader("📈 Success Rate Trend")
        df_daily['success_rate'] = (df_daily['successful_calls'] / df_daily['total_calls'] * 100).fillna(0)
        fig2 = px.line(df_daily, x='date', y='success_rate', title='Daily Success Rate (%)')
        st.plotly_chart(fig2, use_container_width=True)
        
        # Cost analysis
        st.subheader("💰 Cost Analysis")
        fig3 = px.bar(df_daily, x='date', y='total_cost', title='Daily Call Costs')
        st.plotly_chart(fig3, use_container_width=True)
    
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
        
        # Assistant success rate chart
        fig4 = px.bar(df_assistants, x='Assistant', y='Success Rate', title='Assistant Success Rates')
        st.plotly_chart(fig4, use_container_width=True)
    
    # Customer insights
    if customers:
        st.subheader("👥 Customer Insights")
        
        # Customer status distribution
        status_counts = {}
        for customer in customers:
            status = customer['status'] or 'Unknown'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        fig5 = px.pie(values=list(status_counts.values()), names=list(status_counts.keys()), 
                     title="Customer Status Distribution")
        st.plotly_chart(fig5, use_container_width=True)
        
        # Lead score distribution
        lead_scores = [c['lead_score'] for c in customers if c['lead_score']]
        if lead_scores:
            fig6 = px.histogram(x=lead_scores, nbins=20, title="Lead Score Distribution")
            st.plotly_chart(fig6, use_container_width=True)
        
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
    
    # Export analytics
    st.subheader("📥 Export Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Charts"):
            st.info("Chart export feature coming soon!")
    
    with col2:
        if st.button("📋 Export Data"):
            if calls:
                df_calls = pd.DataFrame(calls)
                csv_data = df_calls.to_csv(index=False)
                st.download_button(
                    label="💾 Download Analytics CSV",
                    data=csv_data,
                    file_name=f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    with col3:
        if st.button("📈 Generate Report"):
            st.info("Automated report generation coming soon!")

def render_settings():
    """Render the settings page."""
    st.title("⚙️ Settings")
    st.markdown("Configure your Vapi application settings")
    
    # API Settings
    st.subheader("🔑 API Configuration")
    
    with st.expander("API Settings"):
        current_api_key = st.session_state.api_key
        new_api_key = st.text_input("Vapi API Key", value=current_api_key, type="password")
        
        if new_api_key != current_api_key:
            st.session_state.api_key = new_api_key
            st.success("API key updated!")
        
        # Test connection
        if st.button("🔍 Test API Connection"):
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
        
        if st.session_state.api_key:
            if st.button("📋 Get Available Numbers"):
                with st.spinner("Loading phone numbers..."):
                    result = get_phone_numbers(st.session_state.api_key)
                    if result["success"]:
                        st.write("Available phone numbers:")
                        for number in result["data"]:
                            st.json(number)
                    else:
                        st.error(f"Failed to load numbers: {result['error']}")
    
    # Database Settings
    st.subheader("🗄️ Database Management")
    
    with st.expander("Database Operations"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Reset Demo Data"):
                load_demo_customers()
                st.success("Demo customers reloaded!")
        
        with col2:
            if st.button("📥 Export Database"):
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
                    mime="application/json"
                )
        
        with col3:
            if st.button("⚠️ Clear All Data"):
                if st.checkbox("I understand this will delete all data"):
                    conn = sqlite3.connect('vapi_calls.db')
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM calls')
                    cursor.execute('DELETE FROM customers')
                    cursor.execute('DELETE FROM orders')
                    cursor.execute('DELETE FROM customer_interactions')
                    conn.commit()
                    conn.close()
                    st.success("All data cleared!")
    
    # Application Settings
    st.subheader("🎨 Application Preferences")
    
    with st.expander("UI Settings"):
        # Theme settings (for future implementation)
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
        
        # Default assistant
        default_assistant = st.selectbox("Default Assistant", list(ASSISTANTS.keys()))
        
        # Auto-refresh settings
        auto_refresh = st.checkbox("Auto-refresh call status", value=True)
        refresh_interval = st.slider("Refresh interval (seconds)", 10, 60, 30)
        
        # Notification settings
        enable_notifications = st.checkbox("Enable notifications", value=True)
        
        if st.button("💾 Save Preferences"):
            # Save preferences (would typically save to database or config file)
            st.success("Preferences saved!")
    
    # Google Sheets Integration
    st.subheader("📊 Google Sheets Integration")
    
    with st.expander("Google Sheets Setup"):
        st.write("**Template Information:**")
        template_info = create_google_sheets_template()
        
        st.write("**Required Columns:**")
        for col in template_info["columns"]:
            st.write(f"• {col}")
        
        st.write("**Setup Instructions:**")
        for i, instruction in enumerate(template_info["instructions"], 1):
            st.write(f"{i}. {instruction}")
        
        # CSV import for Google Sheets data
        st.write("**Import from Google Sheets:**")
        uploaded_file = st.file_uploader("Upload CSV exported from Google Sheets", type=['csv'])
        
        if uploaded_file:
            csv_data = uploaded_file.read().decode('utf-8')
            result = import_customers_from_csv(csv_data)
            
            if result["success"]:
                st.success(f"Successfully imported {result['count']} customers!")
            else:
                st.error(f"Import failed: {result['error']}")
    
    # System Information
    st.subheader("ℹ️ System Information")
    
    with st.expander("System Info"):
        st.write(f"**Application Version:** 2.0.0 Enhanced")
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

# Update the main function routing to include all new pages
def main():
    """Main application function with complete routing."""
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


