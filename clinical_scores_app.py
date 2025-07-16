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
# Prefer urea input, else derive from BUN if non-zero
urea = urea_input * 0.357 if urea_unit == "mg/dL" else urea_input
if urea == 0 and bun_input > 0:
    urea = bun / 2.8
bun_unit = st.radio("BUN unit:", ["mg/dL", "mmol/L"], index=0)
bun_input = st.number_input("BUN", 0.0)
bun = bun_input if bun_unit == "mg/dL" else bun_input * 2.8

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
neutrophils = st.number_input("Neutrophils", 0.0)
lymphocytes = st.number_input("Lymphocytes", 0.0)
monocytes = st.number_input("Monocytes", 0.0)
platelets = st.number_input("Platelets", 0.0)
albumin = st.number_input(f"Albumin ({unit_option})", 0.0)
bilirubin = st.number_input("Bilirubin (mg/dL)", 0.0)
creatinine = st.number_input("Creatinine", 0.0)
glucose = st.number_input("Glucose", 0.0)
hba1c = st.number_input("HbA1c", 0.0)
ast = st.number_input("AST", 0.0)
alt = st.number_input("ALT", 0.0)
total_protein = st.number_input(f"Total Protein ({unit_option})", 0.0)
globulin = st.number_input(f"Globulin ({unit_option})", 0.0)

# --- Calculation Block ---
if st.button("Calculate Scores"):
    scores = []
    interpretations = []

    bilirubin_umol = bilirubin * 17.1
    albumin_gl = albumin * unit_multiplier
    total_protein_gl = total_protein * unit_multiplier
    globulin_gl = globulin * unit_multiplier

    # NEWS2
    news2 = 0
    if rr <= 8 or rr >= 25: news2 += 3
    elif 21 <= rr <= 24: news2 += 2
    elif 9 <= rr <= 11: news2 += 1
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
    scores.append(["NEWS2", news2])
    if news2 >= 7:
        interpretations.append("High clinical risk. Urgent clinical review needed.")
    elif news2 >= 5:
        interpretations.append("Medium risk. Monitor and consider escalation.")
    else:
        interpretations.append("Low risk.")

    # PNI
    pni = albumin_gl * 1 + 0.005 * lymphocytes * 1000
    scores.append(["PNI", round(pni, 2)])
    if pni >= 45:
        interpretations.append("Good nutritional and immunological status.")
    elif pni >= 40:
        interpretations.append("Mild malnutrition.")
    else:
        interpretations.append("Severe nutritional risk.")

    # SII
    sii = (neutrophils * platelets) / (lymphocytes + 1e-5)
    scores.append(["SII", round(sii, 2)])
    interpretations.append("High SII may reflect systemic inflammation.")

    # SIRI
    siri = (neutrophils * monocytes) / (lymphocytes + 1e-5)
    scores.append(["SIRI", round(siri, 2)])
    interpretations.append("High SIRI may predict adverse outcomes in infections or cancer.")

    # CURB-65
    curb = 0
    if confusion == "Yes": curb += 1
    # Ensure urea is in mmol/L; threshold for CURB-65 is 7 mmol/L
    if urea > 7: curb += 1
    if rr >= 30: curb += 1
    if sbp < 90: curb += 1
    if age >= 65: curb += 1
    scores.append(["CURB-65", curb])
    if curb >= 3:
        interpretations.append("High risk pneumonia. Hospitalization or ICU recommended.")
    elif curb == 2:
        interpretations.append("Moderate risk pneumonia.")
    else:
        interpretations.append("Low risk.")

    # ALBI
    albi = (math.log10(bilirubin_umol + 1e-5) * 0.66) + (albumin_gl * -0.085)
    scores.append(["ALBI", round(albi, 2)])
    if albi <= -2.60:
        interpretations.append("ALBI Grade 1 (good liver function)")
    elif albi <= -1.39:
        interpretations.append("ALBI Grade 2")
    else:
        interpretations.append("ALBI Grade 3 (poor liver function)")

    # eGFR (MDRD)
    egfr = 175 * (creatinine ** -1.154) * (age ** -0.203) * (0.742 if sex == "Female" else 1)
    scores.append(["eGFR", round(egfr, 2)])
    interpretations.append("eGFR reflects renal function. <60 suggests CKD.")

    # UAR
    uar = urea / albumin_gl if albumin_gl else 0
    scores.append(["UAR", round(uar, 2)])
    interpretations.append("Elevated UAR associated with inflammation and poor prognosis.")

    # SHR
    if hba1c > 0:
        emg = (28.7 * hba1c) - 46.7
        shr = glucose / emg
        scores.append(["SHR", round(shr, 2)])
        if shr > 1.14:
            interpretations.append("High SHR: stress hyperglycemia and worse outcomes.")
        else:
            interpretations.append("SHR in normal range.")

    # ALT/Platelet
    alt_platelet = alt / platelets if platelets else 0
    scores.append(["ALT/Platelet", round(alt_platelet, 4)])
    interpretations.append("ALT/Platelet ratio: marker of liver fibrosis or injury.")

    # Globulin/TP
    gtp = globulin_gl / total_protein_gl if total_protein_gl else 0
    scores.append(["Globulin/TP", round(gtp, 2)])
    interpretations.append("Globulin/TP ratio abnormal in liver disease or gammopathies.")

    df = pd.DataFrame(scores, columns=["Score", "Value"])
    st.subheader("Calculated Scores")
    st.dataframe(df)

    st.subheader("Interpretations")
    for score, interpretation in zip(scores, interpretations):
        st.markdown(f"**{score[0]}**: {interpretation}")

    # PDF export
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Patient: {patient_name} | Date: {report_date}", ln=True)
    pdf.cell(200, 10, txt="Clinical Risk Scores:", ln=True)
    for (score, value), interpretation in zip(scores, interpretations):
        pdf.multi_cell(0, 10, txt=f"{score}: {value} - {interpretation}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        st.download_button(
            label="🔗 Download PDF Report",
            data=open(tmp.name, "rb").read(),
            file_name=f"{patient_name}_clinical_scores.pdf",
            mime="application/pdf"
        )
