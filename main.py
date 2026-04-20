from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os
import sys

# Importar lógica personalizada
from engine import PolykretEngine
from pdf_gen import render_pdf

app = FastAPI(title="Polykret Material Calculator")

# Configurar rutas absolutas seguras
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
templates_dir = os.path.join(base_dir, "templates")

# Intentar montar si existen
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
            return templates.TemplateResponse(
                request=request, 
                name="index.html", 
                context={"request": request}
            )
        except Exception as e:
            return f"<h1>Error de Sistema</h1><p>{str(e)}</p>"
    return "<h1>Polykret API Activa</h1>"

def perform_calculations(data: dict):
    # Parámetros básicos con defaults
    thickness = data.get('thickness', 200)
    cbr = data.get('cbr', 30)
    fc = data.get('fc', 280)
    fiber_type = data.get('fiber_type', 'Dramix 4D 80/60BGE')
    dosage = data.get('dosage', 22.0)
    
    k = engine.calculate_subgrade_modulus(cbr)
    conc = engine.calculate_concrete_properties(fc)
    lel = engine.calculate_elastic_length(thickness, conc["ecm"], k)
    fiber_props = engine.calculate_fiber_properties(fiber_type, dosage)
    reinforcement = {"as": data.get("as_area", 0)}
    m_res = engine.calculate_moment_resistance(thickness, conc, fiber_props=fiber_props, reinforcement=reinforcement)
    
    v_loads = engine.verify_loads(
        data.get('load_f', 0), data.get('plate_x', 150), data.get('plate_y', 150), thickness, lel, 
        m_rd_f=m_res['m_rd_f'], 
        m_rd_total=m_res['m_rd_total'], 
        k=k,
        m_rd_c=m_res['m_rd_c'],
        fck=conc['fck']
    )
    
    if data.get("udl_q"):
        udl_res = engine.verify_udl(data["udl_q"], data.get("udl_w", 4.0), thickness, lel, m_res["m_rd_c"])
        v_loads.update(udl_res)
        
    if data.get("line_p"):
        line_res = engine.verify_line_load(data["line_p"], thickness, lel, m_res["m_rd_c"])
        v_loads.update(line_res)
    
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
        "thickness": thickness, "cbr": cbr, "fc": fc, "fiber_type": fiber_type,
        "dosage": dosage, "load_f": load_f, "plate_x": plate_x, "plate_y": plate_y,
        "udl_q": udl_q, "line_p": line_p, "as_area": as_area
    }
    return perform_calculations(data)

@app.post("/generate-pdf")
async def generate_pdf(
    thickness: int = Form(...),
    cbr: int = Form(...),
    fc: int = Form(...),
    dosage: float = Form(...),
    fiber_type: str = Form("Dramix 4D 80/60BGE"),
    project_name: str = Form("Reporte Técnico Polykret"),
    client_name: str = Form("Instalación Industrial"),
    location: str = Form("Ecuador"),
    load_f: float = Form(0),
    plate_x: int = Form(150),
    plate_y: int = Form(150),
    udl_q: float = Form(0),
    line_p: float = Form(0),
    as_area: float = Form(0)
):
    input_data = {
        "thickness": thickness, "cbr": cbr, "fc": fc, "fiber_type": fiber_type,
        "dosage": dosage, "project_name": project_name, "client_name": client_name,
        "location": location, "load_f": load_f, "plate_x": plate_x, "plate_y": plate_y,
        "udl_q": udl_q, "line_p": line_p, "as_area": as_area
    }
    pdf_params = perform_calculations(input_data)
    pdf_content = render_pdf(pdf_params)
    
    safe_client = "".join([c for c in client_name if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    filename = f"Memoria_Polykret_{safe_client}.pdf"
    
    return Response(
        content=bytes(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
