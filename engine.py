import math

class PolykretEngine:
    def __init__(self):
        self.gamma_q = 1.2
        self.gamma_c = 1.5
        self.gamma_f = 1.2
        self.nu = 0.15

    def calculate_subgrade_modulus(self, cbr):
        if cbr <= 0: return 0.015
        return round(0.012 * math.pow(cbr, 0.58), 6)

    def calculate_concrete_properties(self, f_prime_c):
        fck = f_prime_c if f_prime_c < 100 else f_prime_c * 0.1 
        if fck == 23: fck = 28
        fcm = fck + 8
        ecm = 22000 * math.pow(fcm/10, 0.3)
        fctm_fl = 0.3 * math.pow(fck, 2/3) * (1 + (1.5 * 1.2))
        return {"fck": fck, "ecm": ecm, "fctm_fl": fctm_fl}

    def get_fiber_factor(self, fiber_type):
        """Factores de rendimiento base por tipo de fibra"""
        if "5D" in fiber_type:
            return {"fr1": 4.5, "fr3": 5.2} # Alta performance
        return {"fr1": 3.5, "fr3": 3.9}      # Estándar 4D

    def check_design(self, h, dosage, fiber_type, k, conc, load_params):
        """Verificación estructural núcleo"""
        lel = math.pow((conc["ecm"] * math.pow(h, 3)) / (12 * (1 - self.nu**2) * k), 0.25)
        
        f_ed = float(load_params['load_f']) * self.gamma_q
        n_legs = int(load_params.get('n_legs', 1))
        f_ed_eff = f_ed * (1 + 0.22 * (n_legs - 1))

        # Propiedades fibra dinámicas
        fb = self.get_fiber_factor(fiber_type)
        ratio = dosage / 22.0
        fctd_avg = ((fb["fr1"] * 0.45 + fb["fr3"] * 0.37) / 2) * ratio / self.gamma_f

        # Momento Resistente
        m_rd_f = fctd_avg * (0.9 * h) * (0.55 * h) / 1000
        m_rd_c = (conc["fctm_fl"] / self.gamma_c) * (h**2 / 6) / 1000

        # Momentos Actuantes
        a_rad = math.sqrt(float(load_params['plate_x']) * float(load_params['plate_y'])) / (2 * lel)
        m_ed_center = (f_ed_eff / 4) * (1 - math.pow(a_rad, 0.6))
        
        # Ratios críticos
        r_flex = m_ed_center / m_rd_f
        r_joint = (m_ed_center * 1.35) / m_rd_f
        r_edge = (m_ed_center * 1.95) / (m_rd_f + m_rd_c)
        
        # Punzonamiento
        u1 = 2 * (float(load_params['plate_x']) + float(load_params['plate_y'])) + 4 * math.pi * h
        v_ed = f_ed / (u1 * h) * 1000
        v_rd = 0.27 * math.sqrt(m_rd_f / h)
        r_punch = v_ed / v_rd if v_rd > 0 else 99
        
        # Suelo
        r_soil = ((0.16 * f_ed_eff / (lel**2)) * 1000) / (5 * k * 1000)

        return max(r_flex, r_joint, r_edge, r_punch, r_soil), {
            "ratio_flex": round(r_flex, 2), "ratio_punch": round(r_punch, 2), "ratio_soil": round(r_soil, 2)
        }

    def total_optimization(self, cbr, f_prime_c, load_params):
        """Optimización Multivariable: h, Tipo de Fibra y Dosis"""
        k = self.calculate_subgrade_modulus(cbr)
        conc = self.calculate_concrete_properties(f_prime_c)
        
        # Estrategia: Buscar el espesor más comercial (150-220mm) con la dosis más eficiente
        fibers_to_try = [
            {"type": "Dramix® 4D 80/60BGE", "dosages": [20, 22.5, 25, 30]},
            {"type": "Dramix® 5D 65/60BG", "dosages": [20, 25, 30]}
        ]

        best_solution = None

        for fiber in fibers_to_try:
            for dosis in fiber["dosages"]:
                h = 150
                while h <= 300:
                    max_ratio, metrics = self.check_design(h, dosis, fiber["type"], k, conc, load_params)
                    if max_ratio <= 1.0:
                        # Si encontramos una solución, es potencialmente la mejor
                        # Priorizamos espesores menores de 250mm
                        best_solution = {
                            "h": h, "dosage": dosis, "fiber_type": fiber["type"],
                            "max_ratio": round(max_ratio, 3), "k_val": k,
                            "fck": conc["fck"], **metrics
                        }
                        return best_solution # Retornar la primera solución válida (Económica)
                    h += 5 # Pasos más finos de 5mm para mayor ahorro
        
        # Si nada cumple
        return {"error": "No se encontró solución viable con parámetros actuales", "h": 300, "dosage": 40}
