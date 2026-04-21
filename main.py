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

def perform_full_optimization(data: dict):
    try:
        # Solo necesitamos Suelo, Concreto y Carga
        cbr = float(data.get('cbr', 30))
        fc = float(data.get('fc', 280))
        
        load_params = {
            'load_f': float(data.get('load_f', 0) or 0),
            'plate_x': float(data.get('plate_x', 150) or 150),
            'plate_y': float(data.get('plate_y', 150) or 150),
            'n_legs': int(data.get('n_legs', 1) or 1),
            'fl_wheel_load': float(data.get('fl_wheel_load', 0) or 0),
            'fl_pressure': float(data.get('fl_pressure', 2.0) or 2.0),
            'tr_wheel_load': float(data.get('tr_wheel_load', 0) or 0),
            'tr_pressure': float(data.get('tr_pressure', 0.8) or 0.8)
        }

        # La magia ocurre aquí: Diseño Total
        results = engine.total_optimization(cbr, fc, load_params)
        
        if "error" in results:
            return results

        results.update({
            "date": datetime.now().strftime("%d/%m/%Y"),
            "time": datetime.now().strftime("%H:%M"),
            "project_name": data.get('project_name', 'Unnamed Project'),
            "client_name": data.get('client_name', 'Unnamed Client'),
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
    filename = f"Propuesta_Polykret_{optimized.get('project_name','Recibido').replace(' ', '_')}.pdf"
    
    return Response(
        content=bytes(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
