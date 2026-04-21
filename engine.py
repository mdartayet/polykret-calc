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
        # Entrada flexible: soporta 350 (kg) o 35 (MPa)
        fck = f_prime_c if f_prime_c < 100 else f_prime_c * 0.1 
        if fck < 10: fck = 28 # Fallback
        
        # Módulo elasticidad dinámico según fck (EN 1992)
        ecm = 22000 * math.pow((fck + 8) / 10, 0.3)
        # Resistencia a flexotracción
        fctm_fl = 0.3 * math.pow(fck, 2/3) * (1 + (1.5 * 1.2))
        return {"fck": fck, "ecm": ecm, "fctm_fl": fctm_fl}

    def get_fiber_residual_strength(self, dosage, fiber_type):
        base_dosage = 20.0
        if "5D" in fiber_type:
            fr1, fr3 = 4.8 * (dosage/base_dosage), 5.5 * (dosage/base_dosage)
        else:
            fr1, fr3 = 3.2 * (dosage/base_dosage), 3.6 * (dosage/base_dosage)
        return ((fr1 * 0.45 + fr3 * 0.37) / 2) / self.gamma_f

    def check_design(self, h, dosage, fiber_type, k, conc, load_params):
        lel = math.pow((conc["ecm"] * math.pow(h, 3)) / (12 * (1 - self.nu**2) * k), 0.25)
        fctd_f = self.get_fiber_residual_strength(dosage, fiber_type)
        m_rd_f = fctd_f * (0.9 * h) * (0.55 * h) / 1000
        m_rd_c = (conc["fctm_fl"] / self.gamma_c) * (h**2 / 6) / 1000

        max_ratio_overall = 0
        f_metrics = {"ratio_flex": 0, "ratio_punch": 0, "ratio_soil": 0, "critical_load": "Ninguna"}

        def eval_point_load(f_ed, px, py, label):
            a_rad = math.sqrt(px * py) / (2 * lel) if lel > 0 else 1
            m_ed = (f_ed / 4) * (1 - math.pow(a_rad, 0.6))
            r_flex = (m_ed * 1.35) / m_rd_f
            u1 = 2 * (px + py) + 4 * math.pi * h
            v_ed = (f_ed * 1000) / (u1 * h)
            v_rd = 0.27 * math.sqrt(fctd_f * h / 100)
            r_punch = v_ed / v_rd if v_rd > 0 else 99
            r_soil = ((0.16 * f_ed / (lel**2)) * 1000) / (5 * k * 1000)
            return max(r_flex, r_punch, r_soil), r_flex, r_punch, r_soil, label

        # Evaluar Rack
        f_rack = float(load_params.get('load_f', 0))
        if f_rack > 0:
            f_ed_rack = f_rack * self.gamma_q * (1 + 0.25 * (int(load_params.get('n_legs', 1)) - 1))
            res = eval_point_load(f_ed_rack, float(load_params.get('plate_x', 150)), float(load_params.get('plate_y', 150)), "Racks")
            if res[0] > max_ratio_overall: max_ratio_overall, f_metrics["ratio_flex"], f_metrics["ratio_punch"], f_metrics["ratio_soil"], f_metrics["critical_load"] = res

        # Evaluar Montacargas
        f_fl = float(load_params.get('fl_wheel_load', 0))
        if f_fl > 0:
            f_ed_fl = f_fl * self.gamma_q
            area = (f_fl * 1000) / float(load_params.get('fl_pressure', 2.0))
            side = math.sqrt(area)
            res = eval_point_load(f_ed_fl, side, side, "Montacargas")
            if res[0] > max_ratio_overall: max_ratio_overall, f_metrics["ratio_flex"], f_metrics["ratio_punch"], f_metrics["ratio_soil"], f_metrics["critical_load"] = res

        return max_ratio_overall, f_metrics

    def get_construction_details(self, h):
        """Genera especificaciones de juntas y refuerzo adicional"""
        joint_spacing = min(6.0, round((30 * h) / 1000, 1))
        return {
            "joint_max_dist": f"{joint_spacing}m x {joint_spacing}m",
            "edge_reinforcement": "Varilla Ø8mm cada 100mm (Refuerzo superior en bordes libres)",
            "cover": "40 mm",
            "subbase_req": "Compactación al 95% Protos modificado, base granular nivelada ±10mm",
            "joint_type": "Junta de contracción (aserrada a h/3) o de construcción con pasadores"
        }

    def total_optimization(self, cbr, f_prime_c, load_params):
        # VALIDACIÓN MEJORADA: ¿Hay alguna carga?
        has_load = any([float(load_params.get(x, 0)) > 0 for x in ['load_f', 'fl_wheel_load', 'tr_wheel_load']])
        if not has_load:
            return {"error": "Esperando datos de carga (Rack o Vehículo)...", "h": 0}

        k = self.calculate_subgrade_modulus(cbr)
        conc = self.calculate_concrete_properties(f_prime_c)
        
        fibers = [{"t": "Dramix® 4D 80/60BGE", "d": [20, 25, 30, 35]}, {"t": "Dramix® 5D 65/60BG", "d": [20, 25, 30]}]

        for f in fibers:
            for d in f["d"]:
                h = 150
                while h <= 350:
                    ratio, m = self.check_design(h, d, f["t"], k, conc, load_params)
                    if ratio <= 1.0:
                        details = self.get_construction_details(h)
                        return {"h": h, "dosage": d, "fiber_type": f["t"], "max_ratio": round(ratio, 2), 
                                "k_val": k, "fck": conc["fck"], **m, **details}
                    h += 10
        
        return {"error": "Diseño extremo: requiere revisión manual o mayor espesor.", "h": 400}
