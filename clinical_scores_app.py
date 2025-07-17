import streamlit as st
from fpdf import FPDF
import math
import tempfile
from datetime import date

# --- Unit Toggles ---
unit_option = st.selectbox("Select protein units", ["g/L", "g/dL"])
bun_unit = st.selectbox("Select BUN/Urea units", ["mg/dL", "mmol/L"])
conv_factor = 1 if unit_option == "g/L" else 10

# --- Patient Info ---
patient_name = st.text_input("Patient Name")
report_date = st.date_input("Report Date", value=date.today())

# --- Input Fields ---
age = st.number_input("Age", min_value=1, max_value=120, value=50)
sex = st.selectbox("Sex", ["Male", "Female"])
creatinine = st.number_input("Creatinine (mg/dL)", min_value=0.1, max_value=15.0, value=1.0)
glucose_admission = st.number_input("Admission Glucose (mg/dL)", min_value=50.0, max_value=600.0, value=120.0)
hba1c = st.number_input("HbA1c (%)", min_value=3.0, max_value=15.0, value=6.0)

albumin_raw = st.number_input("Albumin", min_value=1.0, max_value=6.0 if unit_option=="g/dL" else 60.0, value=3.5 if unit_option=="g/dL" else 35.0)
total_protein_raw = st.number_input("Total Protein", min_value=3.0, max_value=10.0 if unit_option=="g/dL" else 100.0, value=7.0 if unit_option=="g/dL" else 70.0)
globulin_raw = total_protein_raw - albumin_raw

bilirubin_mg = st.number_input("Bilirubin (mg/dL)", min_value=0.1, max_value=10.0, value=1.0)
bilirubin = bilirubin_mg * 17.1

alt = st.number_input("ALT (U/L)", min_value=1.0, max_value=1000.0, value=30.0)
platelets = st.number_input("Platelets (/mm³)", min_value=10, max_value=1000, value=200)

bun_input = st.number_input("BUN or Urea", min_value=1.0, max_value=100.0, value=10.0)
bun_mg_dl = bun_input if bun_unit == "mg/dL" else bun_input * 2.8

lymphocytes = st.number_input("Lymphocytes (/mm³)", min_value=100, max_value=10000, value=1500)
neutrophils = st.number_input("Neutrophils (/mm³)", min_value=10, max_value=1000, value=300)
monocytes = st.number_input("Monocytes (/mm³)", min_value=1, max_value=1000, value=50)

albumin = albumin_raw * conv_factor
albumin_g_dl = albumin / 10

# --- Calculation Functions ---
def calculate_albi(albumin, bilirubin):
    return (math.log10(bilirubin) * 0.66) + (albumin * -0.085)

def calculate_pni(albumin_g_dl, lymphocytes):
    return (10 * albumin_g_dl) + (0.005 * lymphocytes)

def calculate_sii(neutrophils, platelets, lymphocytes):
    return (neutrophils * platelets) / lymphocytes

def calculate_siri(neutrophils, monocytes, lymphocytes):
    return (neutrophils * monocytes) / lymphocytes

def calculate_egfr(creatinine, age, sex):
    k = 0.742 if sex == "Female" else 1
    return 186 * (creatinine ** -1.154) * (age ** -0.203) * k

def calculate_uar(bun, albumin):
    return bun / albumin_g_dl

def calculate_shr(glucose, hba1c):
    est_avg_glucose = (28.7 * hba1c) - 46.7
    return glucose / est_avg_glucose if est_avg_glucose > 0 else 0

def calculate_alt_platelet_ratio(alt, platelets):
    return alt / platelets if platelets > 0 else 0

def calculate_globulin_tp_ratio(globulin, total_protein):
    return globulin / total_protein if total_protein > 0 else 0

# --- Interpretation Bands ---
def interpret_albi(value):
    return "Normal (Grade 1)" if value <= -2.60 else "Impaired (Grade 2/3)"

