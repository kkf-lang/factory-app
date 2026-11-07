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

# Admin Password
ADMIN_PASSWORD = "admin123"

# Function to load saved data
def load_data():
    columns = [
        "ID", "Date", "Department", 
        "Production", "Prod_Unit", 
        "Cutting", "Cut_Unit", 
        "Net_Damage_RE", "Damage_Grade", "Damage_Unit", 
        "Attendance", "OT", "Notes"
    ]
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
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
    st.markdown("ဝန်ထမ်းများအနေဖြင့် နေ့စဉ် Data များကို ဤနေရာတွင် ဝင်ရောက် ဖြည့်သွင်းနိုင်ပါသည်။")
    st.markdown("---")
    
    with st.form("staff_data_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            entry_date = st.date_input("Date", datetime.now())
            department = st.selectbox("Department", ["Extruding MoNo", "Weaving", "Mending-1","Scouring","Scouting RE","Stretching","Mending-2
            ","Cutting","Packing MoNo"])
            
            # Attendance & OT
            attendance = st.number_input("Attendance (Employee)", min_value=0.0, step=1.0)
            ot = st.number_input("OT (Employee)", min_value=0.0, step=0.5)
            notes = st.text_area("Remarks / Notes", placeholder="မှတ်ချက်များ (လိုအပ်ပါက)...")

        with col2:
            # Production with Unit
            col_p1, col_p2 = st.columns([2, 1])
            with col_p1:
                production = st.number_input("Production", min_value=0.0, step=1.0, key="prod_input")
            with col_p2:
                prod_unit = st.selectbox("Unit", ["kg", "pcs", "pot","bag"], key="p_unit")
            
            # Cutting with Unit
            col_c1, col_c2 = st.columns([2, 1])
            with col_c1:
                cutting = st.number_input("Cutting", min_value=0.0, step=1.0, key="cut_input")
            with col_c2:
                cut_unit = st.selectbox("Unit", ["kg", "pcs", "pot","bag"], key="c_unit")
            
            # Net_Damage_RE with Grade (B/C) and Unit
            col_d1, col_d2, col_d3 = st.columns([2, 1, 1])
            with col_d1:
                net_damage = st.number_input("Net_Damage_RE", min_value=0.0, step=1.0, key="dmg_input")
            with col_d2:
                damage_grade = st.selectbox("Grade", ["grade_A","grade_B", "grade_C"], key="d_grade")
            with col_d3:
                damage_unit = st.selectbox("Unit", ["kg", "pcs", "pot","bag"], key="d_unit")

        submit_btn = st.form_submit_button("💾 Submit & Save Entry")
        
        if submit_btn:
            df_existing = load_data()
            new_id = int(df_existing["ID"].max() + 1) if not df_existing.empty and "ID" in df_existing.columns and pd.notna(df_existing["ID"].max()) else 1
            
            new_data = pd.DataFrame([{
                "ID": new_id,
                "Date": entry_date.strftime("%Y-%m-%d"),
                "Department": department,
                "Production": production,
                "Prod_Unit": prod_unit,
                "Cutting": cutting,
                "Cut_Unit": cut_unit,
                "Net_Damage_RE": net_damage,
                "Damage_Grade": damage_grade,
                "Damage_Unit": damage_unit,
                "Attendance": attendance,
                "OT": ot,
                "Notes": notes
            }])
            
            df_updated = pd.concat([df_existing, new_data], ignore_index=True)
            df_updated.to_csv(DATA_FILE, index=False)
            
            st.success("✅ Data များကို စနစ်အတွင်းသို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။ ကျေးဇူးတင်ပါသည်။")

elif app_mode == "🔐 Admin Portal":
    st.title("🔐 Admin Management Portal")
    st.markdown("ဤနေရာသည် Admin များအတွက်သာဖြစ်ပြီး Data များကို ကြည့်ရှုခြင်း၊ Filter လုပ်ခြင်း၊ Update နှင့် Delete ပြုလုပ်နိုင်ပါသည်။")
    st.markdown("---")
    
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
        st.header("📈 Data Filtering & Management")
        
        df = load_data()
        
        if not df.empty:
            # --- FILTER SECTION ---
            st.subheader("🔍 Filter Data")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                dept_filter = st.selectbox("Filter by Department", ["All"] + list(df["Department"].unique()))
            with col_f2:
                grade_filter = st.selectbox("Filter by Damage Grade", ["All"] + list(df["Damage_Grade"].unique()))
            
            filtered_df = df.copy()
            if dept_filter != "All":
                filtered_df = filtered_df[filtered_df["Department"] == dept_filter]
            if grade_filter != "All":
                filtered_df = filtered_df[filtered_df["Damage_Grade"] == grade_filter]
            
            # Display Filtered Table
            st.dataframe(filtered_df, use_container_width=True)
            
            # --- SUMMARY STATISTICS ---
            st.subheader("📊 Summary Statistics")
            col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
            col_sum1.metric("Total Attendance", f"{filtered_df['Attendance'].sum():,.0f}")
            col_sum2.metric("Total OT", f"{filtered_df['OT'].sum():,.1f}")
            col_sum3.metric("Total Production", f"{filtered_df['Production'].sum():,.0f}")
            col_sum4.metric("Total Damage", f"{filtered_df['Net_Damage_RE'].sum():,.0f}")
            
            st.markdown("---")
            
            # --- EDIT (UPDATE) & DELETE SECTION ---
            st.subheader("✏️ Update or Delete Specific Record")
            record_ids = filtered_df["ID"].tolist() if "ID" in filtered_df.columns else []
            
            if record_ids:
                selected_id = st.selectbox("Select Record ID to Edit/Delete", record_ids)
                selected_row = df[df["ID"] == selected_id].iloc[0]
                
                with st.form("edit_delete_form"):
                    st.write(f"Editing Record ID: {selected_id}")
                    e_date = st.date_input("Date", pd.to_datetime(selected_row["Date"]))
                    e_dept = st.selectbox("Department", ["Extruding MoNo", "Weaving", "Packing MoNo"], index=["Extruding MoNo", "Weaving", "Packing MoNo"].index(selected_row["Department"]) if selected_row["Department"] in ["Extruding MoNo", "Weaving", "Packing MoNo"] else 0)
                    
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        e_prod = st.number_input("Production", value=float(selected_row["Production"]))
                        e_prod_unit = st.selectbox("Prod Unit", ["kg", "pcs", "pot"], index=["kg", "pcs", "pot"].index(selected_row["Prod_Unit"]) if selected_row["Prod_Unit"] in ["kg", "pcs", "pot"] else 0)
                        e_cut = st.number_input("Cutting", value=float(selected_row["Cutting"]))
                        e_cut_unit = st.selectbox("Cut Unit", ["kg", "pcs", "pot"], index=["kg", "pcs", "pot"].index(selected_row["Cut_Unit"]) if selected_row["Cut_Unit"] in ["kg", "pcs", "pot"] else 0)
                    with col_e2:
                        e_dmg = st.number_input("Net_Damage_RE", value=float(selected_row["Net_Damage_RE"]))
                        e_grade = st.selectbox("Grade", ["grade_B", "grade_C"], index=0 if selected_row["Damage_Grade"]=="grade_B" else 1)
                        e_dmg_unit = st.selectbox("Damage Unit", ["kg", "pcs", "pot"], index=["kg", "pcs", "pot"].index(selected_row["Damage_Unit"]) if selected_row["Damage_Unit"] in ["kg", "pcs", "pot"] else 0)
                        e_att = st.number_input("Attendance", value=float(selected_row["Attendance"]))
                        e_ot = st.number_input("OT", value=float(selected_row["OT"]))
                    
                    e_notes = st.text_area("Notes", value=str(selected_row["Notes"]))
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        update_btn = st.form_submit_button("🔄 Update Record")
                    with col_btn2:
                        delete_btn = st.form_submit_button("🗑️ Delete Record")
                        
                    if update_btn:
                        df.loc[df["ID"] == selected_id, ["Date", "Department", "Production", "Prod_Unit", "Cutting", "Cut_Unit", "Net_Damage_RE", "Damage_Grade", "Damage_Unit", "Attendance", "OT", "Notes"]] = [
                            e_date.strftime("%Y-%m-%d"), e_dept, e_prod, e_prod_unit, e_cut, e_cut_unit, e_dmg, e_grade, e_dmg_unit, e_att, e_ot, e_notes
                        ]
                        df.to_csv(DATA_FILE, index=False)
                        st.success(f"✅ Record ID {selected_id} ကို Update လုပ်ပြီးပါပြီ။")
                        st.rerun()
                        
                    if delete_btn:
                        df = df[df["ID"] != selected_id]
                        df.to_csv(DATA_FILE, index=False)
                        st.success(f"🗑️ Record ID {selected_id} ကို ဖျက်ပြီးပါပြီ။")
                        st.rerun()
            
            st.markdown("---")
            # Download CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download All Data as CSV File",
                data=csv,
                file_name=f"factory_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("ℹ️ လက်ရှိတွင် သိမ်းဆည်းထားသော Data မရှိသေးပါ။")
