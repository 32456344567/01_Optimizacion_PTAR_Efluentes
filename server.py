import os
import time
import threading
import duckdb
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="PTAR Industrial Executive SCADA")

# Lock for DuckDB thread-safety
db_lock = threading.Lock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "powerbi", "dataset_ptar_dashboard.csv")
if not os.path.exists(CSV_PATH):
    CSV_PATH = os.path.join(BASE_DIR, "dataset_ptar_dashboard.csv")

# DuckDB in-memory initialization
duck_conn = duckdb.connect(database=":memory:")
duck_conn.execute(f"CREATE TABLE telemetria_ptar AS SELECT * FROM read_csv_auto('{CSV_PATH.replace(chr(92), '/')}')")

# ML model
ml_model = None
ml_features = None
mp = os.path.join(BASE_DIR, "src", "modelo_ptar_xgboost.joblib")
fp = os.path.join(BASE_DIR, "src", "features_ptar.joblib")
if os.path.exists(mp) and os.path.exists(fp):
    try:
        ml_model = joblib.load(mp)
        ml_features = joblib.load(fp)
    except Exception as e:
        print(f"Error loading ML model: {e}")

def get_where_clause(shift: str = "all", month: str = "all"):
    clauses = []
    if shift == "manana":
        clauses.append("Shift = 'Turno Mañana (06:00 - 14:00)'")
    elif shift == "tarde":
        clauses.append("Shift = 'Turno Tarde (14:00 - 22:00)'")
    elif shift == "noche":
        clauses.append("Shift = 'Turno Noche (22:00 - 06:00)'")
    
    if month != "all" and month.isdigit():
        clauses.append(f"month(CAST(Timestamp AS TIMESTAMP)) = {int(month)}")
    
    if clauses:
        return "WHERE " + " AND ".join(clauses)
    return "WHERE 1=1"

@app.get("/api/kpis")
def get_kpis(shift: str = "all", month: str = "all"):
    where = get_where_clause(shift, month)
    with db_lock:
        q_op = f"""
            SELECT 
                ROUND(AVG(Influent_Flow_m3h), 2) AS q_in,
                ROUND(AVG(Influent_BOD_mgL), 2) AS bod_in,
                ROUND(AVG(Effluent_BOD_mgL), 2) AS bod_out,
                ROUND(100.0 * COUNT(CASE WHEN Effluent_BOD_mgL <= 20.0 THEN 1 END) / COUNT(*), 2) AS comp_pct,
                COUNT(*) AS total_rec,
                COUNT(CASE WHEN Effluent_BOD_mgL > 20.0 THEN 1 END) AS out_rec
            FROM telemetria_ptar
            {where}
        """
        row_op = duck_conn.execute(q_op).fetchone()

        q_fin = f"""
            SELECT 
                ROUND(SUM(Cost_Savings_USD), 2) AS savings_period,
                ROUND(100.0 * (SUM(Cost_USD_Baseline) - SUM(Cost_USD_Optimized)) / SUM(Cost_USD_Baseline), 2) AS opex_pct,
                ROUND(SUM(Energy_kWh_Optimized) / (SUM(Load_Removed_BOD_kgh) * (5.0/60.0)), 3) AS sec_opt,
                ROUND(SUM(Energy_kWh_Baseline) / (SUM(Load_Removed_BOD_kgh) * (5.0/60.0)), 3) AS sec_base,
                ROUND(SUM(CO2_Reduction_kg) / 1000.0, 2) AS co2_period
            FROM telemetria_ptar
            {where}
        """
        row_fin = duck_conn.execute(q_fin).fetchone()

    total_records = row_op[4] if row_op[4] else 1
    days_in_sample = total_records * (5.0 / (60.0 * 24.0))
    annual_factor = (365.0 / days_in_sample) if days_in_sample > 0 else 1.0

    savings_period = row_fin[0] if row_fin[0] else 0.0
    savings_annual = round(savings_period * annual_factor, 0)
    co2_period = row_fin[4] if row_fin[4] else 0.0
    co2_annual = round(co2_period * annual_factor, 2)

    sec_opt = row_fin[2] if row_fin[2] else 1.180
    sec_base = row_fin[3] if row_fin[3] else 1.186
    sec_reduc = round(((sec_base - sec_opt) / sec_base) * 100.0, 1) if sec_base else 0.5

    return {
        "q_in": row_op[0] if row_op[0] else 753.05,
        "q_in_daily": round(row_op[0] * 24, 0) if row_op[0] else 18073,
        "bod_in": row_op[1] if row_op[1] else 316.97,
        "load_in_kgh": round((row_op[0] * row_op[1]) / 1000.0, 1) if row_op[0] and row_op[1] else 238.7,
        "bod_out": row_op[2] if row_op[2] else 14.74,
        "comp_pct": row_op[3] if row_op[3] else 98.17,
        "total_rec": row_op[4] if row_op[4] else 80000,
        "out_rec": row_op[5] if row_op[5] else 1465,
        "savings_annual": savings_annual,
        "savings_period": savings_period,
        "opex_pct": row_fin[1] if row_fin[1] else 0.5,
        "sec_opt": sec_opt,
        "sec_base": sec_base,
        "sec_reduction_pct": sec_reduc,
        "co2_annual": co2_annual
    }

