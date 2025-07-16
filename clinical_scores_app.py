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

# Unit toggle for international users
unit_option = st.radio("Select units for protein measurements:", ["g/dL", "g/L"], index=0)
unit_multiplier = 10 if unit_option == "g/dL" else 1

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
albumin = st.number_input(f"Albumin ({unit_option})", 0.0)
bilirubin = st.number_input("Bilirubin (mg/dL)", 0.0)
creatinine = st.number_input("Creatinine", 0.0)
bun = st.number_input("BUN", 0.0)
glucose = st.number_input("Glucose", 0.0)
hba1c = st.number_input("HbA1c", 0.0)
ast = st.number_input("AST", 0.0)
alt = st.number_input("ALT", 0.0)
total_protein = st.number_input(f"Total Protein ({unit_option})", 0.0)
globulin = st.number_input(f"Globulin ({unit_option})", 0.0)

# Score calculations
def calculate_scores():
    scores = []

    # Convert units
    bilirubin_umol = bilirubin * 17.1  # mg/dL to μmol/L
    albumin_gl = albumin * unit_multiplier  # g/dL or g/L to g/L
    total_protein_gl = total_protein * unit_multiplier
    globulin_gl = globulin * unit_multiplier

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
    if avpu != "A": news2 += 3

    news2_note = "High risk – urgent response" if news2 >= 7 else "Medium risk – urgent review" if news2 >= 5 else "Low risk – monitor" if news2 >= 1 else "No risk"
    scores.append(["NEWS2", news2, news2_note])

    # PNI
    pni = albumin_gl * 1 + 0.005 * lymphocytes * 1000
    pni_note = "Good nutritional-immune status" if pni >= 45 else "Mild malnutrition/inflammation" if pni >= 40 else "Severe malnutrition/inflammation"
    scores.append(["PNI", round(pni, 2), pni_note])

    # SII
    sii = (neutrophils * platelets) / (lymphocytes + 1e-5)
    sii_note = "High inflammation" if sii > 900 else "Moderate inflammation" if sii > 600 else "Low inflammation"
    scores.append(["SII", round(sii, 2), sii_note])

    # SIRI
    siri = (neutrophils * monocytes) / (lymphocytes + 1e-5)
    siri_note = "High immune response" if siri > 1.5 else "Moderate immune response" if siri > 1.0 else "Low immune response"
    scores.append(["SIRI", round(siri, 2), siri_note])

    # CURB-65
    curb = 0
    if confusion == "Yes": curb += 1
    if urea > 7: curb += 1
    if rr >= 30: curb += 1
    if sbp < 90: curb += 1
    if age >= 65: curb += 1
    curb_note = "Severe pneumonia – consider ICU" if curb >= 3 else "Moderate – hospitalize" if curb == 2 else "Mild – outpatient possible"
    scores.append(["CURB-65", curb, curb_note])

    # ALBI
    albi = (math.log10(bilirubin_umol + 1e-5) * 0.66) + (albumin_gl * -0.085)
    albi_note = "Grade 3 – Poor liver function" if albi > -1.39 else "Grade 2 – Moderate" if albi > -2.60 else "Grade 1 – Good liver function"
    scores.append(["ALBI", round(albi, 2), albi_note])

    # eGFR (MDRD)
    egfr = 175 * (creatinine ** -1.154) * (age ** -0.203) * (0.742 if sex == "Female" else 1)
    egfr_note = "Normal" if egfr >= 90 else "Mild CKD" if egfr >= 60 else "Moderate CKD" if egfr >= 30 else "Severe CKD"
    scores.append(["eGFR", round(egfr, 2), egfr_note])

    # UAR
    uar = urea / albumin_gl if albumin_gl else 0
    uar_note = "High catabolism/inflammation" if uar > 10 else "Moderate" if uar > 6 else "Normal"
    scores.append(["UAR", round(uar, 2), uar_note])

    # SHR
    if hba1c > 0:
        estimated_mean_glucose = (28.7 * hba1c) - 46.7
        shr = glucose / estimated_mean_glucose
        shr_note = "Stress hyperglycemia" if shr > 1.14 else "Expected glycemic profile"
        scores.append(["SHR", round(shr, 2), shr_note])

    # ALT/Platelet ratio
    alt_platelet = alt / platelets if platelets else 0
    alt_note = "Possible liver fibrosis" if alt_platelet > 0.02 else "Low risk"
    scores.append(["ALT/Platelet", round(alt_platelet, 4), alt_note])

    # Globulin/Total Protein
    gtp = globulin_gl / total_protein_gl if total_protein_gl else 0
    gtp_note = "High immune activity" if gtp > 0.5 else "Normal"
    scores.append(["Globulin/TP", round(gtp, 2), gtp_note])

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
