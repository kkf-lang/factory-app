from datetime import datetime
import io
from github import Github
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Factory Production & Attendance App", layout="wide"
)

st.title("🏭 Factory Production & Attendance Management System")


# ==========================================
# GITHUB FUNCTIONS
# ==========================================
def get_github_repo():
  """Streamlit Secrets မှ Token နှင့် Repo ကိုယူ၍ GitHub Repository သို့ ချိတ်ဆက်ခြင်း"""
  token = st.secrets["github"]["access_token"]
  repo_name = st.secrets["github"]["repo"]
  g = Github(token)
  return g.get_repo(repo_name)


def load_data():
  """GitHub ပေါ်ရှိ production_data.csv ဖိုင်မှ Data များကို ဖတ်ယူခြင်း"""
  try:
    repo = get_github_repo()
    file_content = repo.get_contents("production_data.csv")
    decoded_content = file_content.decoded_content.decode("utf-8")
    df = pd.read_csv(io.StringIO(decoded_content))
    return df
  except Exception as e:
    # ဖိုင်မရှိသေးပါက သို့မဟုတ် Error ဖြစ်ပါက Headers အမှန်ပါသော DataFrame ကို ပြန်ပေးမည်
    return pd.DataFrame(columns=[
        "ID",
        "Date",
        "Department",
        "Production",
        "Prod_Unit",
        "Cutting",
        "Cut_Unit",
        "Net_Damage_RE",
        "Damage_Grade",
        "Damage_Unit",
        "Attendance",
        "OT",
        "Notes",
        "Timestamp",
    ])


def save_data_to_github(new_row_df):
  """Data အသစ်ထည့်သွင်းသည့်အခါ GitHub ပေါ်ရှိ production_data.csv သို့ အလိုအလျောက် Overwrite/Update လုပ်ခြင်း"""
  try:
    repo = get_github_repo()
    file = repo.get_contents("production_data.csv")
    existing_df = pd.read_csv(io.StringIO(file.decoded_content.decode("utf-8")))

    # Data အဟောင်းနှင့် အသစ်ကို ပေါင်းစပ်ခြင်း
    updated_df = pd.concat([existing_df, new_row_df], ignore_index=True)
    csv_content = updated_df.to_csv(index=False)

    # GitHub ပေါ်ရှိဖိုင်ကို Update လုပ်ခြင်း (SHA ဖြင့် ချိတ်ဆက်သည်)
    repo.update_file(
        path="production_data.csv",
        message="Add new production record via Streamlit App",
        content=csv_content,
        sha=file.sha,
    )
    st.success(
        "✅ Data များကို GitHub သို့ အောင်မြင်စွာ တိုက်ရိုက် သိမ်းဆည်းပြီးပါပြီ!"
    )
  except Exception as e:
    st.error(f"❌ GitHub သို့ သိမ်းဆည်းရာတွင် အမှားအယွင်းရှိပါသည်: {e}")


# ==========================================
# MAIN APP INTERFACE
# ==========================================

# Mode ရွေးချယ်ရန် (Admin Portal သို့မဟုတ် Data Entry)
st.sidebar.title("System Navigation")
mode = st.sidebar.selectbox("Select Mode", ["Admin Portal", "Data Entry Form"])

# Data များကို Load လုပ်ခြင်း
df = load_data()