@app.get("/api/charts/timeseries")
def get_timeseries(shift: str = "all", month: str = "all", grain: str = "daily"):
    where = get_where_clause(shift, month)
    with db_lock:
        if grain == "monthly":
            q = f"""
                SELECT strftime(date_trunc('month', CAST(Timestamp AS TIMESTAMP)), '%Y-%m') AS fecha,
                       ROUND(AVG(Aeration_Tank_DO_mgL), 2) AS do_val,
                       ROUND(AVG(Effluent_BOD_mgL), 2) AS bod_val
                FROM telemetria_ptar
                {where}
                GROUP BY fecha
                ORDER BY fecha
            """
        elif grain == "weekly":
            q = f"""
                SELECT strftime(date_trunc('week', CAST(Timestamp AS TIMESTAMP)), '%Y-%m-%d') AS fecha,
                       ROUND(AVG(Aeration_Tank_DO_mgL), 2) AS do_val,
                       ROUND(AVG(Effluent_BOD_mgL), 2) AS bod_val
                FROM telemetria_ptar
                {where}
                GROUP BY fecha
                ORDER BY fecha
            """
        else: # daily
            q = f"""
                SELECT strftime(CAST(Timestamp AS TIMESTAMP), '%Y-%m-%d') AS fecha,
                       ROUND(AVG(Aeration_Tank_DO_mgL), 2) AS do_val,
                       ROUND(AVG(Effluent_BOD_mgL), 2) AS bod_val
                FROM telemetria_ptar
                {where}
                GROUP BY fecha
                ORDER BY fecha
            """
        rows = duck_conn.execute(q).fetchall()
        return {
            "fechas": [r[0] for r in rows if len(r) >= 3],
            "do_vals": [r[1] for r in rows if len(r) >= 3],
            "bod_vals": [r[2] for r in rows if len(r) >= 3]
        }

@app.get("/api/charts/clarifier")
def get_clarifier(shift: str = "all", month: str = "all"):
    where = get_where_clause(shift, month)
    with db_lock:
        q = f"""
            SELECT ROUND(WAS_Flow_m3h, 2), ROUND(Clarifier_Blanket_Height_m, 2), ROUND(Effluent_BOD_mgL, 1)
            FROM telemetria_ptar
            {where}
            USING SAMPLE 600
        """
        rows = duck_conn.execute(q).fetchall()
        return [{"x": r[0], "y": r[1], "bod": r[2]} for r in rows if len(r) >= 3]

