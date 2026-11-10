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

# Function to load saved data
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
    st.markdown("ဝန်ထမ်းများအနေဖြင့် နေ့စဉ် Data များကို ဤနေရာတွင် ဝင်ရောက် ဖြည့်သွင်းနိုင်ပါသည်။ (ဌာနတစ်ခုလျှင် ၂ ကြိမ်ထက်ပို၍ ချက်ချင်းဆက်တိုက် မထည့်နိုင်ပါ၊ ၅ မိနစ် စောင့်ဆိုင်းရပါမည်)")
    st.markdown("---")
    
    with st.form("staff_data_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            entry_date = st.date_input("Date", datetime.now())
            department = st.selectbox(
                "Department", 
                ["Extruding MoNo", "Weaving", "Packing MoNo", "Mending-1", "Scouring", "Scouting RE", "Stretching"]
            )
            
            attendance = st.number_input("Attendance (Employee)", min_value=0.0, step=1.0)
            ot = st.number_input("OT (Employee)", min_value=0.0, step=0.5)
            notes = st.text_area("Remarks / Notes", placeholder="မှတ်ချက်များ (လိုအပ်ပါက)...")

        with col2:
            col_p1, col_p2 = st.columns([2, 1])
            with col_p1:
                production = st.number_input("Production", min_value=0.0, step=1.0, key="prod_input")
            with col_p2:
                prod_unit = st.selectbox("Unit", ["kg", "pcs", "pot"], key="p_unit")
            
            col_c1, col_c2 = st.columns([2, 1])
            with col_c1:
                cutting = st.number_input("Cutting", min_value=0.0, step=1.0, key="cut_input")
            with col_c2:
                cut_unit = st.selectbox("Unit", ["kg", "pcs", "pot"], key="c_unit")
            
            col_d1, col_d2, col_d3 = st.columns([2, 1, 1])
            with col_d1:
                net_damage = st.number_input("Net_Damage_RE", min_value=0.0, step=1.0, key="dmg_input")
            with col_d2:
                damage_grade = st.selectbox("Grade", ["grade_B", "grade_C", "grade_A"], key="d_grade")
            with col_d3:
                damage_unit = st.selectbox("Unit", ["kg", "pcs", "pot"], key="d_unit")

        submit_btn = st.form_submit_button("💾 Submit & Save Entry")
        
        if submit_btn:
            df_existing = load_data()
            current_time = datetime.now()
            
            if not df_existing.empty and "Timestamp" in df_existing.columns:
                df_existing["Parsed_Time"] = pd.to_datetime(df_existing["Timestamp"], errors="coerce")
                recent_df = df_existing[
                    (df_existing["Department"] == department) & 
                    (df_existing["Parsed_Time"] >= (current_time - timedelta(minutes=5)))
                ]
                
                if len(recent_df) >= 2:
                    st.error(f"⏳ '{department}' ဌာနအတွက် ၅ မိနစ်အတွင်း Data ၂ ကြိမ် ထည့်သွင်းပြီးဖြစ်ပါသည်။ ကျေးဇူးပြု၍ ၅ မိနစ်ခန့် စောင့်ဆိုင်းပြီးမှ ထပ်မံထည့်သွင်းပါ။")
                else:
                    new_id = int(df_existing["ID"].max() + 1) if pd.notna(df_existing["ID"].max()) else 1
                    
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
                        "Notes": notes,
                        "Timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    
                    df_updated = pd.concat([df_existing.drop(columns=["Parsed_Time"], errors="ignore"), new_data], ignore_index=True)
                    df_updated.to_csv(DATA_FILE, index=False)
                    
                    st.success("✅ Data များကို စနစ်အတွင်းသို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။ ကျေးဇူးတင်ပါသည်။")
            else:
                new_id = 1
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
                    "Notes": notes,
                    "Timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
                }])
                new_data.to_csv(DATA_FILE, index=False)
                st.success("✅ Data များကို စနစ်အတွင်းသို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။ ကျေးဇူးတင်ပါသည်။")

