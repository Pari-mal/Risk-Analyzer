...
# Patient Info Input
st.subheader("🧑‍⚕️ Patient Information")
patient_name = st.text_input("Patient Name")
report_date = st.date_input("Report Date")

# Summary Table
...

# PDF Export
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
        pdf.cell(col_widths[0], 10, str(row['Score']), 1)
        pdf.cell(col_widths[1], 10, str(row['Value']), 1)
        pdf.cell(col_widths[2], 10, str(row['Interpretation']), 1)
        pdf.ln()

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

if st.button("📄 Download PDF Report"):
    pdf_bytes = create_pdf(summary_df, patient_name, report_date)
    st.download_button(
        label="📥 Download PDF",
        data=pdf_bytes,
        file_name=f"{patient_name}_clinical_score_summary.pdf",
        mime="application/pdf"
    )