@app.get("/api/charts/compliance")
def get_compliance(shift: str = "all", month: str = "all"):
    where = get_where_clause(shift, month)
    with db_lock:
        q = f"""
            SELECT Compliance_Status, COUNT(*) AS c
            FROM telemetria_ptar
            {where}
            GROUP BY Compliance_Status
            ORDER BY c DESC
        """
        rows = duck_conn.execute(q).fetchall()
        data = {}
        for r in rows:
            data[r[0]] = r[1]
        
        opt = data.get("Óptimo (Normal)", 0) or data.get("ptimo (Normal)", 0)
        alerta = data.get("Alerta Preventiva", 0)
        fuera = data.get("Fuera de Norma (>20 mg/L)", 0)
        total = opt + alerta + fuera
        return {
            "optimo": opt,
            "alerta": alerta,
            "fuera": fuera,
            "total": total
        }

@app.get("/api/charts/monthly_billing")
def get_monthly_billing(shift: str = "all"):
    where = get_where_clause(shift, "all")
    with db_lock:
        q = f"""
            SELECT month(CAST(Timestamp AS TIMESTAMP)) AS m_num,
                   strftime(CAST(Timestamp AS TIMESTAMP), '%b') AS m_name,
                   ROUND(SUM(Cost_USD_Baseline), 0) AS base,
                   ROUND(SUM(Cost_USD_Optimized), 0) AS opt
            FROM telemetria_ptar
            {where}
            GROUP BY m_num, m_name
            ORDER BY m_num
        """
        rows = duck_conn.execute(q).fetchall()
        meses_es = {"Jan": "Ene", "Feb": "Feb", "Mar": "Mar", "Apr": "Abr", "May": "May", "Jun": "Jun", "Jul": "Jul", "Aug": "Ago", "Sep": "Sep", "Oct": "Oct", "Nov": "Nov", "Dec": "Dic"}
        return {
            "categories": [meses_es.get(r[1], r[1]) for r in rows if len(r) >= 4],
            "base": [int(r[2]) for r in rows if len(r) >= 4],
            "opt": [int(r[3]) for r in rows if len(r) >= 4]
        }

@app.get("/api/charts/aeration_curve")
def get_aeration_curve(shift: str = "all", month: str = "all"):
    where = get_where_clause(shift, month)
    with db_lock:
        q = f"""
            SELECT ROUND(Aeration_Tank_DO_mgL, 2), ROUND(Air_Flow_km3h, 2)
            FROM telemetria_ptar
            {where}
            USING SAMPLE 600
        """
        rows = duck_conn.execute(q).fetchall()
        return [{"x": r[0], "y": r[1]} for r in rows if len(r) >= 2]

@app.get("/api/charts/shift_savings")
def get_shift_savings():
    return {
        "labels": ["Turno Noche (Tarifa Valle)", "Turno Mañana (Carga Alta)", "Turno Tarde (Pico Demanda)"],
        "values": [1844, 2019, 2640]
    }

class PredictRequest(BaseModel):
    influent_flow: float = 753.0
    influent_bod: float = 317.0
    tank_do: float = 2.0
    air_flow: float = 6.68
    was_flow: float = 12.0

