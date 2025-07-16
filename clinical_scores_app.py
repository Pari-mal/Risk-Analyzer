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

# Example placeholder data to avoid runtime errors on initial load
age = st.number_input("Age", 0)
sex = st.selectbox("Sex", ["Male", "Female"])
rr = st.number_input("Respiratory Rate", 0)
spo2 = st.number_input("SpO₂", 0.0)
o2_use = st.selectbox("Oxygen Therapy?", ["No", "Yes"])
temp = st.number_input("Temperature (°C)", 0.0)
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

# Clean interpretation without emojis
def clean_interpretation(text):
    return ''.join(char for char in text if ord(char) < 128)

# Minimal PDF export logic using temporary file workaround
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

if st.button("Download PDF Report"):
    dummy_data = pd.DataFrame({
        "Score": ["NEWS2", "PNI"],
        "Value": [5, 45.2],
        "Interpretation": ["Medium risk – urgent review", "Good nutritional-immune status"]
    })
    pdf_bytes = create_pdf(dummy_data, patient_name, report_date)
    st.download_button(
        label="Download PDF",
        data=pdf_bytes,
        file_name=f"{patient_name}_clinical_score_summary.pdf",
        mime="application/pdf"
    )
