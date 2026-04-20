from fpdf import FPDF
from datetime import datetime
import io

class PolykretPDF(FPDF):
    def header(self):
        # Logo placeholder (puedes añadir uno real luego)
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 77, 128)
        self.cell(0, 10, 'POLY KRET - MEMORIA TÉCNICA ESTRUCTURAL', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()} | Dramix Pro Slab on Ground | Generado por Poly Expert', 0, 0, 'C')

def render_pdf(data):
    pdf = PolykretPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # 1. ENCABEZADO DE PROYECTO
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Proyecto: {data['project_name']}", 0, 1, 'L', True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f"Cliente: {data['client_name']}", 0, 1)
    pdf.cell(0, 7, f"Ubicación: {data['location']}", 0, 1)
    pdf.cell(0, 7, f"Fecha: {data['date']} {data['time']}", 0, 1)
    pdf.ln(5)

    # 2. DATOS DE ENTRADA
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "1. PARÁMETROS DE DISEÑO", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    
    col_width = 90
    pdf.cell(col_width, 7, f"Espesor de losa: {data['thickness']} mm", 1)
    pdf.cell(col_width, 7, f"Resistencia Concreto (f'c): {data['fc']} kg/cm2", 1, 1)
    pdf.cell(col_width, 7, f"Suelo (CBR): {data['cbr']}%", 1)
    pdf.cell(col_width, 7, f"Módulo K: {data['k_val']} N/mm3", 1, 1)
    pdf.cell(col_width, 7, f"Fibra: {data['fiber_type']}", 1)
    pdf.cell(col_width, 7, f"Dosificación: {data['dosage']} kg/m3", 1, 1)
    pdf.ln(5)

    # 3. CARGAS
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "2. CARGAS CONSIDERADAS", 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(col_width, 7, f"Carga Puntual Actuante: {data['load_f']} kN", 1)
    pdf.cell(col_width, 7, f"Carga de Diseño (x{data['gamma_q']}): {round(data['load_f']*data['gamma_q'], 1)} kN", 1, 1)
    if data.get('udl_q', 0) > 0:
        pdf.cell(0, 7, f"Carga Distribuida (UDL): {data['udl_q']} kN/m2", 1, 1)
    pdf.ln(5)

    # 4. RESULTADOS DE VERIFICACIÓN
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "3. VERIFICACIÓN DE UTILIZACIÓN (TR34 4th Ed)", 0, 1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(60, 7, "Posición", 1, 0, 'C', True)
    pdf.cell(60, 7, "Momento Actuante", 1, 0, 'C', True)
    pdf.cell(60, 7, "Utilización", 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 10)
    positions = [
        ("Centro de Losa", data['m_ed'], data['utilization']),
        ("Juntas de Construcción", data['m_ed_joint'], data['utilization_joint']),
        ("Bordes / Esquinas", data['m_ed_edge'], data['utilization_edge']),
    ]
    
    for pos, med, util in positions:
        pdf.cell(60, 7, pos, 1)
        pdf.cell(60, 7, f"{round(med, 2)} kNm/m", 1, 0, 'C')
        
        # Color según utilización
        if util > 100:
            pdf.set_text_color(200, 0, 0)
        else:
            pdf.set_text_color(0, 128, 0)
            
        pdf.cell(60, 7, f"{util}%", 1, 1, 'C')
        pdf.set_text_color(0, 0, 0)

    pdf.ln(5)
    pdf.cell(90, 7, "Punzonamiento (Punching):", 1)
    pdf.cell(90, 7, f"{data['utilization_punch']}%", 1, 1, 'C')
    pdf.ln(10)

    # 5. CONCLUSIÓN Y RECOMENDACIONES
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "4. CONCLUSIONES Y RECOMENDACIONES", 0, 1)
    
    if all(u <= 100 for u in [data['utilization'], data['utilization_joint'], data['utilization_edge'], data['utilization_punch']]):
        pdf.set_fill_color(200, 255, 200)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 10, "ESTADO: DISEÑO ACEPTADO", 1, 1, 'C', True)
    else:
        pdf.set_fill_color(255, 200, 200)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 10, "ESTADO: REDISEÑO REQUERIDO", 1, 1, 'C', True)
    
    pdf.ln(5)
    pdf.set_font('Arial', '', 9)
    for rec in data.get('recommendations', []):
        pdf.multi_cell(0, 5, f"* {rec}")
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.multi_cell(0, 4, "Nota: Esta asistencia técnica automatizada debe ser validada por el ingeniero responsable de la obra. Los cálculos siguen los lineamientos de TR34 y Eurocode 2.")

    # Generar salida en bytes
    return pdf.output()
