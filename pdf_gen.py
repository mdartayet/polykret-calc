from fpdf import FPDF
from datetime import datetime

class BekaertPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 77, 128)
        self.cell(0, 10, 'POLY KRET - Bekaert Floor Design Sheet', 0, 1, 'C')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, 'Dramix® Steel Fiber Reinforced Industrial Floor Assistance', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Polykret Online Designer', 0, 0, 'C')

def render_pdf(data):
    pdf = BekaertPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # 1. PROJECT INFO TABLE
    pdf.set_fill_color(0, 77, 128)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, " PROJECT INFORMATION", 0, 1, 'L', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    # Row 1
    pdf.cell(40, 7, " Project name:", 1); pdf.cell(150, 7, f" {data.get('project_name','-')}", 1, 1)
    # Row 2
    pdf.cell(40, 7, " Customer Name:", 1); pdf.cell(60, 7, f" {data.get('client_name','-')}", 1)
    pdf.cell(30, 7, " Project size:", 1); pdf.cell(60, 7, f" {data.get('project_size','-')} m2", 1, 1)
    # Row 3
    pdf.cell(40, 7, " E-mail:", 1); pdf.cell(150, 7, f" {data.get('email','-')}", 1, 1)
    pdf.ln(5)

    # 2. FLOOR & MATERIALS info
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(95, 7, " FLOOR INFORMATION", 1, 0, 'L', True)
    pdf.cell(95, 7, " SUBBASE & SOIL", 1, 1, 'L', True)
    
    pdf.set_font('Arial', '', 9)
    pdf.cell(50, 7, " Floor Type:", 1); pdf.cell(45, 7, f" {data.get('floor_type','-')}", 1)
    pdf.cell(50, 7, " CBR Value:", 1); pdf.cell(45, 7, f" {data.get('cbr','-')} %", 1, 1)
    
    pdf.cell(50, 7, " Joint Type:", 1); pdf.cell(45, 7, f" {data.get('joint_type','-')}", 1)
    pdf.cell(50, 7, " k-value (calculated):", 1); pdf.cell(45, 7, f" {data['k_val']} N/mm3", 1, 1)
    
    pdf.cell(50, 7, " Joint Spacing:", 1); pdf.cell(45, 7, f" {data.get('joint_spacing','-')}", 1)
    pdf.cell(50, 7, " Slab Thickness (h):", 1); pdf.cell(45, 7, f" {data['thickness']} mm", 1, 1)
    pdf.ln(5)

    # 3. REINFORCEMENT
    pdf.set_fill_color(0, 161, 225) # Secondary blue
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, " REINFORCEMENT (DRAMIX® FIBER)", 0, 1, 'L', True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(60, 10, f" Fiber: {data['fiber_type']}", 1)
    pdf.cell(130, 10, f" Steel Fiber Dosage: {data['dosage']} kg/m3", 1, 1, 'C')
    pdf.ln(5)

    # 4. LOAD & RESULTS
    pdf.set_fill_color(0, 77, 128)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, " LOADS & CAPACITY VERIFICATION (TR34 4th Ed)", 0, 1, 'L', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(60, 8, " Design Load Case", 1, 0, 'C', True)
    pdf.cell(40, 8, " Applied (Wester.)", 1, 0, 'C', True)
    pdf.cell(40, 8, " Resistance (Rd)", 1, 0, 'C', True)
    pdf.cell(50, 8, " Utilization Status", 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 9)
    cases = [
        ("Pallet Rack (Center)", f"{data['m_ed_center']} kNm", f"{data['m_rd_total']} kNm", data['utilization']),
        ("Pallet Rack (Joint)", f"{data['m_ed_joint']} kNm", f"{data['m_rd_total']} kNm", data['utilization_joint']),
        ("Pallet Rack (Edge)", f"{data['m_ed_edge']} kNm", f"{data['m_rd_total'] + data['m_rd_c']} kNm", data['utilization_edge']),
    ]
    
    for case, applied, res, util in cases:
        pdf.cell(60, 8, f" {case}", 1)
        pdf.cell(40, 8, f" {applied}", 1, 0, 'C')
        pdf.cell(40, 8, f" {res}", 1, 0, 'C')
        if util > 100:
            pdf.set_text_color(200, 0, 0); pdf.set_font('Arial', 'B', 9)
            pdf.cell(50, 8, f" FAILED ({util}%)", 1, 1, 'C')
        else:
            pdf.set_text_color(0, 128, 0); pdf.set_font('Arial', 'B', 9)
            pdf.cell(50, 8, f" OK ({util}%)", 1, 1, 'C')
        pdf.set_text_color(0,0,0); pdf.set_font('Arial', '', 9)

    pdf.ln(10)
    
    # 5. RECOMMENDATIONS
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, " CONCLUSION / RECOMMENDATIONS", 0, 1)
    pdf.set_font('Arial', '', 9)
    if data['utilization'] <= 100:
        pdf.multi_cell(0, 6, "Based on TR34 4th Edition analysis, the proposed slab thickness and Dramix® dosage are SUFFICIENT for the specified loads at interior and edge locations.")
    else:
        pdf.multi_cell(0, 6, "WARNING: The current utilization exceeds 100%. A thicker slab or higher dosage of Dramix® steel fibers is required to comply with Bekaert structural standards.")
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "Disclaimer: This digital assistance tool provides a preliminary orientation based on the inputs provided. A final stamp and sign by a structural engineer is mandatory for construction.")

    return pdf.output()