elif app_mode == "🔐 Admin Portal":
    st.title("🔐 Admin Management Portal")
    st.markdown("ဤနေရာသည် Admin များအတွက်သာဖြစ်ပြီး Data များကို စီမံခန့်ခွဲခြင်းနှင့် Report ထုတ်ခြင်းများ ပြုလုပ်နိုင်ပါသည်။")
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
        
        # Admin Sub-Navigation (Management vs Reports)
        admin_tab = st.radio("Admin Navigation", ["📊 Data Filtering & Management", "📑 Advanced Report Module"], horizontal=True)
        
        df = load_data()
        
        if admin_tab == "📊 Data Filtering & Management":
            st.header("📈 Data Filtering & Management")
            
            if not df.empty:
                st.subheader("🔍 Filter Data (Date Range & Options)")
                
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    start_date = st.date_input("Start Date", pd.to_datetime(df["Date"]).min().date() if not df.empty else date.today(), key="mgmt_start")
                with col_date2:
                    end_date = st.date_input("End Date", pd.to_datetime(df["Date"]).max().date() if not df.empty else date.today(), key="mgmt_end")
                
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    dept_filter = st.selectbox("Filter by Department", ["All"] + list(df["Department"].unique()), key="mgmt_dept")
                with col_f2:
                    grade_filter = st.selectbox("Filter by Damage Grade", ["All"] + list(df["Damage_Grade"].unique()), key="mgmt_grade")
                
                filtered_df = df.copy()
                filtered_df["Date_Obj"] = pd.to_datetime(filtered_df["Date"]).dt.date
                filtered_df = filtered_df[(filtered_df["Date_Obj"] >= start_date) & (filtered_df["Date_Obj"] <= end_date)]
                filtered_df = filtered_df.drop(columns=["Date_Obj"])
                
                if dept_filter != "All":
                    filtered_df = filtered_df[filtered_df["Department"] == dept_filter]
                if grade_filter != "All":
                    filtered_df = filtered_df[filtered_df["Damage_Grade"] == grade_filter]
                
                st.dataframe(filtered_df, use_container_width=True)
                
                st.subheader("📊 Summary Statistics")
                col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
                col_sum1.metric("Total Attendance", f"{filtered_df['Attendance'].sum():,.0f}")
                col_sum2.metric("Total OT", f"{filtered_df['OT'].sum():,.1f}")
                col_sum3.metric("Total Production", f"{filtered_df['Production'].sum():,.0f}")
                col_sum4.metric("Total Damage", f"{filtered_df['Net_Damage_RE'].sum():,.0f}")
                
                st.markdown("---")
                
                st.subheader("✏️ Select Record ID to Load Data & Edit/Delete")
                record_ids = filtered_df["ID"].tolist() if "ID" in filtered_df.columns else []
                
                if record_ids:
                    selected_id = st.selectbox("Select Record ID", record_ids)
                    selected_row = df[df["ID"] == selected_id].iloc[0]
                    
                    with st.form("edit_delete_form"):
                        st.info(f"📌 Currently Selected Record ID: {selected_id}")
                        
                        e_date = st.date_input("Date", pd.to_datetime(selected_row["Date"]))
                        
                        dept_list = ["Extruding MoNo", "Weaving", "Packing MoNo", "Mending-1", "Scouring", "Scouting RE", "Stretching"]
                        curr_dept = selected_row["Department"]
                        dept_idx = dept_list.index(curr_dept) if curr_dept in dept_list else 0
                        e_dept = st.selectbox("Department", dept_list, index=dept_idx)
                        
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            e_prod = st.number_input("Production", value=float(selected_row["Production"]))
                            
                            p_units = ["kg", "pcs", "pot"]
                            p_u_curr = str(selected_row["Prod_Unit"])
                            e_prod_unit = st.selectbox("Prod Unit", p_units, index=p_units.index(p_u_curr) if p_u_curr in p_units else 0)
                            
                            e_cut = st.number_input("Cutting", value=float(selected_row["Cutting"]))
                            
                            c_units = ["kg", "pcs", "pot"]
                            c_u_curr = str(selected_row["Cut_Unit"])
                            e_cut_unit = st.selectbox("Cut Unit", c_units, index=c_units.index(c_u_curr) if c_u_curr in c_units else 0)
                            
                        with col_e2:
                            e_dmg = st.number_input("Net_Damage_RE", value=float(selected_row["Net_Damage_RE"]))
                            
                            grades = ["grade_B", "grade_C", "grade_A"]
                            g_curr = str(selected_row["Damage_Grade"])
                            e_grade = st.selectbox("Grade", grades, index=grades.index(g_curr) if g_curr in grades else 0)
                            
                            d_units = ["kg", "pcs", "pot"]
                            d_u_curr = str(selected_row["Damage_Unit"])
                            e_dmg_unit = st.selectbox("Damage Unit", d_units, index=d_units.index(d_u_curr) if d_u_curr in d_units else 0)
                            
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
                
                col_dl, col_ul = st.columns(2)
                with col_dl:
                    csv = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Filtered Data as CSV File",
                        data=csv,
                        file_name=f"factory_data_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                with col_ul:
                    uploaded_file = st.file_uploader("📤 Upload Backup CSV File", type=["csv"], key="mgmt_upload")
                    if uploaded_file is not None:
                        try:
                            uploaded_df = pd.read_csv(uploaded_file)
                            uploaded_df.to_csv(DATA_FILE, index=False)
                            st.success("✅ Backup CSV ဖိုင်ကို အောင်မြင်စွာ Upload တင်ပြီး Data များ Restore လုပ်ပြီးပါပြီ။")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ ဖိုင်တင်ရာတွင် အမှားအယွင်းရှိပါသည်: {e}")
            else:
                st.info("ℹ️ လက်ရှိတွင် သိမ်းဆည်းထားသော Data မရှိသေးပါ။")
                uploaded_file = st.file_uploader("📤 Upload Backup CSV File", type=["csv"], key="mgmt_upload_empty")
                if uploaded_file is not None:
                    try:
                        uploaded_df = pd.read_csv(uploaded_file)
                        uploaded_df.to_csv(DATA_FILE, index=False)
                        st.success("✅ Backup CSV ဖိုင်ကို အောင်မြင်စွာ Upload တင်ပြီး Data များ Restore လုပ်ပြီးပါပြီ။")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ ဖိုင်တင်ရာတွင် အမှားအယွင်းရှိပါသည်: {e}")

        elif admin_tab == "📑 Advanced Report Module":
            st.header("📑 Factory Advanced Report Module")
            st.markdown("ဤကဏ္ဍတွင် ရက်စွဲအလိုက် (Date-to-Date) နှင့် ဌာနအလိုက် (Department Filter) ပြည့်စုံသော Report များကို ထုတ်ယူနိုင်ပါသည်။")
            st.markdown("---")
            
            if not df.empty:
                # Report Filtering Controls
                st.subheader("🛠️ Report Parameters & Filters")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    rep_start_date = st.date_input("Report Start Date", pd.to_datetime(df["Date"]).min().date() if not df.empty else date.today(), key="rep_start")
                with col_r2:
                    rep_end_date = st.date_input("Report End Date", pd.to_datetime(df["Date"]).max().date() if not df.empty else date.today(), key="rep_end")
                
                col_r3, col_r4 = st.columns(2)
                with col_r3:
                    rep_dept = st.selectbox("Select Department for Report", ["All Departments"] + list(df["Department"].unique()), key="rep_dept")
                with col_r4:
                    rep_grade = st.selectbox("Select Damage Grade", ["All Grades"] + list(df["Damage_Grade"].unique()), key="rep_grade")
                
                # Apply Report Filters
                report_df = df.copy()
                report_df["Date_Obj"] = pd.to_datetime(report_df["Date"]).dt.date
                report_df = report_df[(report_df["Date_Obj"] >= rep_start_date) & (report_df["Date_Obj"] <= rep_end_date)]
                report_df = report_df.drop(columns=["Date_Obj"])
                
                if rep_dept != "All Departments":
                    report_df = report_df[report_df["Department"] == rep_dept]
                if rep_grade != "All Grades":
                    report_df = report_df[report_df["Damage_Grade"] == rep_grade]
                
                st.markdown("---")
                st.subheader(f"📋 Report Results ({rep_start_date} မှ {rep_end_date} အထိ)")
                
                if not report_df.empty:
                    # Metrics Summary for Report
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Records", f"{len(report_df)}")
                    m2.metric("Total Attendance", f"{report_df['Attendance'].sum():,.0f}")
                    m3.metric("Total Production", f"{report_df['Production'].sum():,.0f}")
                    m4.metric("Total Net Damage", f"{report_df['Net_Damage_RE'].sum():,.0f}")
                    
                    st.markdown("---")
                    st.dataframe(report_df, use_container_width=True)
                    
                    # Department-wise breakdown if All Departments selected
                    if rep_dept == "All Departments":
                        st.subheader("📊 Department-wise Summary Breakdown")
                        dept_summary = report_df.groupby("Department")[["Production", "Cutting", "Net_Damage_RE", "Attendance", "OT"]].sum().reset_index()
                        st.dataframe(dept_summary, use_container_width=True)
                    
                    st.markdown("---")
                    # Export Report Button
                    rep_csv = report_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Official Report as CSV",
                        data=rep_csv,
                        file_name=f"factory_official_report_{rep_start_date}_to_{rep_end_date}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ ရွေးချယ်ထားသော ရက်စွဲ (သို့မဟုတ်) အချက်အလက်များနှင့် ကိုက်ညီသော Report Data မရှိပါ။")
            else:
            
                st.info("ℹ️ လက်ရှိတွင် Report ထုတ်ရန် Data မရှိသေးပါ။")