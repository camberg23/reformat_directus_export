import streamlit as st
import pandas as pd
import json

st.title("Directus → Clean CSV Converter")
st.write("Upload a Directus JSON export and convert it into a flattened CSV matching the Live Site format.")

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
    out["export_variables_last_updated_at"] = cu.get("export_variables_last_updated_at")

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