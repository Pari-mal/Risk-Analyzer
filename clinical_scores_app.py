# Streamlit app: Clinical Indices Calculator with Full Indices (Final)
import streamlit as st
from fpdf import FPDF
import tempfile
from datetime import date
import math

# --- Header ---
# --- Helper Section ---
with st.expander("ℹ️ How to Use This App"):
    st.markdown("""
    **Unit Selection Guidance:**

    1. **Select**:
       - `g/dL` for **proteins** (Albumin, Total Protein)
       - `mg/dL` for **bilirubin** and **urea**
    2. **CBC Input Format:**
       - Use **absolute values**
       - Examples:
         - If Neutrophils = 9.4 /mm³ → enter `9400`
         - If Monocytes = 0.5 → enter `500`
         - If Platelets = 250 → enter `250000`
    3. **Interpretation Bands:** See each index output below for the classification:

       | **Index** | **Full Form** | **Interpretation Bands** |
       |-----------|----------------|---------------------------|
       | NEWS2 | National Early Warning Score 2 | Low / Medium / High |
       | CURB-65 | Confusion, Urea, Respiratory, BP, Age ≥65 | Low / Intermediate / High |
       | PNI | Prognostic Nutritional Index | Normal / Mild / Moderate / Severe |
       | SII | Systemic Immune-Inflammation Index | Normal / Mild / Moderate / Severe |
       | SIRI | Systemic Inflammation Response Index | Normal / Mild / Moderate / Severe |
       | ALBI | Albumin-Bilirubin Score | Grade 1 / Grade 2 / Grade 3 |
       | ALT/PLT Ratio | ALT to Platelet Ratio | Normal / Mild / Moderate / Severe |
       | Globulin/TP Ratio | Globulin to Total Protein Ratio | Low / Normal / High |
       | eGFR | Estimated Glomerular Filtration Rate | Normal / Mild / Moderate / Severe |
       | UAR | Urea-to-Albumin Ratio | Normal / Mild / Moderate / Severe |
       | SHR | Stress Hyperglycemia Ratio | Normal / Mild / Moderate / Severe |
    """)
st.title("Clinical Risk Score Calculator")
report_date = date.today()
patient_name = st.text_input("Patient Name")
diagnosis = st.text_input("Initial Diagnosis (optional)")
st.write(f"Date: {report_date}")

# --- Unit Toggles ---
protein_unit = st.radio("Select protein units", ["g/dL", "g/L"])
bilirubin_unit = st.radio("Select bilirubin units", ["mg/dL", "µmol/L"])
urea_unit = st.radio("Select Urea input", ["mg/dL", "mmol/L"])
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
neutrophils = float(str(st.text_input("Neutrophils (/mm³)", "5000")).replace(',', '.'))
lymphocytes = float(str(st.text_input("Lymphocytes (/mm³)", "1500")).replace(',', '.'))
monocytes = float(str(st.text_input("Monocytes (/mm³)", "500")).replace(',', '.'))
platelets = float(str(st.text_input("Platelets (/mm³)", "250000")).replace(',', '.'))

# Convert to x10^9/L
neutrophils_109 = neutrophils / 1000
lymphocytes_109 = lymphocytes / 1000
monocytes_109 = monocytes / 1000
platelets_109 = platelets / 1000

# --- Renal ---
creatinine = st.number_input("Creatinine (mg/dL)", value=1.0)
urea_input = st.number_input("Urea", value=10.0)
urea_mg_dl = urea_input if urea_unit == "mg/dL" else urea_input * 6.0
bun = urea_mg_dl / 2.14

# --- Liver ---
albumin_raw = st.number_input("Albumin", value=3.5 if protein_unit == "g/dL" else 35.0)
total_protein_raw = st.number_input("Total Protein", value=7.0 if protein_unit == "g/dL" else 70.0)
globulin_raw = total_protein_raw - albumin_raw
albumin_mg_dl = albumin_raw if protein_unit == "g/dL" else albumin_raw / 10

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
    return score, "Low" if score < 5 else "Medium" if score < 7 else "High"

def calculate_curb65():
    score = 0
    if confusion == "Yes": score += 1
    if resp_rate >= 30: score += 1
    if sbp < 90: score += 1
    if urea_mg_dl >= 40: score += 1
    if age >= 65: score += 1
    return score, "Low" if score == 0 else "Intermediate" if score <= 2 else "High"

def calculate_pni():
    return albumin_raw * conv_factor + 5 * (lymphocytes / 1000)

def calculate_sii():
    return (neutrophils_109 * platelets_109) / lymphocytes_109

def calculate_siri():
    return (neutrophils_109 * monocytes_109) / lymphocytes_109

def calculate_albi():
    return (math.log10(bilirubin) * 0.66) - (albumin_raw * conv_factor * 0.085)

def calculate_alt_platelet():
    return alt / platelets_109

