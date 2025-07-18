# Streamlit app: Simplified Clinical Indices Calculator
import streamlit as st
from fpdf import FPDF
import math
import tempfile
from datetime import date

# --- Header ---
st.title("Clinical Risk Score Calculator")
report_date = date.today()
patient_name = st.text_input("Patient Name")
diagnosis = st.text_input("Initial Diagnosis (optional)")
st.write(f"Date: {report_date}")

# --- Unit Toggles ---
protein_unit = st.radio("Select protein units", ["g/dL", "g/L"])
bilirubin_unit = st.radio("Select bilirubin units", ["mg/dL", "µmol/L"])
urea_unit = st.radio("Select Urea input", ["mmol/L", "mg/dL"])
conv_factor = 10 if protein_unit == "g/dL" else 1

# --- Demographics ---
age = st.number_input("Age", min_value=1, max_value=120, value=50)
sex = st.selectbox("Sex", ["Male", "Female"])

# --- NEWS2 inputs ---
avpu = st.selectbox("AVPU", ["Alert", "Voice", "Pain", "Unresponsive"])
confusion = st.selectbox("New Confusion", ["No", "Yes"])
resp_rate = st.number_input("Respiratory Rate (/min)", min_value=5, max_value=50, value=16)
heart_rate = st.number_input("Heart Rate (/min)", min_value=30, max_value=180, value=70)
sbp = st.number_input("Systolic BP (mmHg)", min_value=50, max_value=240, value=120)
temp_f = st.number_input("Temperature (°F)", min_value=90.0, max_value=108.0, value=98.6)
spo2 = st.number_input("SpO₂ (%)", min_value=70, max_value=100, value=98)
o2_required = st.selectbox("Oxygen Required?", ["No", "Yes"])

# --- CBC ---
neutrophils = st.number_input("Neutrophils (/mm³)", value=5000)
lymphocytes = st.number_input("Lymphocytes (/mm³)", value=1500)
monocytes = st.number_input("Monocytes (/mm³)", value=500)
platelets = st.number_input("Platelets (/mm³)", value=250000)

# --- Renal ---
creatinine = st.number_input("Creatinine (mg/dL)", value=1.0)
urea_input = st.number_input("Urea", value=10.0)
if urea_unit == "mmol/L":
    bun = urea_input * 2.8
else:
    bun = urea_input

# --- Liver ---
albumin_raw = st.number_input("Albumin", value=3.5 if protein_unit == "g/dL" else 35.0)
total_protein_raw = st.number_input("Total Protein", value=7.0 if protein_unit == "g/dL" else 70.0)
globulin_raw = total_protein_raw - albumin_raw

bilirubin_input = st.number_input("Bilirubin", value=1.0)
bilirubin = bilirubin_input * 17.1 if bilirubin_unit == "mg/dL" else bilirubin_input

alt = st.number_input("ALT (U/L)", value=30.0)
ast = st.number_input("AST (U/L)", value=30.0)

# --- Glucose ---
adm_glucose = st.number_input("Admission Glucose (mg/dL)", value=120.0)
hba1c = st.number_input("HbA1c (%)", value=6.0)

# --- Calculations ---
def calculate_news2():
    score = 0
    if resp_rate <= 8 or resp_rate >= 25: score += 3
    elif 21 <= resp_rate <= 24: score += 2
    elif 9 <= resp_rate <= 11: score += 1
    if spo2 <= 91: score += 3
    elif 92 <= spo2 <= 93: score += 2
    elif 94 <= spo2 <= 95: score += 1
    if o2_required == "Yes": score += 2
    temp_c = (temp_f - 32) * 5/9
    if temp_c < 35.0 or temp_c >= 39.1: score += 3
    elif 38.1 <= temp_c <= 39.0: score += 1
    elif 35.1 <= temp_c <= 36.0: score += 1
    if sbp <= 90 or sbp >= 220: score += 3
    elif 91 <= sbp <= 100: score += 2
    elif 101 <= sbp <= 110: score += 1
    if heart_rate <= 40 or heart_rate >= 131: score += 3
    elif 111 <= heart_rate <= 130: score += 2
    elif 91 <= heart_rate <= 110: score += 1
    elif 41 <= heart_rate <= 50: score += 1
    if avpu != "Alert": score += 3
    if confusion == "Yes": score += 3
    return score

def calculate_curb65():
    score = 0
    if confusion == "Yes": score += 1
    if resp_rate >= 30: score += 1
    if sbp < 90: score += 1
    if bun >= 20: score += 1
    if age >= 65: score += 1
    return score

# Results list (incomplete, shown for sample only)
results = [
    ("NEWS2", calculate_news2(), [(0, "Normal"), (4, "Low"), (6, "Moderate"), (20, "High")], "Acute Deterioration Risk"),
    ("CURB-65", calculate_curb65(), [(0, "Low"), (1, "Mild"), (2, "Moderate"), (3, "High")], "Pneumonia Severity")
]

if st.button("Calculate Scores"):
    for name, value, bands, meaning in results:
        interpretation = next((label for thresh, label in reversed(bands) if value >= thresh), "")
        st.write(f"**{name}**: {value} — {interpretation} ({meaning})")

    # --- PDF ---
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Clinical Score Report", ln=1, align="C")
    pdf.cell(200, 10, txt=f"Patient: {patient_name}    Date: {report_date}", ln=2)
    if diagnosis: pdf.cell(200, 10, txt=f"Diagnosis: {diagnosis}", ln=3)

    for name, value, bands, meaning in results:
        interpretation = next((label for thresh, label in reversed(bands) if value >= thresh), "")
        pdf.cell(200, 10, txt=f"{name}: {value} — {interpretation} ({meaning})", ln=1)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        with open(tmpfile.name, "rb") as f:
            st.download_button("Download PDF Report", f, file_name="clinical_scores.pdf")
