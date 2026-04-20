from fpdf import FPDF
from datetime import datetime

class BekaertPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 77, 128)
        self.cell(0, 10, 'POLY KRET - MEMORIA TÉCNICA ESTRUCTURAL', 0, 1, 'C')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, 'Asistencia Técnica Basada en Estándares Dramix® SoG / TR34 (4th Ed)', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()} | Documento Generado por Poly Expert | Bekaert Compliant', 0, 0, 'C')

def render_pdf(data):
    pdf = BekaertPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # 1. INFO PROYECTO
    pdf.set_fill_color(230, 240, 250)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f" PROYECTO: {data.get('project_name', 'N/A').upper()}", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(95, 7, f" Cliente: {data.get('client_name', 'N/A')}", 0, 0)
    pdf.cell(95, 7, f" Fecha: {data['date']}", 0, 1, 'R')
    pdf.ln(5)

    # 2. SECCIÓN TÉCNICA
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "1. PROPIEDADES DE MATERIALES Y SOPORTE", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    
    pdf.cell(90, 7, f" Espesor de Losa (h):", 1)
    pdf.cell(90, 7, f" {data['thickness']} mm", 1, 1)
    pdf.cell(90, 7, f" Resistencia Concreto (f'c):", 1)
    pdf.cell(90, 7, f" {data['fc']} kg/cm2 (fck ~ {data['fck']} MPa)", 1, 1)
    pdf.cell(90, 7, f" Suelo (CBR):", 1)
    pdf.cell(90, 7, f" {data['cbr']} %", 1, 1)
    pdf.cell(90, 7, f" Módulo de Reacción K:", 1)
    pdf.cell(90, 7, f" {data['k_val']} N/mm3", 1, 1)
    pdf.cell(90, 7, f" Longitud Elástica (lel):", 1)
    pdf.cell(90, 7, f" {data['lel']} mm", 1, 1)
    pdf.ln(5)

    # 3. CARGAS
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "2. SOLICITACIONES (CARGAS DE DISEÑO)", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(90, 7, f" Carga Puntual (Pata de Rack):", 1)
    pdf.cell(90, 7, f" {data['load_f']} kN", 1, 1)
    pdf.cell(90, 7, f" Placa Base:", 1)
    pdf.cell(90, 7, f" {data['plate_x']} x {data['plate_y']} mm", 1, 1)
    pdf.ln(5)

    # 4. VERIFICACIÓN DE CAPACIDAD
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "3. RESULTADOS DE VERIFICACIÓN (TR34)", 0, 1)
    
    # Capacidad Momentos
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(60, 8, " Ubicación", 1, 0, 'C', True)
    pdf.cell(60, 8, " Momento Actuante", 1, 0, 'C', True)
    pdf.cell(60, 8, " Utilización (%)", 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 10)
    checks = [
        ("Centro de Losa", f"{data['m_ed_center']} kNm/m", data['utilization']),
        ("Juntas Primarias", f"{data['m_ed_joint']} kNm/m", data['utilization_joint']),
        ("Bordes / Esquinas", f"{data['m_ed_edge']} kNm/m", data['utilization_edge']),
        ("Presión Suelo", f"{data['p_ed_soil']} kN/m2", data['utilization_soil']),
    ]
    
    for label, val, util in checks:
        pdf.cell(60, 7, f" {label}", 1)
        pdf.cell(60, 7, f" {val}", 1, 0, 'C')
        if util > 100:
            pdf.set_text_color(200, 0, 0)
            pdf.set_font('Arial', 'B', 10)
        else:
            pdf.set_text_color(0, 100, 0)
        pdf.cell(60, 7, f" {util} %", 1, 1, 'C')
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 10)

    pdf.ln(10)

    # 5. CONCLUSIÓN
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "4. OBSERVACIONES Y RECOMENDACIONES", 0, 1)
    pdf.set_font('Arial', '', 10)
    for rec in data.get('recommendations', []):
        pdf.multi_cell(0, 7, f" * {rec}")
    
    pdf.ln(15)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "Aviso Legal: Los cálculos presentados son referenciales y se basan exclusivamente en las propiedades de las fibras Dramix®. El uso de otras fibras anula la validez de este diseño. Este reporte debe ser verificado y firmado por un Ingeniero Civil colegiado responsable de la obra.")

    return pdf.output()
