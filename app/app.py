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
        font-size: 1.22rem;
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

    /* Guía de Operación y Cajas de Proceso */
    .guide-box {
        background-color: #0B132B;
        border: 1px solid #1E293B;
        border-left: 4px solid #38BDF8;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 1rem;
        font-size: 0.85rem;
        color: #CBD5E1;
        line-height: 1.55;
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
        <div class="topbar-title">PTAR INDUSTRIAL // DIGITAL TWIN, BALANCE INTEGRAL & CONTROL PREDICTIVO</div>
        <div class="topbar-sub">Tren Completo: Desbaste &bull; DAF Físico-Químico &bull; Selector Anóxico &bull; Reactor Aerobio 4,050 m³ &bull; Clarificador | Ing. Angelo Apolo</div>
    </div>
    <div>
        <span class="pill-badge pill-live">● SCADA ONLINE [24/7]</span>
        <span class="pill-badge pill-model">XGBOOST SENSOR VIRTUAL</span>
        <span class="pill-badge pill-norm">TULSMA: DBO &le; 20 mg/L</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. GUÍA RÁPIDA DE OPERACIÓN Y ARQUITECTURA DEL PROCESO
# ==============================================================================
with st.expander("Arquitectura del Proceso Industrial y Guía de Operación del Gemelo Digital", expanded=False):
    st.markdown("""
    <div class="guide-box">
        <p><b>1. Arquitectura del Tren de Tratamiento Industrial Completo:</b></p>
        <ul style="margin-left: 20px; margin-bottom: 10px;">
            <li><b>Pre-tratamiento (T-101):</b> Tamizado y desbaste mecánico para remoción de sólidos gruesos e inertes.</li>
            <li><b>Tratamiento Físico-Químico (DAF-102):</b> Unidad de Flotación por Aire Disuelto con coagulación/floculación. Remueve hasta el 90% de grasas y aceites (GyA) y el 40% de DQO insoluble, protegiendo a la biomasa de asfixia y evitando colmatación en difusores.</li>
            <li><b>Selector Anóxico (R-201A):</b> Cámara desnitrificante con agitación mecánica lenta en ausencia de oxígeno disuelto (DO &approx; 0.1 mg/L). Recibe el efluente clarificado del DAF y el retorno de lodos (RAS), transformando nitratos (NO₃⁻) en nitrógeno gaseoso inerte (N₂&uarr;).</li>
            <li><b>Reactor Biológico Aerobio (R-201B - 4,050 m³):</b> Zona de degradación de DBO soluble por bacterias heterótrofas y nitrificación aerobia, alimentada por difusores de burbuja fina y sopladores centrífugos K-201A/B.</li>
            <li><b>Clarificador Secundario (C-301):</b> Sedimentación por gravedad del lodo biológico, recirculación de biomasa activa (RAS) y purga de lodos de descarte (WAS).</li>
        </ul>
        <p><b>2. Foco Estratégico del Gemelo Digital:</b></p>
        <p>Aunque la planta opera como un tren integrado, <b>el 72% de la factura eléctrica y el riesgo crítico de sanción ambiental (TULSMA DBO &le; 20 mg/L) se concentran en la compresión de aire del reactor aerobio</b>. El sensor virtual XGBoost calcula continuamente la DBO de salida en función de la dinámica horaria del afluente para fijar la consigna óptima de aireación sin incurrir en sobrecostos energéticos.</p>
        <p><b>3. Flujo de Uso en 5 Pasos:</b> [1] Seleccionar Escenario &rarr; [2] Ajustar Consignas en Racks SCADA &rarr; [3] Monitorear PFD & Stream Table &rarr; [4] Evaluar Curva de Monod & What-If &rarr; [5] Emitir Boleta de Despacho Operativo (POE).</p>
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
with st.sidebar.expander("RACK 1: Afluente Crudo & DAF Primario", expanded=True):
    q_in = st.slider("Caudal Entrada FIT-101 (m³/h)", 300.0, 1200.0, float(def_q), step=10.0, help="Caudal de ingreso al pozo de bombeo y desbaste.")
    bod_in = st.slider("DBO Entrada AIT-102 (mg/L)", 150.0, 450.0, float(def_bod_in), step=5.0, help="Demanda Bioquímica de Oxígeno en agua cruda.")
    cod_in = st.slider("DQO Entrada AIT-103 (mg/L)", 300.0, 900.0, float(def_cod_in), step=10.0, help="Demanda Química de Oxígeno total.")
    tss_in = st.slider("Sólidos Entrada TSS-104 (mg/L)", 100.0, 450.0, 298.0, step=5.0)

with st.sidebar.expander("RACK 2: Reactor Biológico & Aireación", expanded=True):
    air_flow = st.slider("Inyección Aire FIT-202 (km³/h)", 2.5, 12.0, float(def_air), step=0.1, help="Flujo inyectado por los sopladores K-201.")
    do_val = st.slider("Oxígeno Disuelto AIT-201 (mg/L)", 0.5, 4.5, float(def_do), step=0.05, help="Concentración en licor mezcla. Rango óptimo: 1.80 a 2.20 mg/L.")
    temp_val = st.slider("Temperatura TIT-203 (°C)", 15.0, 30.0, 22.2, step=0.5)
    mlss_val = st.slider("Licor Mezcla MLSS-204 (mg/L)", 2200.0, 4500.0, 3500.0, step=50.0, help="Biomasa bacteriana en el reactor.")

with st.sidebar.expander("RACK 3: Clarificador & Purgas", expanded=False):
    blanket_val = st.slider("Manto de Lodos LIT-301 (m)", 0.4, 2.2, 1.17, step=0.05, help="Nivel de lodo sedimentado. Umbral crítico: > 1.60 m.")
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
    st.markdown("#### Diagrama de Flujo de Procesos (PFD) // Tren de Tratamiento Completo")
    
    # Renderizado Vectorial Aislado mediante iframe components.html (Tren Completo)
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
            height: 385px;
            background: radial-gradient(circle at 50% 50%, #0F172A 0%, #070B14 100%);
            border: 1px solid #1E293B;
            border-radius: 8px;
            overflow: hidden;
        }}
        .grid-bg {{
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background-image: linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
            background-size: 24px 24px;
            pointer-events: none;
        }}
        .flow-line {{
            stroke-dasharray: 7, 4;
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
            from {{ stroke-dashoffset: 22; }}
            to {{ stroke-dashoffset: 0; }}
        }}
        .bubble {{
            animation: rise 2s infinite ease-in;
        }}
        @keyframes rise {{
            0% {{ transform: translateY(0); opacity: 0.15; }}
            50% {{ opacity: 0.85; }}
            100% {{ transform: translateY(-42px); opacity: 0; }}
        }}
        .rotate-mixer {{
            transform-origin: 282px 175px;
            animation: spin 3s linear infinite;
        }}
        @keyframes spin {{
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    </head>
    <body>
    <div class="pfd-container">
        <div class="grid-bg"></div>
        <svg viewBox="0 0 1100 385" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="waterGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#1E3A8A" stop-opacity="0.6"/>
                    <stop offset="100%" stop-color="#0F172A" stop-opacity="0.95"/>
                </linearGradient>
                <linearGradient id="anoxicGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#14532D" stop-opacity="0.5"/>
                    <stop offset="100%" stop-color="#064E3B" stop-opacity="0.9"/>
                </linearGradient>
                <linearGradient id="dafGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#1E293B" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="#0F172A" stop-opacity="0.95"/>
                </linearGradient>
                <linearGradient id="sludgeGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#451A03" stop-opacity="0.8"/>
                    <stop offset="100%" stop-color="#1E1B18" stop-opacity="0.98"/>
                </linearGradient>
            </defs>

            <!-- ENCABEZADO SCADA -->
            <rect x="15" y="8" width="1070" height="26" fill="#0B132B" stroke="#1E293B" rx="4"/>
            <text x="30" y="25" fill="#94A3B8" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700">ISA-5.1 PFD // TREN COMPLETO: DESBASTE &bull; DAF FÍSICO-QUÍMICO &bull; SELECTOR ANÓXICO &bull; AEROBIO 4,050 m³ &bull; CLARIFICADOR</text>
            <text x="1070" y="25" text-anchor="end" fill="#10B981" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700">SUPERVISIÓN ONLINE</text>

            <!-- ================= TUBERÍAS Y FLUJOS ================= -->
            
            <!-- Corriente 1: Agua Cruda a Desbaste -->
            <path d="M 20 160 L 50 160" stroke="#38BDF8" stroke-width="4" fill="none" class="flow-line"/>
            
            <!-- Desbaste a DAF -->
            <path d="M 100 160 L 130 160" stroke="#38BDF8" stroke-width="3.5" fill="none" class="flow-line"/>
            <polygon points="125,156 135,160 125,164" fill="#38BDF8"/>

            <!-- DAF a Anóxico -->
            <path d="M 210 160 L 245 160" stroke="#38BDF8" stroke-width="3.5" fill="none" class="flow-line"/>
            <polygon points="240,156 250,160 240,164" fill="#38BDF8"/>

            <!-- Anóxico a Aerobio (Paso intermedio) -->
            <path d="M 320 160 L 350 160" stroke="#38BDF8" stroke-width="4" fill="none" class="flow-line"/>
            <polygon points="345,156 355,160 345,164" fill="#38BDF8"/>

            <!-- Aerobio a Clarificador -->
            <path d="M 600 160 L 680 160" stroke="#38BDF8" stroke-width="4" fill="none" class="flow-line"/>
            <polygon points="675,156 685,160 675,164" fill="#38BDF8"/>

            <!-- Clarificador a Salida Efluente -->
            <path d="M 890 145 L 970 145" stroke="{status_color}" stroke-width="4" fill="none" class="flow-line"/>
            <polygon points="965,141 975,145 965,149" fill="{status_color}"/>

            <!-- Aire Soplador a Reactor Aerobio -->
            <path d="M 480 315 L 480 230" stroke="#2DD4BF" stroke-width="3" fill="none" class="air-line"/>
            <polygon points="477,235 480,225 483,235" fill="#2DD4BF"/>

            <!-- Recirculación Lodos RAS (Clarificador a Selector Anóxico) -->
            <path d="M 785 275 L 785 340 L 282 340 L 282 235" stroke="#F59E0B" stroke-width="2.5" fill="none" class="sludge-line"/>
            <polygon points="279,240 282,230 285,240" fill="#F59E0B"/>

            <!-- Purga WAS -->
            <path d="M 785 275 L 785 340 L 910 340" stroke="#EF4444" stroke-width="2.5" fill="none" class="sludge-line"/>
            <polygon points="905,337 915,340 905,343" fill="#EF4444"/>

            <!-- Purga de Lodo Flotado DAF -->
            <path d="M 170 205 L 170 255 L 120 255" stroke="#D97706" stroke-width="2" stroke-dasharray="4,4" fill="none"/>
            <polygon points="125,252 115,255 125,258" fill="#D97706"/>
            <text x="110" y="270" text-anchor="middle" fill="#D97706" font-size="8" font-family="'JetBrains Mono', monospace">LODO DAF</text>

            <!-- ================= EQUIPOS DE PROCESO ================= -->

            <!-- EQUIPO 1: DESBASTE T-101 -->
            <rect x="50" y="125" width="50" height="70" rx="3" fill="#1E293B" stroke="#475569" stroke-width="1.2"/>
            <line x1="65" y1="130" x2="58" y2="190" stroke="#64748B" stroke-width="2"/>
            <line x1="75" y1="130" x2="68" y2="190" stroke="#64748B" stroke-width="2"/>
            <line x1="85" y1="130" x2="78" y2="190" stroke="#64748B" stroke-width="2"/>
            <text x="75" y="118" text-anchor="middle" fill="#94A3B8" font-size="8.5" font-family="'JetBrains Mono', monospace" font-weight="700">T-101</text>
            <text x="75" y="208" text-anchor="middle" fill="#64748B" font-size="7.5" font-family="'JetBrains Mono', monospace">TAMIZ</text>

            <!-- EQUIPO 2: DAF-102 (FLOTACIÓN POR AIRE DISUELTO) -->
            <polygon points="130,120 210,120 210,185 185,205 155,205 130,185" fill="url(#dafGrad)" stroke="#38BDF8" stroke-width="1.5"/>
            <line x1="135" y1="124" x2="205" y2="124" stroke="#D97706" stroke-width="2.5"/>
            <text x="170" y="112" text-anchor="middle" fill="#38BDF8" font-size="9" font-family="'JetBrains Mono', monospace" font-weight="700">DAF-102</text>
            <text x="170" y="145" text-anchor="middle" fill="#94A3B8" font-size="8" font-family="'JetBrains Mono', monospace">FÍSICO-QMC</text>
            <text x="170" y="158" text-anchor="middle" fill="#64748B" font-size="7.5" font-family="'JetBrains Mono', monospace">Grasas &le; 90%</text>
            <circle cx="155" cy="175" r="1.5" fill="#BAE6FD" opacity="0.6"/>
            <circle cx="170" cy="170" r="1.5" fill="#BAE6FD" opacity="0.7"/>
            <circle cx="185" cy="178" r="1.5" fill="#BAE6FD" opacity="0.6"/>

            <!-- EQUIPO 3: R-201A SELECTOR ANÓXICO (PRE-DESNITRIFICACIÓN) -->
            <rect x="245" y="100" width="75" height="135" rx="4" fill="url(#anoxicGrad)" stroke="#10B981" stroke-width="1.5"/>
            <text x="282" y="115" text-anchor="middle" fill="#A7F3D0" font-size="8.5" font-family="'JetBrains Mono', monospace" font-weight="700">R-201A</text>
            <text x="282" y="127" text-anchor="middle" fill="#6EE7B7" font-size="7.5" font-family="'JetBrains Mono', monospace">ANÓXICO</text>
            <text x="282" y="139" text-anchor="middle" fill="#94A3B8" font-size="7" font-family="'JetBrains Mono', monospace">DO &approx; 0.1</text>
            <line x1="282" y1="100" x2="282" y2="175" stroke="#94A3B8" stroke-width="2"/>
            <g class="rotate-mixer">
                <line x1="270" y1="175" x2="294" y2="175" stroke="#34D399" stroke-width="2.5"/>
                <line x1="282" y1="163" x2="282" y2="187" stroke="#34D399" stroke-width="2.5"/>
            </g>
            <text x="282" y="205" text-anchor="middle" fill="#6EE7B7" font-size="7.5" font-family="'JetBrains Mono', monospace">NO₃ &rarr; N₂&uarr;</text>

            <!-- EQUIPO 4: R-201B REACTOR AEROBIO (4,050 m³) -->
            <rect x="350" y="90" width="250" height="145" rx="6" fill="url(#waterGrad)" stroke="#38BDF8" stroke-width="2"/>
            <text x="475" y="110" text-anchor="middle" fill="#F8FAFC" font-size="11" font-weight="700">R-201B REACTOR AEROBIO</text>
            <text x="475" y="124" text-anchor="middle" fill="#64748B" font-size="9" font-family="'JetBrains Mono', monospace">VOL: 4,050 m³ | MLSS: {mlss_val:.0f} mg/L</text>
            
            <line x1="355" y1="135" x2="595" y2="135" stroke="#38BDF8" stroke-width="1.5" stroke-dasharray="4,2"/>
            <line x1="370" y1="225" x2="580" y2="225" stroke="#2DD4BF" stroke-width="3"/>
            
            <!-- Burbujas animadas -->
            <g class="bubble">
                <circle cx="400" cy="210" r="2.5" fill="#A7F3D0"/>
                <circle cx="460" cy="205" r="3" fill="#A7F3D0"/>
                <circle cx="515" cy="215" r="2.5" fill="#A7F3D0"/>
                <circle cx="560" cy="205" r="3" fill="#A7F3D0"/>
            </g>
            <g class="bubble" style="animation-delay: 0.9s;">
                <circle cx="420" cy="180" r="2" fill="#6EE7B7"/>
                <circle cx="485" cy="175" r="3.5" fill="#6EE7B7"/>
                <circle cx="540" cy="185" r="2" fill="#6EE7B7"/>
            </g>

            <!-- EQUIPO 5: SOPLADORES VFD (K-201A/B) -->
            <circle cx="480" cy="315" r="20" fill="#1E293B" stroke="#2DD4BF" stroke-width="2"/>
            <path d="M 472 305 L 488 315 L 472 325 Z" fill="#2DD4BF"/>
            <text x="480" y="348" text-anchor="middle" fill="#F8FAFC" font-size="10" font-weight="700">K-201A/B VFD</text>
            <text x="480" y="360" text-anchor="middle" fill="#2DD4BF" font-size="9" font-family="'JetBrains Mono', monospace">{air_flow:.1f} km³/h · {power_kw:.1f} kW</text>

            <!-- EQUIPO 6: CLARIFICADOR C-301 -->
            <polygon points="680,100 890,100 890,195 815,270 755,270 680,195" fill="url(#waterGrad)" stroke="#38BDF8" stroke-width="2"/>
            <polygon points="700,190 870,190 890,195 815,270 755,270 680,195" fill="url(#sludgeGrad)" stroke="none"/>
            <text x="785" y="118" text-anchor="middle" fill="#F8FAFC" font-size="11" font-weight="700">C-301 CLARIFICADOR</text>
            <text x="785" y="131" text-anchor="middle" fill="#64748B" font-size="9" font-family="'JetBrains Mono', monospace">SEDIMENTADOR SECUNDARIO</text>
            
            <line x1="680" y1="100" x2="890" y2="100" stroke="#94A3B8" stroke-width="3"/>
            <rect x="780" y="90" width="10" height="20" fill="#64748B"/>
            <line x1="700" y1="190" x2="870" y2="190" stroke="#F59E0B" stroke-width="2" stroke-dasharray="4,2"/>
            <text x="785" y="205" text-anchor="middle" fill="#FCD34D" font-size="9" font-family="'JetBrains Mono', monospace" font-weight="700">MANTO: {blanket_val:.2f} m</text>

            <!-- EQUIPO 7: BOMBAS RAS/WAS (P-301) -->
            <circle cx="785" cy="290" r="14" fill="#1E293B" stroke="#F59E0B" stroke-width="1.5"/>
            <text x="785" y="294" text-anchor="middle" fill="#F59E0B" font-size="8" font-weight="700">P-301</text>
            <text x="845" y="325" fill="#94A3B8" font-size="8.5" font-family="'JetBrains Mono', monospace">WAS: {was_val:.1f} m³/h</text>
            <text x="690" y="355" fill="#94A3B8" font-size="8.5" font-family="'JetBrains Mono', monospace">RAS: {ras_val:.1f} m³/h</text>

            <!-- ================= INSTRUMENTACIÓN ISA-5.1 ================= -->

            <!-- FIT-101 Entrada -->
            <g transform="translate(45, 45)">
                <rect x="0" y="0" width="85" height="42" rx="4" fill="#0F172A" stroke="#38BDF8" stroke-width="1.2"/>
                <line x1="0" y1="16" x2="85" y2="16" stroke="#1E293B" stroke-width="1"/>
                <text x="42.5" y="12" text-anchor="middle" fill="#94A3B8" font-size="8.5" font-family="'JetBrains Mono', monospace" font-weight="700">FIT-101</text>
                <text x="42.5" y="32" text-anchor="middle" fill="#F8FAFC" font-size="12" font-family="'JetBrains Mono', monospace" font-weight="800">{q_in:.0f} m³/h</text>
                <line x1="42.5" y1="42" x2="42.5" y2="125" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>
            </g>

            <!-- AIT-201 Oxígeno Disuelto -->
            <g transform="translate(430, 30)">
                <rect x="0" y="0" width="90" height="42" rx="4" fill="#0F172A" stroke="#2DD4BF" stroke-width="1.5"/>
                <line x1="0" y1="16" x2="90" y2="16" stroke="#1E293B" stroke-width="1"/>
                <text x="45" y="12" text-anchor="middle" fill="#94A3B8" font-size="8.5" font-family="'JetBrains Mono', monospace" font-weight="700">AIT-201 (DO)</text>
                <text x="45" y="33" text-anchor="middle" fill="#2DD4BF" font-size="13" font-family="'JetBrains Mono', monospace" font-weight="800">{do_val:.2f} mg/L</text>
                <line x1="45" y1="42" x2="45" y2="90" stroke="#2DD4BF" stroke-width="1" stroke-dasharray="2,2"/>
            </g>

            <!-- LIT-301 Manto Lodos -->
            <g transform="translate(805, 45)">
                <rect x="0" y="0" width="80" height="38" rx="4" fill="#0F172A" stroke="#F59E0B" stroke-width="1.2"/>
                <text x="40" y="14" text-anchor="middle" fill="#94A3B8" font-size="8" font-family="'JetBrains Mono', monospace">LIT-301 (MANTO)</text>
                <text x="40" y="30" text-anchor="middle" fill="#FCD34D" font-size="11" font-family="'JetBrains Mono', monospace" font-weight="800">{blanket_val:.2f} m</text>
                <line x1="40" y1="38" x2="40" y2="100" stroke="#F59E0B" stroke-width="1" stroke-dasharray="2,2"/>
            </g>

            <!-- AIT-401 Efluente DBO Final -->
            <g transform="translate(945, 65)">
                <rect x="0" y="0" width="130" height="52" rx="4" fill="#0F172A" stroke="{status_color}" stroke-width="2"/>
                <line x1="0" y1="18" x2="130" y2="18" stroke="#1E293B" stroke-width="1"/>
                <text x="65" y="13" text-anchor="middle" fill="{status_color}" font-size="8.5" font-family="'JetBrains Mono', monospace" font-weight="800">AIT-401 // DBO FINAL</text>
                <text x="65" y="39" text-anchor="middle" fill="#FFFFFF" font-size="16" font-family="'JetBrains Mono', monospace" font-weight="900">{bod_out:.2f} mg/L</text>
                <line x1="65" y1="52" x2="65" y2="145" stroke="{status_color}" stroke-width="1.5" stroke-dasharray="2,2"/>
            </g>

            <!-- BADGE NORMATIVO -->
            <rect x="945" y="122" width="130" height="18" rx="3" fill="#0F172A" stroke="{status_color}" stroke-width="1"/>
            <text x="1010" y="135" text-anchor="middle" fill="{status_color}" font-size="8" font-family="'JetBrains Mono', monospace" font-weight="700">{status_label[:15]}</text>
        </svg>
    </div>
    </body>
    </html>
    """
    components.html(pfd_html, height=395, scrolling=False)
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    # Tabla de Corrientes de Proceso (Stream Table)
    st.markdown("##### Balance Másico Integral del Tren de Tratamiento (Stream Table)")
    
    # Estimaciones fisicoquímicas del DAF
    bod_daf_out = bod_in * 0.82  # ~18% remoción DBO particulada en DAF
    cod_daf_out = cod_in * 0.65  # ~35% remoción DQO particulada/grasas en DAF
    tss_daf_out = tss_in * 0.20  # ~80% remoción de sólidos suspendidos en DAF
    
    streams_df = pd.DataFrame([
        {"Corriente": "1. Afluente Crudo", "Origen / Destino": "Rejas T-101 &rarr; DAF-102", "Caudal (m³/h)": f"{q_in:.1f}", "DBO₅ (mg/L)": f"{bod_in:.1f}", "DQO (mg/L)": f"{cod_in:.1f}", "Sólidos SST (mg/L)": f"{tss_in:.1f}", "Carga Másica (kg/h)": f"{load_bod_in_kgh:.2f}", "Estado ISA": "Normal"},
        {"Corriente": "2. Salida Clarificada DAF", "Origen / Destino": "DAF-102 &rarr; Anóxico R-201A", "Caudal (m³/h)": f"{q_in*0.98:.1f}", "DBO₅ (mg/L)": f"{bod_daf_out:.1f}", "DQO (mg/L)": f"{cod_daf_out:.1f}", "Sólidos SST (mg/L)": f"{tss_daf_out:.1f}", "Carga Másica (kg/h)": f"{(q_in*0.98*bod_daf_out)/1000:.2f}", "Estado ISA": "Normal (Libre de Grasas)"},
        {"Corriente": "3. Retorno Lodos (RAS)", "Origen / Destino": "Clarificador C-301 &rarr; R-201A", "Caudal (m³/h)": f"{ras_val:.1f}", "DBO₅ (mg/L)": "Biomasa Retorno", "DQO (mg/L)": "—", "Sólidos SST (mg/L)": f"{mlss_val*2.2:.0f}", "Carga Másica (kg/h)": "—", "Estado ISA": "Activo"},
        {"Corriente": "4. Licor Mezcla Aerobio", "Origen / Destino": "Reactor R-201B (4,050 m³)", "Caudal (m³/h)": f"{q_in + ras_val:.1f}", "DBO₅ (mg/L)": f"DO: {do_val:.2f}", "DQO (mg/L)": f"MLSS: {mlss_val:.0f}", "Sólidos SST (mg/L)": f"{mlss_val:.0f}", "Carga Másica (kg/h)": f"HRT: {hrt_val:.2f} h", "Estado ISA": "Óptimo" if 1.8 <= do_val <= 2.2 else "Alerta"},
        {"Corriente": "5. Purga Lodos Biológicos (WAS)", "Origen / Destino": "Clarificador C-301 &rarr; Espesador", "Caudal (m³/h)": f"{was_val:.1f}", "DBO₅ (mg/L)": f"Manto: {blanket_val:.2f} m", "DQO (mg/L)": "—", "Sólidos SST (mg/L)": f"{mlss_val*2.5:.0f}", "Carga Másica (kg/h)": "—", "Estado ISA": "Normal" if blanket_val <= 1.6 else "Alerta Manto"},
        {"Corriente": "6. Lodo Flotado DAF", "Origen / Destino": "Tolva DAF &rarr; Deshidratación", "Caudal (m³/h)": f"{q_in*0.02:.1f}", "DBO₅ (mg/L)": "Lodo Primario", "DQO (mg/L)": "Grasas > 85%", "Sólidos SST (mg/L)": "35,000", "Carga Másica (kg/h)": "—", "Estado ISA": "Activo"},
        {"Corriente": "7. Efluente Final Tratado", "Origen / Destino": "Vertedero C-301 &rarr; Descarga", "Caudal (m³/h)": f"{q_in:.1f}", "DBO₅ (mg/L)": f"{bod_out:.2f}", "DQO (mg/L)": f"{bod_out*2.1:.1f}", "Sólidos SST (mg/L)": "18.5", "Carga Másica (kg/h)": f"{load_bod_out_kgh:.2f}", "Estado ISA": status_label[:14]}
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
BOLETA DE CONTROL Y DESPACHO OPERATIVO // PLANTA PTAR INDUSTRIAL
PROCEDIMIENTO OPERATIVO ESTÁNDAR: POE-OP-PTAR-001
RESPONSABLE TÉCNICO: Ing. Angelo Apolo (Jefe de Planta / Ing. de Procesos)
========================================================================================
1. ESTADO DE TELEMETRÍA Y VARIABLES DEL TREN DE PROCESO
   - Caudal de Entrada (FIT-101):         {q_in:.1f} m³/h
   - Carga Orgánica Entrada (AIT-102):     {bod_in:.1f} mg/L ({load_bod_in_kgh:.1f} kg DBO/h)
   - Concentración Biomasa (MLSS-204):     {mlss_val:.0f} mg/L
   - Tiempo de Retención Hidráulica:       {hrt_val:.2f} horas
   - Relación Alimento/Microorganismo:     {fm_ratio:.3f} kg DBO/kg MLSS·d
   - Estado de Pre-tratamiento:           DAF Operativo (Remoción GyA activa)
   - Estado de Desnitrificación:          Selector Anóxico R-201A Estable (DO &approx; 0.1 mg/L)

2. DIAGNÓSTICO PREDICTIVO DEL SENSOR VIRTUAL (XGBOOST)
   - Oxígeno Disuelto Reactor (AIT-201):  {do_val:.2f} mg/L
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
st.caption("PTAR DIGITAL TWIN v2.2 // SISTEMA SCADA DE ALTO RENDIMIENTO ISA-101 // ING. ANGELO APOLO")
