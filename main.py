from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

from engine import PolykretEngine
from pdf_gen import render_pdf

app = FastAPI(title="Polykret | Material Calculator (Bekaert Standard)")

base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
templates_dir = os.path.join(base_dir, "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = None
if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)

engine = PolykretEngine()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    if templates:
        try:
            # Renderizado manual para evitar el error de Starlette en Vercel
            content = templates.get_template("index.html").render({"request": request})
            return HTMLResponse(content=content)
        except Exception as e:
            return f"<h1>Error de Renderizado</h1><p>{str(e)}</p>"
    return "<h1>API Polykret Activa</h1>"

def perform_calculations(data: dict):
    # 1. Preparar parámetros técnicos
    thickness = float(data.get('thickness', 200))
    cbr = float(data.get('cbr', 30))
    fc = float(data.get('fc', 280))
    dosage = float(data.get('dosage', 22))
    fiber_type = data.get('fiber_type', '4D 80/60BGE')
    
    # carga de pallet rack
    load_f = float(data.get('load_f', 77))
    plate_x = float(data.get('plate_x', 150))
    plate_y = float(data.get('plate_y', 150))

    # 2. Ejecutar Motor Riguroso
    k = engine.calculate_subgrade_modulus(cbr)
    conc = engine.calculate_concrete_properties(fc)
    lel = engine.calculate_elastic_length(thickness, conc["ecm"], k)
    fiber_props = engine.calculate_fiber_properties(fiber_type, dosage)
    
    # Resistencias
    m_res = engine.calculate_moment_resistance(thickness, conc, fiber_props)
    
    # Verificaciones
    v_loads = engine.verify_loads(
        load_f, plate_x, plate_y, thickness, lel, 
        m_res['m_rd_c'], m_res['m_rd_total'], k
    )
    
    results = {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "time": datetime.now().strftime("%H:%M"),
        "k_val": k,
        "fck": conc["fck"],
        "ecm": int(conc["ecm"]),
        "lel": int(lel),
        "m_rd_c": m_res['m_rd_c'],
        "m_rd_total": m_res['m_rd_total'],
        **v_loads,
        **data # Incluye project_name, etc
    }
    
    # Añadir recomendaciones basadas en utilizaciones
    recs = []
    if results['utilization'] > 100 or results['utilization_joint'] > 100:
        recs.append("REDISEÑO REQUERIDO: Se excede capacidad a flexión.")
    if results['utilization_soil'] > 100:
        recs.append("ALERTA: Presión en suelo excede límite admisible (5mm).")
    if not recs:
        recs.append("DISEÑO ÓPTIMO: La losa cumple con todos los requisitos TR34.")
        
    results["recommendations"] = recs
    return results

@app.post("/calculate")
async def calculate(
    thickness: float = Form(...), cbr: float = Form(...), fc: float = Form(...), 
    dosage: float = Form(...), fiber_type: str = Form(...), 
    load_f: float = Form(...), plate_x: float = Form(...), plate_y: float = Form(...),
    project_name: str = Form(...), client_name: str = Form(...)
):
    data = locals()
    return perform_calculations(data)

@app.post("/generate-pdf")
async def generate_pdf(
    thickness: float = Form(...), cbr: float = Form(...), fc: float = Form(...), 
    dosage: float = Form(...), fiber_type: str = Form(...), 
    load_f: float = Form(...), plate_x: float = Form(...), plate_y: float = Form(...),
    project_name: str = Form(...), client_name: str = Form(...)
):
    data = locals()
    pdf_params = perform_calculations(data)
    pdf_content = render_pdf(pdf_params)
    
    filename = f"Memoria_Tecnica_{project_name.replace(' ', '_')}.pdf"
    return Response(
        content=bytes(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
