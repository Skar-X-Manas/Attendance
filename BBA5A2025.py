import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_sheets"], scope)
client = gspread.authorize(creds)

# Open the sheet by name
sheet = client.open("RGUATTEND")
worksheet = sheet.worksheet("BBASectionA")  # 👈 use your actual sheet/tab name here

# Get the data as a DataFrame
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# --- Ensure Required Columns ---
required_columns = {"sl no", "roll no", "names"}
if not required_columns.issubset(df.columns):
    st.error("Sheet is missing required columns: sl no, roll no, names")
    st.stop()

# --- UI: Date Selection ---
date = st.date_input("Select Attendance Date", datetime.date.today())
date_col = date.strftime("%Y-%m-%d")

# --- Add date column if missing ---
if date_col not in df.columns:
    df[date_col] = 0

# --- Initialize Attendance State ---
if "attendance" not in st.session_state:
    st.session_state.attendance = df.set_index("roll no")[date_col].astype(bool).to_dict()

# --- Count Refresh Function ---
def refresh_counts():
    present_count = sum(st.session_state.attendance.values())
    absentees_count = len(df) - present_count
    return present_count, absentees_count

# --- Search Bar ---
search_query = st.text_input("Search by Name or Roll No").strip().lower()
filtered_df = df[df["names"].str.lower().str.contains(search_query, na=False) |
                 df["roll no"].astype(str).str.contains(search_query, na=False)] if search_query else df

# --- Display Present/Absent Counts ---
st.session_state.present_count, st.session_state.absentees_count = refresh_counts()
col1, col2, col3 = st.columns(3)
col1.metric("Present", st.session_state.present_count)
col2.metric("Absentees", st.session_state.absentees_count)
if col3.button("Refresh"):
    st.session_state.present_count, st.session_state.absentees_count = refresh_counts()

# --- Attendance Checkboxes ---
st.write("### Mark Attendance")
for _, row in filtered_df.iterrows():
    roll_no = row["roll no"]
    is_present = st.checkbox(f"{row['names']} ({roll_no})", value=st.session_state.attendance.get(roll_no, False))
    st.session_state.attendance[roll_no] = is_present

# --- Save Attendance to Google Sheet ---
if st.button("Save Attendance"):
    df[date_col] = df["roll no"].map(lambda x: int(st.session_state.attendance.get(x, False)))
    worksheet.update([df.columns.tolist()] + df.values.tolist())
    st.success("Attendance saved to Google Sheets!")

# --- Export Absentees ---
if st.button("Export Absentees"):
    absentees = df[df[date_col] == 0][["sl no", "roll no", "names"]]
    if absentees.empty:
        st.info("No absentees to export for the selected date.")
    else:
        absentee_csv = absentees.to_csv(index=False).encode('utf-8')
        st.download_button("Download Absentees CSV", absentee_csv, file_name=f"absentees_{date_col}.csv", mime="text/csv")

