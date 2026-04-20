import math

class PolykretEngine:
    def __init__(self):
        # Factores de Seguridad (pág 11 de SoG Promart)
        self.gamma_q = 1.2    # Cargas
        self.gamma_c = 1.5    # Concreto
        self.gamma_f = 1.2    # Fibra
        self.gamma_s = 1.15   # Acero (refuerzo)
        self.alpha_cc = 0.85  # Coef. largo plazo concreto

    def calculate_subgrade_modulus(self, cbr):
        """Calcula k (N/mm3) basado en CBR usando el gráfico de Mark Stet (pág 14)"""
        # Ajuste logarítmico aproximado al gráfico de Bekaert
        # CBR 2% -> ~0.015 N/mm3
        # CBR 30% -> ~0.0898 N/mm3
        if cbr <= 0: return 0.01
        k_nmm3 = 0.012 * math.pow(cbr, 0.58)
        return round(k_nmm3, 6)

    def calculate_concrete_properties(self, f_prime_c):
        """Propiedades según Eurocode 2 (pág 10)"""
        fck = f_prime_c * 0.8  # Aprox kg/cm2 a MPa cilindro
        fcm = fck + 8
        ecm = 22000 * math.pow(fcm/10, 0.3) # MPa
        fctm_fl = 0.3 * math.pow(fck, 2/3) * (1 + (1.5 * 1.2)) # Simplificado
        return {
            "fck": fck,
            "fctm_fl": round(fctm_fl, 2),
            "ecm": round(ecm, 2),
            "fcd": round(self.alpha_cc * fck / self.gamma_c, 2)
        }

    def calculate_fiber_properties(self, fiber_type, dosage):
        """Propiedades de flexión post-fisura (pág 10/20)"""
        # Para 4D 80/60BGE a 22kg/m3 (valores de SoG Promart)
        # Escalamiento lineal por dosificación
        ref_dosage = 22.0
        ratio = dosage / ref_dosage
        
        fr1m = 3.50 * ratio
        fr3m = 3.94 * ratio
        
        # Resistencia a tensión residual (fctd,s / fctd,u)
        fctd_s = (0.45 * fr1m) / self.gamma_f
        fctd_u = (0.37 * fr3m) / self.gamma_f
        
        return {"fctd_s": fctd_s, "fctd_u": fctd_u}

    def calculate_elastic_length(self, h, ecm, k):
        """Fórmula pág 15"""
        nu = 0.15
        numerator = ecm * math.pow(h, 3)
        denominator = 12 * (1 - nu**2) * k
        return round(math.pow(numerator / denominator, 0.25), 0)

    def calculate_moment_resistance(self, h, conc, fiber_props, as_area=0):
        """Cálculo pág 20-21 (concreto + fibras + refuerzo)"""
        # mRd concreto simple (fisuración)
        m_rd_c = (conc["fctm_fl"] / self.gamma_c) * (h**2 / 6) / 1000 # kNm/m
        
        # mRd fibras (ULS) - simplificado de la pág 20
        # Basado en el eje neutro x (~0.1h según doc)
        x = 0.1 * h
        fctd_avg = (fiber_props["fctd_s"] + fiber_props["fctd_u"]) / 2
        m_rd_f = fctd_avg * (h - x) * (h/2 + x/2) / 1000
        
        # Refuerzo superior (si existe)
        m_rd_as = 0
        if as_area > 0:
            d = h - 40 # recubrimiento
            m_rd_as = (as_area * (500/self.gamma_s) * (d - 0.5*x)) / 1e6

        return {
            "m_rd_c": round(m_rd_c, 2),
            "m_rd_f": round(m_rd_f, 2),
            "m_rd_total": round(m_rd_f + m_rd_as, 2)
        }

    def verify_loads(self, f_kN, plate_x, plate_y, h, lel, m_rd_c, m_rd_total, k):
        """Verificación pág 23-24"""
        f_ed = f_kN * self.gamma_q
        a = math.sqrt(plate_x * plate_y) / (2 * lel) # radio relativo
        
        # Momentos Actuantes (Westergaard / TR34)
        m_ed_center = (f_ed / 4) * (1 - math.pow(a, 0.6)) # Simplificado
        m_ed_joint = m_ed_center * 1.2
        m_ed_edge = m_ed_center * 1.8
        
        # Utilizaciones (%)
        util_center = (m_ed_center / m_rd_total) * 100 if m_rd_total > 0 else 999
        util_joint = (m_ed_joint / m_rd_total) * 100
        util_edge = (m_ed_edge / (m_rd_total + m_rd_c)) * 100 # Borde usa mRd total
        
        # Presión suelo (pág 24)
        p_ed = (0.15 * f_ed / (lel**2)) * 1000 # kN/m2
        p_rd = 5 * k * 1000 # 5mm asiento admisible x K
        util_soil = (p_ed / p_rd) * 100
        
        # Punzonamiento (Punching) - Eurocode 2 simplificado
        u1 = 2 * (plate_x + plate_y) + 4 * math.pi * h
        v_ed = f_ed / (u1 * h) * 1000 # MPa
        v_rd = 0.25 * math.sqrt(m_rd_total / h) # Estimación TR34
        util_punch = (v_ed / v_rd) * 100 if v_rd > 0 else 0

        return {
            "m_ed_center": round(m_ed_center, 2),
            "m_ed_joint": round(m_ed_joint, 2),
            "m_ed_edge": round(m_ed_edge, 2),
            "utilization": round(util_center, 1),
            "utilization_joint": round(util_joint, 1),
            "utilization_edge": round(util_edge, 1),
            "p_ed_soil": round(p_ed, 1),
            "p_rd_soil": round(p_rd, 1),
            "utilization_soil": round(util_soil, 1),
            "utilization_punch": round(util_punch, 1)
        }
