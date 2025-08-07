import streamlit as st
import pandas as pd
import datetime

# Load attendance file
file_path = "Attendance.csv"
try:
    df = pd.read_csv(file_path).dropna(axis=1, how='all')  # Remove unnamed columns if any
except FileNotFoundError:
    st.error("Attendance.csv not found!")
    st.stop()

# Ensure required columns exist
required_columns = {"sl no", "roll no", "names"}
if not required_columns.issubset(df.columns):
    st.error("CSV file is missing required columns!")
    st.stop()

# UI for date selection
date = st.date_input("Select Attendance Date", datetime.date.today())
date_col = date.strftime("%Y-%m-%d")

# Add date column if not present
df[date_col] = df.get(date_col, 0)

# Initialize attendance state if not present
if "attendance" not in st.session_state:
    st.session_state.attendance = df.set_index("roll no")[date_col].astype(bool).to_dict()

# Function to refresh the counts
def refresh_counts():
    present_count = sum(st.session_state.attendance.values())
    absentees_count = len(df) - present_count
    return present_count, absentees_count

# Search bar
search_query = st.text_input("Search by Name or Roll No").strip().lower()
filtered_df = df[df["names"].str.lower().str.contains(search_query, na=False) |
                  df["roll no"].astype(str).str.contains(search_query, na=False)] if search_query else df

# Display Present and Absentees count
st.session_state.present_count, st.session_state.absentees_count = refresh_counts()
col1, col2, col3 = st.columns(3)
col1.metric("Present", st.session_state.present_count)
col2.metric("Absentees", st.session_state.absentees_count)
if col3.button("Refresh"):
    st.session_state.present_count, st.session_state.absentees_count = refresh_counts()

# Display student list with checkboxes
st.write("### Mark Attendance")
for _, row in filtered_df.iterrows():
    roll_no = row["roll no"]
    is_present = st.checkbox(f"{row['names']} ({roll_no})", value=st.session_state.attendance[roll_no])
    st.session_state.attendance[roll_no] = is_present

# Save attendance
if st.button("Save Attendance"):
    df[date_col] = df["roll no"].map(lambda x: int(st.session_state.attendance[x]))
    df.to_csv(file_path, index=False)
    st.success("Attendance saved successfully!")
