import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(
    page_title="PTAR Digital Twin | Simulador Operativo",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS modernos compatibles al 100% con Tema Claro y Tema Oscuro
st.markdown("""
<style>
    /* Título con gradiente legible en modo claro y oscuro */
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #2563EB, #059669);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        opacity: 0.85;
        margin-bottom: 1rem;
        line-height: 1.4;
    }
    /* Tarjeta de guía operativa */
    .guide-box {
        background-color: rgba(37, 99, 235, 0.08);
        border-left: 4px solid #2563EB;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 1.5rem;
    }
    /* Tarjetas de métricas adaptables */
    [data-testid="stMetric"] {
        background-color: rgba(125, 125, 125, 0.08) !important;
        border: 1px solid rgba(125, 125, 125, 0.2) !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.88rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        font-weight: 800 !important;
    }
    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        text-align: center;
        width: 100%;
        margin-top: 6px;
    }
    .badge-optimo {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10B981;
        border: 1px solid #10B981;
    }
    .badge-alerta {
        background-color: rgba(245, 158, 11, 0.2);
        color: #F59E0B;
        border: 1px solid #F59E0B;
    }
    .badge-excedido {
        background-color: rgba(239, 68, 68, 0.2);
        color: #EF4444;
        border: 1px solid #EF4444;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado principal
st.markdown('<div class="main-title">🌊 PTAR Digital Twin: Simulador Operativo y Optimización Energética</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle"><b>Ingeniería de Procesos & Operaciones</b> | Desarrollado por Ing. Angelo Apolo<br>Simulador en tiempo real de balances de materia, cinética biológica y optimización del consumo eléctrico en sopladores de aireación.</div>', unsafe_allow_html=True)

# Guía Rápida de Uso desplegable e intuitiva
with st.expander("ℹ️ **¿CÓMO UTILIZAR ESTE SIMULADOR? (GUÍA RÁPIDA EN 3 PASOS)**", expanded=True):
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        st.markdown("""
        **1️⃣ Selecciona un Escenario o Ajusta**
        * En la barra lateral izquierda, elige un **escenario preestablecido** (ej: *Consigna Óptima* o *Línea Base*).
        * O mueve manualmente los controles de caudal, carga orgánica ($DBO$) o flujo de aire.
        """)
    with col_g2:
        st.markdown("""
        **2️⃣ Monitorea los Indicadores Clave**
        * **Tacómetro de Cumplimiento:** Verifica que la DBO de salida no supere los **$20\\text{ mg/L}$** (Norma ambiental TULSMA).
        * **Ahorro Financiero:** Observa el impacto en $\\text{USD/año}$ y $\\text{kWh/año}$ al evitar sobre-airear.
        """)
    with col_g3:
        st.markdown("""
        **3️⃣ Revisa la Consigna de Turno (POE)**
        * El panel inferior te indica la acción exacta para el operador en piso (ajuste de frecuencia VFD en Hz, purgas $WAS$ y recirculación $RAS$).
        """)

# Cargar modelo y features
@st.cache_resource
def load_model_artifacts():
    base_dir = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, 'modelo_ptar_xgboost.joblib')
    features_path = os.path.join(base_dir, 'features_ptar.joblib')
    
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

# SIDEBAR: Panel de control de consignas
st.sidebar.header("🎛️ Panel de Control de Planta")
st.sidebar.caption("Modifica las variables para simular la respuesta del sistema biológico y el costo eléctrico.")

escenario = st.sidebar.selectbox(
    "📌 Seleccionar Escenario Preestablecido:",
    [
        "Consigna Óptima (Recomendada POE: 1.8 - 2.2 mg/L)",
        "Línea Base Histórica (Sobre-aireada / Desperdicio)",
        "Pico Diurno Crítico (Sobrecarga de Entrada)",
        "Valle Nocturno (Baja Carga / Ahorro Máximo)",
        "Personalizado (Manual)"
    ],
    help="Escoge una condición típica de fábrica para ver automáticamente cómo reacciona la planta."
)

# Valores por defecto según escenario
if escenario == "Línea Base Histórica (Sobre-aireada / Desperdicio)":
    def_flow, def_bod_in, def_cod_in, def_do, def_air = 750.0, 315.0, 665.0, 3.2, 8.5
elif escenario == "Consigna Óptima (Recomendada POE: 1.8 - 2.2 mg/L)":
    def_flow, def_bod_in, def_cod_in, def_do, def_air = 750.0, 315.0, 665.0, 2.0, 6.2
elif escenario == "Pico Diurno Crítico (Sobrecarga de Entrada)":
    def_flow, def_bod_in, def_cod_in, def_do, def_air = 850.0, 380.0, 800.0, 1.4, 10.5
elif escenario == "Valle Nocturno (Baja Carga / Ahorro Máximo)":
    def_flow, def_bod_in, def_cod_in, def_do, def_air = 680.0, 260.0, 520.0, 1.9, 4.8
else:
    def_flow, def_bod_in, def_cod_in, def_do, def_air = 753.0, 317.0, 666.0, 2.0, 6.68

st.sidebar.markdown("---")
st.sidebar.subheader("1. Hidráulica y Carga de Entrada")
influent_flow = st.sidebar.slider(
    "Caudal Afluente (m³/h)", 
    300.0, 1200.0, float(def_flow), step=10.0,
    help="Volumen de agua residual que ingresa a la planta por hora. Promedio de diseño: 753 m³/h."
)
influent_bod = st.sidebar.slider(
    "DBO Entrada (mg/L)", 
    150.0, 450.0, float(def_bod_in), step=5.0,
    help="Demanda Bioquímica de Oxígeno en agua cruda. Picos diurnos alcanzan hasta 360 mg/L."
)
influent_cod = st.sidebar.slider(
    "DQO Entrada (mg/L)", 
    300.0, 900.0, float(def_cod_in), step=10.0,
    help="Demanda Química de Oxígeno total a la entrada del reactor."
)
influent_tss = st.sidebar.slider(
    "Sólidos Suspendidos Entrada TSS (mg/L)", 
    100.0, 450.0, 298.0, step=5.0,
    help="Carga de sólidos suspendidos totales que ingresan al sistema."
)

st.sidebar.markdown("---")
st.sidebar.subheader("2. Sistema de Aireación y Biológico")
air_flow = st.sidebar.slider(
    "Inyección de Aire Sopladores (km³/h)", 
    2.5, 12.0, float(def_air), step=0.1,
    help="Flujo volumétrico inyectado por los sopladores. Cada km³/h equivale a ~40 kW de potencia eléctrica."
)
aeration_do = st.sidebar.slider(
    "Oxígeno Disuelto DO (mg/L)", 
    0.5, 4.5, float(def_do), step=0.1,
    help="Oxígeno disuelto en el reactor biológico. Rango óptimo según POE: 1.8 - 2.2 mg/L."
)
temp_c = st.sidebar.slider(
    "Temperatura Reactor (°C)", 
    15.0, 30.0, 22.2, step=0.5,
    help="Modula la velocidad de actividad biológica de los lodos activados."
)
mlss = st.sidebar.slider(
    "Sólidos en Licor Mezcla MLSS (mg/L)", 
    2200.0, 4200.0, 3500.0, step=50.0,
    help="Concentración de biomasa activa en el tanque biológico. Valor de consigna estándar: 3,500 mg/L."
)

st.sidebar.markdown("---")
st.sidebar.subheader("3. Clarificador y Retornos")
clarifier_blanket = st.sidebar.slider(
    "Altura Manto de Lodos Clarificador (m)", 
    0.4, 2.2, 1.17, step=0.05,
    help="Nivel del manto en decantador secundario. Si supera 1.6 m existe riesgo de arrastre de sólidos al vertedero."
)
ras_flow = st.sidebar.slider(
    "Recirculación RAS (m³/h)", 
    200.0, 750.0, 525.0, step=10.0,
    help="Caudal de lodos activados retornados desde el fondo del clarificador al reactor biológico."
)
was_flow = st.sidebar.slider(
    "Purga de Lodos WAS (m³/h)", 
    4.0, 20.0, 12.0, step=0.5,
    help="Caudal de descarte de lodos para controlar la edad del lodo (SRT)."
)

# Cálculos de Proceso e Inferencia en Vivo
V_REACTOR_M3 = 4050.0
SPECIFIC_ENERGY_KWH_M3 = 0.040
ELECTRIC_TARIFF_USD_KWH = 0.092
LIMIT_TULSMA = 20.0

load_bod_in_kgh = (influent_flow * influent_bod) / 1000.0
load_cod_in_kgh = (influent_flow * influent_cod) / 1000.0
hrt_hours = V_REACTOR_M3 / influent_flow

# Potencia y Costos Eléctricos
power_kw_current = air_flow * 1000.0 * SPECIFIC_ENERGY_KWH_M3
power_kw_baseline_ref = 6.68 * 1000.0 * SPECIFIC_ENERGY_KWH_M3

annual_cost_current = power_kw_current * 8760.0 * ELECTRIC_TARIFF_USD_KWH
annual_cost_base = power_kw_baseline_ref * 8760.0 * ELECTRIC_TARIFF_USD_KWH
annual_savings_usd = annual_cost_base - annual_cost_current
annual_energy_saved_kwh = (power_kw_baseline_ref - power_kw_current) * 8760.0
annual_co2_saved_tons = (annual_energy_saved_kwh * 0.420) / 1000.0

# Vector para el Sensor Virtual (XGBoost)
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
    pred_bod_out = 14.7 + (2.0 - aeration_do) * 2.2 + (influent_bod - 317.0) * 0.02

# Variables derivadas
removal_eff = ((influent_bod - pred_bod_out) / influent_bod) * 100.0
load_bod_out_kgh = (influent_flow * pred_bod_out) / 1000.0
load_removed_kgh = load_bod_in_kgh - load_bod_out_kgh
sec_kwh_kg = power_kw_current / (load_removed_kgh if load_removed_kgh > 0 else 1.0)

# FILA 1: TARJETAS DE INDICADORES CLAVE (KPIS)
st.subheader("📊 Métricas Operativas y Financieras en Tiempo Real")

col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_norma = pred_bod_out - LIMIT_TULSMA
    st.metric(
        label="🎯 DBO Efluente (Sensor Virtual)", 
        value=f"{pred_bod_out:.2f} mg/L", 
        delta=f"{delta_norma:+.2f} vs Límite 20",
        delta_color="inverse",
        help="Demanda Bioquímica de Oxígeno predicha al instante por el modelo XGBoost."
    )
    if pred_bod_out <= 16.0:
        st.markdown('<div class="status-badge badge-optimo">🟢 CUMPLE NORMA (ÓPTIMO)</div>', unsafe_allow_html=True)
    elif pred_bod_out <= LIMIT_TULSMA:
        st.markdown('<div class="status-badge badge-alerta">🟡 ALERTA PREVENTIVA</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge badge-excedido">🔴 FUERA DE NORMA (&gt;20 mg/L)</div>', unsafe_allow_html=True)

with col2:
    st.metric(
        label="📉 Eficiencia de Remoción", 
        value=f"{removal_eff:.2f}%", 
        delta=f"{removal_eff - 95.28:+.2f}% vs Histórico",
        help="Porcentaje de carga contaminante eliminada en el reactor biológico y sedimentador."
    )
    st.caption(f"Carga Removida: **{load_removed_kgh:.1f} kg DBO/h**")

with col3:
    st.metric(
        label="⚡ Potencia Sopladores", 
        value=f"{power_kw_current:.1f} kW", 
        delta=f"{power_kw_current - power_kw_baseline_ref:+.1f} kW vs Base",
        delta_color="inverse",
        help="Demanda eléctrica instantánea de los motores de compresión de aire."
    )
    st.caption(f"Consumo Específico: **{sec_kwh_kg:.3f} kWh/kg DBO**")

with col4:
    st.metric(
        label="💰 Ahorro Económico Proyectado", 
        value=f"${annual_savings_usd:+,.0f} USD/año", 
        delta=f"{annual_energy_saved_kwh:+,.0f} kWh/año",
        help="Ahorro financiero anualizado frente a la línea base histórica operando a $0.092/kWh."
    )
    if annual_savings_usd >= 0:
        st.caption(f"🌱 CO₂ Evitado: **{annual_co2_saved_tons:.1f} t/año**")
    else:
        st.caption(f"⚠️ Sobrecosto: **${abs(annual_savings_usd):,.0f} USD/año**")

st.markdown("---")

# FILA 2: GRÁFICOS INTERACTIVOS (TACÓMETRO + COMPARATIVA FINANCIERA)
g_col1, g_col2 = st.columns([1, 1])

with g_col1:
    st.subheader("🎯 Tacómetro de Calidad de Vertido")
    st.caption("Límite normativo TULSMA: **20 mg/L**. Zona Verde: < 16 mg/L | Zona Amarilla: 16 - 20 mg/L | Zona Roja: > 20 mg/L")
    
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pred_bod_out,
        domain={'x': [0, 1], 'y': [0, 1]},
        delta={'reference': 20.0, 'increasing': {'color': "#EF4444"}, 'decreasing': {'color': "#10B981"}},
        number={'suffix': " mg/L", 'font': {'size': 26, 'color': '#0F172A' if pred_bod_out <= 20 else '#EF4444'}},
        gauge={
            'axis': {'range': [0, 30], 'tickwidth': 1, 'tickcolor': "gray"},
            'bar': {'color': "#2563EB", 'thickness': 0.3},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 1,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 16], 'color': 'rgba(16, 185, 129, 0.35)'},
                {'range': [16, 20], 'color': 'rgba(245, 158, 11, 0.35)'},
                {'range': [20, 30], 'color': 'rgba(239, 68, 68, 0.35)'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.8,
                'value': 20.0
            }
        }
    ))
    fig_gauge.update_layout(
        height=280, 
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with g_col2:
    st.subheader("💵 Gasto Anualizado de Sopladores")
    st.caption("Comparación de costos anuales ($ USD/año) entre la operación histórica y tu simulación actual.")
    
    fig_bar = go.Figure(data=[
        go.Bar(
            name='Línea Base Histórica', 
            x=['Costo Anual Eléctrico'], 
            y=[annual_cost_base], 
            marker_color='#D97706', 
            text=[f"${annual_cost_base:,.0f} USD"], 
            textposition='inside',
            textfont=dict(size=14, color='white')
        ),
        go.Bar(
            name='Simulación Actual', 
            x=['Costo Anual Eléctrico'], 
            y=[annual_cost_current], 
            marker_color='#059669' if annual_savings_usd >= 0 else '#DC2626', 
            text=[f"${annual_cost_current:,.0f} USD"], 
            textposition='inside',
            textfont=dict(size=14, color='white')
        )
    ])
    fig_bar.update_layout(
        barmode='group',
        height=280,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis_title="Dólares / año ($)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# FILA 3: BALANCES DE MATERIA Y DICTAMEN POE
b_col1, b_col2 = st.columns([1, 1])

with b_col1:
    st.subheader("⚖️ Balance de Masa Hidráulico y Biológico")
    st.caption("Cálculo instantáneo según principios de ingeniería química y reactores continuos.")
    
    balance_df = pd.DataFrame({
        "Parámetro de Proceso": [
            "Caudal Volumétrico de Entrada (Q_in)",
            "Carga Orgánica DBO Entrada",
            "Carga Orgánica DBO Efluente",
            "Carga Orgánica Total Removida",
            "Tiempo de Retención Hidráulico (HRT)",
            "Relación Alimento/Microorganismo (F/M)"
        ],
        "Valor Calculado": [
            f"{influent_flow:.1f} m³/h ({influent_flow * 24:,.0f} m³/día)",
            f"{load_bod_in_kgh:.2f} kg/h ({load_bod_in_kgh * 24:,.1f} kg/día)",
            f"{load_bod_out_kgh:.2f} kg/h ({load_bod_out_kgh * 24:,.1f} kg/día)",
            f"{load_removed_kgh:.2f} kg/h ({load_removed_kgh * 24:,.1f} kg/día)",
            f"{hrt_hours:.2f} horas (reactor de 4,050 m³)",
            f"{(load_bod_in_kgh * 24) / (V_REACTOR_M3 * mlss / 1000):.3f} kg DBO / kg MLSS·d"
        ]
    })
    st.dataframe(balance_df, use_container_width=True, hide_index=True)

with b_col2:
    st.subheader("📋 Dictamen Operativo para Turno de Planta")
    st.caption("Recomendación técnica inmediata basada en el Procedimiento Operativo Estándar POE-OP-PTAR-001.")
    
    if aeration_do > 2.5:
        st.warning(f"""
        **⚠️ SOBRE-AIREACIÓN DETECTADA (DESPERDICIO ENERGÉTICO)**
        * **Lectura actual:** Oxígeno Disuelto a **{aeration_do:.1f} mg/L** (excede la banda óptima de 1.8 - 2.2 mg/L).
        * **Efecto de Proceso:** La degradación bacteriana ya está saturada (cinética de Monod). Inyectar más aire no reduce más DBO.
        * **Acción para el Operador:** Reducir la frecuencia del variador (VFD) del soplador en **-4 a -6 Hz** hasta modular el caudal de aire hacia **{max(4.5, air_flow * 0.78):.1f} km³/h**.
        * **Pérdida Económica:** Se están quemando aproximadamente **${abs(annual_savings_usd):,.0f} USD/año** innecesariamente.
        """)
    elif aeration_do < 1.5:
        st.error(f"""
        **🚨 SUB-AIREACIÓN CRÍTICA (RIESGO DE INCUMPLIMIENTO)**
        * **Lectura actual:** Oxígeno Disuelto a **{aeration_do:.1f} mg/L** (por debajo del mínimo biológico de 1.5 mg/L).
        * **Efecto de Proceso:** Riesgo de asfixia del fango activo, lodos filamentosos (*bulking*) y escape de DBO fuera de norma (> 20 mg/L).
        * **Acción Inmediata:** Incrementar sopladores a **{min(11.0, air_flow * 1.35):.1f} km³/h** (+8 Hz en VFD) hasta restablecer 2.0 mg/L de DO.
        """)
    else:
        st.success(f"""
        **✅ OPERACIÓN EN BANDA ÓPTIMA (SWEET SPOT)**
        * **Lectura actual:** Oxígeno Disuelto en **{aeration_do:.1f} mg/L** (dentro del rango ideal de 1.8 - 2.2 mg/L).
        * **Efecto de Proceso:** Máxima degradación de carga orgánica con el menor consumo de compresión eléctrica.
        * **Acción para el Operador:** Mantener consigna actual y verificar que la altura del manto en el clarificador secundario permanezca en **< 1.6 m**.
        """)

st.markdown("---")
st.caption("PTAR Digital Twin v1.2 | Sistema de Monitoreo y Simulación de Procesos | Desarrollado con Streamlit & XGBoost")
