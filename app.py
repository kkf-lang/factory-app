import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="Factory Data Collection System",
    page_icon="🏭",
    layout="wide"
)

# CSV File name for permanent storage
DATA_FILE = "production_data.csv"

# Admin Password (လိုသလို ပြောင်းလဲနိုင်ပါသည်)
ADMIN_PASSWORD = "admin123"

# Function to load saved data
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_csv(DATA_FILE)
        except Exception:
            return pd.DataFrame(columns=["Date", "Department", "Unit", "Attendance", "OT (Hrs)", "Production", "Cutting", "Damage", "Notes"])
    else:
        return pd.DataFrame(columns=["Date", "Department", "Unit", "Attendance", "OT (Hrs)", "Production", "Cutting", "Damage", "Notes"])

# Sidebar Navigation & Role Control
st.sidebar.header("📌 System Navigation")
app_mode = st.sidebar.selectbox("Select Mode", ["📝 Data Entry (Staff)", "🔐 Admin Portal"])

if app_mode == "📝 Data Entry (Staff)":
    st.title("🏭 Factory Production & Attendance Data Entry")
    st.markdown("ဝန်ထမ်းများအနေဖြင့် နေ့စဉ် Data များကို ဤနေရာတွင် ဝင်ရောက် ဖြည့်သွင်းနိုင်ပါသည်။")
    st.markdown("---")
    
    with st.form("staff_data_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            entry_date = st.date_input("Date", datetime.now())
            department = st.selectbox("Department", ["Extruding MoNo", "Weaving","Mending-1","Scouring","Scouring RE","Stretching","Stretching QC","Mending-2","Packing MoNo"])
            unit = st.selectbox("Unit", ["kg", "pcs", "pot"])
            attendance = st.number_input("Attendance (Count/Hours)", min_value=0.0, step=1.0)
            ot = st.number_input("OT (Hours)", min_value=0.0, step=0.5)

        with col2:
            production = st.number_input("Production", min_value=0.0, step=1.0)
            cutting = st.number_input("Cutting", min_value=0.0, step=1.0)
            damage = st.number_input("Damage", min_value=0.0, step=1.0)
            notes = st.text_area("Remarks / Notes", placeholder="မှတ်ချက်များ (လိုအပ်ပါက)...")

        submit_btn = st.form_submit_button("💾 Submit & Save Entry")
        
        if submit_btn:
            new_data = pd.DataFrame([{
                "Date": entry_date.strftime("%Y-%m-%d"),
                "Department": department,
                "Unit": unit,
                "Attendance": attendance,
                "OT": ot,
                "Production": production,
                "Cutting": cutting,
                "Damage": damage,
                "Notes": notes
            }])
            
            df_existing = load_data()
            df_updated = pd.concat([df_existing, new_data], ignore_index=True)
            df_updated.to_csv(DATA_FILE, index=False)
            
            st.success("✅ Data များကို စနစ်အတွင်းသို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။ ကျေးဇူးတင်ပါသည်။")

elif app_mode == "🔐 Admin Portal":
    st.title("🔐 Admin Management Portal")
    st.markdown("ဤနေရာသည် Admin များအတွက်သာဖြစ်ပြီး Password ဖြင့် ဝင်ရောက်ရမည်ဖြစ်ပါသည်။")
    st.markdown("---")
    
    # Password Protection Session State
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
        
    if not st.session_state.is_admin:
        with st.form("admin_login_form"):
            entered_password = st.text_input("Enter Admin Password", type="password")
            login_btn = st.form_submit_button("Login")
            
            if login_btn:
                if entered_password == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.success("🎉 Admin Login အောင်မြင်ပါသည်။")
                    st.rerun()
                else:
                    st.error("❌ Password မှားယွင်းနေပါသည်။")
    else:
        st.success("🔓 Admin အဖြစ် ဝင်ရောက်ထားပါသည်။")
        if st.button("🔒 Logout"):
            st.session_state.is_admin = False
            st.rerun()
            
        st.markdown("---")
        st.header("📈 Saved Data & Statistics (Admin View)")
        
        df = load_data()
        
        if not df.empty:
            # Display Table
            st.dataframe(df, use_container_width=True)
            
            # Quick Statistics Summary
            st.subheader("📊 Summary Statistics")
            col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
            col_sum1.metric("Total Attendance", f"{df['Attendance'].sum():,.0f}")
            col_sum2.metric("Total OT Hours", f"{df['OT (Hrs)'].sum():,.1f} hrs")
            col_sum3.metric("Total Production", f"{df['Production'].sum():,.0f}")
            col_sum4.metric("Total Damage", f"{df['Damage'].sum():,.0f}")
            
            st.markdown("---")
            
            # Download as CSV Button (Admin only)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download All Data as CSV File",
                data=csv,
                file_name=f"factory_production_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Delete All Data Option
            if st.button("🗑️ Clear All Saved Data"):
                if os.path.exists(DATA_FILE):
                    os.path.exists(DATA_FILE)
                    os.remove(DATA_FILE)
                    st.success("🔄 Data အားလုံးကို ဖျက်ပြီးပါပြီ။")
                    st.rerun()
        else:
            st.info("ℹ️ လက်ရှိတွင် သိမ်းဆည်းထားသော Data မရှိသေးပါ။")
