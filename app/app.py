import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(
    page_title="PTAR Digital Twin | Optimización de Efluentes & Energía",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS industriales y elegantes
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border-left: 5px solid #1E3A8A;
        margin-bottom: 1rem;
    }
    .stMetric {
        background-color: #F8FAFC !important;
        padding: 12px !important;
        border-radius: 8px !important;
        border: 1px solid #E2E8F0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado
st.markdown('<div class="main-title">🌊 PTAR Digital Twin: Simulador Operativo y Optimización Energética</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle"><b>Ingeniería de Procesos & Utilidades</b> | Ing. Angelo Apolo<br>Simulación de balances de materia, estimación de calidad de efluente (DBO) y optimización de sopladores de aireación.</div>', unsafe_allow_html=True)

# Cargar modelo y features
@st.cache_resource
def load_model_artifacts():
    base_dir = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, 'modelo_ptar_xgboost.joblib')
    features_path = os.path.join(base_dir, 'features_ptar.joblib')
    
    # Fallback si se ejecuta desde la raíz
    if not os.path.exists(model_path):
        model_path = os.path.join('app', 'modelo_ptar_xgboost.joblib')
        features_path = os.path.join('app', 'features_ptar.joblib')
        
    model = joblib.load(model_path)
    features = joblib.load(features_path)
    return model, features

try:
    model, feature_names = load_model_artifacts()
    model_loaded = True
except Exception as e:
    st.error(f"Error al cargar el modelo: {e}")
    model_loaded = False

# Sidebar - Parámetros de Operación
st.sidebar.header("🎛️ Consignas de Planta")

# Escenarios preestablecidos
escenario = st.sidebar.selectbox(
    "Seleccionar Escenario Operativo Preestablecido:",
    [
        "Personalizado (Manual)",
        "Línea Base Histórica (Sobre-aireada)",
        "Consigna Óptima (Recomendada POE: 1.8 - 2.2 mg/L)",
        "Pico Diurno Crítico (Sobrecarga de Entrada)",
        "Valle Nocturno (Baja Carga / Ahorro Máximo)"
    ]
)

# Valores por defecto según escenario
if escenario == "Línea Base Histórica (Sobre-aireada)":
    def_flow, def_bod_in, def_cod_in, def_do, def_air = 750.0, 315.0, 665.0, 3.2, 8.5
elif escenario == "Consigna Óptima (Recomendada POE: 1.8 - 2.2 mg/L)":
    def_flow, def_bod_in, def_cod_in, def_do, def_air = 750.0, 315.0, 665.0, 2.0, 6.2
elif escenario == "Pico Diurno Crítico (Sobrecarga de Entrada)":
    def_flow, def_bod_in, def_cod_in, def_do, def_air = 850.0, 380.0, 800.0, 1.4, 10.5
elif escenario == "Valle Nocturno (Baja Carga / Ahorro Máximo)":
    def_flow, def_bod_in, def_cod_in, def_do, def_air = 680.0, 260.0, 520.0, 1.9, 4.8
else:
    def_flow, def_bod_in, def_cod_in, def_do, def_air = 753.0, 317.0, 666.0, 2.0, 6.68

st.sidebar.subheader("1. Hidráulica y Carga de Entrada")
influent_flow = st.sidebar.slider("Caudal de Entrada Influent_Flow (m³/h)", 300.0, 1200.0, float(def_flow), step=10.0)
influent_bod = st.sidebar.slider("DBO Afluente Influent_BOD (mg/L)", 150.0, 450.0, float(def_bod_in), step=5.0)
influent_cod = st.sidebar.slider("DQO Afluente Influent_COD (mg/L)", 300.0, 900.0, float(def_cod_in), step=10.0)
influent_tss = st.sidebar.slider("Sólidos Suspendidos Entrada (mg/L)", 100.0, 450.0, 298.0, step=5.0)

