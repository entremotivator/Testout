import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional

# Configure the page
st.set_page_config(
    page_title="Vapi Outbound Calling",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'call_results' not in st.session_state:
    st.session_state.call_results = []

def make_vapi_call(
    api_key: str,
    assistant_id: str,
    phone_number_id: str,
    customers: List[Dict],
    schedule_plan: Optional[Dict] = None,
    base_url: str = "https://api.vapi.ai"
) -> Dict:
    """Make a call to the Vapi API for outbound calling."""
    
    url = f"{base_url}/call"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare the payload
    payload = {
        "assistantId": assistant_id,
        "phoneNumberId": phone_number_id,
    }
    
    # Add customers (single or multiple)
    if len(customers) == 1:
        payload["customer"] = customers[0]
    else:
        payload["customers"] = customers
    
    # Add schedule plan if provided
    if schedule_plan:
        payload["schedulePlan"] = schedule_plan
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e), "status_code": getattr(e.response, 'status_code', None)}

def validate_phone_number(phone: str) -> bool:
    """Basic phone number validation."""
    # Remove spaces and common formatting
    clean_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Check if it starts with + and has appropriate length
    if clean_phone.startswith("+") and len(clean_phone) >= 10:
        return True
    return False

def parse_bulk_numbers(text: str) -> List[str]:
    """Parse bulk phone numbers from text input."""
    lines = text.strip().split('\n')
    numbers = []
    for line in lines:
        line = line.strip()
        if line and validate_phone_number(line):
            numbers.append(line)
    return numbers

