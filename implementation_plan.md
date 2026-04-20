# Proyecto: Polykret Material Calculator

## Objetivo
Desarrollar un servicio web que permita calcular las cantidades de material necesarias para pavimentos industriales reforzados con fibras de acero, generando un reporte técnico en PDF profesional basado en el estándar TR34/Eurocódigo 2.

## Fases del Proyecto

### 🏗️ Fase 1: Estructura y Motor de Cálculo (Backend)
- [ ] Crear estructura de carpetas (FastAPI).
- [ ] Implementar `engine.py`: Lógica matemática y física (Elastic Length, Moment Capacity, Punching Shear).
- [ ] Validar resultados contra el PDF de ejemplo (Promart).

### 📄 Fase 2: Generación de PDF
- [ ] Diseñar template HTML/CSS que replique la estética de Bekaert/Polykret.
- [ ] Implementar `pdf_generator.py` usando `xhtml2pdf` o `WeasyPrint`.
- [ ] Cargar logos y estilos de Polykret.

### 🌐 Fase 3: Interfaz Web (Frontend)
- [ ] Desarrollar formulario dinámico (HTML/Vanilla CSS).
- [ ] Implementar visualización previa de los cálculos en pantalla.
- [ ] Conectar el botón de "Generar PDF".

### 🧪 Fase 4: Despliegue y Validación
- [ ] Pruebas finales con diferentes cargas y CBRs.
- [ ] Optimización de la interfaz.

## Parámetros Técnicos Extraídos
- **Fórmulas**: Página 15 (Elastic Length), Página 20 (Moment Resistant), Página 24 (Shear/Punching).
- **Materiales**: Bekaert Dramix Series 4D/5D.
- **Normativa**: TR34 4th Edition.
