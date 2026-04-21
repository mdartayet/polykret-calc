from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os
import json

from engine import PolykretEngine
from pdf_gen import render_pdf

app = FastAPI(title="Polykret | Multi-Load Optimizer PRO")

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

def safe_float(val, default=0.0):
    try:
        if val is None or str(val).strip().lower() in ["", "null", "undefined", "nan"]:
            return default
        # Maneja tanto floats puros como strings con comas
        return float(str(val).replace(',', '.'))
    except (ValueError, TypeError):
        return default

async def get_request_data(request: Request):
    """Extrae datos intentando JSON primero y Form después"""
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            # Si el JSON viene envuelto en un objeto 'body' o 'arguments' (típico de bots)
            if isinstance(body, dict):
                if "body" in body and isinstance(body["body"], dict): return body["body"]
                if "arguments" in body and isinstance(body["arguments"], dict): return body["arguments"]
            return body
        # Fallback a form-data
        form_data = await request.form()
        return dict(form_data)
    except Exception:
        return {}

def perform_full_optimization(data: dict):
    try:
        # Normalización total de llaves (case-insensitive para el bot)
        clean_data = {str(k).lower(): v for k, v in data.items()}
        
        cbr = safe_float(clean_data.get('cbr'), 30.0)
        fc = safe_float(clean_data.get('fc'), 280.0)
        
        load_params = {
            'load_f': safe_float(clean_data.get('load_f', clean_data.get('carga_rack', 0.0))),
            'plate_x': safe_float(clean_data.get('plate_x'), 150.0),
            'plate_y': safe_float(clean_data.get('plate_y'), 150.0),
            'n_legs': int(safe_float(clean_data.get('n_legs'), 1.0)),
            'fl_wheel_load': safe_float(clean_data.get('fl_wheel_load', clean_data.get('carga_montacargas', 0.0))),
            'fl_pressure': safe_float(clean_data.get('fl_pressure'), 2.0),
            'tr_wheel_load': safe_float(clean_data.get('tr_wheel_load', clean_data.get('carga_camion', 0.0))),
            'tr_pressure': safe_float(clean_data.get('tr_pressure'), 0.8)
        }

        # Ejecutar diseño
        results = engine.total_optimization(cbr, fc, load_params)
        
        if "error" in results:
            return {"response": results}

        # Enriquecer resultados para el bot y el PDF
        results.update({
            "date": datetime.now().strftime("%d/%m/%Y"),
            "time": datetime.now().strftime("%H:%M"),
            "project_name": str(data.get('project_name', 'Nuevo Proyecto')),
            "client_name": str(data.get('client_name', 'Consultante')),
            "load_f": load_params['load_f']
        })
        return {"response": results} # Respondemos siempre dentro de un objeto 'response' para compatibilidad
        
    except Exception as e:
        return {"response": {"error": f"Fallo interno: {str(e)}", "h": 0}}

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
    
    optimized_wrapper = perform_full_optimization(data)
    optimized = optimized_wrapper["response"]
    
    if "error" in optimized and not optimized.get('h'):
        return Response(content=optimized["error"], status_code=400)
        
    pdf_content = render_pdf(optimized)
    filename = f"Propuesta_Polykret.pdf"
    
    return Response(
        content=bytes(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