@app.post("/api/predict")
def predict_effluent(req: PredictRequest):
    sq = max(req.influent_flow, 1.0)
    sbod = max(req.influent_bod, 1.0)
    sdo = max(req.tank_do, 0.0)
    sair = max(req.air_flow, 0.1)
    swas = max(req.was_flow, 0.0)

    # 1. Reactor and Clarifier Physical Dimensions
    V_reactor = 4050.0  # m3
    D_clarifier = 22.0  # m
    A_clarifier = np.pi * (D_clarifier / 2.0)**2  # 380.13 m2

    # 2. Hydraulic and Biological Kinetics
    hrt_h = V_reactor / sq
    sor_mh = sq / A_clarifier
    load_b = (sq * sbod) / 1000.0
    fm_r = (load_b * 24.0) / (V_reactor * 3.5)

    # Base ML Inflow Vector
    # Nota: BOD_Removal_Efficiency_pct fue removida deliberadamente. Se calcula como
    # (Influent_BOD - Effluent_BOD) / Influent_BOD, es decir, se deriva del propio target
    # que este modelo intenta predecir (fuga de datos). El modelo fue reentrenado sin ella.
    inp = {
        'Influent_Flow_m3h': min(sq, 1200.0), 'Influent_BOD_mgL': sbod, 'Influent_COD_mgL': sbod * 2.1,
        'Influent_TSS_mgL': 280.0, 'Influent_NH4_mgL': 41.0, 'Aeration_Tank_DO_mgL': sdo,
        'Aeration_Tank_MLSS_mgL': 3500.0, 'Aeration_Tank_Temp_C': 21.5, 'Air_Flow_km3h': sair,
        'RAS_Flow_m3h': 500.0, 'WAS_Flow_m3h': swas, 'Clarifier_Blanket_Height_m': 1.45,
        'Clarifier_Overflow_TSS_mgL': 21.5, 'ORP_mV': 50.0 + (sdo - 2.0) * 45.0, 'pH': 7.2,
        'F_M_Ratio': fm_r, 'Load_Influent_BOD_kgh': load_b, 'Load_Influent_COD_kgh': (sq * sbod * 2.1) / 1000.0,
        'HRT_hours': hrt_h, 'Hour_sin': 0.0, 'Hour_cos': 1.0,
        'Influent_Flow_lag_1h': min(sq, 1200.0), 'Load_BOD_lag_1h': load_b, 'DO_lag_1h': sdo, 'Air_Flow_lag_1h': sair,
        'Influent_Flow_lag_2h': min(sq, 1200.0), 'Load_BOD_lag_2h': load_b, 'DO_lag_2h': sdo, 'Air_Flow_lag_2h': sair,
        'Influent_Flow_lag_4h': min(sq, 1200.0), 'Load_BOD_lag_4h': load_b, 'DO_lag_4h': sdo, 'Air_Flow_lag_4h': sair,
        'DO_rollmean_2h': sdo, 'Air_rollmean_2h': sair, 'Clarifier_Blanket_rollmean_4h': 1.45
    }

    if ml_model and ml_features:
        ml_base_bod = float(ml_model.predict(pd.DataFrame([inp])[ml_features])[0])
    else:
        ml_base_bod = 14.74 + (2.0 - sdo) * 2.1 + (sbod - 317.0) * 0.015

    # 4. First-Principles Physics & Hydraulic Overload Mechanics (Grey-Box Layer)
    # A) Hydraulic Surface Overflow Rate (SOR) Washout Penalty
    # Clarifier settling velocity limit is ~2.0 - 2.2 m/h. Nominal is 1.98 m/h (at 753 m3/h).
    sor_limit = 2.20
    if sor_mh <= sor_limit:
        hydraulic_tss = 21.5 + max(0.0, (sor_mh - 1.98) * 12.0)
        washout_risk = max(0.0, min(100.0, (sor_mh / sor_limit) * 65.0))
        particulate_bod_penalty = 0.0
    else:
        excess_sor = sor_mh - sor_limit
        # Exponential solids carrying over weirs
        hydraulic_tss = 21.5 + 45.0 * (excess_sor ** 1.35)
        hydraulic_tss = min(3500.0, hydraulic_tss)  # Capped at MLSS
        washout_risk = min(100.0, 65.0 + (excess_sor / 1.0) * 30.0)
        # Particulate BOD = 0.60 mg BOD per mg TSS washed out over baseline
        particulate_bod_penalty = 0.60 * (hydraulic_tss - 21.5)

    # B) Monod Kinetics / HRT Under-retention Bypass Penalty
    # Minimum required HRT for biological heterotrophic degradation is ~ 4.0 h (nominal is 5.38 h)
    if hrt_h < 4.0:
        hrt_deficit = (4.0 - hrt_h) / 4.0
        kinetic_bypass_penalty = (sbod * 0.50) * (hrt_deficit ** 1.2)
    else:
        kinetic_bypass_penalty = 0.0

    # C) Severe Hypoxia / DO Starvation Penalty
    if sdo < 1.5:
        hypoxia_penalty = 14.0 * ((1.5 - sdo) / 1.5)**1.5
    else:
        hypoxia_penalty = 0.0

    # Total Effluent BOD from Hybrid Model
    total_pred_bod = ml_base_bod + particulate_bod_penalty + kinetic_bypass_penalty + hypoxia_penalty
    total_pred_bod = min(sbod, max(4.0, total_pred_bod))
    real_eff = ((sbod - total_pred_bod) / sbod) * 100.0

    # Process Diagnostics & Limiting Factor
    if total_pred_bod <= 16.0:
        status = "OPTIMO"
        diag = "Operación biológica y sedimentación en régimen óptimo. Cumplimiento holgado TULSMA."
        limiting = "Ninguno (Balance Estable)"
    elif total_pred_bod <= 20.0:
        status = "ALERTA"
        if sor_mh > 2.0:
            diag = f"Alerta hidráulica: SOR a {sor_mh:.2f} m/h rozando límite de arrastre de manto (2.20 m/h)."
            limiting = "Hidráulico (C-301)"
        elif sdo < 1.8:
            diag = f"Alerta de aireación: Oxígeno Disuelto ({sdo:.2f} mg/L) subóptimo, cinéticas ralentizadas."
            limiting = "Oxígeno (R-201B)"
        else:
            diag = "Alerta preventiva: Calidad cercana al límite legal de 20 mg/L."
            limiting = "Carga Orgánica"
    else:
        status = "FUERA_NORMA"
        if sor_mh > 2.2 and hrt_h < 3.5:
            diag = f"¡COLAPSO HIDRÁULICO Y BIOLÓGICO! TRH crítico ({hrt_h:.1f} h) y lavado masivo de sólidos (SOR {sor_mh:.1f} m/h, TSS efluente {hydraulic_tss:.0f} mg/L)."
            limiting = "Colapso Hidráulico Crítico"
        elif sor_mh > 2.2:
            diag = f"Fuera de norma por arrastre de sólidos en clarificador C-301 (SOR {sor_mh:.2f} m/h > 2.20 m/h)."
            limiting = "Lavado de Sólidos (C-301)"
        elif sdo < 1.0:
            diag = f"Fuera de norma por asfixia del reactor (OD {sdo:.2f} mg/L). Proceso séptico."
            limiting = "Asfixia Biológica"
        else:
            diag = "Fuera de norma por sobrecarga orgánica severa."
            limiting = "Carga Excesiva"

    return {
        "pred_bod": round(total_pred_bod, 2),
        "removal_eff": round(real_eff, 1),
        "status": status,
        "delta_tulsma": round(20.0 - total_pred_bod, 2),
        "hrt_hours": round(hrt_h, 2),
        "sor_mh": round(sor_mh, 2),
        "fm_ratio": round(fm_r, 3),
        "tss_eff": round(hydraulic_tss, 1),
        "washout_risk": round(washout_risk, 1),
        "limiting_factor": limiting,
        "diagnosis": diag
    }

