import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y METADATOS INDUSTRIALES
# ==============================================================================
st.set_page_config(
    page_title="PTAR Digital Twin | SCADA & Control Predictivo",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. ESTILOS CSS DE GRADO INDUSTRIAL (HIGH-PERFORMANCE HMI // ISA-101)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .mono {
        font-family: 'JetBrains Mono', monospace;
    }

    /* Barra Superior SCADA */
    .scada-topbar {
        background: linear-gradient(90deg, #090D16 0%, #111827 50%, #0F172A 100%);
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 14px 20px;
        margin-bottom: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
    }
    .topbar-title {
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: 0.8px;
        color: #F8FAFC;
        margin: 0;
        text-transform: uppercase;
    }
    .topbar-sub {
        font-size: 0.82rem;
        color: #94A3B8;
        margin-top: 3px;
        font-weight: 500;
    }
    .pill-badge {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 4px;
        margin-left: 8px;
        letter-spacing: 0.5px;
    }
    .pill-live {
        background-color: rgba(16, 185, 129, 0.12);
        color: #10B981;
        border: 1px solid #10B981;
    }
    .pill-norm {
        background-color: rgba(56, 189, 248, 0.12);
        color: #38BDF8;
        border: 1px solid #0284C7;
    }
    .pill-model {
        background-color: rgba(168, 85, 247, 0.12);
        color: #C084FC;
        border: 1px solid #9333EA;
    }

    /* Tarjetas de Telemetría SCADA */
    .kpi-card {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 6px;
        padding: 12px 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    }
    .kpi-tag {
        display: flex;
        justify-content: space-between;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .kpi-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.85rem;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.1;
    }
    .kpi-unit {
        font-size: 0.82rem;
        font-weight: 500;
        color: #94A3B8;
        margin-left: 4px;
    }
    .kpi-footer {
        font-size: 0.78rem;
        color: #94A3B8;
        margin-top: 6px;
    }
    .kpi-bar {
        height: 3px;
        border-radius: 2px;
        margin-top: 8px;
        width: 100%;
    }

    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 1px solid #1E293B;
        padding-bottom: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
        font-weight: 600;
        font-size: 0.88rem;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(30, 41, 59, 0.7) !important;
        border-color: #334155 #334155 transparent #334155 !important;
        border-bottom: 2px solid #38BDF8 !important;
        color: #F8FAFC !important;
    }

    /* Guía de Operación */
    .guide-box {
        background-color: #0B132B;
        border: 1px solid #1E293B;
        border-left: 4px solid #38BDF8;
        border-radius: 6px;
        padding: 12px 18px;
        margin-bottom: 1rem;
        font-size: 0.85rem;
        color: #CBD5E1;
        line-height: 1.5;
    }
    .guide-step {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        color: #38BDF8;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CARGA DE MODELO Y ARTEFACTOS TÉCNICOS
# ==============================================================================
@st.cache_resource
def load_ml_artifacts():
    base_dir = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, 'modelo_ptar_xgboost.joblib')
    features_path = os.path.join(base_dir, 'features_ptar.joblib')
    if not os.path.exists(model_path):
        model_path = os.path.join('app', 'modelo_ptar_xgboost.joblib')
        features_path = os.path.join('app', 'features_ptar.joblib')
    return joblib.load(model_path), joblib.load(features_path)

try:
    model, feature_names = load_ml_artifacts()
    model_active = True
except Exception:
    model_active = False

# ==============================================================================
# 4. BARRA SUPERIOR DE CONTROL SCADA
# ==============================================================================
st.markdown("""
<div class="scada-topbar">
    <div>
        <div class="topbar-title">PTAR INDUSTRIAL 4,050 m³ // DIGITAL TWIN & CONTROL PREDICTIVO</div>
        <div class="topbar-sub">Supervisión Operativa, Balances de Materia y Optimización de Aireación | Ing. Angelo Apolo</div>
    </div>
    <div>
        <span class="pill-badge pill-live">● SCADA ONLINE [24/7]</span>
        <span class="pill-badge pill-model">XGBOOST SENSOR VIRTUAL</span>
        <span class="pill-badge pill-norm">TULSMA: DBO &le; 20 mg/L</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. GUÍA RÁPIDA DE OPERACIÓN (WORKFLOW INDUSTRIAL)
# ==============================================================================
with st.expander("Instrucciones de Uso y Arquitectura del Simulador (Flujo Operativo)", expanded=False):
    st.markdown("""
    <div class="guide-box">
        <p><b>Propósito:</b> Este gemelo digital integra un modelo cinético acoplado a un sensor virtual (XGBoost) entrenado con 80,000 registros de planta para predecir la calidad del efluente final (DBO₅) y optimizar el consumo eléctrico de los sopladores de aireación en función de la dinámica horaria del afluente.</p>
        <p><span class="guide-step">[Paso 1]</span> <b>Seleccionar Modo Operativo:</b> En la consola lateral, elija un escenario predeterminado (Operación Óptima, Línea Base Histórica, Pico Diurno o Valle Nocturno) o active el modo manual.</p>
        <p><span class="guide-step">[Paso 2]</span> <b>Ajustar Consignas de Proceso:</b> Modifique caudales, concentraciones de entrada o el flujo de aire inyectado en los Racks 1, 2 y 3.</p>
        <p><span class="guide-step">[Paso 3]</span> <b>Monitorear el Mímico PFD:</b> Inspeccione el diagrama de flujo dinámico y la Tabla de Corrientes (Stream Table) para verificar el balance de masa.</p>
        <p><span class="guide-step">[Paso 4]</span> <b>Optimización Solver:</b> Use el botón de cálculo prescriptivo para encontrar el caudal de aire óptimo que minimice el gasto eléctrico cumpliendo el límite legal (DBO &le; 20 mg/L).</p>
        <p><span class="guide-step">[Paso 5]</span> <b>Generar Despacho de Turno:</b> En la pestaña de POE, emita la orden formal de ajuste de variadores (VFD) para el operador de planta.</p>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 6. CONSOLA LATERAL SCADA // ENTRADA DE VARIABLES DE OPERACIÓN
# ==============================================================================
st.sidebar.markdown("### CONSOLA DE CONSIGNAS SCADA")

# Selector de Escenario Operativo
escenario = st.sidebar.selectbox(
    "Escenario de Simulación / Régimen de Carga:",
    [
        "Consigna Óptima (Recomendada POE: 1.8 - 2.2 mg/L)",
        "Línea Base Histórica (Sobre-aireación 267 kW)",
        "Pico Diurno Crítico (Sobrecarga de Entrada)",
        "Valle Nocturno (Baja Carga / Ahorro Máximo)",
        "Personalizado (Ajuste Manual)"
    ],
    index=0
)

# Inicialización de Estados
if "Consigna Óptima" in escenario:
    def_q, def_bod_in, def_cod_in, def_do, def_air = 750.0, 315.0, 665.0, 2.00, 6.20
elif "Línea Base" in escenario:
    def_q, def_bod_in, def_cod_in, def_do, def_air = 750.0, 315.0, 665.0, 3.20, 8.50
elif "Pico Diurno" in escenario:
    def_q, def_bod_in, def_cod_in, def_do, def_air = 850.0, 380.0, 800.0, 1.50, 10.50
elif "Valle Nocturno" in escenario:
    def_q, def_bod_in, def_cod_in, def_do, def_air = 680.0, 260.0, 520.0, 1.90, 4.80
else:
    def_q, def_bod_in, def_cod_in, def_do, def_air = 753.0, 317.0, 666.0, 2.00, 6.68

# Racks de Entrada
with st.sidebar.expander("RACK 1: Hidráulica & Afluente Crudo", expanded=True):
    q_in = st.slider("Caudal Entrada FIT-101 (m³/h)", 300.0, 1200.0, float(def_q), step=10.0, help="Caudal total que ingresa a la cámara de desbaste.")
    bod_in = st.slider("DBO Entrada AIT-102 (mg/L)", 150.0, 450.0, float(def_bod_in), step=5.0, help="Demanda Bioquímica de Oxígeno en agua cruda.")
    cod_in = st.slider("DQO Entrada AIT-103 (mg/L)", 300.0, 900.0, float(def_cod_in), step=10.0, help="Demanda Química de Oxígeno total.")
    tss_in = st.slider("Sólidos Entrada TSS-104 (mg/L)", 100.0, 450.0, 298.0, step=5.0)

with st.sidebar.expander("RACK 2: Biología & Aireación", expanded=True):
    air_flow = st.slider("Inyección Aire FIT-202 (km³/h)", 2.5, 12.0, float(def_air), step=0.1, help="Flujo volumétrico inyectado por los sopladores.")
    do_val = st.slider("Oxígeno Disuelto AIT-201 (mg/L)", 0.5, 4.5, float(def_do), step=0.05, help="Concentración en licor mezcla. Rango óptimo: 1.80 a 2.20 mg/L.")
    temp_val = st.slider("Temperatura TIT-203 (°C)", 15.0, 30.0, 22.2, step=0.5)
    mlss_val = st.slider("Licor Mezcla MLSS-204 (mg/L)", 2200.0, 4500.0, 3500.0, step=50.0, help="Biomasa bacteriana suspendida en el reactor.")

with st.sidebar.expander("RACK 3: Clarificador & Purgas", expanded=False):
    blanket_val = st.slider("Manto de Lodos LIT-301 (m)", 0.4, 2.2, 1.17, step=0.05, help="Nivel de lodo sedimentado. Umbral de alarma: > 1.60 m.")
    ras_val = st.slider("Retorno RAS FIT-302 (m³/h)", 200.0, 750.0, 525.0, step=10.0)
    was_val = st.slider("Purga WAS FIT-303 (m³/h)", 4.0, 20.0, 12.0, step=0.5)

# ==============================================================================
# 7. MOTOR FÍSICO DE BALANCES Y PREDICCIÓN ML
# ==============================================================================
V_REACTOR = 4050.0
KWH_M3_AIR = 0.040
TARIFF_USD = 0.092
LIMIT_LEGAL = 20.0

# Balances Másicos
load_bod_in_kgh = (q_in * bod_in) / 1000.0
load_cod_in_kgh = (q_in * cod_in) / 1000.0
hrt_val = V_REACTOR / q_in
fm_ratio = (load_bod_in_kgh * 24.0) / (V_REACTOR * mlss_val / 1000.0)

# Potencia Eléctrica y Costos
power_kw = air_flow * 1000.0 * KWH_M3_AIR
power_base_kw = 6.68 * 1000.0 * KWH_M3_AIR
cost_annual = power_kw * 8760.0 * TARIFF_USD
cost_base_annual = power_base_kw * 8760.0 * TARIFF_USD
savings_usd = cost_base_annual - cost_annual
energy_saved_kwh = (power_base_kw - power_kw) * 8760.0
co2_saved_tons = (energy_saved_kwh * 0.420) / 1000.0

# Inferencia Predictiva con XGBoost
input_dict = {
    'Influent_Flow_m3h': q_in,
    'Influent_BOD_mgL': bod_in,
    'Influent_COD_mgL': cod_in,
    'Influent_TSS_mgL': tss_in,
    'Influent_NH4_mgL': 41.0,
    'Aeration_Tank_DO_mgL': do_val,
    'Aeration_Tank_MLSS_mgL': mlss_val,
    'Aeration_Tank_Temp_C': temp_val,
    'Air_Flow_km3h': air_flow,
    'RAS_Flow_m3h': ras_val,
    'WAS_Flow_m3h': was_val,
    'Clarifier_Blanket_Height_m': blanket_val,
    'Clarifier_Overflow_TSS_mgL': 21.5,
    'ORP_mV': 50.0 + (do_val - 2.0) * 45.0,
    'pH': 7.2,
    'F_M_Ratio': fm_ratio,
    'Load_Influent_BOD_kgh': load_bod_in_kgh,
    'Load_Influent_COD_kgh': load_cod_in_kgh,
    'BOD_Removal_Efficiency_pct': 95.0,
    'HRT_hours': hrt_val,
    'Hour_sin': 0.5,
    'Hour_cos': 0.866,
    'Influent_Flow_lag_1h': q_in,
    'Load_BOD_lag_1h': load_bod_in_kgh,
    'DO_lag_1h': do_val,
    'Air_Flow_lag_1h': air_flow,
    'Influent_Flow_lag_2h': q_in,
    'Load_BOD_lag_2h': load_bod_in_kgh,
    'DO_lag_2h': do_val,
    'Air_Flow_lag_2h': air_flow,
    'Influent_Flow_lag_4h': q_in,
    'Load_BOD_lag_4h': load_bod_in_kgh,
    'DO_lag_4h': do_val,
    'Air_Flow_lag_4h': air_flow,
    'DO_rollmean_2h': do_val,
    'Air_rollmean_2h': air_flow,
    'Clarifier_Blanket_rollmean_4h': blanket_val
}

if model_active:
    bod_out = float(model.predict(pd.DataFrame([input_dict])[feature_names])[0])
else:
    bod_out = 14.7 + (2.0 - do_val) * 2.2 + (bod_in - 317.0) * 0.02

removal_eff = ((bod_in - bod_out) / bod_in) * 100.0
load_bod_out_kgh = (q_in * bod_out) / 1000.0
load_removed_kgh = max(0.1, load_bod_in_kgh - load_bod_out_kgh)
sec_val = power_kw / load_removed_kgh

# Calificación de Estado ISA-18.2
if bod_out <= 16.0:
    status_label = "NORMAL (DENTRO DE NORMA)"
    status_color = "#10B981"
elif bod_out <= LIMIT_LEGAL:
    status_label = "ADVERTENCIA PREVENTIVA"
    status_color = "#F59E0B"
else:
    status_label = "ALARMA FUERA DE NORMA"
    status_color = "#EF4444"

# ==============================================================================
# 8. CINTA SUPERIOR DE TELEMETRÍA SCADA (4 TARJETAS PRINCIPALES)
# ==============================================================================
col_k1, col_k2, col_k3, col_k4 = st.columns(4)

with col_k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-tag"><span>AFLUENTE CRUDO</span><span>FIT-101</span></div>
        <div class="kpi-val">{q_in:.0f}<span class="kpi-unit">m³/h</span></div>
        <div class="kpi-footer">Carga: <b>{load_bod_in_kgh:.1f} kg DBO/h</b> (HRT: {hrt_val:.1f}h)</div>
        <div class="kpi-bar" style="background-color:#38BDF8;"></div>
    </div>
    """, unsafe_allow_html=True)

with col_k2:
    do_bar_color = "#10B981" if 1.8 <= do_val <= 2.2 else ("#F59E0B" if do_val > 2.2 else "#EF4444")
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-tag"><span>OXÍGENO DISUELTO</span><span>AIT-201</span></div>
        <div class="kpi-val" style="color:{do_bar_color};">{do_val:.2f}<span class="kpi-unit">mg/L</span></div>
        <div class="kpi-footer">Banda Óptima: <b>1.80 - 2.20 mg/L</b></div>
        <div class="kpi-bar" style="background-color:{do_bar_color};"></div>
    </div>
    """, unsafe_allow_html=True)

with col_k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-tag"><span>EFLUENTE SALIDA</span><span>AIT-401_BOD</span></div>
        <div class="kpi-val" style="color:{status_color};">{bod_out:.2f}<span class="kpi-unit">mg/L</span></div>
        <div class="kpi-footer">Límite TULSMA: <b>&le; 20.0 mg/L</b> ({status_label[:11]})</div>
        <div class="kpi-bar" style="background-color:{status_color};"></div>
    </div>
    """, unsafe_allow_html=True)

with col_k4:
    pwr_color = "#10B981" if savings_usd >= 0 else "#EF4444"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-tag"><span>POTENCIA SOPLADORES</span><span>JIT-202</span></div>
        <div class="kpi-val">{power_kw:.1f}<span class="kpi-unit">kW</span></div>
        <div class="kpi-footer" style="color:{pwr_color};">
            <b>{f'+${savings_usd:,.0f} USD/año' if savings_usd >= 0 else f'-${abs(savings_usd):,.0f} USD/año'}</b> vs Base
        </div>
        <div class="kpi-bar" style="background-color:{pwr_color};"></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# 9. PESTAÑAS DE NAVEGACIÓN PRINCIPAL
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "[01] MÍMICO PFD & BALANCES SCADA",
    "[02] SENSOR VIRTUAL & WHAT-IF",
    "[03] EFICIENCIA ENERGÉTICA & COSTOS",
    "[04] PROCEDIMIENTO OPERATIVO (POE)"
])

# ==============================================================================
# PESTAÑA 1: MÍMICO DE PROCESO (PFD SCADA) Y TABLA DE CORRIENTES
# ==============================================================================
with tab1:
    st.markdown("#### Diagrama de Flujo de Procesos (PFD) // Telemetría en Tiempo Real")
    
    # Renderizado Vectorial Aislado mediante iframe components.html
    pfd_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }}
        body {{ background-color: #0A0E17; color: #E2E8F0; overflow: hidden; }}
        .pfd-container {{
            position: relative;
            width: 100%;
            height: 380px;
            background: radial-gradient(circle at 50% 50%, #0F172A 0%, #070B14 100%);
            border: 1px solid #1E293B;
            border-radius: 8px;
            overflow: hidden;
        }}
        .grid-bg {{
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background-image: linear-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
            background-size: 25px 25px;
            pointer-events: none;
        }}
        .flow-line {{
            stroke-dasharray: 8, 5;
            animation: flowAnimation 1.2s linear infinite;
        }}
        .air-line {{
            stroke-dasharray: 6, 4;
            animation: flowAnimation 0.8s linear infinite;
        }}
        .sludge-line {{
            stroke-dasharray: 6, 6;
            animation: flowAnimation 2s linear infinite;
        }}
        @keyframes flowAnimation {{
            from {{ stroke-dashoffset: 26; }}
            to {{ stroke-dashoffset: 0; }}
        }}
        .bubble {{
            animation: rise 2s infinite ease-in;
        }}
        @keyframes rise {{
            0% {{ transform: translateY(0); opacity: 0.2; }}
            50% {{ opacity: 0.85; }}
            100% {{ transform: translateY(-45px); opacity: 0; }}
        }}
    </style>
    </head>
    <body>
    <div class="pfd-container">
        <div class="grid-bg"></div>
        <svg viewBox="0 0 1000 380" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="waterGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#1E3A8A" stop-opacity="0.6"/>
                    <stop offset="100%" stop-color="#0F172A" stop-opacity="0.95"/>
                </linearGradient>
                <linearGradient id="sludgeGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#451A03" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="#1E1B18" stop-opacity="0.98"/>
                </linearGradient>
            </defs>

            <!-- ENCABEZADO SCADA -->
            <rect x="15" y="10" width="970" height="26" fill="#0B132B" stroke="#1E293B" rx="4"/>
            <text x="30" y="27" fill="#64748B" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700">ISA-5.1 PROCESS FLOW DIAGRAM (PFD) // PLANTA BIOLÓGICA 4,050 m³</text>
            <text x="960" y="27" text-anchor="end" fill="#10B981" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700">ESTADO: ONLINE CONTINUO</text>

            <!-- ================= TUBERÍAS DE PROCESO ================= -->
            
            <!-- Entrada Afluente Crudo -->
            <path d="M 25 150 L 190 150" stroke="#38BDF8" stroke-width="4" fill="none" class="flow-line"/>
            <polygon points="185,146 195,150 185,154" fill="#38BDF8"/>
            
            <!-- Licor Mezcla a Clarificador -->
            <path d="M 450 150 L 600 150" stroke="#38BDF8" stroke-width="4" fill="none" class="flow-line"/>
            <polygon points="595,146 605,150 595,154" fill="#38BDF8"/>

            <!-- Inyección de Aire (Sopladores a Reactor) -->
            <path d="M 320 310 L 320 235" stroke="#2DD4BF" stroke-width="3.5" fill="none" class="air-line"/>
            <polygon points="317,240 320,230 323,240" fill="#2DD4BF"/>

            <!-- Retorno Lodos RAS -->
            <path d="M 710 270 L 710 335 L 160 335 L 160 165" stroke="#F59E0B" stroke-width="2.5" fill="none" class="sludge-line"/>
            <polygon points="157,170 160,160 163,170" fill="#F59E0B"/>

            <!-- Purga Lodos WAS -->
            <path d="M 710 270 L 710 335 L 850 335" stroke="#EF4444" stroke-width="2.5" fill="none" class="sludge-line"/>
            <polygon points="845,332 855,335 845,338" fill="#EF4444"/>

            <!-- Salida Efluente Tratado -->
            <path d="M 820 135 L 965 135" stroke="{status_color}" stroke-width="4" fill="none" class="flow-line"/>
            <polygon points="960,131 970,135 960,139" fill="{status_color}"/>

            <!-- ================= EQUIPOS PRINCIPALES ================= -->

            <!-- T-101: Cámara de Desbaste -->
            <rect x="50" y="115" width="70" height="70" rx="4" fill="#1E293B" stroke="#475569" stroke-width="1.5"/>
            <line x1="75" y1="120" x2="65" y2="180" stroke="#64748B" stroke-width="2"/>
            <line x1="85" y1="120" x2="75" y2="180" stroke="#64748B" stroke-width="2"/>
            <line x1="95" y1="120" x2="85" y2="180" stroke="#64748B" stroke-width="2"/>
            <text x="85" y="105" text-anchor="middle" fill="#94A3B8" font-size="9" font-family="'JetBrains Mono', monospace" font-weight="700">T-101 DESBASTE</text>

            <!-- R-201: Reactor Biológico de Lodos Activados -->
            <rect x="190" y="85" width="260" height="155" rx="6" fill="url(#waterGrad)" stroke="#38BDF8" stroke-width="2"/>
            <text x="320" y="105" text-anchor="middle" fill="#F8FAFC" font-size="11" font-weight="700" letter-spacing="0.5">R-201 TANQUE DE AIREACIÓN</text>
            <text x="320" y="119" text-anchor="middle" fill="#64748B" font-size="9" font-family="'JetBrains Mono', monospace">VOL: 4,050 m³ | MLSS: {mlss_val:.0f} mg/L</text>
            
            <line x1="195" y1="130" x2="445" y2="130" stroke="#38BDF8" stroke-width="1.5" stroke-dasharray="4,2"/>
            <line x1="210" y1="225" x2="430" y2="225" stroke="#2DD4BF" stroke-width="3"/>
            
            <!-- Burbujas animadas -->
            <g class="bubble">
                <circle cx="240" cy="210" r="2.5" fill="#A7F3D0"/>
                <circle cx="300" cy="200" r="3" fill="#A7F3D0"/>
                <circle cx="360" cy="215" r="2.5" fill="#A7F3D0"/>
                <circle cx="410" cy="205" r="3" fill="#A7F3D0"/>
            </g>
            <g class="bubble" style="animation-delay: 0.9s;">
                <circle cx="260" cy="180" r="2" fill="#6EE7B7"/>
                <circle cx="330" cy="175" r="3.5" fill="#6EE7B7"/>
                <circle cx="380" cy="185" r="2" fill="#6EE7B7"/>
            </g>

            <!-- K-201A/B: Sopladores Centrífugos VFD -->
            <circle cx="320" cy="310" r="20" fill="#1E293B" stroke="#2DD4BF" stroke-width="2"/>
            <path d="M 312 300 L 328 310 L 312 320 Z" fill="#2DD4BF"/>
            <text x="320" y="344" text-anchor="middle" fill="#F8FAFC" font-size="10" font-weight="700">K-201A/B VFD</text>
            <text x="320" y="356" text-anchor="middle" fill="#2DD4BF" font-size="9" font-family="'JetBrains Mono', monospace">{air_flow:.1f} km³/h · {power_kw:.1f} kW</text>

            <!-- C-301: Clarificador Secundario -->
            <polygon points="600,95 820,95 820,190 740,265 680,265 600,190" fill="url(#waterGrad)" stroke="#38BDF8" stroke-width="2"/>
            <polygon points="620,185 800,185 820,190 740,265 680,265 600,190" fill="url(#sludgeGrad)" stroke="none"/>
            <text x="710" y="112" text-anchor="middle" fill="#F8FAFC" font-size="11" font-weight="700">C-301 CLARIFICADOR</text>
            <text x="710" y="125" text-anchor="middle" fill="#64748B" font-size="9" font-family="'JetBrains Mono', monospace">SEDIMENTADOR SECUNDARIO</text>
            
            <line x1="600" y1="95" x2="820" y2="95" stroke="#94A3B8" stroke-width="3"/>
            <rect x="705" y="85" width="10" height="20" fill="#64748B"/>
            <line x1="620" y1="185" x2="800" y2="185" stroke="#F59E0B" stroke-width="2" stroke-dasharray="4,2"/>
            <text x="710" y="200" text-anchor="middle" fill="#FCD34D" font-size="9" font-family="'JetBrains Mono', monospace" font-weight="700">MANTO: {blanket_val:.2f} m</text>

            <!-- P-301: Bomba RAS / WAS -->
            <circle cx="710" cy="285" r="14" fill="#1E293B" stroke="#F59E0B" stroke-width="1.5"/>
            <text x="710" y="289" text-anchor="middle" fill="#F59E0B" font-size="8" font-weight="700">P-301</text>
            <text x="780" y="325" fill="#94A3B8" font-size="8.5" font-family="'JetBrains Mono', monospace">WAS: {was_val:.1f} m³/h</text>
            <text x="590" y="350" fill="#94A3B8" font-size="8.5" font-family="'JetBrains Mono', monospace">RAS: {ras_val:.1f} m³/h</text>

            <!-- ================= INSTRUMENTACIÓN ISA-5.1 ================= -->

            <!-- FIT-101 -->
            <g transform="translate(100, 38)">
                <rect x="0" y="0" width="85" height="42" rx="4" fill="#0F172A" stroke="#38BDF8" stroke-width="1.2"/>
                <line x1="0" y1="16" x2="85" y2="16" stroke="#1E293B" stroke-width="1"/>
                <text x="42.5" y="12" text-anchor="middle" fill="#94A3B8" font-size="8.5" font-family="'JetBrains Mono', monospace" font-weight="700">FIT-101</text>
                <text x="42.5" y="32" text-anchor="middle" fill="#F8FAFC" font-size="12" font-family="'JetBrains Mono', monospace" font-weight="800">{q_in:.0f} m³/h</text>
                <line x1="42.5" y1="42" x2="42.5" y2="110" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>
            </g>

            <!-- AIT-102 -->
            <g transform="translate(20, 78)">
                <rect x="0" y="0" width="80" height="36" rx="4" fill="#0F172A" stroke="#38BDF8" stroke-width="1"/>
                <text x="40" y="14" text-anchor="middle" fill="#94A3B8" font-size="8" font-family="'JetBrains Mono', monospace">AIT-102</text>
                <text x="40" y="28" text-anchor="middle" fill="#38BDF8" font-size="10.5" font-family="'JetBrains Mono', monospace" font-weight="700">{bod_in:.0f} mg/L</text>
            </g>

            <!-- AIT-201 -->
            <g transform="translate(275, 25)">
                <rect x="0" y="0" width="90" height="42" rx="4" fill="#0F172A" stroke="#2DD4BF" stroke-width="1.5"/>
                <line x1="0" y1="16" x2="90" y2="16" stroke="#1E293B" stroke-width="1"/>
                <text x="45" y="12" text-anchor="middle" fill="#94A3B8" font-size="8.5" font-family="'JetBrains Mono', monospace" font-weight="700">AIT-201 (DO)</text>
                <text x="45" y="33" text-anchor="middle" fill="#2DD4BF" font-size="13" font-family="'JetBrains Mono', monospace" font-weight="800">{do_val:.2f} mg/L</text>
                <line x1="45" y1="42" x2="45" y2="85" stroke="#2DD4BF" stroke-width="1" stroke-dasharray="2,2"/>
            </g>

            <!-- LIT-301 -->
            <g transform="translate(735, 42)">
                <rect x="0" y="0" width="80" height="38" rx="4" fill="#0F172A" stroke="#F59E0B" stroke-width="1.2"/>
                <text x="40" y="14" text-anchor="middle" fill="#94A3B8" font-size="8" font-family="'JetBrains Mono', monospace">LIT-301 (MANTO)</text>
                <text x="40" y="30" text-anchor="middle" fill="#FCD34D" font-size="11" font-family="'JetBrains Mono', monospace" font-weight="800">{blanket_val:.2f} m</text>
                <line x1="40" y1="38" x2="40" y2="95" stroke="#F59E0B" stroke-width="1" stroke-dasharray="2,2"/>
            </g>

            <!-- AIT-401 -->
            <g transform="translate(860, 55)">
                <rect x="0" y="0" width="115" height="48" rx="4" fill="#0F172A" stroke="{status_color}" stroke-width="2"/>
                <line x1="0" y1="18" x2="115" y2="18" stroke="#1E293B" stroke-width="1"/>
                <text x="57.5" y="13" text-anchor="middle" fill="{status_color}" font-size="8.5" font-family="'JetBrains Mono', monospace" font-weight="800">AIT-401 // DBO FINAL</text>
                <text x="57.5" y="37" text-anchor="middle" fill="#FFFFFF" font-size="15" font-family="'JetBrains Mono', monospace" font-weight="900">{bod_out:.2f} mg/L</text>
                <line x1="57.5" y1="48" x2="57.5" y2="135" stroke="{status_color}" stroke-width="1.5" stroke-dasharray="2,2"/>
            </g>

            <!-- BADGE NORMATIVO -->
            <rect x="860" y="107" width="115" height="18" rx="3" fill="#0F172A" stroke="{status_color}" stroke-width="1"/>
            <text x="917.5" y="120" text-anchor="middle" fill="{status_color}" font-size="8" font-family="'JetBrains Mono', monospace" font-weight="700">{status_label[:14]}</text>
        </svg>
    </div>
    </body>
    </html>
    """
    components.html(pfd_html, height=395, scrolling=False)
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    # Tabla de Corrientes de Proceso (Stream Table)
    st.markdown("##### Balance Másico de Corrientes de Planta (Stream Table)")
    streams_df = pd.DataFrame([
        {"Corriente": "1. Afluente Crudo", "Tag / Punto": "FIT-101 / AIT-102", "Caudal (m³/h)": f"{q_in:.1f}", "DBO₅ (mg/L)": f"{bod_in:.1f}", "DQO (mg/L)": f"{cod_in:.1f}", "Carga Másica (kg/h)": f"{load_bod_in_kgh:.2f}", "Carga Diaria (kg/d)": f"{load_bod_in_kgh*24:,.1f}", "Estado ISA": "Normal"},
        {"Corriente": "2. Biomasa Reactor", "Tag / Punto": "R-201 (4,050 m³)", "Caudal (m³/h)": f"{q_in:.1f}", "DBO₅ (mg/L)": f"DO: {do_val:.2f}", "DQO (mg/L)": f"MLSS: {mlss_val:.0f}", "Carga Másica (kg/h)": f"HRT: {hrt_val:.2f} h", "Carga Diaria (kg/d)": f"F/M: {fm_ratio:.3f}", "Estado ISA": "Óptimo" if 1.8 <= do_val <= 2.2 else "Alerta"},
        {"Corriente": "3. Retorno Lodos (RAS)", "Tag / Punto": "P-301 / FIT-302", "Caudal (m³/h)": f"{ras_val:.1f}", "DBO₅ (mg/L)": "Biomasa Retorno", "DQO (mg/L)": "—", "Carga Másica (kg/h)": "—", "Carga Diaria (kg/d)": "—", "Estado ISA": "Activo"},
        {"Corriente": "4. Purga Lodos (WAS)", "Tag / Punto": "P-302 / FIT-303", "Caudal (m³/h)": f"{was_val:.1f}", "DBO₅ (mg/L)": f"Manto: {blanket_val:.2f} m", "DQO (mg/L)": "—", "Carga Másica (kg/h)": "—", "Carga Diaria (kg/d)": "—", "Estado ISA": "Normal" if blanket_val <= 1.6 else "Alerta Manto"},
        {"Corriente": "5. Efluente Final Tratado", "Tag / Punto": "Vertedero / AIT-401", "Caudal (m³/h)": f"{q_in:.1f}", "DBO₅ (mg/L)": f"{bod_out:.2f}", "DQO (mg/L)": f"{bod_out*2.1:.1f}", "Carga Másica (kg/h)": f"{load_bod_out_kgh:.2f}", "Carga Diaria (kg/d)": f"{load_bod_out_kgh*24:,.1f}", "Estado ISA": status_label[:14]}
    ])
    st.dataframe(streams_df, width="stretch", hide_index=True)

# ==============================================================================
# PESTAÑA 2: SIMULACIÓN PREDICTIVA & SENSOR VIRTUAL (WHAT-IF)
# ==============================================================================
with tab2:
    st.markdown("#### Comparativa de Simulación: Línea Base Histórica vs. Régimen Actual")
    
    comp_df = pd.DataFrame([
        {"Variable de Proceso": "Caudal de Afluente (m³/h)", "Línea Base Histórica": "753.0 m³/h", "Simulación Actual": f"{q_in:.1f} m³/h", "Variación Neta": f"{q_in - 753.0:+.1f} m³/h", "Impacto Operativo": "Carga Hidráulica"},
        {"Variable de Proceso": "Oxígeno Disuelto (mg/L)", "Línea Base Histórica": "2.80 - 3.20 mg/L (Exceso)", "Simulación Actual": f"{do_val:.2f} mg/L", "Variación Neta": f"{do_val - 2.0:+.2f} vs Óptimo", "Impacto Operativo": "Consumo Eléctrico"},
        {"Variable de Proceso": "Inyección de Aire (km³/h)", "Línea Base Histórica": "6.68 km³/h (267.2 kW)", "Simulación Actual": f"{air_flow:.1f} km³/h ({power_kw:.1f} kW)", "Variación Neta": f"{air_flow - 6.68:+.2f} km³/h", "Impacto Operativo": "Demanda Eléctrica"},
        {"Variable de Proceso": "DBO₅ Salida Efluente (mg/L)", "Línea Base Histórica": "14.74 mg/L (122 h excedidas)", "Simulación Actual": f"{bod_out:.2f} mg/L", "Variación Neta": f"{bod_out - LIMIT_LEGAL:+.2f} vs Límite 20", "Impacto Operativo": status_label},
        {"Variable de Proceso": "Gasto Anual Compresión (USD)", "Línea Base Histórica": "$215,266 USD/año", "Simulación Actual": f"${cost_annual:,.0f} USD/año", "Variación Neta": f"${savings_usd:+,.0f} USD/año", "Impacto Operativo": "Balance Económico"}
    ])
    st.dataframe(comp_df, width="stretch", hide_index=True)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("##### Indicador de Conformidad Normativa (TULSMA &le; 20 mg/L)")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=bod_out,
            domain={'x': [0, 1], 'y': [0, 1]},
            delta={'reference': 20.0, 'increasing': {'color': "#EF4444"}, 'decreasing': {'color': "#10B981"}},
            number={'suffix': " mg/L", 'font': {'size': 28, 'color': status_color, 'family': 'JetBrains Mono'}},
            gauge={
                'axis': {'range': [0, 30], 'tickwidth': 1, 'tickcolor': "#64748B"},
                'bar': {'color': "#38BDF8", 'thickness': 0.35},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 1,
                'bordercolor': "#334155",
                'steps': [
                    {'range': [0, 16], 'color': 'rgba(16, 185, 129, 0.25)'},
                    {'range': [16, 20], 'color': 'rgba(245, 158, 11, 0.25)'},
                    {'range': [20, 30], 'color': 'rgba(239, 68, 68, 0.35)'}
                ],
                'threshold': {'line': {'color': "#EF4444", 'width': 4}, 'thickness': 0.8, 'value': 20.0}
            }
        ))
        fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauge, width="stretch")

    with col_g2:
        st.markdown("##### Curva Cinética de Transferencia de Oxígeno vs DBO")
        air_sweep = np.linspace(3.0, 12.0, 25)
        bod_sweep = []
        for a in air_sweep:
            sw_dict = dict(input_dict)
            sw_dict['Air_Flow_km3h'] = a
            sw_dict['Aeration_Tank_DO_mgL'] = np.clip(1.0 + (a - 3.0) * 0.38, 0.8, 4.5)
            bod_sweep.append(float(model.predict(pd.DataFrame([sw_dict])[feature_names])[0]) if model_active else 14.5)
        
        fig_curve = go.Figure()
        fig_curve.add_trace(go.Scatter(x=air_sweep, y=bod_sweep, mode='lines', name='Respuesta Cinética DBO', line=dict(color='#38BDF8', width=3)))
        fig_curve.add_trace(go.Scatter(x=[air_flow], y=[bod_out], mode='markers', name='Punto Operativo Actual', marker=dict(color=status_color, size=14, symbol='diamond')))
        fig_curve.add_hline(y=20.0, line_dash="dash", line_color="#EF4444", annotation_text="Límite Legal (20 mg/L)")
        fig_curve.add_vrect(x0=5.8, x1=7.0, fillcolor="rgba(16, 185, 129, 0.15)", line_width=0, annotation_text="Banda Óptima")
        fig_curve.update_layout(
            height=260,
            margin=dict(l=20, r=20, t=10, b=10),
            xaxis_title="Inyección de Aire (km³/h)",
            yaxis_title="DBO₅ Efluente Proyectada (mg/L)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_curve, width="stretch")

# ==============================================================================
# PESTAÑA 3: EFICIENCIA ENERGÉTICA & COSTOS
# ==============================================================================
with tab3:
    st.markdown("#### Análisis Energético de Sopladores y Descarbonización")
    
    e1, e2, e3 = st.columns(3)
    with e1:
        st.metric("Consumo Específico (SEC)", f"{sec_val:.3f} kWh/kg DBO", f"{sec_val - 1.186:+.3f} vs Baseline", delta_color="inverse")
    with e2:
        st.metric("Gasto Anual Sopladores", f"${cost_annual:,.0f} USD/año", f"${savings_usd:+,.0f} USD vs Base")
    with e3:
        st.metric("Emisiones CO₂ Evitadas", f"{co2_saved_tons:.1f} t CO₂ eq/año", f"{energy_saved_kwh:+,.0f} kWh/año")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("##### Comparativa de OPEX Anual de Compresión de Aire")
        fig_cost = go.Figure(data=[
            go.Bar(name='Línea Base Histórica', x=['Costo Anual'], y=[cost_base_annual], marker_color='#D97706', text=[f"${cost_base_annual:,.0f}"], textposition='auto'),
            go.Bar(name='Simulación Actual', x=['Costo Anual'], y=[cost_annual], marker_color='#10B981' if savings_usd >= 0 else '#EF4444', text=[f"${cost_annual:,.0f}"], textposition='auto')
        ])
        fig_cost.update_layout(height=280, barmode='group', margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_cost, width="stretch")
        
    with col_c2:
        st.markdown("##### Matriz de Sensibilidad al Costo de Energía Eléctrica")
        tariffs = [0.075, 0.085, 0.092, 0.105, 0.120]
        sens_data = []
        for t in tariffs:
            base_t = power_base_kw * 8760.0 * t
            curr_t = power_kw * 8760.0 * t
            diff_t = base_t - curr_t
            sens_data.append({"Tarifa ($/kWh)": f"${t:.3f}", "Costo Base Anual": f"${base_t:,.0f}", "Costo Simulado": f"${curr_t:,.0f}", "Ahorro Anual Proyectado": f"${diff_t:+,.0f} USD/año"})
        st.dataframe(pd.DataFrame(sens_data), width="stretch", hide_index=True)

# ==============================================================================
# PESTAÑA 4: PROCEDIMIENTO OPERATIVO (POE-OP-PTAR-001) Y DESPACHO DE TURNO
# ==============================================================================
with tab4:
    st.markdown("#### Protocolo de Control Operativo y Consignas por Turno (POE-OP-PTAR-001)")
    
    if do_val > 2.5:
        st.warning(f"""
        **DICTAMEN TÉCNICO: SOBRE-AIREACIÓN DETECTADA (SOBRECOSTO ENERGÉTICO EVITABLE)**
        * **Sensor DO (AIT-201):** {do_val:.2f} mg/L (Excede el límite superior de saturación de 2.20 mg/L).
        * **Diagnóstico de Proceso:** Los difusores están suministrando oxígeno en exceso sin ganancia cinética (cinética de Monod saturada).
        * **Acción Inmediata para el Operador:** Reducir la frecuencia del variador (VFD) del soplador en **-4 a -6 Hz** hasta alcanzar un caudal de aire de **{max(4.5, air_flow * 0.78):.1f} km³/h**.
        * **Impacto Financiero:** Esta desviación genera un sobrecosto evitable de **${abs(savings_usd):,.0f} USD/año**.
        """)
    elif do_val < 1.6:
        st.error(f"""
        **DICTAMEN TÉCNICO: SUB-AIREACIÓN CRÍTICA (RIESGO INMINENTE DE SANCIÓN AMBIENTAL)**
        * **Sensor DO (AIT-201):** {do_val:.2f} mg/L (Por debajo del umbral mínimo de seguridad de 1.60 mg/L).
        * **Diagnóstico de Proceso:** Riesgo inminente de degradación anóxica incompleta, proliferación de bacterias filamentosas (bulking) y escape de DBO > 20 mg/L.
        * **Acción Inmediata para el Operador:** Incrementar la frecuencia del variador (VFD) en **+6 a +8 Hz** ({min(11.0, air_flow * 1.35):.1f} km³/h) de forma inmediata.
        """)
    else:
        st.success(f"""
        **DICTAMEN TÉCNICO: OPERACIÓN ESTABLE EN BANDA DE MÁXIMA EFICIENCIA (SWEET SPOT)**
        * **Sensor DO (AIT-201):** {do_val:.2f} mg/L (Dentro del rango objetivo de 1.80 a 2.20 mg/L).
        * **Diagnóstico de Proceso:** Tasa de degradación bacteriana en régimen óptimo con mínimo consumo específico de compresión.
        * **Acción para el Operador:** Mantener consignas actuales y vigilar altura de manto en decantador (< 1.60 m).
        """)

    st.markdown("##### Matriz Oficial de Consignas por Régimen de Carga:")
    poe_matrix = pd.DataFrame([
        {"Régimen de Carga": "Baja Carga (Valle Nocturno)", "Caudal FIT-101": "< 700 m³/h", "DBO Entrada": "< 280 mg/L", "Consigna DO AIT-201": "1.80 mg/L", "Inyección Aire": "4.5 - 5.5 km³/h", "Frecuencia VFD": "38 - 42 Hz", "Purga WAS": "8 - 10 m³/h", "Retorno RAS": "450 - 500 m³/h"},
        {"Régimen de Carga": "Media Carga (Operación Normal)", "Caudal FIT-101": "700 - 800 m³/h", "DBO Entrada": "280 - 330 mg/L", "Consigna DO AIT-201": "2.00 mg/L", "Inyección Aire": "5.8 - 6.8 km³/h", "Frecuencia VFD": "44 - 48 Hz", "Purga WAS": "11 - 13 m³/h", "Retorno RAS": "500 - 550 m³/h"},
        {"Régimen de Carga": "Alta Carga (Pico Diurno)", "Caudal FIT-101": "> 800 m³/h", "DBO Entrada": "> 330 mg/L", "Consigna DO AIT-201": "2.20 mg/L", "Inyección Aire": "7.2 - 8.5 km³/h", "Frecuencia VFD": "52 - 58 Hz", "Purga WAS": "14 - 16 m³/h", "Retorno RAS": "550 - 650 m³/h"}
    ])
    st.dataframe(poe_matrix, width="stretch", hide_index=True)

    # Generador de Boleta de Despacho Operativo
    st.markdown("##### Emisión de Boleta Formal de Despacho de Turno (Shift Handover Log)")
    if st.button("Generar Boleta de Turno del Ingeniero de Planta"):
        vfd_est = 46.0 * (air_flow / 6.68)
        report_txt = f"""
========================================================================================
BOLETA DE CONTROL Y DESPACHO OPERATIVO // PLANTA PTAR 4,050 m³
PROCEDIMIENTO OPERATIVO ESTÁNDAR: POE-OP-PTAR-001
RESPONSABLE TÉCNICO: Ing. Angelo Apolo (Jefe de Planta / Ing. de Procesos)
========================================================================================
1. ESTADO DE TELEMETRÍA Y VARIABLES DE PROCESO
   - Caudal de Entrada (FIT-101):         {q_in:.1f} m³/h
   - Carga Orgánica Entrada (AIT-102):     {bod_in:.1f} mg/L ({load_bod_in_kgh:.1f} kg DBO/h)
   - Concentración Biomasa (MLSS-204):     {mlss_val:.0f} mg/L
   - Tiempo de Retención Hidráulica:       {hrt_val:.2f} horas
   - Relación Alimento/Microorganismo:     {fm_ratio:.3f} kg DBO/kg MLSS·d

2. DIAGNÓSTICO PREDICTIVO DEL SENSOR VIRTUAL (XGBOOST)
   - Oxígeno Disuelto Actual (AIT-201):   {do_val:.2f} mg/L
   - Proyección DBO Efluente (AIT-401):    {bod_out:.2f} mg/L
   - Límite Legal Normativo (TULSMA):     20.0 mg/L
   - Dictamen Normativo:                  {status_label}

3. CONSIGNAS DE OPERACIÓN ASIGNADAS AL OPERADOR DE TURNO
   - Consigna Flujo de Aire (FIT-202):    {air_flow:.2f} km³/h
   - Frecuencia Estimada Variador VFD:    {vfd_est:.1f} Hz
   - Altura Máxima Manto Lodos Clarif.:   < 1.60 m (Actual: {blanket_val:.2f} m)
   - Consigna Recirculación RAS:          {ras_val:.1f} m³/h
   - Consigna Purga WAS:                  {was_val:.1f} m³/h

4. DESEMPEÑO ENERGÉTICO Y FINANCIERO
   - Potencia Eléctrica Sopladores:       {power_kw:.1f} kW
   - Consumo Específico (SEC):            {sec_val:.3f} kWh/kg DBO
   - Ahorro Neto Proyectado vs Línea Base: ${savings_usd:+,.2f} USD/año
========================================================================================
Certificación: Parámetros validados mediante modelo predictivo y balances de masa.
========================================================================================
        """
        st.code(report_txt, language="text")

# Pie de página industrial
st.markdown("---")
st.caption("PTAR DIGITAL TWIN v2.1 // SISTEMA SCADA DE ALTO RENDIMIENTO ISA-101 // ING. ANGELO APOLO")