if mode == "Data Entry Form":
  st.subheader("📝 Production & Attendance Entry Form")

  with st.form("production_form"):
    col1, col2 = st.columns(2)

    with col1:
      selected_date = st.date_input("Date", value=datetime.today())
      department = st.selectbox(
          "Department",
          ["Stretching", "Scouring", "Mending-1", "Mending-2", "Packing"],
      )
      production = st.number_input("Production", min_value=0, value=0)
      prod_unit = st.selectbox(
          "Production Unit", ["pcs", "pot", "kg"], key="p_unit"
      )
      cutting = st.number_input("Cutting", min_value=0, value=0)
      cut_unit = st.selectbox("Cutting Unit", ["pcs", "kg", "pot"], key="c_unit")

    with col2:
      net_damage = st.number_input("Net Damage (RE)", min_value=0, value=0)
      damage_grade = st.selectbox(
          "Damage Grade", ["grade_A", "grade_B", "grade_C"]
      )
      damage_unit = st.selectbox(
          "Damage Unit", ["pcs", "pot", "kg"], key="d_unit"
      )
      attendance = st.number_input("Attendance", min_value=0, value=1)
      ot = st.number_input("OT (Hours)", min_value=0.0, value=0.0, step=0.5)

    notes = st.text_area("Notes / Remarks")

    submit_button = st.form_submit_button("💾 Submit & Save to GitHub")

    if submit_button:
      # 自動 ID ဖန်တီးခြင်း (DataFrame ထဲတွင် ရှိပြီးသား ID အပေါ် မူတည်၍)
      next_id = int(df["ID"].max() + 1) if not df.empty and "ID" in df.columns else 1

      new_data = {
          "ID": [next_id],
          "Date": [str(selected_date)],
          "Department": [department],
          "Production": [production],
          "Prod_Unit": [prod_unit],
          "Cutting": [cutting],
          "Cut_Unit": [cut_unit],
          "Net_Damage_RE": [net_damage],
          "Damage_Grade": [damage_grade],
          "Damage_Unit": [damage_unit],
          "Attendance": [attendance],
          "OT": [ot],
          "Notes": [notes],
          "Timestamp": [str(datetime.now())],
      }

      new_row_df = pd.DataFrame(new_data)

      # GitHub သို့ တိုက်ရိုက်သိမ်းဆည်းသည့် Function ကို ခေါ်သုံးခြင်း
      save_data_to_github(new_row_df)

      # App ကို Refresh လုပ်ခြင်း
      st.rerun()

elif mode == "Admin Portal":
  st.subheader("📊 Admin Portal & Data Viewer")

  if df.empty:
    st.warning(
        "⚠️ လက်လွယ်စရာ Data များ မရှိသေးပါ။ (သို့မဟုတ် GitHub မှ ဖိုင်အလွတ်ကို"
        " ဖတ်နေရပါသည်)"
    )
  else:
    # Filter Options
    st.markdown("### 🔍 Filter Data")
    col1, col2, col3 = st.columns(3)

    with col1:
      start_date = st.date_input("Start Date", value=pd.to_datetime("today"))
    with col2:
      end_date = st.date_input("End Date", value=pd.to_datetime("today"))
    with col3:
      dept_list = (
          ["All"] + list(df["Department"].unique())
          if "Department" in df.columns
          else ["All"]
      )
      selected_dept = st.selectbox("Filter by Department", dept_list)

    # Filtering Logic
    filtered_df = df.copy()
    if "Date" in filtered_df.columns:
      filtered_df["Date"] = pd.to_datetime(filtered_df["Date"])
      filtered_df = filtered_df[
          (filtered_df["Date"] >= pd.to_datetime(start_date))
          & (filtered_df["Date"] <= pd.to_datetime(end_date))
      ]

    if selected_dept != "All":
      filtered_df = filtered_df[filtered_df["Department"] == selected_dept]

    # Display Table
    st.dataframe(filtered_df, use_container_width=True)

    # Summary Statistics
    st.markdown("### 📈 Summary Statistics")
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
      st.metric(
          "Total Attendance",
          int(filtered_df["Attendance"].sum())
          if "Attendance" in filtered_df.columns
          else 0,
      )
    with sc2:
      st.metric(
          "Total OT",
          float(filtered_df["OT"].sum()) if "OT" in filtered_df.columns else 0.0,
      )
    with sc3:
      st.metric(
          "Total Production",
          int(filtered_df["Production"].sum())
          if "Production" in filtered_df.columns
          else 0,
      )
    with sc4:
      st.metric(
          "Total Damage",
          int(filtered_df["Net_Damage_RE"].sum())
          if "Net_Damage_RE" in filtered_df.columns
          else 0,
      )