st.sidebar.subheader("2. Sistema de Aireación y Biológico")
air_flow = st.sidebar.slider("Flujo Aire Sopladores Air_Flow (km³/h)", 2.5, 12.0, float(def_air), step=0.1)
aeration_do = st.sidebar.slider("Oxígeno Disuelto DO (mg/L)", 0.5, 4.5, float(def_do), step=0.1)
temp_c = st.sidebar.slider("Temperatura Reactor (°C)", 15.0, 30.0, 22.2, step=0.5)
mlss = st.sidebar.slider("Sólidos Licor Mezcla MLSS (mg/L)", 2200.0, 4200.0, 3500.0, step=50.0)

st.sidebar.subheader("3. Clarificación y Retornos")
clarifier_blanket = st.sidebar.slider("Manto de Lodos Clarificador (m)", 0.4, 2.2, 1.17, step=0.05)
ras_flow = st.sidebar.slider("Recirculación RAS (m³/h)", 200.0, 750.0, 525.0, step=10.0)
was_flow = st.sidebar.slider("Purga WAS (m³/h)", 4.0, 20.0, 12.0, step=0.5)

# Cálculos de Proceso en Tiempo Real
V_REACTOR_M3 = 4050.0
SPECIFIC_ENERGY_KWH_M3 = 0.040
ELECTRIC_TARIFF_USD_KWH = 0.092
LIMIT_TULSMA = 20.0

load_bod_in_kgh = (influent_flow * influent_bod) / 1000.0
load_cod_in_kgh = (influent_flow * influent_cod) / 1000.0
hrt_hours = V_REACTOR_M3 / influent_flow

# Potencia y Costos Instantáneos
power_kw_current = air_flow * 1000.0 * SPECIFIC_ENERGY_KWH_M3
power_kw_baseline_ref = 6.68 * 1000.0 * SPECIFIC_ENERGY_KWH_M3

annual_cost_current = power_kw_current * 8760.0 * ELECTRIC_TARIFF_USD_KWH
annual_cost_base = power_kw_baseline_ref * 8760.0 * ELECTRIC_TARIFF_USD_KWH
annual_savings_usd = annual_cost_base - annual_cost_current
annual_energy_saved_kwh = (power_kw_baseline_ref - power_kw_current) * 8760.0
annual_co2_saved_tons = (annual_energy_saved_kwh * 0.420) / 1000.0

# Preparar vector para el Modelo Predictivo (Sensor Virtual)
input_dict = {
    'Influent_Flow_m3h': influent_flow,
    'Influent_BOD_mgL': influent_bod,
    'Influent_COD_mgL': influent_cod,
    'Influent_TSS_mgL': influent_tss,
    'Influent_NH4_mgL': 41.0,
    'Aeration_Tank_DO_mgL': aeration_do,
    'Aeration_Tank_MLSS_mgL': mlss,
    'Aeration_Tank_Temp_C': temp_c,
    'Air_Flow_km3h': air_flow,
    'RAS_Flow_m3h': ras_flow,
    'WAS_Flow_m3h': was_flow,
    'Clarifier_Blanket_Height_m': clarifier_blanket,
    'Clarifier_Overflow_TSS_mgL': 21.5,
    'ORP_mV': 50.0 + (aeration_do - 2.0) * 45.0,
    'pH': 7.2,
    'F_M_Ratio': 0.4,
    'Load_Influent_BOD_kgh': load_bod_in_kgh,
    'Load_Influent_COD_kgh': load_cod_in_kgh,
    'BOD_Removal_Efficiency_pct': 95.0,
    'HRT_hours': hrt_hours,
    'Hour_sin': 0.5,
    'Hour_cos': 0.866,
    'Influent_Flow_lag_1h': influent_flow,
    'Load_BOD_lag_1h': load_bod_in_kgh,
    'DO_lag_1h': aeration_do,
    'Air_Flow_lag_1h': air_flow,
    'Influent_Flow_lag_2h': influent_flow,
    'Load_BOD_lag_2h': load_bod_in_kgh,
    'DO_lag_2h': aeration_do,
    'Air_Flow_lag_2h': air_flow,
    'Influent_Flow_lag_4h': influent_flow,
    'Load_BOD_lag_4h': load_bod_in_kgh,
    'DO_lag_4h': aeration_do,
    'Air_Flow_lag_4h': air_flow,
    'DO_rollmean_2h': aeration_do,
    'Air_rollmean_2h': air_flow,
    'Clarifier_Blanket_rollmean_4h': clarifier_blanket
}

