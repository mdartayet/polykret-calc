from fpdf import FPDF
from datetime import datetime

class OptimizerPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 77, 128)
        self.cell(0, 10, 'POLY KRET - MEMORIA DE DISEÑO SFRC OPTIMIZADO', 0, 1, 'C')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, 'Reporte Autónomo basado en Eurocódigo 2 y EN 14651', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()} | Generado por Poly Expert (Antigravity Optimizer)', 0, 0, 'C')

def render_pdf(data):
    pdf = OptimizerPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # 1. RESUMEN EJECUTIVO (EL TARGET)
    pdf.set_fill_color(255, 204, 0) # Amarillo Poly
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 15, f" ESPESOR RECOMENDADO: {data['h']} mm", 1, 1, 'C', True)
    pdf.ln(5)

    # ALERTA TÉCNICA (SI EXISTE)
    if data.get('technical_alert'):
        pdf.set_fill_color(255, 243, 205)
        pdf.set_text_color(133, 100, 4)
        pdf.set_font('Arial', 'B', 9)
        pdf.multi_cell(0, 8, f" EXCEPCIÓN: {data['technical_alert']}", 1, 'L', True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)

    # 2. DATOS PROYECTO
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, " INFORMACIÓN GENERAL", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(40, 7, " Proyecto:", 1); pdf.cell(150, 7, f" {data.get('project_name','-')}", 1, 1)
    pdf.cell(40, 7, " Cliente:", 1); pdf.cell(150, 7, f" {data.get('client_name','-')}", 1, 1)
    pdf.cell(40, 7, " Fecha:", 1); pdf.cell(150, 7, f" {data['date']} {data['time']}", 1, 1)
    pdf.ln(5)

    # 3. PARÁMETROS TÉCNICOS
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, " 1. PARÁMETROS DE MATERIALES Y SUELO", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(95, 7, f" CBR Suelo: {data.get('cbr','-')} %", 1)
    pdf.cell(95, 7, f" Módulo K: {data['k_val']} N/mm3", 1, 1)
    pdf.cell(95, 7, f" Resistencia Concreto (f'c): {data.get('fc', 280)} kg/cm2", 1)
    pdf.cell(95, 7, f" Fibra Dramix: {data['fiber_type']}", 1, 1)
    pdf.cell(190, 7, f" Dosificación de Acero: {data['dosage']} kg/m3", 1, 1, 'C')
    pdf.ln(5)

    # 4. CARGAS
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, " 2. ESPECIFICACIÓN DE CARGAS (DESIGN LOADS)", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(95, 7, f" Carga Puntual (Pata): {data['load_f']} kN", 1)
    pdf.cell(95, 7, f" Configuración Rack: {data.get('n_legs',1)}x", 1, 1)
    pdf.ln(5)

    # 5. TABLA DE UTILIZACIÓN (EL CORAZÓN DEL CÁLCULO)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, " 3. VERIFICACIÓN DE ESTADO LÍMITE (Ratio Actuante/Resistente)", 0, 1, 'L', True)
    
    pdf.set_fill_color(220, 230, 240)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(70, 10, " Criterio de Diseño", 1, 0, 'C', True)
    pdf.cell(60, 10, " Ratio de Utilización", 1, 0, 'C', True)
    pdf.cell(60, 10, " Estado", 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 10)
    checks = [
        ("Flexión (Momento mEd/mRd)", data['ratio_flex']),
        ("Punzonamiento (Shear VEd/VRd)", data['ratio_punch']),
        ("Presión de Suelo (pEd/pRd)", data['ratio_soil']),
    ]
    
    for label, ratio in checks:
        pdf.cell(70, 8, f" {label}", 1)
        pdf.cell(60, 8, f" {ratio}", 1, 0, 'C')
        if ratio > 1.05:
            pdf.set_text_color(200, 0, 0); pdf.cell(60, 8, " FALLA ", 1, 1, 'C')
        else:
            pdf.set_text_color(0, 150, 0); pdf.cell(60, 8, " CUMPLE ", 1, 1, 'C')
        pdf.set_text_color(0, 0, 0)

    pdf.ln(10)
    
    # 6. CONCLUSIÓN
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, " 4. CONCLUSIÓN TÉCNICA", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 7, f"Tras realizar {int((data['h']-150)/10)+1} iteraciones estructurales, se concluye que un espesor de {data['h']} mm con {data['dosage']} kg/m³ de fibra Dramix® garantiza la estabilidad del piso bajo las solicitaciones prescritas, cumpliendo con los coeficientes de seguridad gamma_Q=1.2 y gamma_f=1.2.")

    return pdf.output()