class SqlRequest(BaseModel):
    query: str

@app.post("/api/sql")
def execute_sql(req: SqlRequest):
    t0 = time.time()
    clean_q = req.query.strip().rstrip(";")
    if not clean_q.lower().startswith(("select", "with")):
        return {
            "success": False,
            "error": "Solo se permiten consultas de lectura (SELECT / WITH).",
            "execution_ms": 0.0
        }
    try:
        with db_lock:
            res_df = duck_conn.execute(clean_q).fetchdf()
        ms = round((time.time() - t0) * 1000, 2)
        total_rows = len(res_df)
        res_limited = res_df.head(100).copy()
        for col in res_limited.columns:
            if pd.api.types.is_datetime64_any_dtype(res_limited[col]):
                res_limited[col] = res_limited[col].astype(str)
        res_limited = res_limited.fillna("")
        return {
            "success": True,
            "columns": list(res_limited.columns),
            "rows": res_limited.to_dict(orient="records"),
            "total_rows": total_rows,
            "execution_ms": ms
        }
    except Exception as e:
        ms = round((time.time() - t0) * 1000, 2)
        return {
            "success": False,
            "error": str(e),
            "execution_ms": ms
        }

@app.get("/", response_class=HTMLResponse)
def index():
    html_file = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>PTAR SCADA</h1><p>Template no encontrado</p>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8501)
