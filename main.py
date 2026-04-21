from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

from engine import PolykretEngine
from pdf_gen import render_pdf

app = FastAPI(title="Polykret | Poly Expert Design Optimizer")

# Rutas
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
templates_dir = os.path.join(base_dir, "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir)
engine = PolykretEngine()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    content = templates.get_template("index.html").render({"request": request})
    return HTMLResponse(content=content)

async def get_request_data(request: Request):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return await request.json()
    else:
        form_data = await request.form()
        return dict(form_data)

def safe_float(val, default=0.0):
    """Convierte a float de forma segura manejando strings, comillas y vacíos"""
    try:
        if val is None or str(val).strip() == "" or str(val).strip() == "null":
            return default
        return float(str(val).replace(',', '.'))
    except:
        return default

def perform_full_optimization(data: dict):
    try:
        # Conversión ultra-segura de tipos (Soporta comillas del bot)
        cbr = safe_float(data.get('cbr'), 30.0)
        fc = safe_float(data.get('fc'), 280.0)
        
        load_params = {
            'load_f': safe_float(data.get('load_f'), 0.0),
            'plate_x': safe_float(data.get('plate_x'), 150.0),
            'plate_y': safe_float(data.get('plate_y'), 150.0),
            'n_legs': int(safe_float(data.get('n_legs'), 1.0)),
            'fl_wheel_load': safe_float(data.get('fl_wheel_load'), 0.0),
            'fl_pressure': safe_float(data.get('fl_pressure'), 2.0),
            'tr_wheel_load': safe_float(data.get('tr_wheel_load'), 0.0),
            'tr_pressure': safe_float(data.get('tr_pressure'), 0.8)
        }

        results = engine.total_optimization(cbr, fc, load_params)
        
        if "error" in results:
            return results

        results.update({
            "date": datetime.now().strftime("%d/%m/%Y"),
            "time": datetime.now().strftime("%H:%M"),
            "project_name": str(data.get('project_name', 'Unnamed Project')),
            "client_name": str(data.get('client_name', 'Unnamed Client')),
            "load_f": load_params['load_f']
        })
        return results
    except Exception as e:
        return {"error": f"Error técnico: {str(e)}", "h": 0}

@app.post("/calculate")
async def calculate(request: Request):
    data = await get_request_data(request)
    return perform_full_optimization(data)

@app.api_route("/generate-pdf", methods=["GET", "POST"])
async def generate_pdf(request: Request):
    if request.method == "GET":
        data = dict(request.query_params)
    else:
        data = await get_request_data(request)
    
    optimized = perform_full_optimization(data)
    
    if "error" in optimized and not optimized.get('h'):
        return Response(content=optimized["error"], status_code=400)
        
    pdf_content = render_pdf(optimized)
    filename = f"Propuesta_Polykret_{str(optimized.get('project_name','Report')).replace(' ', '_')}.pdf"
    
    return Response(
        content=bytes(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
