import math

class PolykretEngine:
    def __init__(self):
        # Factores de Seguridad estrictos
        self.gamma_q = 1.2
        self.gamma_c = 1.5
        self.gamma_f = 1.2
        self.nu = 0.15

    def calculate_subgrade_modulus(self, cbr):
        if cbr <= 0: return 0.015
        return round(0.012 * math.pow(cbr, 0.58), 6)

    def calculate_concrete_properties(self, f_prime_c):
        fck = f_prime_c * 0.8
        fcm = fck + 8
        ecm = 22000 * math.pow(fcm/10, 0.3)
        # Resistencia a flexotensión media (EN 1992-1-1)
        fctm_fl = 0.3 * math.pow(fck, 2/3) * (1 + (1.5 * 1.2))
        return {
            "fck": fck, "ecm": ecm, "fctm_fl": fctm_fl,
            "fcd": 0.85 * fck / self.gamma_c
        }

    def calculate_fiber_properties(self, fiber_type, dosage):
        ratio = dosage / 22.0
        # Valores base de Dramix 4D 80/60BGE
        fr1k = 3.50 * ratio
        fr3k = 3.94 * ratio
        fctd_s = (0.45 * fr1k) / self.gamma_f
        fctd_u = (0.37 * fr3k) / self.gamma_f
        return {"fctd_s": fctd_s, "fctd_u": fctd_u}

    def check_design(self, h, k, conc, fiber_props, load_params):
        """Valida los 3 escenarios críticos requeridos"""
        lel = math.pow((conc["ecm"] * math.pow(h, 3)) / (12 * (1 - self.nu**2) * k), 0.25)
        
        f_kN = float(load_params.get('load_f', 77))
        f_ed = f_kN * self.gamma_q
        px = float(load_params.get('plate_x', 150))
        py = float(load_params.get('plate_y', 150))
        n_legs = int(load_params.get('n_legs', 1))
        
        # Carga total de diseño considerando configuración de patas
        f_ed_total = f_ed * (1 + 0.22 * (n_legs - 1)) 

        # Resistencia de la sección (mRd)
        x = 0.1 * h
        fctd_avg = (fiber_props["fctd_s"] + fiber_props["fctd_u"]) / 2
        m_rd_total = fctd_avg * (h - x) * (h/2 + x/2) / 1000
        m_rd_c = (conc["fctm_fl"] / self.gamma_c) * (h**2 / 6) / 1000

        # Momentos Actuantes (Westergaard / TR34)
        a = math.sqrt(px * py) / (2 * lel)
        
        # 1. Centro (Positivo)
        m_ed_center = (f_ed_total / 4) * (1 - math.pow(a, 0.6))
        
        # 2. Junta Secundaria / Corte (Crítico - factor 1.35)
        m_ed_joint = m_ed_center * 1.35
        
        # 3. Borde Libre (El más alto - factor 1.8)
        m_ed_edge = m_ed_center * 1.95

        # Ratios
        ratio_flex = m_ed_center / m_rd_total
        ratio_joint = m_ed_joint / m_rd_total
        ratio_edge = m_ed_edge / (m_rd_total + m_rd_c)

        # Punzonamiento
        u1 = 2 * (px + py) + 4 * math.pi * h
        v_ed = f_ed / (u1 * h) * 1000
        v_rd = 0.27 * math.sqrt(m_rd_total / h) 
        ratio_punch = v_ed / v_rd if v_rd > 0 else 999

        # Suelo (Límite 5mm)
        p_ed = (0.16 * f_ed_total / (lel**2)) * 1000
        p_rd = 5 * k * 1000
        ratio_soil = p_ed / p_rd

        max_ratio = max(ratio_flex, ratio_joint, ratio_edge, ratio_punch, ratio_soil)
        
        return {
            "h": h, "lel": round(lel, 1), 
            "max_ratio": round(max_ratio, 3),
            "ratio_flex": round(ratio_flex, 2),
            "ratio_joint": round(ratio_joint, 2),
            "ratio_edge": round(ratio_edge, 2),
            "ratio_punch": round(ratio_punch, 2),
            "ratio_soil": round(ratio_soil, 2),
            "m_rd": round(m_rd_total, 2),
            "p_ed": round(p_ed, 1)
        }

    def optimize_thickness(self, cbr, f_prime_c, dosage, fiber_type, load_params):
        k = self.calculate_subgrade_modulus(cbr)
        conc = self.calculate_concrete_properties(f_prime_c)
        fiber_props = self.calculate_fiber_properties(fiber_type, dosage)
        
        current_h = 150
        max_h = 350
        best_design = None
        technical_alert = None
        
        while current_h <= max_h:
            design = self.check_design(current_h, k, conc, fiber_props, load_params)
            
            # Regla de los 250mm
            if current_h >= 250 and design["max_ratio"] > 1.0:
                technical_alert = "ALERTA TÉCNICA: Se recomienda incrementar la dosis de fibra o cambiar a una fibra de mayor rendimiento (ej. Dramix® 5D) antes de seguir aumentando el espesor."
            
            if design["max_ratio"] <= 1.02: # 2% de tolerancia técnica
                best_design = design
                break
            current_h += 10
            
        if not best_design:
            best_design = self.check_design(max_h, k, conc, fiber_props, load_params)
            best_design["falla_total"] = True
            
        best_design.update({
            "k_val": k, "fck": conc["fck"], "ecm": int(conc["ecm"]),
            "dosage": dosage, "fiber_type": fiber_type,
            "technical_alert": technical_alert
        })
        return best_design