input_df = pd.DataFrame([input_dict])[feature_names]

if model_loaded:
    pred_bod_out = float(model.predict(input_df)[0])
else:
    # Heurística de respaldo
    pred_bod_out = 14.7 + (2.0 - aeration_do) * 2.2 + (influent_bod - 317.0) * 0.02

# Eficiencia de remoción resultante
removal_eff = ((influent_bod - pred_bod_out) / influent_bod) * 100.0
load_bod_out_kgh = (influent_flow * pred_bod_out) / 1000.0
load_removed_kgh = load_bod_in_kgh - load_bod_out_kgh
sec_kwh_kg = power_kw_current / (load_removed_kgh if load_removed_kgh > 0 else 1.0)

# FILA 1: TARJETAS DE INDICADORES CLAVE (KPIS)
col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_norma = pred_bod_out - LIMIT_TULSMA
    if pred_bod_out <= 16.0:
        st.metric("🎯 DBO Efluente Estimada", f"{pred_bod_out:.2f} mg/L", f"{delta_norma:.2f} vs Norma", delta_color="inverse")
        st.success("🟢 ESTADO: ÓPTIMO (En Norma)")
    elif pred_bod_out <= LIMIT_TULSMA:
        st.metric("⚠️ DBO Efluente Estimada", f"{pred_bod_out:.2f} mg/L", f"{delta_norma:.2f} vs Norma", delta_color="inverse")
        st.warning("🟡 ESTADO: ALERTA PREVENTIVA")
    else:
        st.metric("🚨 DBO Efluente Estimada", f"{pred_bod_out:.2f} mg/L", f"+{delta_norma:.2f} EXCEDIDO", delta_color="inverse")
        st.error("🔴 ESTADO: FUERA DE NORMA")

with col2:
    st.metric("📉 Eficiencia de Remoción DBO", f"{removal_eff:.2f}%", f"{removal_eff - 95.28:+.2f}% vs Histórico")
    st.info(f"Carga Removida: **{load_removed_kgh:.1f} kg/h**")

with col3:
    st.metric("⚡ Potencia Eléctrica Sopladores", f"{power_kw_current:.1f} kW", f"{power_kw_current - power_kw_baseline_ref:+.1f} kW vs Base", delta_color="inverse")
    st.info(f"Consumo Específico: **{sec_kwh_kg:.3f} kWh/kg**")

with col4:
    st.metric("💰 Ahorro Financiero Anual", f"${annual_savings_usd:+,.2f} USD", f"{annual_energy_saved_kwh:+,.0f} kWh/año")
    if annual_savings_usd >= 0:
        st.success(f"🌱 CO₂ Evitado: **{annual_co2_saved_tons:.1f} t/año**")
    else:
        st.warning(f"⚠️ Sobrecosto: **${abs(annual_savings_usd):,.2f}/año**")

st.markdown("---")

# FILA 2: GRÁFICOS INTERACTIVOS (GAUGE + BARRAS FINANCIERAS)
g_col1, g_col2 = st.columns([1, 1])

with g_col1:
    st.subheader("🎯 Tacómetro de Cumplimiento Ambiental (Norma: 20 mg/L)")
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pred_bod_out,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "DBO de Salida (mg/L)", 'font': {'size': 18}},
        delta={'reference': 20.0, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
        gauge={
            'axis': {'range': [0, 30], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#1E3A8A"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 16], 'color': '#D1FAE5'},
                {'range': [16, 20], 'color': '#FEF3C7'},
                {'range': [20, 30], 'color': '#FEE2E2'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.8,
                'value': 20.0
            }
        }
    ))
    fig_gauge.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