def calculate_globulin_tp():
    return globulin_raw / total_protein_raw

def calculate_egfr():
    return 186 * (creatinine ** -1.154) * (age ** -0.203)

def calculate_uar():
    urea_mmol_l = urea_mg_dl / 6.0
    return urea_mmol_l / albumin_mg_dl

def calculate_shr():
    return adm_glucose / (28.7 * hba1c - 46.7)

def interpret_band(val, bands):
    for (low, high, band) in bands:
        if low <= val < high:
            return band
    return bands[-1][2]

# Display results
if st.button("Calculate Scores"):
    results = []
    comments = {
        "NEWS2": "Acute Deterioration Risk",
        "CURB-65": "Pneumonia Severity",
        "PNI": "Nutritional Status",
        "SIRI": "Inflammatory Response",
        "SII": "Immune Inflammation",
        "ALBI": "Liver Function",
        "ALT/PLT Ratio": "Liver Injury Index",
        "Globulin/TP Ratio": "Immune Protein Balance",
        "eGFR": "Kidney Function",
        "UAR": "Renal-Protein Balance",
        "SHR": "Stress Hyperglycemia"
    }

    news2_score, news2_band = calculate_news2()
    results.append(("NEWS2", news2_score, news2_band))

    curb_score, curb_band = calculate_curb65()
    results.append(("CURB-65", curb_score, curb_band))

    pni = round(calculate_pni(), 2)
    pni_band = interpret_band(pni, [(0, 40, "Severe"), (40, 45, "Moderate"), (45, 50, "Mild"), (50, 1000, "Normal")])
    results.append(("PNI", pni, pni_band))

    sii = round(calculate_sii(), 2)
    sii_band = interpret_band(sii, [(0, 500, "Normal"), (500, 1000, "Mild"), (1000, 1500, "Moderate"), (1500, 1e6, "Severe")])
    results.append(("SII", sii, sii_band))

    siri = round(calculate_siri(), 2)
    siri_band = interpret_band(siri, [(0, 0.5, "Normal"), (0.5, 1.0, "Mild"), (1.0, 1.5, "Moderate"), (1.5, 100, "Severe")])
    results.append(("SIRI", siri, siri_band))

    albi = round(calculate_albi(), 3)
    albi_band = interpret_band(albi, [(-10, -2.6, "Grade 1"), (-2.6, -1.39, "Grade 2"), (-1.39, 10, "Grade 3")])
    results.append(("ALBI", albi, albi_band))

    altplt = round(calculate_alt_platelet(), 3)
    altplt_band = interpret_band(altplt, [(0, 0.2, "Normal"), (0.2, 0.5, "Mild"), (0.5, 1.0, "Moderate"), (1.0, 10, "Severe")])
    results.append(("ALT/PLT Ratio", altplt, altplt_band))

    globtp = round(calculate_globulin_tp(), 3)
    globtp_band = interpret_band(globtp, [(0.0, 0.4, "Low"), (0.4, 0.6, "Normal"), (0.6, 1.0, "High")])
    results.append(("Globulin/TP Ratio", globtp, globtp_band))

    egfr = round(calculate_egfr(), 1)
    egfr_band = interpret_band(egfr, [(0, 30, "Severe"), (30, 60, "Moderate"), (60, 90, "Mild"), (90, 200, "Normal")])
    results.append(("eGFR", egfr, egfr_band))

    uar = round(calculate_uar(), 3)
    uar_band = interpret_band(uar, [(0, 5, "Normal"), (5, 10, "Mild"), (10, 15, "Moderate"), (15, 100, "Severe")])
    results.append(("UAR", uar, uar_band))

    shr = round(calculate_shr(), 3)
    shr_band = interpret_band(shr, [(0, 0.8, "Low"), (0.8, 1.0, "Normal"), (1.0, 1.4, "Mild"), (1.4, 2.0, "Moderate"), (2.0, 100, "Severe")])
    results.append(("SHR", shr, shr_band))

    for name, val, band in results:
        st.write(f"**{name}**: {val} — {band} ({comments.get(name, '')})")

    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Clinical Risk Score Report", ln=True, align='C')
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Patient Name: {patient_name}".encode('latin-1', 'replace').decode('latin-1'), ln=True)
    pdf.cell(200, 10, txt=f"Date: {report_date}", ln=True)
    pdf.cell(200, 10, txt=f"Diagnosis: {diagnosis}".encode('latin-1', 'replace').decode('latin-1'), ln=True)
    pdf.ln(5)
    for name, val, band in results:
        comment = comments.get(name, '')
        line = f"{name}: {val} — {band} ({comment})"
        pdf.cell(200, 10, txt=line.encode('latin-1', 'replace').decode('latin-1'), ln=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        with open(tmpfile.name, "rb") as f:
            st.download_button("Download PDF Report", f, file_name="Clinical_Risk_Report.pdf")
