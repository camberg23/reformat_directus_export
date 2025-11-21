import streamlit as st
import pandas as pd
import json
from datetime import datetime
from zoneinfo import ZoneInfo

st.title("Directus → Clean CSV Converter")
st.write("Upload a Directus JSON export and convert it into a flattened CSV matching the current site format.")

# -------------------------
# Utility: Convert UTC timestamp to Pacific date
# -------------------------
def utc_to_pacific_date(utc_str):
    """Convert UTC timestamp string to Pacific Time date (YYYY-MM-DD)."""
    if not utc_str:
        return None
    try:
        # Parse the UTC timestamp (handles 'Z' suffix and fractional seconds)
        utc_dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
        # Convert to Pacific Time
        pacific_dt = utc_dt.astimezone(ZoneInfo("America/Los_Angeles"))
        # Return just the date
        return pacific_dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return utc_str  # Return original if parsing fails

# -------------------------
# Utility: Flatten a workplace_user record (OLD FORMAT)
# -------------------------
def flatten_workplace_user(rec):
    """Flatten one workplace_user record into a single row."""
    out = {}
    # folder (simple scalar)
    out["folder"] = rec.get("folder")
    # client_user fields
    cu = rec.get("client_user", {}) or {}
    out["user_name"]  = cu.get("name")
    out["user_email"] = cu.get("email")
    
    # Convert the timestamp to Pacific date
    raw_timestamp = cu.get("export_variables_last_updated_at")
    out["export_variables_last_updated_at"] = utc_to_pacific_date(raw_timestamp)
    
    # export_variables (nested test results)
    ev = cu.get("export_variables") or {}
    if isinstance(ev, dict):
        for k, v in ev.items():
            out[k] = v
    return out

# -------------------------
# Utility: Flatten a test submission record (NEW FORMAT)
# -------------------------
def flatten_test_submission(rec):
    """Flatten one test submission record into a single row."""
    out = {}
    
    # Basic fields
    out["submission_id"] = rec.get("id")
    out["test_id"] = rec.get("test")
    out["type"] = rec.get("type")
    out["website_url"] = rec.get("website_url")
    
    # User info
    user = rec.get("user", {}) or {}
    out["user_email"] = user.get("email")
    
    # Convert timestamp to Pacific date
    raw_timestamp = rec.get("submitted")
    out["export_variables_last_updated_at"] = utc_to_pacific_date(raw_timestamp)
    
    # Flatten variables array into columns
    variables = rec.get("variables", []) or []
    for var_obj in variables:
        if isinstance(var_obj, dict):
            var_info = var_obj.get("variable", {})
            machine_name = var_info.get("machine_name")
            value = var_obj.get("value")
            if machine_name:
                out[machine_name] = value
    
    return out

# -------------------------
# Upload widget
# -------------------------
uploaded = st.file_uploader("Upload Directus JSON file", type=["json"])

if uploaded:
    data = json.load(uploaded)
    
    # Detect format
    if isinstance(data, list) and len(data) > 0:
        first_item = data[0]
        
        # Check if it's the OLD format (workplace_users)
        if "workplace_users" in first_item:
            st.info("Detected: Workplace Users format (old)")
            workplace_users = first_item.get("workplace_users", [])
            if not workplace_users:
                st.error("No workplace_users found in JSON.")
            else:
                rows = [flatten_workplace_user(r) for r in workplace_users]
                df = pd.DataFrame(rows)
        
        # Check if it's the NEW format (test submissions)
        elif "submitted" in first_item and "variables" in first_item:
            st.info("Detected: Test Submissions format (new)")
            rows = [flatten_test_submission(r) for r in data]
            df = pd.DataFrame(rows)
        
        else:
            st.error("Unknown JSON format. Expected either 'workplace_users' or 'submitted' fields.")
            df = None
    else:
        st.error("Invalid JSON structure.")
        df = None
    
    if df is not None:
        st.subheader("Preview of Flattened Data")
        st.dataframe(df.head())
        
        # Show column count
        st.write(f"**Total columns:** {len(df.columns)}")
        st.write(f"**Total rows:** {len(df)}")
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "directus_cleaned_export.csv",
            "text/csv"
        )
        st.success("Conversion complete! You can download the CSV above.")
