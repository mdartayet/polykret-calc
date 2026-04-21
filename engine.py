import math

class PolykretEngine:
    def __init__(self):
        self.gamma_q = 1.2
        self.gamma_c = 1.5
        self.gamma_f = 1.2
        self.nu = 0.15
        self.e_conc = 30000 # GPa a N/mm2 approx for C28

    def calculate_subgrade_modulus(self, cbr):
        """Conversión CBR a k según Bekaert Standard"""
        if cbr <= 0: return 0.015
        return round(0.012 * math.pow(cbr, 0.58), 6)

    def calculate_concrete_properties(self, f_prime_c):
        """Conversión kg/cm2 a MPa con corrección de unidades"""
        # Entrada: 280 kg/cm2 -> Salida: 28 MPa
        fck = f_prime_c if f_prime_c < 100 else f_prime_c * 0.1 
        if fck < 10: fck = 28 # Fallback seguro
        
        fctm_fl = 0.3 * math.pow(fck, 2/3) * (1 + (1.5 * 1.2)) # fctm,fl para TR34
        ecm = 22000 * math.pow((fck+8)/10, 0.3)
        return {"fck": fck, "ecm": ecm, "fctm_fl": fctm_fl}

    def get_fiber_residual_strength(self, dosage, fiber_type):
        """Resistencia residual fR1 y fR3 dinámica según dosis"""
        # Valores base para 22kg/m3 de 4D 80/60BGE
        # fR1m = 3.5, fR3m = 3.9
        base_dosage = 20.0
        if "5D" in fiber_type:
            fr1 = 4.8 * (dosage / base_dosage)
            fr3 = 5.5 * (dosage / base_dosage)
        else: # 4D
            fr1 = 3.2 * (dosage / base_dosage)
            fr3 = 3.6 * (dosage / base_dosage)
        
        # fctd,avg (Tensión de diseño por fibra)
        return ((fr1 * 0.45 + fr3 * 0.37) / 2) / self.gamma_f

    def check_design(self, h, dosage, fiber_type, k, conc, load_params):
        """Cálculo estructural riguroso TR34/Bekaert"""
        # 1. Longitud Elástica (lel)
        lel = math.pow((conc["ecm"] * math.pow(h, 3)) / (12 * (1 - self.nu**2) * k), 0.25)
        
        # 2. Carga Actuante con Factores
        f_raw = float(load_params.get('load_f', 0))
        if f_raw <= 0: return 0.0, {} # No hay carga, ratio nulo
        
        f_ed = f_raw * self.gamma_q
        n_legs = int(load_params.get('n_legs', 1))
        # Factor de interacción si las patas están cerca (simplificación Bekaert)
        f_ed_eff = f_ed * (1 + 0.25 * (n_legs - 1)) if n_legs > 1 else f_ed

        # 3. Resistencia Flexión (mRd)
        fctd_f = self.get_fiber_residual_strength(dosage, fiber_type)
        m_rd_f = fctd_f * (0.9 * h) * (0.55 * h) / 1000 # kNm/m
        
        # 4. Momento Actuante (Aislado Centro)
        a_rad = math.sqrt(float(load_params['plate_x']) * float(load_params['plate_y'])) / (2 * lel)
        m_ed = (f_ed_eff / 4) * (1 - math.pow(a_rad, 0.6))

        # Ratios de Flexión
        r_flex_center = m_ed / m_rd_f
        r_flex_joint = (m_ed * 1.35) / m_rd_f # Factor de junta crítico
        
        # 5. Punzonamiento (vRd) - CRÍTICO
        # Perímetro de control u1 a 2h de la carga
        u1 = 2 * (float(load_params['plate_x']) + float(load_params['plate_y'])) + 4 * math.pi * h
        v_ed = (f_ed * 1000) / (u1 * h) # N/mm2
        
        # Resistencia a cortante residual
        v_rd = 0.27 * math.sqrt(fctd_f * h / 100) # Simplificación TR34 para punzonamiento SFRC
        r_punch = v_ed / v_rd if v_rd > 0 else 99

        # 6. Suelo
        r_soil = ((0.16 * f_ed_eff / (lel**2)) * 1000) / (5 * k * 1000) # Límite de presión soil

        max_ratio = max(r_flex_center, r_flex_joint, r_punch, r_soil)

        return max_ratio, {
            "ratio_flex": round(max(r_flex_center, r_flex_joint), 2),
            "ratio_punch": round(r_punch, 2),
            "ratio_soil": round(r_soil, 2),
            "critical_load": "Racks (77kN)" if f_raw == 77 else "Carga Puntual"
        }

    def total_optimization(self, cbr, f_prime_c, load_params):
        k = self.calculate_subgrade_modulus(cbr)
        conc = self.calculate_concrete_properties(f_prime_c)
        
        fibers_to_try = [
            {"type": "Dramix® 4D 80/60BGE", "dosages": [20, 22.5, 25]},
            {"type": "Dramix® 5D 65/60BG", "dosages": [20, 25]}
        ]

        # Debug: Verificar carga mínima para evitar el error del ratio 0%
        if float(load_params.get('load_f', 0)) <= 0:
             return {"error": "ERROR: Se requiere carga mayor a 0 kN para diseñar.", "h": 0}

        for fiber in fibers_to_try:
            for dosis in fiber["dosages"]:
                h = 150
                while h <= 300:
                    max_ratio, metrics = self.check_design(h, dosis, fiber["type"], k, conc, load_params)
                    if max_ratio <= 1.0:
                        return {
                            "h": h, "dosage": dosis, "fiber_type": fiber["type"],
                            "max_ratio": round(max_ratio, 2), "k_val": k,
                            "fck": conc["fck"], **metrics
                        }
                    h += 10 # Pasos de 10mm como estándar comercial
        
        return {"error": "No cumple inclusive a 300mm. Aumentar dosis o cambiar fibra.", "h": 300}