# Main app
def main():
    st.title("📞 Vapi Outbound Calling")
    st.markdown("Send single or bulk outbound calls using the Vapi API")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Configuration
        api_key = st.text_input("Vapi API Key", type="password", help="Your Vapi API key")
        assistant_id = st.text_input("Assistant ID", help="Your configured assistant ID")
        phone_number_id = st.text_input("Phone Number ID", help="Your Vapi phone number ID")
        
        st.divider()
        
        # Call Type Selection
        st.header("📋 Call Type")
        call_type = st.radio(
            "Select calling mode:",
            ["Single Call", "Bulk Calls"],
            help="Choose between making a single call or multiple calls"
        )
        
        st.divider()
        
        # Scheduling Options
        st.header("⏰ Scheduling")
        schedule_call = st.checkbox("Schedule call for later", help="Schedule the call for a future time")
        
        earliest_datetime = None
        latest_datetime = None
        
        if schedule_call:
            col1, col2 = st.columns(2)
            with col1:
                earliest_date = st.date_input("Earliest Date", datetime.now().date())
                earliest_time = st.time_input("Earliest Time", datetime.now().time())
            with col2:
                latest_date = st.date_input("Latest Date", datetime.now().date())
                latest_time = st.time_input("Latest Time", (datetime.now() + timedelta(hours=1)).time())
            
            earliest_datetime = datetime.combine(earliest_date, earliest_time)
            latest_datetime = datetime.combine(latest_date, latest_time)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Single Call Interface
        if call_type == "Single Call":
            st.header("📱 Single Call")
            
            customer_number = st.text_input(
                "Customer Phone Number",
                placeholder="+1234567890",
                help="Enter the customer's phone number with country code"
            )
            
            if st.button("📞 Make Call", type="primary", disabled=not all([api_key, assistant_id, phone_number_id, customer_number])):
                if not validate_phone_number(customer_number):
                    st.error("Please enter a valid phone number with country code (e.g., +1234567890)")
                else:
                    # Prepare customer data
                    customers = [{"number": customer_number}]
                    
                    # Prepare schedule plan
                    schedule_plan = None
                    if schedule_call and earliest_datetime:
                        schedule_plan = {"earliestAt": earliest_datetime.isoformat() + "Z"}
                        if latest_datetime:
                            schedule_plan["latestAt"] = latest_datetime.isoformat() + "Z"
                    
                    # Make the call
                    with st.spinner("Making call..."):
                        result = make_vapi_call(
                            api_key=api_key,
                            assistant_id=assistant_id,
                            phone_number_id=phone_number_id,
                            customers=customers,
                            schedule_plan=schedule_plan
                        )
                    
                    if result["success"]:
                        st.success("Call initiated successfully!")
                        st.json(result["data"])
                        
                        # Store result in session state
                        st.session_state.call_results.append({
                            "timestamp": datetime.now().isoformat(),
                            "type": "Single Call",
                            "customer": customer_number,
                            "result": result
                        })
                    else:
                        st.error(f"Call failed: {result['error']}")
                        if result.get('status_code'):
                            st.error(f"Status Code: {result['status_code']}")
        
        # Bulk Call Interface
        else:
            st.header("📞 Bulk Calls")
            
            # Options for bulk input
            bulk_input_method = st.radio(
                "How would you like to input phone numbers?",
                ["Text Input", "Upload CSV"],
                horizontal=True
            )
            
            customer_numbers = []
            
            if bulk_input_method == "Text Input":
                bulk_numbers_text = st.text_area(
                    "Phone Numbers (one per line)",
                    placeholder="+1234567890\n+0987654321\n+1122334455",
                    height=150,
                    help="Enter one phone number per line with country code"
                )
                
                if bulk_numbers_text:
                    customer_numbers = parse_bulk_numbers(bulk_numbers_text)
                    st.info(f"Found {len(customer_numbers)} valid phone numbers")
                    
                    if customer_numbers:
                        with st.expander("Preview Numbers"):
                            for i, num in enumerate(customer_numbers[:10], 1):
                                st.write(f"{i}. {num}")
                            if len(customer_numbers) > 10:
                                st.write(f"... and {len(customer_numbers) - 10} more")
            
            else:  # CSV Upload
                uploaded_file = st.file_uploader(
                    "Upload CSV file",
                    type=['csv'],
                    help="CSV should have a column named 'phone' or 'number'"
                )
                
                if uploaded_file:
                    try:
                        df = pd.read_csv(uploaded_file)
                        st.write("Preview of uploaded data:")
                        st.dataframe(df.head())
                        
                        # Try to find phone number column
                        phone_column = None
                        for col in ['phone', 'number', 'phone_number', 'Phone', 'Number']:
                            if col in df.columns:
                                phone_column = col
                                break
                        
                        if phone_column:
                            customer_numbers = []
                            for phone in df[phone_column].dropna():
                                phone_str = str(phone).strip()
                                if validate_phone_number(phone_str):
                                    customer_numbers.append(phone_str)
                            
                            st.info(f"Found {len(customer_numbers)} valid phone numbers from column '{phone_column}'")
                        else:
                            st.error("Could not find a phone number column. Please ensure your CSV has a column named 'phone' or 'number'")
                    
                    except Exception as e:
                        st.error(f"Error reading CSV: {str(e)}")
            
            # Bulk call button
            if st.button("📞 Make Bulk Calls", type="primary", disabled=not all([api_key, assistant_id, phone_number_id]) or not customer_numbers):
                # Prepare customer data
                customers = [{"number": num} for num in customer_numbers]
                
                # Prepare schedule plan
                schedule_plan = None
                if schedule_call and earliest_datetime:
                    schedule_plan = {"earliestAt": earliest_datetime.isoformat() + "Z"}
                    if latest_datetime:
                        schedule_plan["latestAt"] = latest_datetime.isoformat() + "Z"
                
                # Make the bulk call
                with st.spinner(f"Making {len(customers)} calls..."):
                    result = make_vapi_call(
                        api_key=api_key,
                        assistant_id=assistant_id,
                        phone_number_id=phone_number_id,
                        customers=customers,
                        schedule_plan=schedule_plan
                    )
                
                if result["success"]:
                    st.success(f"Bulk calls initiated successfully for {len(customers)} numbers!")
                    st.json(result["data"])
                    
                    # Store result in session state
                    st.session_state.call_results.append({
                        "timestamp": datetime.now().isoformat(),
                        "type": "Bulk Calls",
                        "customer_count": len(customers),
                        "customers": customer_numbers,
                        "result": result
                    })
                else:
                    st.error(f"Bulk calls failed: {result['error']}")
                    if result.get('status_code'):
                        st.error(f"Status Code: {result['status_code']}")
    
    # Right column - Call History
    with col2:
        st.header("📋 Call History")
        
        if st.session_state.call_results:
            for i, call_result in enumerate(reversed(st.session_state.call_results)):
                with st.expander(f"{call_result['type']} - {call_result['timestamp'][:19]}"):
                    st.write(f"**Type:** {call_result['type']}")
                    
                    if call_result['type'] == 'Single Call':
                        st.write(f"**Customer:** {call_result['customer']}")
                    else:
                        st.write(f"**Customers:** {call_result['customer_count']} numbers")
                    
                    st.write(f"**Success:** {'✅' if call_result['result']['success'] else '❌'}")
                    
                    if call_result['result']['success']:
                        st.json(call_result['result']['data'])
                    else:
                        st.error(call_result['result']['error'])
            
            if st.button("🗑️ Clear History"):
                st.session_state.call_results = []
                st.rerun()
        else:
            st.info("No calls made yet")
    
    # Footer with information
    st.divider()
    st.markdown("""
    ### 📚 Usage Notes:
    - **Single Call**: Make one call to a specific number
    - **Bulk Calls**: Make multiple calls to different numbers simultaneously
    - **Scheduling**: Schedule calls for future execution
    - **Phone Numbers**: Must include country code (e.g., +1234567890)
    - **CSV Format**: Should have a column named 'phone' or 'number'
    """)

if __name__ == "__main__":
    main()
