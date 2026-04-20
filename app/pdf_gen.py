from xhtml2pdf import pisa
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
import os

def render_pdf(data):
    """
    Renderiza un PDF basado en un template HTML y los datos calculados.
    """
    template_path = os.path.join(os.path.dirname(__file__), 'templates/pdf_template.html')
    env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))
    template = env.get_template('pdf_template.html')
    
    html_content = template.render(data=data)
    
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=result)
    
    if pisa_status.err:
        return None
    
    return result.getvalue()