def interpret_pni(value):
    if value <= 40:
        return "Poor nutritional status"
    elif value <= 45:
        return "Borderline nutritional status"
    else:
        return "Good nutritional status"

def interpret_sii(value):
    if value <= 500:
        return "Low inflammation"
    elif value <= 1000:
        return "Mild inflammation"
    elif value <= 1500:
        return "Moderate inflammation"
    elif value <= 2000:
        return "High inflammation"
    else:
        return "Very high inflammation"

def interpret_siri(value):
    if value <= 0.5:
        return "Low inflammation"
    elif value <= 1.0:
        return "Mild inflammation"
    elif value <= 1.5:
        return "Moderate inflammation"
    else:
        return "High inflammation"

def interpret_egfr(value):
    if value >= 90:
        return "Normal"
    elif value >= 60:
        return "Mild CKD"
    elif value >= 30:
        return "Moderate CKD"
    elif value >= 15:
        return "Severe CKD"
    else:
        return "Kidney failure"

def interpret_uar(value):
    if value <= 0.15:
        return "Normal"
    elif value <= 0.25:
        return "Borderline"
    else:
        return "High risk"

def interpret_shr(value):
    if value <= 0.9:
        return "Low risk"
    elif value <= 1.2:
        return "Moderate risk"
    else:
        return "High risk"

def interpret_alt_platelet(value):
    if value <= 0.3:
        return "Normal"
    else:
        return "Abnormal"

def interpret_globulin_tp(value):
    if value <= 0.5:
        return "Low Globulin"
    elif value <= 0.7:
        return "Normal"
    else:
        return "High Globulin"

# --- PDF Export ---
class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 14)
        self.cell(0, 10, "Clinical Score Summary", ln=True, align='C')
        self.ln(5)
        self.set_font("Arial", '', 12)
        self.cell(0, 10, f"Patient: {patient_name}     Date: {report_date}", ln=True)
        self.ln(10)

    def add_results(self, data):
        self.set_font("Arial", size=12)
        for name, value, interpretation in data:
            self.cell(0, 10, f"{name}: {value:.2f} — {interpretation}", ln=True)

# --- Score Calculations ---
albi = calculate_albi(albumin, bilirubin)
pni = calculate_pni(albumin_g_dl, lymphocytes)
sii = calculate_sii(neutrophils, platelets, lymphocytes)
siri = calculate_siri(neutrophils, monocytes, lymphocytes)
egfr = calculate_egfr(creatinine, age, sex)

uar = calculate_uar(bun_mg_dl, albumin)
shr = calculate_shr(glucose_admission, hba1c)
alt_pl_ratio = calculate_alt_platelet_ratio(alt, platelets)
glob_tp_ratio = calculate_globulin_tp_ratio(globulin_raw * conv_factor, total_protein_raw * conv_factor)

results = [
    ("ALBI", albi, interpret_albi(albi)),
    ("PNI", pni, interpret_pni(pni)),
    ("SII", sii, interpret_sii(sii)),
    ("SIRI", siri, interpret_siri(siri)),
    ("eGFR", egfr, interpret_egfr(egfr)),
    ("UAR", uar, interpret_uar(uar)),
    ("SHR", shr, interpret_shr(shr)),
    ("ALT/PLT Ratio", alt_pl_ratio, interpret_alt_platelet(alt_pl_ratio)),
    ("Globulin/TP Ratio", glob_tp_ratio, interpret_globulin_tp(glob_tp_ratio))
]

# --- Display Results ---
st.title("Clinical Score Calculator")
for name, value, interpretation in results:
    st.write(f"**{name}**: {value:.2f} — {interpretation}")

# --- Export PDF ---
if st.button("Export to PDF"):
    pdf = PDFReport()
    pdf.add_page()
    pdf.add_results(results)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        with open(tmpfile.name, "rb") as f:
            st.download_button("Download PDF Report", f, file_name="clinical_scores.pdf")
