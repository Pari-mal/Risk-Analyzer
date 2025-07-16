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

# Urea and BUN inputs with conversion toggle
urea_unit = st.radio("Urea unit:", ["mg/dL", "mmol/L"], index=0)
urea_input = st.number_input("Urea", 0.0)

bun_unit = st.radio("BUN unit:", ["mg/dL", "mmol/L"], index=0)
bun_input = st.number_input("BUN", 0.0)
bun = bun_input if bun_unit == "mg/dL" else bun_input * 2.8

st.write(f"Converted Urea (mmol/L): {urea_input * 0.357:.2f}" if urea_unit == "mg/dL" else f"Entered Urea (mmol/L): {urea_input:.2f}")
st.write(f"Converted BUN (mg/dL): {bun_input:.2f}" if bun_unit == "mg/dL" else f"Converted BUN (mg/dL): {bun:.2f}")

# Prefer urea input, else derive from BUN if urea input is zero
urea = urea_input * 0.357 if urea_unit == "mg/dL" else urea_input
if urea == 0 and bun > 0:
    urea = bun / 2.8

# Add more clinical inputs and calculations below this block as needed

# Clinical and biochemical inputs
age = st.number_input("Age", 0)
sex = st.selectbox("Sex", ["Male", "Female"])
rr = st.number_input("Respiratory Rate", 0)
spo2 = st.number_input("SpO₂ (%)", 0.0)
o2_use = st.selectbox("Oxygen Therapy?", ["No", "Yes"])
temp_f = st.number_input("Temperature (°F)", 94.0, 108.0)
temp = (temp_f - 32) * 5.0 / 9.0
sbp = st.number_input("Systolic Blood Pressure", 0)
hr = st.number_input("Heart Rate", 0)
avpu = st.selectbox("AVPU Scale", ["A", "V", "P", "U"])
confusion = st.selectbox("New Confusion?", ["No", "Yes"])
neutrophils = st.number_input("Neutrophils", 0.0)
lymphocytes = st.number_input("Lymphocytes", 0.0)
monocytes = st.number_input("Monocytes", 0.0)
platelets = st.number_input("Platelets", 0.0)
albumin = st.number_input(f"Albumin ({unit_option})", 0.0) * unit_multiplier
bilirubin = st.number_input("Bilirubin (mg/dL)", 0.0)
creatinine = st.number_input("Creatinine (mg/dL)", 0.0)
glucose = st.number_input("Admission Glucose (mg/dL)", 0.0)
hba1c = st.number_input("HbA1c (%)", 0.0)
ast = st.number_input("AST (U/L)", 0.0)
alt = st.number_input("ALT (U/L)", 0.0)
total_protein = st.number_input(f"Total Protein ({unit_option})", 0.0) * unit_multiplier
globulin = st.number_input(f"Globulin ({unit_option})", 0.0) * unit_multiplier

# Derived parameters
globulin_ratio = globulin / total_protein if total_protein > 0 else 0
alt_platelet_ratio = alt / platelets if platelets > 0 else 0
albi = (math.log10(bilirubin * 17.1) * 0.66) + (-0.085 * albumin) if bilirubin > 0 and albumin > 0 else 0
egfr = 186 * (creatinine ** -1.154) * (age ** -0.203)
if sex == "Female":
    egfr *= 0.742

pn_index = (10 * albumin) + (0.005 * platelets)
sii = (neutrophils * platelets) / lymphocytes if lymphocytes > 0 else 0
siri = (neutrophils * monocytes) / lymphocytes if lymphocytes > 0 else 0
shr = glucose / ((28.7 * hba1c) - 46.7) if hba1c > 0 else 0

# CURB-65
curb = 0
if confusion == "Yes": curb += 1
if bun >= 20: curb += 1
if rr >= 30: curb += 1
if sbp < 90: curb += 1
if age >= 65: curb += 1

# NEWS2
news2 = 0
news2 += 3 if rr <= 8 or rr >= 25 else 1 if rr in [21, 22, 23, 24] else 0
news2 += 2 if spo2 < 92 else 1 if spo2 in [92, 93] else 0
news2 += 2 if o2_use == "Yes" else 0
news2 += 3 if temp < 35 or temp > 39.1 else 1 if temp in [38.1, 39.0] else 0
news2 += 3 if sbp <= 90 or sbp >= 220 else 2 if sbp in range(91, 101) else 1 if sbp in range(101, 111) else 0
news2 += 3 if hr <= 40 or hr >= 131 else 2 if hr in range(111, 131) else 1 if hr in range(91, 111) else 0
news2 += 0 if avpu == "A" else 3

# Score summary
scores = [
    ("NEWS2", news2),
    ("CURB-65", curb),
    ("PNI", round(pn_index, 2)),
    ("SII", round(sii, 2)),
    ("SIRI", round(siri, 2)),
    ("ALBI", round(albi, 3)),
    ("eGFR", round(egfr, 1)),
    ("UAR", round(urea / albumin, 3) if albumin > 0 else 0),
    ("SHR", round(shr, 3)),
    ("ALT/PLT Ratio", round(alt_platelet_ratio, 3)),
    ("Globulin/TP Ratio", round(globulin_ratio, 3))
]

# Display scores and interpretations
st.subheader("Score Summary")
interpretations = []
for score, value in scores:
    interpretation = "Normal"
    if score == "NEWS2" and value >= 7:
        interpretation = "High clinical risk"
    elif score == "CURB-65" and value >= 3:
        interpretation = "Severe pneumonia risk"
    elif score == "ALBI" and value > -2.6:
        interpretation = "Abnormal liver reserve"
    elif score == "eGFR" and value < 60:
        interpretation = "Impaired renal function"
    elif score == "SHR" and value > 1.14:
        interpretation = "Significant stress hyperglycemia"

    flag = "❗" if interpretation != "Normal" else ""
    st.markdown(f"{flag} **{score}**: {value} — {interpretation}")
    interpretations.append(interpretation)

# PDF export
if st.button("Download PDF Report"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Patient: {patient_name} | Date: {report_date}", ln=True)
    pdf.cell(200, 10, txt=f"Protein units: {unit_option}, Urea: {urea_unit}, BUN: {bun_unit}, Temp in °F", ln=True)
    pdf.cell(200, 10, txt="Clinical Risk Scores:", ln=True)

    for (score, value), interpretation in zip(scores, interpretations):
        flag = "❗" if (score == "NEWS2" and value >= 7) or (score == "CURB-65" and value >= 3) else ""
        pdf.multi_cell(0, 10, txt=f"{flag}{score}: {value} - {interpretation}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        with open(tmpfile.name, "rb") as f:
            st.download_button("Download Report", f, file_name="clinical_scores_report.pdf")
st.subheader("Score Summary")
for score, value in scores:
    interpretation = "Normal"
    if score == "NEWS2" and value >= 7:
        interpretation = "High clinical risk"
    elif score == "CURB-65" and value >= 3:
        interpretation = "Severe pneumonia risk"
    elif score == "ALBI" and value > -2.6:
        interpretation = "Abnormal liver reserve"
    elif score == "eGFR" and value < 60:
        interpretation = "Impaired renal function"
    elif score == "SHR" and value > 1.14:
        interpretation = "Significant stress hyperglycemia"

    flag = "❗" if interpretation != "Normal" else ""
    st.markdown(f"{flag} **{score}**: {value} — {interpretation}")
