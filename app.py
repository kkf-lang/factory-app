import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import requests
import json
import io
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Page configuration
st.set_page_config(
    page_title="Factory Data Collection System",
    page_icon="🏭",
    layout="wide"
)

# Admin Password
ADMIN_PASSWORD = "admin123"

# GitHub Configuration from Streamlit Secrets
try:
    GITHUB_TOKEN = st.secrets["github"]["access_token"]
    GITHUB_REPO = st.secrets["github"]["repo"]
except Exception:
    st.error("❌ GitHub Secrets are not configured correctly in Streamlit Cloud Settings.")
    st.stop()

# Local CSV File name (acting as a temporary cache)
LOCAL_DATA_FILE = "production_data.csv"
GITHUB_DATA_FILE_PATH = "production_data.csv" # Path inside the repo

# Define the data schema
COLUMNS = [
    "ID", "Date", "Department", 
    "Production", "Prod_Unit", 
    "Cutting", "Cut_Unit", 
    "Net_Damage_RE", "Damage_Grade", "Damage_Unit", 
    "Attendance", "OT", "Notes", "Timestamp"
]

# Configure Requests with Retries for better reliability
def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Function to load data directly from GitHub CSV file
def load_data_from_github():
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_DATA_FILE_PATH}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3.raw"
        }
        response = requests_retry_session().get(url, headers=headers)
        
        if response.status_code == 200:
            csv_content = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_content))
            # Strict date conversion to prevent day/month mix-ups
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
            df = df.dropna(subset=["Date"])
            # Cache the file locally to speed up cooldonwn checks
            df.to_csv(LOCAL_DATA_FILE, index=False)
            return df
        elif response.status_code == 404:
            # File does not exist yet
            return pd.DataFrame(columns=COLUMNS)
        else:
            # Other GitHub API error
            st.error(f"❌ Failed to load data from GitHub: {response.status_code} - {response.text}")
            return pd.DataFrame(columns=COLUMNS)
    except Exception as e:
        # Network or other error
        st.warning(f"⚠️ Unable to connect to GitHub. Loading from local cache if available. Error: {e}")
        try:
            # Fallback to local cache if available
            return pd.read_csv(LOCAL_DATA_FILE)
        except Exception:
            # Local cache also not available
            return pd.DataFrame(columns=COLUMNS)

# Function to save data (append a new row) back to GitHub CSV file
def save_data_to_github(new_row_dict):
    df_existing = load_data_from_github()
    df_new_row = pd.DataFrame([new_row_dict])
    
    # Combined DataFrame
    df_updated = pd.concat([df_existing, df_new_row], ignore_index=True)
    
    # Convert DataFrame back to CSV content
    csv_content = df_updated.to_csv(index=False).encode('utf-8')
    
    # Push updated CSV content to GitHub
    try:
        # Get the current file's SHA (required for updating)
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_DATA_FILE_PATH}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3.json"
        }
        response = requests_retry_session().get(url, headers=headers)
        sha = None
        if response.status_code == 200:
            sha = response.json().get('sha')
        elif response.status_code != 404:
             st.error(f"❌ Failed to push data: Could not fetch SHA. Code: {response.status_code}")
             return False

        # Build the commit payload
        payload = {
            "message": f"Add production data record ID: {new_row_dict['ID']}",
            "content": csv_content.decode('ascii'), # API needs base64 decoded as string
            "sha": sha
        }
        
        # API expects content as base64 string
        import base64
        payload['content'] = base64.b64encode(csv_content).decode('ascii')

        # Put the new content back to GitHub
        put_response = requests_retry_session().put(url, headers=headers, data=json.dumps(payload))
        
        if put_response.status_code in [200, 201]:
            st.success(f"✅ Data record saved successfully and synced to GitHub repo `{GITHUB_REPO}`.")
            return True
        else:
            st.error(f"❌ Failed to push updated data to GitHub: {put_response.status_code} - {put_response.text}")
            return False
            
    except Exception as e:
        st.error(f"❌ Sync Error: An unexpected error occurred while syncing with GitHub: {e}")
        return False

# Sidebar Navigation
st.sidebar.header("📌 System Navigation")
app_mode = st.sidebar.selectbox("Select Mode", ["📝 Data Entry (Staff)", "🔐 Admin Portal"])

# Load data initially and display current state
st.sidebar.markdown(f"**Permanent Storage:** Syncing with GitHub repo `{GITHUB_REPO}`.")
df_all = load_data_from_github()

