from datetime import datetime, date, timedelta
import io
from github import Github
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Factory Data Collection System", page_icon="🏭", layout="wide"
)

# Admin Password
ADMIN_PASSWORD = "admin123"


# ==========================================
# GITHUB API FUNCTIONS (Permanent Cloud Storage)
# ==========================================
def get_github_repo():
  """Streamlit Secrets မှ Token နှင့် Repo ကိုယူ၍ GitHub Repository သို့ ချိတ်ဆက်ခြင်း"""
  token = st.secrets["github"]["access_token"]
  repo_name = st.secrets["github"]["repo"]
  g = Github(token)
  return g.get_repo(repo_name)


def load_data():
  """GitHub ပေါ်ရှိ production_data.csv ဖိုင်မှ Data များကို ဖတ်ယူခြင်း"""
  columns = [
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
  ]
  try:
    repo = get_github_repo()
    file_content = repo.get_contents("production_data.csv")
    decoded_content = file_content.decoded_content.decode("utf-8")
    df = pd.read_csv(io.StringIO(decoded_content))

    for col in columns:
      if col not in df.columns:
        df[col] = ""

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime(
        "%Y-%m-%d"
    )
    df = df.dropna(subset=["Date"])
    return df
  except Exception:
    return pd.DataFrame(columns=columns)


def save_to_github(df_updated, commit_message="Update production data via app"):
  """DataFrame အသစ်ကို GitHub ပေါ်ရှိ production_data.csv သို့ တိုက်ရိုက် Overwrite/Update လုပ်ခြင်း"""
  try:
    repo = get_github_repo()
    file = repo.get_contents("production_data.csv")
    csv_content = df_updated.to_csv(index=False)
    repo.update_file(
        path="production_data.csv",
        message=commit_message,
        content=csv_content,
        sha=file.sha,
    )
    return True
  except Exception as e:
    st.error(f"❌ GitHub သို့ သိမ်းဆည်းရာတွင် အမှားအယွင်းရှိပါသည်: {e}")
    return False


# Sidebar Navigation
st.sidebar.header("📌 System Navigation")
app_mode = st.sidebar.selectbox(
    "Select Mode", ["📝 Data Entry (Staff)", "🔐 Admin Portal"]
)

