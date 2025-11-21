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
# Utility: Flatten a single record
# -------------------------
def flatten_record(rec):
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
# Upload widget
# -------------------------
uploaded = st.file_uploader("Upload Directus JSON file", type=["json"])

if uploaded:
    data = json.load(uploaded)
    # Directus usually gives something like: [{"workplace_users": [...] }]
    root = data[0] if isinstance(data, list) else data
    workplace_users = root.get("workplace_users", [])
    
    if not workplace_users:
        st.error("No workplace_users found in JSON.")
    else:
        # Flatten each user
        rows = [flatten_record(r) for r in workplace_users]
        df = pd.DataFrame(rows)
        
        st.subheader("Preview of Flattened Data")
        st.dataframe(df.head())
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "directus_cleaned_export.csv",
            "text/csv"
        )
        st.success("Conversion complete! You can download the CSV above.")
