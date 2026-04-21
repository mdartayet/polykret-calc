from fpdf import FPDF
from datetime import datetime

class EngineeringReportPDF(FPDF):
    def header(self):
        # Fondo decorativo para el título
        self.set_fill_color(0, 77, 128)
        self.rect(0, 0, 210, 40, 'F')
        
        self.set_y(10)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'ESTUDIO TÉCNICO DE PAVIMENTOS INDUSTRIALES', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'Refuerzo con Fibras de Acero Dramix® | Norma TR34 4th Ed', 0, 1, 'C')
        self.ln(15)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'Este documento es un estudio técnico automatizado basado en estándares TR34 y Eurocódigo 2.', 0, 1, 'C')
        self.cell(0, 5, f'Página {self.page_no()} | Polykret - Consultoría de Ingeniería', 0, 0, 'C')

def render_pdf(data):
    pdf = EngineeringReportPDF()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    
    # --- BLOQUE 0: INFO PROYECTO ---
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, f" RESUMEN DEL PROYECTO: {data.get('project_name','-')}", 1, 1, 'L', True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(95, 7, f" Cliente: {data.get('client_name','-')}", 1, 0)
    pdf.cell(95, 7, f" Fecha: {data.get('date','-')} {data.get('time','')}", 1, 1)
    pdf.ln(5)

    # --- BLOQUE 1: ESPECIFICACIÓN DE COMPONENTES ---
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 77, 128)
    pdf.cell(0, 10, "1. ESPECIFICACIÓN DE COMPONENTES DEL PAVIMENTO", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    
    # Cuadro resumen componentes
    pdf.set_fill_color(245, 245, 255)
    pdf.cell(50, 8, " Espesor de la losa:", 1, 0, 'L', True); pdf.set_font('Arial', 'B', 10); pdf.cell(140, 8, f" {data['h']} mm", 1, 1); pdf.set_font('Arial', '', 10)
    pdf.cell(50, 8, " Clase de Concreto:", 1, 0, 'L', True); pdf.cell(140, 8, f" C{int(data['fck'])}/{int(data['fck']+5)} ({int(data['fck']*10)} kg/cm2)", 1, 1)
    pdf.cell(50, 8, " Refuerzo de Fibra:", 1, 0, 'L', True); pdf.cell(140, 8, f" {data['fiber_type']} @ {data['dosage']} kg/m3", 1, 1)
    pdf.cell(50, 8, " Refuerzo Adicional:", 1, 0, 'L', True); pdf.cell(140, 8, f" {data.get('edge_reinforcement','-')}", 1, 1)
    pdf.cell(50, 8, " Recubrimiento:", 1, 0, 'L', True); pdf.cell(140, 8, f" {data.get('cover','40 mm')}", 1, 1)
    pdf.cell(50, 10, " Suelo / Sub-base:", 1, 0, 'L', True); pdf.multi_cell(140, 5, f" {data.get('subbase_req','-')}\n CBR: {data.get('cbr','-')}% | K: {data.get('k_val','-')} N/mm3", 1)
    pdf.ln(5)

    # --- BLOQUE 2: PLANIFICACIÓN DE JUNTAS ---
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 77, 128)
    pdf.cell(0, 10, "2. PLANIFICACIÓN Y CONTROL DE JUNTAS", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    
    pdf.multi_cell(0, 6, f"* Distribución de Paneles: Se establece una cuadrícula máxima de {data.get('joint_max_dist','-')} para el control de contracción.\n"
                         f"* Tipología: {data.get('joint_type','-')}.\n"
                         f"* Transferencia de Carga: Estimada en un 85% a través de la trabazón de agregado con fibras o uso de pasadores mecánicos en juntas de construcción.")
    pdf.ln(5)

    # --- BLOQUE 3: VERIFICACIÓN DE SEGURIDAD Y ESTABILIDAD ---
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 77, 128)
    pdf.cell(0, 10, "3. VERIFICACIÓN DE SEGURIDAD Y ESTABILIDAD (RATIOS)", 0, 1)
    pdf.set_text_color(0, 0, 0)
    
    # Tabla de Ratios
    pdf.set_fill_color(0, 77, 128)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(80, 8, " Análisis de Escenario", 1, 0, 'C', True)
    pdf.cell(60, 8, " Ratio de Utilización", 1, 0, 'C', True)
    pdf.cell(50, 8, " Estatus", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    
    analysis_data = [
        ("Carga Puntual en Centro (Flexión)", f"{data.get('ratio_flex','-')}", "SEGURO" if data.get('ratio_flex',0) <= 1.0 else "FALLA"),
        ("Carga en Juntas / Bordes", f"{data.get('max_ratio','-')}", "SEGURO" if data.get('max_ratio',0) <= 1.0 else "FALLA"),
        ("Resistencia al Punzonamiento", f"{data.get('ratio_punch','-')}", "SEGURO" if data.get('ratio_punch',0) <= 1.0 else "FALLA"),
        ("Capacidad de Soporte Terreno (Soil)", f"{data.get('ratio_soil','-')}", "SEGURO" if data.get('ratio_soil',0) <= 1.0 else "FALLA"),
    ]

    for label, ratio, status in analysis_data:
        pdf.cell(80, 8, f" {label}", 1)
        pdf.cell(60, 8, f" {ratio}", 1, 0, 'C')
        if status == "FALLA": pdf.set_text_color(200, 0, 0)
        else: pdf.set_text_color(0, 128, 0)
        pdf.cell(50, 8, f" {status}", 1, 1, 'C')
        pdf.set_text_color(0, 0, 0)

    pdf.ln(10)
    pdf.set_font('Arial', 'I', 9)
    pdf.multi_cell(0, 5, "Nota: El análisis de flexión asegura que la losa soporte los racks sin fracturarse por doblamiento. El análisis de punzonamiento valida que las patas de los racks no perforen el concreto.")

    return pdf.output()
