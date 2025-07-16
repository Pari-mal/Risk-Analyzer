import streamlit as st
import numpy as np
import pandas as pd
from fpdf import FPDF
import math
import tempfile

# 🧑‍⚕️ Patient Info Input
st.title("Clinical Risk Score Analyzer")
st.subheader("Patient Information")
patient_name = st.text_input("Patient Name")
report_date = st.date_input("Report Date")

# Inputs
age = st.number_input("Age", 0)
sex = st.selectbox("Sex", ["Male", "Female"])
rr = st.number_input("Respiratory Rate", 0)
spo2 = st.number_input("SpO₂", 0.0)
o2_use = st.selectbox("Oxygen Therapy?", ["No", "Yes"])
temp_f = st.number_input("Temperature (°F)", 94.0, 108.0)
temp = (temp_f - 32) * 5.0/9.0  # Celsius internally
sbp = st.number_input("Systolic BP", 0)
hr = st.number_input("Heart Rate", 0)
avpu = st.selectbox("AVPU", ["A", "V", "P", "U"])
confusion = st.selectbox("Confusion", ["No", "Yes"])
urea = st.number_input("Urea", 0.0)
neutrophils = st.number_input("Neutrophils", 0.0)
lymphocytes = st.number_input("Lymphocytes", 0.0)
monocytes = st.number_input("Monocytes", 0.0)
platelets = st.number_input("Platelets", 0.0)
albumin = st.number_input("Albumin", 0.0)
bilirubin = st.number_input("Bilirubin", 0.0)
creatinine = st.number_input("Creatinine", 0.0)
bun = st.number_input("BUN", 0.0)
glucose = st.number_input("Glucose", 0.0)
hba1c = st.number_input("HbA1c", 0.0)
ast = st.number_input("AST", 0.0)
alt = st.number_input("ALT", 0.0)
total_protein = st.number_input("Total Protein", 0.0)
globulin = st.number_input("Globulin", 0.0)

# Score calculations
def calculate_scores():
    scores = []

    # NEWS2
    news2 = 0
    if rr <= 8 or rr >= 25: news2 += 3
    elif rr in range(21, 25): news2 += 2
    elif rr in range(9, 11): news2 += 1
    if spo2 < 92: news2 += 3
    elif 92 <= spo2 <= 93: news2 += 2
    elif 94 <= spo2 <= 95: news2 += 1
    if o2_use == "Yes": news2 += 2
    if sbp <= 90 or sbp >= 220: news2 += 3
    elif 91 <= sbp <= 100: news2 += 2
    elif 101 <= sbp <= 110: news2 += 1
    if hr <= 40 or hr >= 131: news2 += 3
    elif 111 <= hr <= 130: news2 += 2
    elif 91 <= hr <= 110: news2 += 1
    if temp <= 35.0 or temp >= 39.1: news2 += 3
    elif 38.1 <= temp <= 39.0: news2 += 1
    if avpu == "V": news2 += 3
    elif avpu == "P" or avpu == "U": news2 += 3

    if news2 >= 7:
        news2_note = "High risk – urgent response"
    elif news2 >= 5:
        news2_note = "Medium risk – urgent review"
    elif news2 >= 1:
        news2_note = "Low risk – monitor"
    else:
        news2_note = "No risk"
    scores.append(["NEWS2", news2, news2_note])

    # PNI
    pni = albumin * 10 + 0.005 * lymphocytes * 1000
    if pni >= 45:
        pni_note = "Good nutritional-immune status"
    elif 40 <= pni < 45:
        pni_note = "Mild malnutrition/inflammation"
    else:
        pni_note = "Severe malnutrition/inflammation"
    scores.append(["PNI", round(pni, 2), pni_note])

    # More scores can be added here using similar logic

    return pd.DataFrame(scores, columns=["Score", "Value", "Interpretation"])

# Clean interpretation
def clean_interpretation(text):
    return ''.join(char for char in text if ord(char) < 128)

# PDF generation
def create_pdf(dataframe, name, date):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Clinical Score Summary", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Patient: {name}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {date}", ln=True)
    pdf.ln(5)
    col_widths = [40, 30, 120]

    for i, row in dataframe.iterrows():
        interp = clean_interpretation(row['Interpretation'])
        pdf.cell(col_widths[0], 10, str(row['Score']), 1)
        pdf.cell(col_widths[1], 10, str(row['Value']), 1)
        pdf.cell(col_widths[2], 10, str(interp), 1)
        pdf.ln()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        pdf.output(tmp_file.name)
        tmp_file.seek(0)
        pdf_data = tmp_file.read()

    return pdf_data

# Main UI
if st.button("Calculate and Download PDF Report"):
    results_df = calculate_scores()
    st.dataframe(results_df)
    pdf_bytes = create_pdf(results_df, patient_name, report_date)
    st.download_button(
        label="Download PDF",
        data=pdf_bytes,
        file_name=f"{patient_name}_clinical_score_summary.pdf",
        mime="application/pdf"
    )
