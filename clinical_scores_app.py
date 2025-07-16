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

# (Rest of the code remains unchanged, using `urea` in calculations)
