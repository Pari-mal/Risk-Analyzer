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
urea_unit = st.radio("Select Urea/BUN input", ["Urea (mmol/L)", "BUN (mg/dL)"])
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
urea_input = st.number_input("Urea or BUN", value=10.0)
if urea_unit == "Urea (mmol/L)":
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
    return 0  # placeholder

def calculate_curb65():
    score = 0
    if confusion == "Yes": score += 1
    if resp_rate >= 30: score += 1
    if sbp < 90: score += 1
    if bun >= 20: score += 1
    if age >= 65: score += 1
    return score

def calculate_pni():
    albumin_g_dl = albumin_raw if protein_unit == "g/dL" else albumin_raw / 10
    return (10 * albumin_g_dl) + (0.005 * lymphocytes)

def calculate_sii():
    return (neutrophils * platelets) / lymphocytes

def calculate_siri():
    return (neutrophils * monocytes) / lymphocytes

def calculate_albi():
    albumin = albumin_raw * conv_factor
    return (math.log10(bilirubin) * 0.66) + (albumin * -0.085)

def calculate_egfr():
    k = 0.742 if sex == "Female" else 1
    return 186 * (creatinine ** -1.154) * (age ** -0.203) * k

def calculate_uar():
    albumin_g_dl = albumin_raw if protein_unit == "g/dL" else albumin_raw / 10
    return bun / albumin_g_dl

def calculate_shr():
    est_avg_gluc = (28.7 * hba1c) - 46.7
    return adm_glucose / est_avg_gluc if est_avg_gluc > 0 else 0

def calculate_alt_pl():
    return alt / platelets if platelets > 0 else 0

def calculate_glob_tp():
    total_protein = total_protein_raw * conv_factor
    globulin = globulin_raw * conv_factor
    return globulin / total_protein if total_protein > 0 else 0

# --- Interpretations ---
def interpret(value, bands):
    for threshold, label in bands:
        if value <= threshold:
            return label
    return bands[-1][1]

results = [
    ("CURB-65", calculate_curb65(), [(0, "Normal"), (1, "Mild"), (2, "Moderate"), (5, "Severe")], "Pneumonia Severity"),
    ("PNI", calculate_pni(), [(40, "Poor"), (45, "Borderline"), (100, "Good")], "Nutrition Status"),
    ("SII", calculate_sii(), [(500, "Low"), (1000, "Mild"), (2000, "High"), (10000, "Very High")], "Inflammation"),
    ("SIRI", calculate_siri(), [(0.5, "Low"), (1.0, "Mild"), (1.5, "Moderate"), (10, "High")], "Inflammation"),
    ("ALBI", calculate_albi(), [(-2.6, "Normal"), (10, "Impaired")], "Liver Function"),
    ("ALT/PLT", calculate_alt_pl(), [(0.3, "Normal"), (1000, "Abnormal")], "Liver Stress"),
    ("Globulin/TP", calculate_glob_tp(), [(0.5, "Low"), (0.7, "Normal"), (2, "High")], "Protein Balance"),
    ("eGFR", calculate_egfr(), [(15, "Failure"), (30, "Severe"), (60, "Moderate"), (90, "Mild"), (1000, "Normal")], "Kidney Function"),
    ("UAR", calculate_uar(), [(0.15, "Normal"), (0.25, "Borderline"), (100, "High")], "Renal Stress"),
    ("SHR", calculate_shr(), [(0.9, "Low"), (1.2, "Moderate"), (100, "High")], "Glycemic Risk")
]

# --- Display Results ---
if st.button("Show Results"):
    for name, val, bands, comment in results:
        interpretation = interpret(val, bands)
        st.write(f"**{name}**: {val:.2f} — {interpretation} ({comment})")

    if st.button("Export PDF"):
        class PDFReport(FPDF):
            def header(self):
                self.set_font("Arial", 'B', 14)
                self.cell(0, 10, "Clinical Risk Summary", ln=True, align='C')
                self.ln(5)
                self.set_font("Arial", '', 12)
                self.cell(0, 10, f"Patient: {patient_name}     Date: {report_date}", ln=True)
                if diagnosis:
                    self.cell(0, 10, f"Diagnosis: {diagnosis}", ln=True)
                self.ln(5)
            def add_results(self, data):
                self.set_font("Arial", size=12)
                for name, val, bands, comment in data:
                    interpretation = interpret(val, bands)
                    self.cell(0, 10, f"{name}: {val:.2f} — {interpretation} ({comment})", ln=True)

        pdf = PDFReport()
        pdf.add_page()
        pdf.add_results(results)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf.output(tmpfile.name)
            with open(tmpfile.name, "rb") as f:
                st.download_button("Download PDF", f, file_name="clinical_scores.pdf")
