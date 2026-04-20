from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

from engine import PolykretEngine
from pdf_gen import render_pdf

app = FastAPI(title="Polykret | Bekaert Standard")

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
            content = templates.get_template("index.html").render({"request": request})
            return HTMLResponse(content=content)
        except Exception as e:
            return f"<h1>Error de Renderizado</h1><p>{str(e)}</p>"
    return "<h1>API Polykret Activa</h1>"

def perform_calculations(data: dict):
    # 1. Parámetros Técnicos
    thickness = float(data.get('thickness', 200))
    cbr = float(data.get('cbr', 30))
    fc = float(data.get('fc', 28)) # MPa ahora por el selector
    dosage = float(data.get('dosage', 22))
    fiber_type = data.get('fiber_type', '4D 80/60BGE')
    
    # 2. Carga de rack (gobernante por defecto)
    load_f = float(data.get('load_f', 77) or 0)
    plate_x = float(data.get('plate_x', 150) or 150)
    plate_y = float(data.get('plate_y', 150) or 150)

    # 3. Motor
    k = engine.calculate_subgrade_modulus(cbr)
    conc = engine.calculate_concrete_properties(fc * 10) # convertir de selector
    lel = engine.calculate_elastic_length(thickness, conc["ecm"], k)
    fiber_props = engine.calculate_fiber_properties(fiber_type, dosage)
    m_res = engine.calculate_moment_resistance(thickness, conc, fiber_props)
    
    v_loads = engine.verify_loads(
        load_f, plate_x, plate_y, thickness, lel, 
        m_res['m_rd_c'], m_res['m_rd_total'], k
    )
    
    return {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "time": datetime.now().strftime("%H:%M"),
        "k_val": k,
        "fck": conc["fck"],
        "ecm": int(conc["ecm"]),
        "lel": int(lel),
        "m_rd_c": m_res['m_rd_c'],
        "m_rd_total": m_res['m_rd_total'],
        **v_loads,
        **data
    }

@app.post("/calculate")
async def calculate(request: Request):
    form_data = await request.form()
    data = dict(form_data)
    # Sanitizar numéricos
    for k, v in data.items():
        if v == '': data[k] = 0
    return perform_calculations(data)

@app.post("/generate-pdf")
async def generate_pdf(request: Request):
    form_data = await request.form()
    data = dict(form_data)
    for k, v in data.items():
        if v == '': data[k] = 0
        
    pdf_params = perform_calculations(data)
    pdf_content = render_pdf(pdf_params)
    
    project = data.get('project_name', 'Reporte').replace(' ', '_')
    filename = f"Memoria_Polykret_{project}.pdf"
    
    return Response(
        content=bytes(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