if app_mode == "📝 Data Entry (Staff)":
  st.title("🏭 Factory Production & Attendance Data Entry")
  st.markdown(
      "ဝန်ထမ်းများအနေဖြင့် နေ့စဉ် Data များကို ဤနေရာတွင် ဝင်ရောက်"
      " ဖြည့်သွင်းနိုင်ပါသည်။ *(Attendance, OT နှင့် Production တို့ကို"
      " မဖြစ်မနေ ဖြည့်သွင်းရပါမည်။ Production သည် 0 ထက်ကြီးရပါမည်)*"
  )
  st.markdown("---")

  with st.form("staff_data_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
      entry_date = st.date_input("Date", value=date.today())
      department = st.selectbox(
          "Department",
          [
              "Extruding MoNo",
              "Weaving",
              "Packing MoNo",
              "Mending-1",
              "Scouring",
              "Scouting RE",
              "Stretching",
          ],
      )

      attendance = st.number_input(
          "Attendance (Employee) *",
          min_value=0.0,
          step=1.0,
          value=0.0,
          format="%.0f",
      )
      ot = st.number_input("OT (Employee) *", min_value=0.0, step=0.5, value=0.0)
      notes = st.text_area(
          "Remarks / Notes", placeholder="မှတ်ချက်များ (လိုအပ်ပါက)..."
      )

    with col2:
      col_p1, col_p2 = st.columns([2, 1])
      with col_p1:
        production = st.number_input(
            "Production *", min_value=0.0, step=1.0, value=0.0, key="prod_input"
        )
      with col_p2:
        prod_unit = st.selectbox("Unit", ["kg", "pcs", "pot"], key="p_unit")

      col_c1, col_c2 = st.columns([2, 1])
      with col_c1:
        cutting = st.number_input(
            "Cutting", min_value=0.0, step=1.0, value=0.0, key="cut_input"
        )
      with col_c2:
        cut_unit = st.selectbox("Unit", ["kg", "pcs", "pot"], key="c_unit")

      col_d1, col_d2, col_d3 = st.columns([2, 1, 1])
      with col_d1:
        net_damage = st.number_input(
            "Net_Damage_RE", min_value=0.0, step=1.0, value=0.0, key="dmg_input"
        )
      with col_d2:
        damage_grade = st.selectbox(
            "Grade", ["grade_B", "grade_C", "grade_A"], key="d_grade"
        )
      with col_d3:
        damage_unit = st.selectbox(
            "Unit", ["kg", "pcs", "pot"], key="d_unit"
        )

    submit_btn = st.form_submit_button("💾 Submit & Save Entry")

    if submit_btn:
      if production <= 0.0:
        st.error(
            "❌ ကျေးဇူးပြု၍ **Production** ပမာဏကို ထည့်သွင်းပေးပါရန်။"
            " Production သည် 0 ထက် ကြီးရပါမည်။"
        )
      elif attendance == 0.0 and ot == 0.0:
        st.error(
            "❌ ကျေးဇူးပြု၍ **Attendance** သို့မဟုတ် **OT** အနည်းဆုံး တစ်ခုခု"
            " ဖြည့်သွင်းပေးပါရန်။"
        )
      else:
        df_existing = load_data()
        current_time = datetime.now()

        if not df_existing.empty and "Timestamp" in df_existing.columns:
          df_existing["Parsed_Time"] = pd.to_datetime(
              df_existing["Timestamp"], errors="coerce"
          )
          recent_df = df_existing[
              (df_existing["Department"] == department)
              & (df_existing["Parsed_Time"] >= (current_time - timedelta(minutes=5)))
          ]

          if len(recent_df) >= 2:
            st.error(
                f"⏳ '{department}' ဌာနအတွက် ၅ မိနစ်အတွင်း Data ၂ ကြိမ်"
                " ထည့်သွင်းပြီးဖြစ်ပါသည်။ ကျေးဇူးပြု၍ ၅ မိနစ်ခန့် စောင့်ဆိုင်းပြီးမှ"
                " ထပ်မံထည့်သွင်းပါ။"
            )
          else:
            new_id = (
                int(df_existing["ID"].max() + 1)
                if pd.notna(df_existing["ID"].max())
                and not df_existing["ID"].empty
                else 1
            )

            new_data = pd.DataFrame([{
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
                "Timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            }])

            df_updated = pd.concat(
                [
                    df_existing.drop(columns=["Parsed_Time"], errors="ignore"),
                    new_data,
                ],
                ignore_index=True,
            )
            if save_to_github(
                df_updated, commit_message=f"Add record ID {new_id}"
            ):
              st.success(
                  "✅ Data များကို GitHub သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။"
                  " ကျေးဇူးတင်ပါသည်။"
              )
        else:
          new_id = 1
          new_data = pd.DataFrame([{
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
              "Timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
          }])
          if save_to_github(
              new_data, commit_message=f"Add first record ID {new_id}"
          ):
            st.success(
                "✅ Data များကို GitHub သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။"
                " ကျေးဇူးတင်ပါသည်။"
            )

elif app_mode == "🔐 Admin Portal":
  st.title("🔐 Admin Management Portal")
  st.markdown(
      "ဤနေရာသည် Admin များအတွက်သာဖြစ်ပြီး Data များကို စီမံခန့်ခွဲခြင်းနှင့်"
      " Report ထုတ်ခြင်းများ ပြုလုပ်နိုင်ပါသည်။"
  )
  st.markdown("---")

  if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

  if not st.session_state.is_admin:
    with st.form("admin_login_form"):
      entered_password = st.text_input(
          "Enter Admin Password", type="password"
      )
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

    admin_tab = st.radio(
        "Admin Navigation",
        [
            "📊 Data Filtering & Management",
            "📑 Advanced Report Module",
        ],
        horizontal=True,
    )

    df = load_data()

    if admin_tab == "📊 Data Filtering & Management":
      st.header("📈 Data Filtering & Management")

      if not df.empty:
        st.subheader("🔍 Filter Data (Date Range & Options)")

        valid_dates = pd.to_datetime(df["Date"], errors="coerce").dropna()
        min_d = (
            valid_dates.min().date() if not valid_dates.empty else date.today()
        )
        max_d = (
            valid_dates.max().date() if not valid_dates.empty else date.today()
        )

        col_date1, col_date2 = st.columns(2)
        with col_date1:
          start_date = st.date_input("Start Date", min_d, key="mgmt_start")
        with col_date2:
          end_date = st.date_input("End Date", max_d, key="mgmt_end")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
          dept_filter = st.selectbox(
              "Filter by Department",
              ["All"] + list(df["Department"].unique()),
              key="mgmt_dept",
          )
        with col_f2:
          grade_filter = st.selectbox(
              "Filter by Damage Grade",
              ["All"] + list(df["Damage_Grade"].unique()),
              key="mgmt_grade",
          )

        filtered_df = df.copy()
        filtered_df["Date_Obj"] = pd.to_datetime(
            filtered_df["Date"], errors="coerce"
        ).dt.date
        filtered_df = filtered_df[
            (filtered_df["Date_Obj"] >= start_date)
            & (filtered_df["Date_Obj"] <= end_date)
        ]
        filtered_df = filtered_df.drop(columns=["Date_Obj"])

        if dept_filter != "All":
          filtered_df = filtered_df[filtered_df["Department"] == dept_filter]
        if grade_filter != "All":
          filtered_df = filtered_df[filtered_df["Damage_Grade"] == grade_filter]

        st.dataframe(filtered_df, use_container_width=True)

        st.subheader("📊 Summary Statistics")
        col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
        col_sum1.metric(
            "Total Attendance", f"{filtered_df['Attendance'].sum():,.0f}"
        )
        col_sum2.metric("Total OT", f"{filtered_df['OT'].sum():,.1f}")
        col_sum3.metric(
            "Total Production", f"{filtered_df['Production'].sum():,.0f}"
        )
        col_sum4.metric(
            "Total Damage", f"{filtered_df['Net_Damage_RE'].sum():,.0f}"
        )

        st.markdown("---")

        st.subheader("✏️ Select Record ID to Load Data & Edit/Delete")
        record_ids = filtered_df["ID"].tolist() if "ID" in filtered_df.columns else []

        if record_ids:
          selected_id = st.selectbox("Select Record ID", record_ids)
          selected_row = df[df["ID"] == selected_id].iloc[0]

          with st.form("edit_delete_form"):
            st.info(f"📌 Currently Selected Record ID: {selected_id}")

            parsed_selected_date = pd.to_datetime(
                selected_row["Date"], errors="coerce"
            )
            default_edit_date = (
                parsed_selected_date.date()
                if pd.notna(parsed_selected_date)
                else date.today()
            )
            e_date = st.date_input("Date", value=default_edit_date)

            dept_list = [
                "Extruding MoNo",
                "Weaving",
                "Packing MoNo",
                "Mending-1",
                "Scouring",
                "Scouting RE",
                "Stretching",
            ]
            curr_dept = selected_row["Department"]
            e_dept = st.selectbox(
                "Department",
                dept_list,
                index=dept_list.index(curr_dept)
                if curr_dept in dept_list
                else 0,
            )

            col_e1, col_e2 = st.columns(2)
            with col_e1:
              e_prod = st.number_input(
                  "Production", value=float(selected_row["Production"])
              )
              p_units = ["kg", "pcs", "pot"]
              p_u_curr = str(selected_row["Prod_Unit"])
              e_prod_unit = st.selectbox(
                  "Prod Unit",
                  p_units,
                  index=p_units.index(p_u_curr) if p_u_curr in p_units else 0,
              )
              e_cut = st.number_input(
                  "Cutting", value=float(selected_row["Cutting"])
              )
              c_units = ["kg