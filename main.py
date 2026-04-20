from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, Response, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

# Importar lógica personalizada
from engine import PolykretEngine
from pdf_gen import render_pdf

app = FastAPI(title="Polykret Material Calculator")

# Rutas
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
    if not templates:
        return "<h1>API Polykret Activa</h1><p>Sistema en línea.</p>"
    try:
        # Usar la firma más básica posible
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        return f"<h1>Error de Sistema</h1><p>{str(e)}</p>"

def perform_calculations(data: dict):
    # Lógica de cálculo (omito detalles por brevedad pero está completa)
    k = engine.calculate_subgrade_modulus(data.get('cbr', 30))
    conc = engine.calculate_concrete_properties(data.get('fc', 280))
    lel = engine.calculate_elastic_length(data.get('thickness', 200), conc["ecm"], k)
    fiber_props = engine.calculate_fiber_properties(data.get('fiber_type', 'Dramix 4D 80/60BGE'), data.get('dosage', 22))
    reinforcement = {"as": data.get("as_area", 0)}
    m_res = engine.calculate_moment_resistance(data.get('thickness', 200), conc, fiber_props=fiber_props, reinforcement=reinforcement)
    
    v_loads = engine.verify_loads(
        data.get('load_f', 0), data.get('plate_x', 150), data.get('plate_y', 150), data.get('thickness', 200), lel, 
        m_rd_f=m_res['m_rd_f'], m_rd_total=m_res['m_rd_total'], k=k, m_rd_c=m_res['m_rd_c'], fck=conc['fck']
    )
    
    if data.get("udl_q"):
        udl_res = engine.verify_udl(data["udl_q"], data.get("udl_w", 4.0), data.get('thickness', 200), lel, m_res["m_rd_c"])
        v_loads.update(udl_res)
    if data.get("line_p"):
        line_res = engine.verify_line_load(data["line_p"], data.get('thickness', 200), lel, m_res["m_rd_c"])
        v_loads.update(line_res)
    
    recommendations = engine.generate_recommendations(v_loads)
    return {**v_loads, "recommendations": recommendations, "date": datetime.now().strftime("%d/%m/%Y"), "time": datetime.now().strftime("%H:%M"), "k_val": k, "lel": lel, "m_rd_c": m_res['m_rd_c'], "m_rd_f": m_res['m_rd_f'], "m_rd_total": m_res['m_rd_total'], "gamma_q": 1.5, **data}

@app.post("/calculate")
async def calculate(thickness: int = Form(200), cbr: int = Form(30), fc: int = Form(280), fiber_type: str = Form(""), dosage: float = Form(22)):
    return perform_calculations({"thickness": thickness, "cbr": cbr, "fc": fc, "fiber_type": fiber_type, "dosage": dosage})

@app.post("/generate-pdf")
async def generate_pdf(thickness: int = Form(...), cbr: int = Form(...), fc: int = Form(...), dosage: float = Form(...), client_name: str = Form("Cliente")):
    params = perform_calculations({"thickness": thickness, "cbr": cbr, "fc": fc, "dosage": dosage, "client_name": client_name})
    pdf_content = render_pdf(params)
    return Response(content=bytes(pdf_content), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=Memoria_{client_name}.pdf"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