if app_mode == "📝 Data Entry (Staff)":
    st.title("🏭 Factory Production & Attendance Data Entry")
    st.markdown("ဝန်ထမ်းများအနေဖြင့် နေ့စဉ် Data များကို ဤနေရာတွင် ဝင်ရောက် ဖြည့်သွင်းနိုင်ပါသည်။ *(Attendance, OT နှင့် Production တို့ကို မဖြစ်မနေ ဖြည့်သွင်းရပါမည်။ Production သည် 0 ထက်ကြီးရပါမည်)*")
    st.markdown("---")
    
    with st.form("staff_data_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            entry_date = st.date_input("Date", value=date.today())
            department = st.selectbox(
                "Department", 
                ["Extruding MoNo", "Weaving", "Packing MoNo", "Mending-1", "Scouring", "Scouting RE", "Stretching"]
            )
            
            attendance = st.number_input("Attendance (Employee) *", min_value=0.0, step=1.0, value=0.0, format="%.0f")
            ot = st.number_input("OT (Employee) *", min_value=0.0, step=0.5, value=0.0)
            notes = st.text_area("Remarks / Notes", placeholder="မှတ်ချက်များ (လိုအပ်ပါက)...")

        with col2:
            col_p1, col_p2 = st.columns([2, 1])
            with col_p1:
                production = st.number_input("Production *", min_value=0.0, step=1.0, value=0.0, key="prod_input")
            with col_p2:
                prod_unit = st.selectbox("Unit", ["kg", "pcs", "pot"], key="p_unit")
            
            col_c1, col_c2 = st.columns([2, 1])
            with col_c1:
                cutting = st.number_input("Cutting", min_value=0.0, step=1.0, value=0.0, key="cut_input")
            with col_c2:
                cut_unit = st.selectbox("Unit", ["kg", "pcs", "pot"], key="c_unit")
            
            col_d1, col_d2, col_d3 = st.columns([2, 1, 1])
            with col_d1:
                net_damage = st.number_input("Net_Damage_RE", min_value=0.0, step=1.0, value=0.0, key="dmg_input")
            with col_d2:
                damage_grade = st.selectbox("Grade", ["grade_B", "grade_C", "grade_A"], key="d_grade")
            with col_d3:
                damage_unit = st.selectbox("Unit", ["kg", "pcs", "pot"], key="d_unit")

        submit_btn = st.form_submit_button("💾 Submit & Save Entry")
        
        if submit_btn:
            # Mandatory Validation Check
            if production <= 0.0:
                st.error("❌ ကျေးဇူးပြု၍ **Production** ပမာဏကို ထည့်သွင်းပေးပါရန်။ Production သည် 0 ထက် ကြီးရပါမည်။")
            elif attendance == 0.0 and ot == 0.0:
                 st.error("❌ ကျေးဇူးပြု၍ **Attendance** သို့မဟုတ် **OT** အနည်းဆုံး တစ်ခုခု ဖြည့်သွင်းပေးပါရန်။")
            else:
                # Cooldown logic (5 mins for the same department)
                # Ensure Timestamp check uses local cache for performance
                try:
                    df_cache = pd.read_csv(LOCAL_DATA_FILE)
                except:
                    df_cache = df_all # Fallback if cache fails
                
                current_time = datetime.now()
                
                cooldown_active = False
                if not df_cache.empty and "Timestamp" in df_cache.columns and "Department" in df_cache.columns:
                    # Convert to datetime for comparison
                    timestamps = pd.to_datetime(df_cache["Timestamp"], errors='coerce')
                    # Find records within the last 5 minutes for the same department
                    # Filter for non-NaT values before comparisons
                    valid_mask = timestamps.notna()
                    recent_records = df_cache[valid_mask & (df_cache["Department"] == department)]
                    recent_timestamps = timestamps[valid_mask & (df_cache["Department"] == department)]
                    
                    recent_df = recent_records[
                        (recent_timestamps >= (current_time - timedelta(minutes=5)))
                    ]
                    
                    if len(recent_df) >= 2:
                        cooldown_active = True
                        st.error(f"⏳ '{department}' ဌာနအတွက် ၅ မိနစ်အတွင်း Data ၂ ကြိမ် ထည့်သွင်းပြီးဖြစ်ပါသည်။ ကျေးဇူးပြု၍ ၅ မိနစ်ခန့် စောင့်ဆိုင်းပြီးမှ ထပ်မံထည့်သွင်းပါ။")

                if not cooldown_active:
                    # Generate a new ID based on current GitHub data
                    new_id = int(df_all["ID"].max() + 1) if not df_all.empty and "ID" in df_all.columns and pd.notna(df_all["ID"].max()) else 1
                    
                    # Prepare the new record dictionary
                    new_data_dict = {
                        "ID": new_id,
                        "Date": entry_date.strftime("%Y-%m-%d"),
                        "Department": department,
                        "Production": float(production),
                        "Prod_Unit": str(prod_unit),
                        "Cutting": float(cutting),
                        "Cut_Unit": str(cut_unit),
                        "Net_Damage_RE": float(net_damage),
                        "Damage_Grade": str(damage_grade),
                        "Damage_Unit": str(damage_unit),
                        "Attendance": float(attendance),
                        "OT": float(ot),
                        "Notes": str(notes),
                        "Timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Save the new data record back to GitHub and update local state
                    if save_data_to_github(new_data_dict):
                        st.balloons()
                        # Update the main DataFrame state for other parts of the app
                        # But wait for it to reload to reflect the true sync state.
                        st.info("Reloading main data...")
                        st.rerun() # Reload the whole app to refresh df_all and Admin view

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
        
        admin_tab = st.radio("Admin Navigation", ["📊 Data Filtering & Management", "📑 Advanced Report Module"], horizontal=True)
        
        # Admin Portal uses the global loaded DataFrame df_all
        df = df_all
        
        if admin_tab == "📊 Data Filtering & Management":
            st.header("📈 Data Filtering & Management")
            
            if not df.empty:
                st.subheader("🔍 Filter Data (Date Range & Options)")
                
                valid_dates = pd.to_datetime(df["Date"], errors="coerce").dropna()
                min_d = valid_dates.min().date() if not valid_dates.empty else date.today()
                max_d = valid_dates.max().date() if not valid_dates.empty else date.today()
                
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    start_date = st.date_input("Start Date", min_d, key="mgmt_start")
                with col_date2:
                    end_date = st.date_input("End Date", max_d, key="mgmt_end")
                
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    dept_filter = st.selectbox("Filter by Department", ["All"] + list(df["Department"].unique()), key="mgmt_dept")
                with col_f2:
                    grade_filter = st.selectbox("Filter by Damage Grade", ["All"] + list(df["Damage_Grade"].unique()), key="mgmt_grade")
                
                filtered_df = df.copy()
                filtered_df["Date_Obj"] = pd.to_datetime(filtered_df["Date"], errors="coerce").dt.date
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
                st.info("ℹ️ NOTE: Record Update or Deletion features are currently disabled as they require complex GitHub API merge logic not yet implemented for real-time transactional editing. Use staff mode for entry only.")
                
            else:
                st.info("ℹ️ လက်ရှိတွင် GitHub Repository ထဲ၌ သိမ်းဆည်းထားသော Data မရှိသေးပါ။")

        elif admin_tab == "📑 Advanced Report Module":
            st.header("📑 Factory Advanced Report Module")
            st.markdown("ဤကဏ္ဍတွင် ရက်စွဲအလိုက် (Date-to-Date) နှင့် ဌာနအလိုက် (Department Filter) ပြည့်စုံသော Report များကို ထုတ်ယူနိုင်ပါသည်။")
            st.markdown("---")
            
            if not df.empty:
                valid_dates = pd.to_datetime(df["Date"], errors="coerce").dropna()
                min_d = valid_dates.min().date() if not valid_dates.empty else date.today()
                max_d = valid_dates.max().date() if not valid_dates.empty else date.today()
                
                st.subheader("🛠️ Report Parameters & Filters")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    rep_start_date = st.date_input("Report Start Date", min_d, key="rep_start")
                with col_r2:
                    rep_end_date = st.date_input("Report End Date", max_d, key="rep_end")
                
                col_r3, col_r4 = st.columns(2)
                with col_r3:
                    rep_dept = st.selectbox("Select Department for Report", ["All Departments"] + list(df["Department"].unique()), key="rep_dept")
                with col_r4:
                    rep_grade = st.selectbox("Select Damage Grade", ["All Grades"] + list(df["Damage_Grade"].unique()), key="rep_grade")
                
                report_df = df.copy()
                report_df["Date_Obj"] = pd.to_datetime(report_df["Date"], errors="coerce").dt.date
                report_df = report_df[(report_df["Date_Obj"] >= rep_start_date) & (report_df["Date_Obj"] <= rep_end_date)]
                report_df = report_df.drop(columns=["Date_Obj"])
                
                if rep_dept != "All Departments":
                    report_df = report_df[report_df["Department"] == rep_dept]
                if rep_grade != "All Grades":
                    report_df = report_df[report_df["Damage_Grade"] == rep_grade]
                
                st.markdown("---")
                st.subheader(f"📋 Report Results ({rep_start_date} မှ {rep_end_date} အထိ)")
                
                if not report_df.empty:
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Records", f"{len(report_df)}")
                    m2.metric("Total Attendance", f"{report_df['Attendance'].sum():,.0f}")
                    m3.metric("Total Production", f"{report_df['Production'].sum():,.0f}")
                    m4.metric("Total Net Damage", f"{report_df['Net_Damage_RE'].sum():,.0f}")
                    
                    st.markdown("---")
                    st.dataframe(report_df, use_container_width=True)
                    
                    if rep_dept == "All Departments":
                        st.subheader("📊 Department-wise Summary Breakdown")
                        dept_summary = report_df.groupby("Department")[["Production", "Cutting", "Net_Damage_RE", "Attendance", "OT"]].sum().reset_index()
                        st.dataframe(dept_summary, use_container_width=True)
                    
                    st.markdown("---")
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