import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os

# Page configuration
st.set_page_config(
    page_title="Factory Data Collection System",
    page_icon="🏭",
    layout="wide"
)

# CSV File name for permanent storage
DATA_FILE = "production_data.csv"

# Admin Password
ADMIN_PASSWORD = "admin123"

# Function to load saved data with strict and safe date formatting
def load_data():
    columns = [
        "ID", "Date", "Department", 
        "Production", "Prod_Unit", 
        "Cutting", "Cut_Unit", 
        "Net_Damage_RE", "Damage_Grade", "Damage_Unit", 
        "Attendance", "OT", "Notes", "Timestamp"
    ]
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            
            # Strict date conversion to prevent day/month mix-ups
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
            df = df.dropna(subset=["Date"])
            return df
        except Exception:
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)

# Sidebar Navigation
st.sidebar.header("📌 System Navigation")
app_mode = st.sidebar.selectbox("Select Mode", ["📝 Data Entry (Staff)", "🔐 Admin Portal"])

if app_mode == "📝 Data Entry (Staff)":
    st.title("🏭 Factory Production & Attendance Data Entry")
    st.markdown("ဝန်ထမ်းများအနေဖြင့် နေ့စဉ် Data များကို ဤနေရာတွင် ဝင်ရောက် ဖြည့်သွင်းနိုင်ပါသည်။ *(Attendance, OT နှင့် Production တို့ကို မဖြစ်မနေ ဖြည့်သွင်းရပါမည်)*")
    st.markdown("---")
    
    with st.form("staff_data_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            entry_date = st.date_input("Date", value=date.today())
            department = st.selectbox(
                "Department", 
                ["Extruding MoNo", "Weaving", "Packing MoNo", "Mending-1", "Scouring", "Scouting RE", "Stretching"]
            )
            
            # Use minimal valid value as 0.0 to allow for explicit 'zero' data, but mandatory presence
            attendance = st.number_input("Attendance (Employee) *", min_value=0.0, step=1.0, value=0.0, format="%.0f")
            ot = st.number_input("OT (Employee) *", min_value=0.0, step=0.5, value=0.0)
            notes = st.text_area("Remarks / Notes", placeholder="မှတ်ချက်များ (လိုအပ်ပါက)...")

        with col2:
            col_p1, col_p2 = st.columns([2, 1])
            with col_p1:
                # Require production to be filled
                production = st.number_