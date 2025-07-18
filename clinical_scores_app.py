# Streamlit app: Clinical Indices Calculator with Full Indices
import streamlit as st
from fpdf import FPDF
import tempfile
from datetime import date
import math

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
neutrophils = float(str(st.text_input("Neutrophils (/mm³)", "5000", help="Enter absolute count (e.g., 5000, not %)")).replace(',', '.'))
lymphocytes = float(str(st.text_input("Lymphocytes (/mm³)", "1500", help="Enter absolute count (e.g., 1500, not % or decimal)")).replace(',', '.'))
monocytes = float(str(st.text_input("Monocytes (/mm³)", "500", help="Enter absolute count (e.g., 500, not %)")).replace(',', '.'))
platelets = float(str(st.text_input("Platelets (/mm³)", "250000", help="Enter full count (e.g., 250000, not in lakhs or thousands)")).replace(',', '.'))

# --- Renal ---
creatinine = st.number_input("Creatinine (mg/dL)", value=1.0)
urea_input = st.number_input("Urea", value=10.0)
bun = urea_input * 2.8 if urea_unit == "mmol/L" else urea_input

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

# --- Score Calculations ---
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

def calculate_pni():
    albumin = albumin_raw * conv_factor
    return albumin + 5 * (lymphocytes / 1000)

def calculate_siri():
    return (float(neutrophils) * float(monocytes)) / (float(lymphocytes) + 1)

def calculate_sii():
    return (float(neutrophils) * float(platelets)) / (float(lymphocytes) + 1)

def calculate_albi():
    albumin = albumin_raw * conv_factor
    return (math.log10(bilirubin) * 0.66) - (0.085 * albumin)

def calculate_alt_plat():
    return (alt * 1000) / platelets

def calculate_globulin_ratio():
    return globulin_raw / total_protein_raw

def calculate_egfr():
    return 186 * (creatinine ** -1.154) * (age ** -0.203)

def calculate_uar():
    albumin = albumin_raw * conv_factor
    return urea_input / albumin

def calculate_shr():
    est_glucose = (28.7 * hba1c) - 46.7
    return adm_glucose / est_glucose

# PDF creation and download
if st.button("Calculate and Download Report"):
    results = [
        ("NEWS2", calculate_news2(), [(0, "Normal"), (4, "Low"), (6, "Moderate"), (20, "High")], "Acute Deterioration Risk"),
        ("CURB-65", calculate_curb65(), [(0, "Low"), (1, "Mild"), (2, "Moderate"), (3, "High")], "Pneumonia Severity"),
        ("PNI", round(calculate_pni(), 2), [(0, "Severe"), (35, "Moderate"), (40, "Mild"), (45, "Normal")], "Nutritional Status"),
        ("SIRI", round(calculate_siri(), 2), [(0.8, "Normal"), (1.5, "Elevated"), (2.5, "High")], "Inflammatory Response"),
        ("SII", round(calculate_sii(), 2), [(300, "Normal"), (600, "Moderate"), (1000, "High")], "Immune Inflammation"),
        ("ALBI", round(calculate_albi(), 3), [(-2.6, "Grade 1"), (-1.39, "Grade 2"), (10, "Grade 3")], "Liver Function"),
        ("ALT/PLT Ratio", round(calculate_alt_plat(), 3), [(0, "Normal"), (0.2, "Mild"), (0.3, "Significant")], "Liver Injury Index"),
        ("Globulin/TP Ratio", round(calculate_globulin_ratio(), 3), [(0.4, "Low"), (0.5, "Normal"), (0.6, "Elevated")], "Immune Protein Balance"),
        ("eGFR", round(calculate_egfr(), 1), [(0, "Failure"), (15, "Severe"), (30, "Moderate"), (60, "Mild"), (90, "Normal")], "Kidney Function"),
        ("UAR", round(calculate_uar(), 3), [(0.2, "Normal"), (0.3, "Elevated"), (0.5, "High")], "Renal-Protein Balance"),
        ("SHR", round(calculate_shr(), 3), [(0, "Low"), (1.14, "Moderate Risk"), (1.4, "High Risk")], "Stress Hyperglycemia")
    ]

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Clinical Score Report", ln=1, align="C")
    pdf.cell(200, 10, txt=f"Patient: {patient_name}    Date: {report_date}", ln=2)
    if diagnosis:
        pdf.cell(200, 10, txt=f"Diagnosis: {diagnosis}", ln=3)

    for name, value, bands, meaning in results:
        interpretation = next((label for thresh, label in reversed(bands) if value >= thresh), "")
        line = f"{name}: {value} - {interpretation} ({meaning})"
        try:
            pdf.cell(200, 10, txt=line.encode('latin-1', 'replace').decode('latin-1'), ln=1)
        except:
            pdf.cell(200, 10, txt="Encoding Error", ln=1)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        with open(tmpfile.name, "rb") as f:
            st.download_button("Download PDF Report", f, file_name="clinical_scores.pdf")
