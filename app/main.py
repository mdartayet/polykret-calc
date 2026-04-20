from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

# Importar lógica personalizada
import os
import sys

# Asegurar que el directorio actual esté en el path para despliegue
sys.path.append(os.path.dirname(__file__))

from engine import PolykretEngine
from pdf_gen import render_pdf

app = FastAPI(title="Polykret Material Calculator")

# Configurar estáticos y templates
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
templates_dir = os.path.join(base_dir, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

engine = PolykretEngine()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

def perform_calculations(data: dict):
    # Parámetros básicos con defaults
    thickness = data.get('thickness', 200)
    cbr = data.get('cbr', 30)
    fc = data.get('fc', 280)
    fiber_type = data.get('fiber_type', 'Dramix 4D 80/60BGE')
    dosage = data.get('dosage', 22.0)
    
    # 1. Ejecutar Motor de Cálculo
    k = engine.calculate_subgrade_modulus(cbr)
    conc = engine.calculate_concrete_properties(fc)
    lel = engine.calculate_elastic_length(thickness, conc["ecm"], k)
    
    # Props de fibras dinámicas
    fiber_props = engine.calculate_fiber_properties(fiber_type, dosage)
    
    # Refuerzo (opcional)
    reinforcement = {"as": data.get("as_area", 0)}
    
    # Calcular resistencias
    m_res = engine.calculate_moment_resistance(thickness, conc, fiber_props=fiber_props, reinforcement=reinforcement)
    
    # Verificar cargas en múltiples posiciones
    v_loads = engine.verify_loads(
        data.get('load_f', 0), data.get('plate_x', 150), data.get('plate_y', 150), thickness, lel, 
        m_rd_f=m_res['m_rd_f'], 
        m_rd_total=m_res['m_rd_total'], 
        k=k,
        m_rd_c=m_res['m_rd_c'],
        fck=conc['fck']
    )
    
    # Verificaciones adicionales si existen
    if data.get("udl_q"):
        udl_res = engine.verify_udl(data["udl_q"], data.get("udl_w", 4.0), thickness, lel, m_res["m_rd_c"])
        v_loads.update(udl_res)
        
    if data.get("line_p"):
        line_res = engine.verify_line_load(data["line_p"], thickness, lel, m_res["m_rd_c"])
        v_loads.update(line_res)
    
    # Generar Recomendaciones
    recommendations = engine.generate_recommendations(v_loads)
    
    return {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "time": datetime.now().strftime("%H:%M"),
        "fck": conc["fck"],
        "ecm": int(conc["ecm"]),
        "k_val": k,
        "lel": lel,
        "m_rd_c": m_res['m_rd_c'],
        "m_rd_f": m_res['m_rd_f'],
        "m_rd_total": m_res['m_rd_total'],
        "m_ed": v_loads['m_ed_center'],
        "m_ed_joint": v_loads['m_ed_joint'],
        "m_ed_edge": v_loads['m_ed_edge'],
        "m_ed_corner": v_loads['m_ed_corner'],
        "p_ed": v_loads['p_ed_soil'],
        "v_rd_punch": v_loads['v_rd_punch'],
        "utilization": v_loads['utilization_center'],
        "utilization_joint": v_loads['utilization_joint'],
        "utilization_edge": v_loads['utilization_edge'],
        "utilization_corner": v_loads['utilization_corner'],
        "utilization_punch": v_loads.get("utilization_punch", 0),
        "utilization_udl": v_loads.get("utilization_udl", 0),
        "utilization_line": v_loads.get("utilization_line", 0),
        "recommendations": recommendations,
        "gamma_q": engine.gamma_q,
        "gamma_c": engine.gamma_c,
        "gamma_f": engine.gamma_f,
        "gamma_s": engine.gamma_s,
        **data
    }

@app.post("/calculate")
async def calculate(
    thickness: int = Form(200),
    cbr: int = Form(30),
    fc: int = Form(280),
    fiber_type: str = Form(""),
    dosage: float = Form(22.0),
    load_f: float = Form(77.0),
    plate_x: int = Form(150),
    plate_y: int = Form(150),
    udl_q: float = Form(0),
    line_p: float = Form(0),
    as_area: float = Form(0)
):
    data = {
        "thickness": thickness,
        "cbr": cbr,
        "fc": fc,
        "fiber_type": fiber_type,
        "dosage": dosage,
        "load_f": load_f,
        "plate_x": plate_x,
        "plate_y": plate_y,
        "udl_q": udl_q,
        "line_p": line_p,
        "as_area": as_area
    }
    return perform_calculations(data)

@app.post("/generate-pdf")
async def generate_pdf(
    thickness: int = Form(...),
    cbr: int = Form(...),
    fc: int = Form(...),
    fiber_type: str = Form("Dramix 4D 80/60BGE"),
    dosage: float = Form(...),
    project_name: str = Form("Reporte Técnico Polykret"),
    client_name: str = Form("Instalación Industrial"),
    location: str = Form("Ecuador"),
    contact_person: str = Form("N/A"),
    email: str = Form("N/A"),
    phone: str = Form("N/A"),
    observation: str = Form(""),
    prepared_by: str = Form("Melanie Naranjo"),
    company_name: str = Form("IdealAlambrec Bekaert"),
    designer_email: str = Form("Melanie.Naranjo@bekaert.com"),
    joint_dist: float = Form(4.0),
    load_f: float = Form(0),
    plate_x: int = Form(150),
    plate_y: int = Form(150),
    udl_q: float = Form(0),
    line_p: float = Form(0),
    as_area: float = Form(0)
):
    input_data = {
        "thickness": thickness,
        "cbr": cbr,
        "fc": fc,
        "fiber_type": fiber_type,
        "dosage": dosage,
        "project_name": project_name,
        "client_name": client_name,
        "location": location,
        "contact_person": contact_person,
        "email": email,
        "phone": phone,
        "observation": observation,
        "prepared_by": prepared_by,
        "company_name": company_name,
        "designer_email": designer_email,
        "joint_dist": joint_dist,
        "load_f": load_f,
        "plate_x": plate_x,
        "plate_y": plate_y,
        "udl_q": udl_q,
        "line_p": line_p,
        "as_area": as_area
    }
    
    # 1. Ejecutar Motor de Cálculo
    pdf_params = perform_calculations(input_data)
    
    # 2. Generar PDF
    pdf_content = render_pdf(pdf_params)
    
    if not pdf_content:
        return Response(content="Error generando PDF", status_code=500)
    
    # Limpiar nombre de archivo
    safe_client = "".join([c for c in client_name if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    filename = f"Memoria_Polykret_{safe_client}.pdf"
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
