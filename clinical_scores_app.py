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

# Urea/BUN unit toggle
urea_source = st.radio("Choose input for nitrogen waste:", ["Urea", "BUN"], index=0)

if urea_source == "Urea":
    urea_unit = st.radio("Urea unit:", ["mg/dL", "mmol/L"], index=0)
    urea_input = st.number_input("Urea", 0.0)
    urea = urea_input * 0.357 if urea_unit == "mg/dL" else urea_input
else:
    bun = st.number_input("BUN (mg/dL)", 0.0)
    urea = bun * 0.357  # Convert BUN to urea in mmol/L

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

    # PNI
    pni = albumin_gl * 1 + 0.005 * lymphocytes * 1000
    scores.append(["PNI", round(pni, 2)])

    # SII
    sii = (neutrophils * platelets) / (lymphocytes + 1e-5)
    scores.append(["SII", round(sii, 2)])

    # SIRI
    siri = (neutrophils * monocytes) / (lymphocytes + 1e-5)
    scores.append(["SIRI", round(siri, 2)])

    # CURB-65
    curb = 0
    if confusion == "Yes": curb += 1
    if urea > 7: curb += 1
    if rr >= 30: curb += 1
    if sbp < 90: curb += 1
    if age >= 65: curb += 1
    scores.append(["CURB-65", curb])

    # ALBI
    albi = (math.log10(bilirubin_umol + 1e-5) * 0.66) + (albumin_gl * -0.085)
    scores.append(["ALBI", round(albi, 2)])

    # eGFR (MDRD)
    egfr = 175 * (creatinine ** -1.154) * (age ** -0.203) * (0.742 if sex == "Female" else 1)
    scores.append(["eGFR", round(egfr, 2)])

    # UAR
    uar = urea / albumin_gl if albumin_gl else 0
    scores.append(["UAR", round(uar, 2)])

    # SHR
    if hba1c > 0:
        emg = (28.7 * hba1c) - 46.7
        shr = glucose / emg
        scores.append(["SHR", round(shr, 2)])

    # ALT/Platelet
    alt_platelet = alt / platelets if platelets else 0
    scores.append(["ALT/Platelet", round(alt_platelet, 4)])

    # Globulin/TP
    gtp = globulin_gl / total_protein_gl if total_protein_gl else 0
    scores.append(["Globulin/TP", round(gtp, 2)])

    df = pd.DataFrame(scores, columns=["Score", "Value"])
    st.subheader("Calculated Scores")
    st.dataframe(df)
