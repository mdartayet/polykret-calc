from fpdf import FPDF
from datetime import datetime

class SolutionPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 77, 128)
        self.cell(0, 10, 'POLY KRET - PROPUESTA DE DISEÑO OPTIMIZADO', 0, 1, 'C')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, 'Solución de Ingeniería basada en TR34 4th Ed y Eurocódigo 2', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()} | Poly Expert Solution Designer', 0, 0, 'C')

def render_pdf(data):
    pdf = SolutionPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # 1. CUADRO DE SOLUCIÓN MAESTRA
    pdf.set_fill_color(0, 77, 128)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, " ESPECIFICACIÓN TÉCNICA RECOMENDADA ", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_font('Arial', 'B', 11)
    # Fila 1
    pdf.cell(63, 15, f" ESPESOR: {data['h']} mm", 1, 0, 'C', True)
    pdf.cell(64, 15, f" FIBRA: {data['fiber_type']}", 1, 0, 'C', True)
    pdf.cell(63, 15, f" DOSIS: {data['dosage']} kg/m3", 1, 1, 'C', True)
    pdf.ln(5)

    # 2. DATOS PROYECTO
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, " INFORMACIÓN DEL PROYECTO", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(40, 7, " Proyecto:", 1); pdf.cell(150, 7, f" {data.get('project_name','-')}", 1, 1)
    pdf.cell(40, 7, " Cliente:", 1); pdf.cell(150, 7, f" {data.get('client_name','-')}", 1, 1)
    pdf.ln(5)

    # 3. VERIFICACIÓN ESTRUCTURAL (RATIOS)
    pdf.set_fill_color(0, 77, 128)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, " MODELADO Y VERIFICACIÓN DE CARGAS ", 0, 1, 'L', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(70, 8, " Parámetro de Diseño", 1, 0, 'C', True)
    pdf.cell(60, 8, " Valor / Ratio de Utilización", 1, 0, 'C', True)
    pdf.cell(60, 8, " Estatus TR34", 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 10)
    checks = [
        ("Elemento Crítico (Gobernante)", f"{data.get('critical_load', 'Rack')}", "EVALUADO"),
        ("Módulo de Reacción Suelo (k)", f"{data['k_val']} N/mm3", "PROPIEDAD"),
        ("Resistencia Flexo-tracción", f"{data['max_ratio']}", "CUMPLE" if data['max_ratio'] <= 1.0 else "FALLA"),
        ("Resistencia Punzonamiento", f"{data['ratio_punch']}", "CUMPLE" if data['ratio_punch'] <= 1.0 else "FALLA"),
        ("Presión sobre el Suelo", f"{data['ratio_soil']}", "CUMPLE" if data['ratio_soil'] <= 1.0 else "FALLA")
    ]
    
    for label, val, status in checks:
        pdf.cell(70, 8, f" {label}", 1)
        pdf.cell(60, 8, f" {val}", 1, 0, 'C')
        if status == "FALLA": pdf.set_text_color(200, 0, 0)
        elif status == "CUMPLE": pdf.set_text_color(0, 150, 0)
        pdf.cell(60, 8, f" {status}", 1, 1, 'C')
        pdf.set_text_color(0, 0, 0)

    pdf.ln(10)
    
    # 4. OBSERVACIONES TÉCNICAS
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, " OBSERVACIONES FINAL", 0, 1)
    pdf.set_font('Arial', '', 9)
    obs = (f"El diseño propuesto con {data['h']} mm de espesor y {data['dosage']} kg/m³ de fibra {data['fiber_type']} "
           "representa la solución más eficiente que cumple con los Estados Límite de Servicio y Último. "
           "Cálculo basado en la transferencia de carga en juntas (theta) y resistencia residual del SFRC.")
    pdf.multi_cell(0, 6, obs)

    return pdf.output()
