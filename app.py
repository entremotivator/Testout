import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional
import time
import base64
from io import BytesIO

# Configure the page
st.set_page_config(
    page_title="Vapi Outbound Calling Pro",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Initialize session state
if 'call_results' not in st.session_state:
    st.session_state.call_results = []
if 'call_monitoring' not in st.session_state:
    st.session_state.call_monitoring = {}

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

def download_call_recording(api_key: str, recording_url: str) -> Dict:
    """Download call recording from URL."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
        }
        
        response = requests.get(recording_url, headers=headers, timeout=60)
        response.raise_for_status()
        
        return {"success": True, "data": response.content}
        
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

def make_vapi_call(
    api_key: str,
    assistant_id: str,
    customers: List[Dict],
    schedule_plan: Optional[Dict] = None,
    base_url: str = "https://api.vapi.ai"
) -> Dict:
    """Make a call to the Vapi API for outbound calling."""
    
    url = f"{base_url}/call"
    
    # Ensure all strings are properly encoded
    try:
        # Clean and validate input strings
        api_key = str(api_key).strip()
        assistant_id = str(assistant_id).strip()
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # Prepare the payload with proper string handling
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
                    # Remove any non-printable characters and ensure proper encoding
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
        
        # Convert payload to JSON string first to check for encoding issues
        json_payload = json.dumps(payload, ensure_ascii=False)
        
        response = requests.post(
            url, 
            headers=headers, 
            data=json_payload.encode('utf-8'),
            timeout=30
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
        
    except UnicodeEncodeError as e:
        return {"success": False, "error": f"Unicode encoding error: {str(e)}", "status_code": None}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON encoding error: {str(e)}", "status_code": None}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout - the API took too long to respond", "status_code": None}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error - unable to reach the API", "status_code": None}
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error: {e.response.status_code}"
        try:
            error_details = e.response.json()
            error_msg += f" - {error_details.get('message', 'Unknown error')}"
        except:
            error_msg += f" - {e.response.text[:200]}"
        return {"success": False, "error": error_msg, "status_code": e.response.status_code}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Request error: {str(e)}", "status_code": getattr(e.response, 'status_code', None)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}", "status_code": None}

def validate_phone_number(phone: str) -> bool:
    """Basic phone number validation."""
    try:
        # Convert to string and remove any non-printable characters
        phone_str = str(phone).strip()
        phone_str = ''.join(char for char in phone_str if char.isprintable())
        
        # Remove spaces and common formatting
        clean_phone = phone_str.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace(".", "")
        
        # Check if it starts with + and has appropriate length
        if clean_phone.startswith("+") and len(clean_phone) >= 10 and len(clean_phone) <= 18:
            # Check if the rest are digits
            if clean_phone[1:].isdigit():
                return True
        return False
    except Exception:
        return False

def parse_bulk_numbers(text: str) -> List[str]:
    """Parse bulk phone numbers from text input."""
    try:
        # Clean the text of any non-printable characters
        clean_text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\r', '\t'])
        lines = clean_text.strip().split('\n')
        numbers = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Clean each phone number
                clean_line = ''.join(char for char in line if char.isprintable()).strip()
                if clean_line and validate_phone_number(clean_line):
                    numbers.append(clean_line)
        return numbers
    except Exception:
        return []

def monitor_call_status(api_key: str, call_id: str) -> Dict:
    """Monitor call status and retrieve details when complete."""
    try:
        call_details = get_call_details(api_key, call_id)
        if call_details["success"]:
            call_data = call_details["data"]
            status = call_data.get("status", "unknown")
            
            # Check if call is complete and has transcript/recording
            if status in ["ended", "completed"]:
                return {
                    "success": True,
                    "status": status,
                    "data": call_data,
                    "has_transcript": "transcript" in call_data,
                    "has_recording": "recordingUrl" in call_data
                }
            else:
                return {
                    "success": True,
                    "status": status,
                    "data": call_data,
                    "has_transcript": False,
                    "has_recording": False
                }
        else:
            return call_details
    except Exception as e:
        return {"success": False, "error": str(e)}

def export_call_history() -> str:
    """Export call history to CSV format."""
    if not st.session_state.call_results:
        return ""
    
    # Prepare data for CSV
    csv_data = []
    for call in st.session_state.call_results:
        row = {
            "Timestamp": call.get("timestamp", ""),
            "Type": call.get("type", ""),
            "Assistant": call.get("assistant", ""),
            "Customer": call.get("customer", ""),
            "Customer Name": call.get("customer_name", ""),
            "Call ID": call.get("call_id", ""),
            "Status": call.get("status", ""),
            "Notes": call.get("notes", "")
        }
        csv_data.append(row)
    
    # Convert to DataFrame and then to CSV
    df = pd.DataFrame(csv_data)
    return df.to_csv(index=False)

# Main app
def main():
    st.title("📞 Vapi Outbound Calling Pro")
    st.markdown("Advanced outbound calling with call monitoring, transcripts, and recordings")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Configuration
        api_key = st.text_input(
            "Vapi API Key", 
            type="password",
            help="Your Vapi API key"
        )
        
        # Assistant Selection
        st.subheader("🤖 Assistant Selection")
        assistant_name = st.selectbox(
            "Choose an Assistant",
            options=list(ASSISTANTS.keys()),
            help="Select from your pre-configured assistants"
        )
        assistant_id = ASSISTANTS[assistant_name]
        
        # Display selected assistant info
        st.info(f"**Selected:** {assistant_name}")
        st.code(f"ID: {assistant_id}")
        
        # Phone Number Display
        st.subheader("📱 Phone Number")
        st.info(f"**Using Static Number:**\n`{STATIC_PHONE_NUMBER_ID}`")
        
        # API Key validation
        if api_key:
            if len(api_key.strip()) < 10:
                st.warning("⚠️ API key seems too short. Please verify it's correct.")
            elif not any(char.isalnum() for char in api_key):
                st.warning("⚠️ API key should contain alphanumeric characters.")
            else:
                st.success("✅ API key format looks valid")
        
        # Test API connection
        if st.button("🔍 Test API Connection"):
            if not api_key:
                st.error("Please enter your API key first")
            else:
                with st.spinner("Testing API connection..."):
                    test_result = test_api_connection(api_key)
                    if test_result["success"]:
                        st.success("✅ API connection successful!")
                        st.json(test_result["data"][:3] if isinstance(test_result["data"], list) else test_result["data"])
                    else:
                        st.error(f"❌ API connection failed: {test_result['error']}")
                        if test_result.get('status_code') == 401:
                            st.error("🔑 **Authentication Error**: Please check your API key")
                        elif test_result.get('status_code') == 403:
                            st.error("🚫 **Access Denied**: Your API key doesn't have permission")
                        elif test_result.get('status_code') == 404:
                            st.error("🔍 **Not Found**: Check your credentials")

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
        
        st.divider()
        
        # Call Monitoring
        st.header("🔍 Call Monitoring")
        auto_monitor = st.checkbox("Auto-monitor calls", value=True, help="Automatically check for call completion and retrieve transcripts/recordings")
        monitor_interval = st.slider("Monitor interval (seconds)", 10, 60, 30)

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
            
            # Additional customer info
            with st.expander("📋 Additional Customer Info (Optional)"):
                customer_name = st.text_input("Customer Name", placeholder="John Doe")
                customer_email = st.text_input("Customer Email", placeholder="john@example.com")
                customer_notes = st.text_area("Notes", placeholder="Additional context for the call...")
            
            if st.button("📞 Make Call", type="primary", disabled=not all([api_key, customer_number])):
                if not validate_phone_number(customer_number):
                    st.error("Please enter a valid phone number with country code (e.g., +1234567890)")
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
                    if schedule_call and earliest_datetime:
                        schedule_plan = {"earliestAt": earliest_datetime.isoformat() + "Z"}
                        if latest_datetime:
                            schedule_plan["latestAt"] = latest_datetime.isoformat() + "Z"
                    
                    # Make the call
                    with st.spinner("Making call..."):
                        result = make_vapi_call(
                            api_key=api_key,
                            assistant_id=assistant_id,
                            customers=customers,
                            schedule_plan=schedule_plan
                        )
                    
                    if result["success"]:
                        st.success("Call initiated successfully!")
                        call_data = result["data"]
                        
                        # Display call information
                        if isinstance(call_data, dict) and "id" in call_data:
                            call_id = call_data["id"]
                            st.info(f"**Call ID:** `{call_id}`")
                            st.json(call_data)
                            
                            # Store result in session state
                            call_result = {
                                "timestamp": datetime.now().isoformat(),
                                "type": "Single Call",
                                "assistant": assistant_name,
                                "customer": customer_number,
                                "customer_name": customer_name,
                                "call_id": call_id,
                                "result": result,
                                "status": "initiated",
                                "notes": customer_notes
                            }
                            st.session_state.call_results.append(call_result)
                            
                            # Start monitoring if enabled
                            if auto_monitor:
                                st.session_state.call_monitoring[call_id] = {
                                    "api_key": api_key,
                                    "start_time": datetime.now(),
                                    "customer": customer_number,
                                    "assistant": assistant_name
                                }
                        else:
                            st.json(call_data)
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
                                try:
                                    # Convert to string and clean
                                    phone_str = str(phone).strip()
                                    phone_str = ''.join(char for char in phone_str if char.isprintable()).strip()
                                    
                                    # Handle potential float values from CSV
                                    if phone_str.replace('.', '').replace('-', '').replace('+', '').isdigit():
                                        # If it's a number without +, add it
                                        if not phone_str.startswith('+'):
                                            phone_str = '+' + phone_str.replace('.', '').replace('-', '')
                                    
                                    if validate_phone_number(phone_str):
                                        customer_numbers.append(phone_str)
                                except Exception:
                                    continue  # Skip invalid entries
                            
                            st.info(f"Found {len(customer_numbers)} valid phone numbers from column '{phone_column}'")
                        else:
                            st.error("Could not find a phone number column. Please ensure your CSV has a column named 'phone' or 'number'")
                    
                    except Exception as e:
                        st.error(f"Error reading CSV: {str(e)}")

            # Bulk call button
            if st.button("📞 Make Bulk Calls", type="primary", disabled=not all([api_key]) or not customer_numbers):
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
                        customers=customers,
                        schedule_plan=schedule_plan
                    )
                
                if result["success"]:
                    st.success(f"Bulk calls initiated successfully for {len(customers)} numbers!")
                    call_data = result["data"]
                    st.json(call_data)
                    
                    # Store result in session state
                    call_result = {
                        "timestamp": datetime.now().isoformat(),
                        "type": "Bulk Calls",
                        "assistant": assistant_name,
                        "customer_count": len(customers),
                        "customers": customer_numbers,
                        "call_ids": [],
                        "result": result,
                        "status": "initiated"
                    }
                    
                    # Extract call IDs if available
                    if isinstance(call_data, list):
                        call_ids = [call.get("id") for call in call_data if isinstance(call, dict) and "id" in call]
                        call_result["call_ids"] = call_ids
                        
                        # Start monitoring if enabled
                        if auto_monitor:
                            for call_id in call_ids:
                                st.session_state.call_monitoring[call_id] = {
                                    "api_key": api_key,
                                    "start_time": datetime.now(),
                                    "customer": "bulk_call",
                                    "assistant": assistant_name
                                }
                    
                    st.session_state.call_results.append(call_result)
                else:
                    st.error(f"Bulk calls failed: {result['error']}")
                    if result.get('status_code'):
                        st.error(f"Status Code: {result['status_code']}")

    # Right column - Call History and Monitoring
    with col2:
        st.header("📋 Call Management")
        
        # Active Call Monitoring
        if st.session_state.call_monitoring:
            st.subheader("🔍 Active Call Monitoring")
            
            # Auto-refresh for monitoring
            if auto_monitor:
                time.sleep(1)  # Small delay for UI responsiveness
                
                for call_id, monitor_info in list(st.session_state.call_monitoring.items()):
                    elapsed = (datetime.now() - monitor_info["start_time"]).total_seconds()
                    
                    if elapsed > 300:  # Stop monitoring after 5 minutes
                        del st.session_state.call_monitoring[call_id]
                        continue
                    
                    # Check call status
                    status_result = monitor_call_status(monitor_info["api_key"], call_id)
                    
                    if status_result["success"]:
                        status = status_result["status"]
                        
                        with st.expander(f"📞 {call_id[:8]}... - {status.upper()}"):
                            st.write(f"**Customer:** {monitor_info['customer']}")
                            st.write(f"**Assistant:** {monitor_info['assistant']}")
                            st.write(f"**Status:** {status}")
                            st.write(f"**Duration:** {int(elapsed)}s")
                            
                            # If call is complete, show transcript and recording options
                            if status in ["ended", "completed"]:
                                call_data = status_result["data"]
                                
                                # Display transcript
                                if status_result.get("has_transcript"):
                                    st.subheader("📝 Transcript")
                                    transcript = call_data.get("transcript", "No transcript available")
                                    st.text_area("Call Transcript", transcript, height=100)
                                
                                # Display recording download
                                if status_result.get("has_recording"):
                                    recording_url = call_data.get("recordingUrl")
                                    if recording_url:
                                        st.subheader("🎵 Recording")
                                        if st.button(f"Download Recording", key=f"download_{call_id}"):
                                            with st.spinner("Downloading recording..."):
                                                recording_result = download_call_recording(monitor_info["api_key"], recording_url)
                                                if recording_result["success"]:
                                                    st.download_button(
                                                        label="💾 Save Recording",
                                                        data=recording_result["data"],
                                                        file_name=f"call_{call_id[:8]}.mp3",
                                                        mime="audio/mpeg"
                                                    )
                                                else:
                                                    st.error(f"Failed to download recording: {recording_result['error']}")
                                
                                # Remove from monitoring once complete
                                del st.session_state.call_monitoring[call_id]
                            
                            # Manual refresh button
                            if st.button("🔄 Refresh", key=f"refresh_{call_id}"):
                                st.rerun()

        # Manual monitoring controls
        st.subheader("🎛️ Manual Monitoring")
        manual_call_id = st.text_input("Enter Call ID to monitor", placeholder="call-id-here")
        
        if st.button("🔍 Check Call Status") and manual_call_id and api_key:
            with st.spinner("Checking call status..."):
                status_result = monitor_call_status(api_key, manual_call_id)
                
                if status_result["success"]:
                    st.success(f"Call Status: {status_result['status']}")
                    call_data = status_result["data"]
                    
                    # Show transcript
                    if status_result.get("has_transcript"):
                        st.subheader("📝 Transcript")
                        transcript = call_data.get("transcript", "No transcript available")
                        st.text_area("Call Transcript", transcript, height=150)
                    
                    # Show recording download
                    if status_result.get("has_recording"):
                        recording_url = call_data.get("recordingUrl")
                        if recording_url:
                            st.subheader("🎵 Recording")
                            if st.button("Download Recording", key="manual_download"):
                                with st.spinner("Downloading recording..."):
                                    recording_result = download_call_recording(api_key, recording_url)
                                    if recording_result["success"]:
                                        st.download_button(
                                            label="💾 Save Recording",
                                            data=recording_result["data"],
                                            file_name=f"call_{manual_call_id[:8]}.mp3",
                                            mime="audio/mpeg"
                                        )
                                    else:
                                        st.error(f"Failed to download recording: {recording_result['error']}")
                    
                    # Show full call data
                    with st.expander("📊 Full Call Data"):
                        st.json(call_data)
                else:
                    st.error(f"Failed to get call status: {status_result['error']}")

        st.divider()

        # Call History
        st.subheader("📚 Call History")
        
        if st.session_state.call_results:
            # Export button
            csv_data = export_call_history()
            if csv_data:
                st.download_button(
                    label="📥 Export History (CSV)",
                    data=csv_data,
                    file_name=f"call_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            # Clear history button
            if st.button("🗑️ Clear History", type="secondary"):
                st.session_state.call_results = []
                st.success("Call history cleared!")
                st.rerun()
            
            # Display recent calls
            st.write(f"**Total Calls:** {len(st.session_state.call_results)}")
            
            for i, call in enumerate(reversed(st.session_state.call_results[-10:])):  # Show last 10 calls
                with st.expander(f"📞 {call.get('type', 'Unknown')} - {call.get('timestamp', '')[:16]}"):
                    st.write(f"**Assistant:** {call.get('assistant', 'N/A')}")
                    st.write(f"**Customer:** {call.get('customer', 'N/A')}")
                    if call.get('customer_name'):
                        st.write(f"**Name:** {call.get('customer_name')}")
                    st.write(f"**Status:** {call.get('status', 'N/A')}")
                    if call.get('call_id'):
                        st.code(f"Call ID: {call.get('call_id')}")
                    if call.get('notes'):
                        st.write(f"**Notes:** {call.get('notes')}")
                    
                    # Show bulk call details
                    if call.get('type') == 'Bulk Calls':
                        st.write(f"**Customer Count:** {call.get('customer_count', 0)}")
                        if call.get('call_ids'):
                            st.write(f"**Call IDs:** {len(call.get('call_ids', []))}")
        else:
            st.info("No calls made yet. Start by making your first call!")

    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>📞 Vapi Outbound Calling Pro | Built with Streamlit</p>
        <p><small>Monitor your calls, download transcripts, and manage your outbound campaigns efficiently.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