with g_col2:
    st.subheader("💵 Comparativa Financiera Anualizada de Sopladores")
    fig_bar = go.Figure(data=[
        go.Bar(name='Línea Base Histórica', x=['Costo Anual (USD)'], y=[annual_cost_base], marker_color='#D97706', text=[f"${annual_cost_base:,.0f}"], textposition='auto'),
        go.Bar(name='Simulación Actual', x=['Costo Anual (USD)'], y=[annual_cost_current], marker_color='#059669', text=[f"${annual_cost_current:,.0f}"], textposition='auto')
    ])
    fig_bar.update_layout(
        barmode='group',
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis_title="Gasto Eléctrico (USD/año)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# FILA 3: BALANCES DE MATERIA Y OPERACIÓN
b_col1, b_col2 = st.columns([1, 1])

with b_col1:
    st.subheader("⚖️ Balance de Masa en Vivo")
    balance_df = pd.DataFrame({
        "Parámetro de Proceso": [
            "Caudal de Entrada (Q_in)",
            "Carga DBO Entrada",
            "Carga DBO Efluente",
            "Carga DBO Removida",
            "Tiempo Retención Hidráulico (HRT)",
            "Relación Alimento/Biomasa (F/M Estimada)"
        ],
        "Valor Instantáneo": [
            f"{influent_flow:.1f} m³/h ({influent_flow * 24:,.0f} m³/d)",
            f"{load_bod_in_kgh:.2f} kg/h ({load_bod_in_kgh * 24:,.1f} kg/d)",
            f"{load_bod_out_kgh:.2f} kg/h ({load_bod_out_kgh * 24:,.1f} kg/d)",
            f"{load_removed_kgh:.2f} kg/h ({load_removed_kgh * 24:,.1f} kg/d)",
            f"{hrt_hours:.2f} horas en reactor biológico",
            f"{(load_bod_in_kgh * 24) / (V_REACTOR_M3 * mlss / 1000):.3f} kg DBO / kg MLSS·d"
        ]
    })
    st.dataframe(balance_df, use_container_width=True, hide_index=True)

with b_col2:
    st.subheader("📋 Consigna Operativa Recomendada (POE-OP-PTAR-001)")
    if aeration_do > 2.5:
        st.warning(f"""
        **⚠️ DICTAMEN DE PLANTA: SOBRE-AIREACIÓN DETECTADA**
        * El Oxígeno Disuelto actual ({aeration_do:.1f} mg/L) excede la banda óptima de saturación (1.8 - 2.2 mg/L).
        * **Acción para el Operador:** Modular el variador de frecuencia (VFD) del soplador hacia abajo en -5 Hz o reducir inyección de aire a **{max(4.5, air_flow * 0.75):.1f} km³/h**.
        * **Impacto Económico:** Estás perdiendo **${abs(annual_savings_usd):,.2f} USD/año** en energía innecesaria.
        """)
    elif aeration_do < 1.5:
        st.error(f"""
        **🚨 DICTAMEN DE PLANTA: SUB-AIREACIÓN CRÍTICA**
        * El Oxígeno Disuelto actual ({aeration_do:.1f} mg/L) pone en riesgo la flora bacteriana heterótrofa.
        * **Acción Inmediata:** Incrementar sopladores a **{min(11.0, air_flow * 1.3):.1f} km³/h** para recuperar el setpoint de 2.0 mg/L y evitar una excedencia de la norma TULSMA (> 20 mg/L).
        """)
    else:
        st.success(f"""
        **✅ DICTAMEN DE PLANTA: OPERACIÓN EN BANDA ÓPTIMA (SWEET SPOT)**
        * Oxígeno Disuelto ({aeration_do:.1f} mg/L) dentro del rango óptimo establecido en el POE (1.8 - 2.2 mg/L).
        * Máxima degradación biológica con el mínimo costo eléctrico.
        * **Acción:** Mantener consignas y verificar manto de lodos en clarificador (< 1.6 m).
        """)

st.markdown("---")
st.caption("PTAR Digital Twin v1.2 | Sistema de Monitoreo y Simulación de Procesos | Streamlit & XGBoost")
