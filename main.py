from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os

from engine import PolykretEngine
from pdf_gen import render_pdf

app = FastAPI(title="Polykret | Bekaert Standard Optimizer")

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
    """Detecta automáticamente si la entrada es JSON o Form-Data"""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return await request.json()
    else:
        form_data = await request.form()
        return dict(form_data)

def perform_optimization_logic(data: dict):
    # Sanitizar y asegurar tipos
    try:
        cbr = float(data.get('cbr', 30))
        fc = float(data.get('fc', 280))
        dosage = float(data.get('dosage', 22))
        fiber_type = data.get('fiber_type', '4D 80/60BGE')
        
        load_params = {
            'load_f': float(data.get('load_f', 77) or 0),
            'plate_x': float(data.get('plate_x', 150) or 150),
            'plate_y': float(data.get('plate_y', 150) or 150),
            'rack_z': float(data.get('rack_z', 300) or 300),
            'rack_x': float(data.get('rack_x', 1200) or 1200),
            'n_legs': int(data.get('n_legs', 1))
        }

        results = engine.optimize_thickness(cbr, fc, dosage, fiber_type, load_params)
        
        results.update({
            "date": datetime.now().strftime("%d/%m/%Y"),
            "time": datetime.now().strftime("%H:%M"),
            "project_name": data.get('project_name', 'Unnamed Project'),
            "client_name": data.get('client_name', 'Unnamed Client'),
            "dosage": dosage,
            "load_f": load_params['load_f']
        })
        return results
    except Exception as e:
        return {"error": str(e), "msg": "Error en el procesamiento de datos de entrada."}

@app.post("/calculate")
async def calculate(request: Request):
    data = await get_request_data(request)
    return perform_optimization_logic(data)

@app.post("/generate-pdf")
async def generate_pdf(request: Request):
    data = await get_request_data(request)
    
    optimized_results = perform_optimization_logic(data)
    if "error" in optimized_results:
        return Response(content=optimized_results["error"], status_code=400)
        
    pdf_content = render_pdf(optimized_results)
    
    project = str(optimized_results.get('project_name', 'Report')).replace(' ', '_')
    filename = f"Memoria_Polykret_{project}.pdf"
    
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
