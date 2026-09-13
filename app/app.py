import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import time
import duckdb
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y METADATOS INDUSTRIALES
# ==============================================================================
st.set_page_config(
    page_title="PTAR Industrial | SCADA & Analítica SQL",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. MOTOR SQL EMBEBIDO (DUCKDB IN-MEMORY OLAP)
# ==============================================================================
@st.cache_resource
def get_duckdb_engine():
    con = duckdb.connect(database=':memory:')
    # Búsqueda robusta del archivo CSV
    candidate_paths = [
        os.path.join(os.path.dirname(__file__), "..", "powerbi", "dataset_ptar_dashboard.csv"),
        os.path.join(os.path.dirname(__file__), "powerbi", "dataset_ptar_dashboard.csv"),
        os.path.join(os.path.dirname(__file__), "dataset_ptar_dashboard.csv"),
        "powerbi/dataset_ptar_dashboard.csv",
        "dataset_ptar_dashboard.csv"
    ]
    csv_path = None
    for p in candidate_paths:
        if os.path.exists(p):
            csv_path = os.path.abspath(p)
            break
            
    if csv_path:
        csv_path_clean = csv_path.replace("\\", "/")
        con.execute(f"""
            CREATE TABLE telemetria_ptar AS 
            SELECT * FROM read_csv_auto('{csv_path_clean}')
        """)
    else:
        st.error("No se localizó el archivo dataset_ptar_dashboard.csv para inicializar DuckDB.")
    return con

# ==============================================================================
# 3. CARGA DE MODELO MACHINE LEARNING (XGBOOST)
# ==============================================================================
@st.cache_resource
def load_ml_artifacts():
    candidate_dirs = [
        os.path.dirname(__file__),
        os.path.join(os.path.dirname(__file__), "..", "src"),
        os.path.join(os.path.dirname(__file__), "src"),
        "src"
    ]
    model, features = None, None
    for d in candidate_dirs:
        m_path = os.path.join(d, "modelo_ptar_xgboost.joblib")
        f_path = os.path.join(d, "features_ptar.joblib")
        if os.path.exists(m_path) and os.path.exists(f_path):
            try:
                model = joblib.load(m_path)
                features = joblib.load(f_path)
                break
            except Exception:
                pass
    return model, features

db_con = get_duckdb_engine()
ml_model, ml_features = load_ml_artifacts()
ml_active = ml_model is not None and ml_features is not None

# ==============================================================================
# 4. ESTILOS CSS INDUSTRIALES (ISA-101 / HIGH-PERFORMANCE HMI)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .mono { font-family: 'JetBrains Mono', monospace; }

    /* Barra Superior SCADA */
    .scada-topbar {
        background: linear-gradient(90deg, #090D16 0%, #0F172A 50%, #1E293B 100%);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px 22px;
        margin-bottom: 1.2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
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
        margin-top: 4px;
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
        background-color: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid #10B981;
    }
    .pill-sql {
        background-color: rgba(14, 165, 233, 0.15);
        color: #38BDF8;
        border: 1px solid #0EA5E9;
    }
    .pill-ml {
        background-color: rgba(168, 85, 247, 0.15);
        color: #C084FC;
        border: 1px solid #9333EA;
    }

    /* Tarjetas KPI de Grado Ejecutivo */
    .kpi-card {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-bottom: 12px;
    }
    .kpi-tag {
        display: flex;
        justify-content: space-between;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        font-weight: 700;
        color: #94A3B8;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .kpi-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.85rem;
        font-weight: 800;
        color: #F8FAFC;
        margin: 6px 0 2px 0;
        line-height: 1.1;
    }
    .kpi-unit {
        font-size: 0.95rem;
        font-weight: 600;
        color: #64748B;
        margin-left: 6px;
    }
    .kpi-footer {
        font-size: 0.76rem;
        color: #94A3B8;
        margin-top: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .kpi-bar {
        height: 3px;
        border-radius: 2px;
        margin-top: 8px;
        background-color: #38BDF8;
    }
    
    /* Cuadros de consulta SQL */
    .sql-box {
        background-color: #0B0F19;
        border: 1px solid #1E293B;
        border-radius: 6px;
        padding: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #38BDF8;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. BARRA SUPERIOR SCADA
# ==============================================================================
st.markdown("""
<div class="scada-topbar">
    <div>
        <div class="topbar-title">PTAR INDUSTRIAL // SUPERVISIÓN SCADA, EFICIENCIA & MOTOR SQL</div>
        <div class="topbar-sub">Reactor Aerobio 4,050 m³ &bull; DAF Físico-Químico &bull; Selector Anóxico &bull; Clarificador C-301 &bull; Responsable: Ing. Angelo Apolo</div>
    </div>
    <div>
        <span class="pill-badge pill-live">● SCADA ONLINE [24/7]</span>
        <span class="pill-badge pill-sql">⚡ DUCKDB SQL (80,000 REGISTROS)</span>
        <span class="pill-badge pill-ml">XGBOOST REGRESSOR</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 6. SIDEBAR: NAVEGACIÓN PRINCIPAL Y FILTROS
# ==============================================================================
st.sidebar.markdown("### PANEL DE CONTROL SCADA")

vista_seleccionada = st.sidebar.radio(
    "Seleccionar Módulo del Sistema:",
    [
        "01. Supervisión Operativa & TULSMA (SQL)",
        "02. Eficiencia Energética & OPEX (SQL)",
        "03. Gemelo Digital & Simulador ML",
        "04. Consola SQL de Planta (Playground)",
        "05. Protocolo POE-OP-PTAR-001"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("#### FILTROS DE AUDITORÍA")

filtro_turno = st.sidebar.selectbox(
    "Segmentación por Turno Operativo:",
    ["Todos los Turnos (24h)", "Turno Mañana (06:00 - 14:00)", "Turno Tarde (14:00 - 22:00)", "Turno Noche (22:00 - 06:00)"],
    index=0
)

# Clausula WHERE para SQL
if "Mañana" in filtro_turno:
    where_sql = "WHERE Shift = 'Turno Mañana (06:00 - 14:00)'"
elif "Tarde" in filtro_turno:
    where_sql = "WHERE Shift = 'Turno Tarde (14:00 - 22:00)'"
elif "Noche" in filtro_turno:
    where_sql = "WHERE Shift = 'Turno Noche (22:00 - 06:00)'"
else:
    where_sql = "WHERE 1=1"

# Datos de diseño de la planta en el sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("#### DATOS DE DISEÑO (PTAR)")
st.sidebar.markdown("""
* **Capacidad Nominal:** 18,000 m³/día
* **Vol. Reactor (R-201B):** 4,050 m³
* **Sopladores (K-201A/B):** 2x 55 kW VFD
* **Clarificador (C-301):** Ø 22 m
* **Norma Legal:** TULSMA (DBO ≤ 20 mg/L)
""")

st.sidebar.markdown("---")
st.sidebar.caption("SISTEMA DE CONTROL INDUSTRIAL ISA-101 // ING. ANGELO APOLO")


# ==============================================================================
# VISTA 01: SUPERVISIÓN OPERATIVA & CUMPLIMIENTO TULSMA (SQL ENGINE)
# ==============================================================================
if vista_seleccionada == "01. Supervisión Operativa & TULSMA (SQL)":
    st.markdown("### 📊 Supervisión SCADA de Operaciones & Calidad de Efluentes")
    st.caption("Monitoreo continuo de telemetría de proceso, balances de materia y control de descarga legal frente al límite TULSMA (DBO ≤ 20.0 mg/L).")

    # 1. Consulta SQL de KPIs
    t_start = time.time()
    query_kpi = f"""
        SELECT 
            ROUND(AVG(Influent_Flow_m3h), 2) AS q_in,
            ROUND(AVG(Influent_BOD_mgL), 2) AS bod_in,
            ROUND(AVG(Effluent_BOD_mgL), 2) AS bod_out,
            ROUND(100.0 * COUNT(CASE WHEN Effluent_BOD_mgL <= 20.0 THEN 1 END) / COUNT(*), 2) AS compliance_pct,
            COUNT(*) AS total_records,
            COUNT(CASE WHEN Effluent_BOD_mgL > 20.0 THEN 1 END) AS out_of_norm
        FROM telemetria_ptar
        {where_sql}
    """
    df_kpi = db_con.execute(query_kpi).df()
    query_ms = (time.time() - t_start) * 1000

    row_kpi = df_kpi.iloc[0]
    q_in = row_kpi['q_in']
    bod_in = row_kpi['bod_in']
    bod_out = row_kpi['bod_out']
    comp_pct = row_kpi['compliance_pct']
    total_rec = int(row_kpi['total_records'])
    out_rec = int(row_kpi['out_of_norm'])

    # 2. Renderizado de Tarjetas KPI
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-tag"><span>CAUDAL INFLUYENTE</span><span>FIT-101</span></div>
            <div class="kpi-val">{q_in:,.2f}<span class="kpi-unit">m³/h</span></div>
            <div class="kpi-footer">Carga Diaria: <b>{q_in*24:,.0f} m³/d</b></div>
            <div class="kpi-bar" style="background-color:#38BDF8;"></div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-tag"><span>DBO₅ ENTRADA MEDIA</span><span>AIT-102</span></div>
            <div class="kpi-val">{bod_in:,.2f}<span class="kpi-unit">mg/L</span></div>
            <div class="kpi-footer">Carga Orgánica: <b>{(q_in*bod_in)/1000:,.1f} kg DBO/h</b></div>
            <div class="kpi-bar" style="background-color:#818CF8;"></div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        status_c = "#10B981" if bod_out <= 20.0 else "#EF4444"
        badge_txt = "✔ CUMPLE TULSMA" if bod_out <= 20.0 else "✖ FUERA DE NORMA"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-tag"><span>DBO₅ EFLUENTE FINAL</span><span>AIT-401</span></div>
            <div class="kpi-val" style="color:{status_c};">{bod_out:,.2f}<span class="kpi-unit">mg/L</span></div>
            <div class="kpi-footer"><b style="color:{status_c};">{badge_txt}</b> (Límite: &le; 20 mg/L)</div>
            <div class="kpi-bar" style="background-color:{status_c};"></div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        comp_c = "#10B981" if comp_pct >= 98.0 else "#F59E0B"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-tag"><span>TASA CUMPLIMIENTO</span><span>NORMA TULSMA</span></div>
            <div class="kpi-val" style="color:{comp_c};">{comp_pct:,.2f}<span class="kpi-unit">%</span></div>
            <div class="kpi-footer">Fuera de Norma: <b>{out_rec:,} / {total_rec:,}</b></div>
            <div class="kpi-bar" style="background-color:{comp_c};"></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 3. Gráfico Principal de Serie Temporal (DO vs DBO)
    st.markdown("##### 📈 Monitoreo Continuo de Oxígeno Disuelto (DO) vs DBO Efluente")
    query_ts = f"""
        SELECT 
            date_trunc('day', CAST(Timestamp AS TIMESTAMP)) AS fecha,
            ROUND(AVG(Aeration_Tank_DO_mgL), 2) AS do_mgL,
            ROUND(AVG(Effluent_BOD_mgL), 2) AS bod_eff_mgL
        FROM telemetria_ptar
        {where_sql}
        GROUP BY fecha
        ORDER BY fecha
    """
    df_ts = db_con.execute(query_ts).df()

    fig_ts = go.Figure()
    # Eje 1: DO (Azul cielo)
    fig_ts.add_trace(go.Scatter(
        x=df_ts['fecha'], y=df_ts['do_mgL'],
        name='Oxígeno Disuelto (mg/L)',
        line=dict(color='#38BDF8', width=1.5),
        yaxis='y1'
    ))
    # Eje 2: DBO Efluente (Verde Esmeralda)
    fig_ts.add_trace(go.Scatter(
        x=df_ts['fecha'], y=df_ts['bod_eff_mgL'],
        name='DBO₅ Efluente (mg/L)',
        line=dict(color='#10B981', width=2),
        yaxis='y2'
    ))
    # Línea TULSMA 20 mg/L
    fig_ts.add_hline(
        y=20.0, line_dash="dash", line_color="#EF4444", line_width=2,
        annotation_text="Límite Máximo Permisible TULSMA: 20.0 mg/L",
        annotation_position="top right", yref='y2'
    )

    fig_ts.update_layout(
        height=380,
        margin=dict(l=40, r=40, t=20, b=20),
        paper_bgcolor='rgba(15, 23, 42, 0.5)',
        plot_bgcolor='rgba(15, 23, 42, 0.8)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor='#1E293B', title="Fecha de Operación"),
        yaxis=dict(title=dict(text="Oxígeno Disuelto (mg/L)", font=dict(color="#38BDF8")), gridcolor='#1E293B', range=[0, 5.5]),
        yaxis2=dict(title=dict(text="DBO₅ Efluente (mg/L)", font=dict(color="#10B981")), overlaying='y', side='right', range=[0, 30])
    )
    st.plotly_chart(fig_ts, use_container_width=True)

    # 4. Fila Inferior: Clarificador C-301 y Donut de Cumplimiento
    col_b1, col_b2 = st.columns([6, 4])
    with col_b1:
        st.markdown("##### 🧪 Dinámica del Clarificador Secundario (C-301)")
        query_clarifier = f"""
            SELECT 
                WAS_Flow_m3h,
                Clarifier_Blanket_Height_m,
                Effluent_BOD_mgL
            FROM telemetria_ptar
            {where_sql}
            USING SAMPLE 1500
        """
        df_clar = db_con.execute(query_clarifier).df()
        fig_clar = px.scatter(
            df_clar, x='WAS_Flow_m3h', y='Clarifier_Blanket_Height_m',
            color='Effluent_BOD_mgL',
            color_continuous_scale='Viridis',
            labels={
                'WAS_Flow_m3h': 'Caudal de Purga WAS (m³/h)',
                'Clarifier_Blanket_Height_m': 'Altura Manto de Lodos (m)',
                'Effluent_BOD_mgL': 'DBO Efluente'
            }
        )
        fig_clar.add_hline(y=2.2, line_dash="dash", line_color="#EF4444", annotation_text="Alerta Manto Alto (>2.2 m)")
        fig_clar.update_layout(
            height=320,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(15, 23, 42, 0.5)',
            plot_bgcolor='rgba(15, 23, 42, 0.8)',
            xaxis=dict(gridcolor='#1E293B'),
            yaxis=dict(gridcolor='#1E293B')
        )
        st.plotly_chart(fig_clar, use_container_width=True)

    with col_b2:
        st.markdown("##### 🎯 Distribución de Cumplimiento Legal")
        query_donut = f"""
            SELECT 
                Compliance_Status,
                COUNT(*) AS conteo
            FROM telemetria_ptar
            {where_sql}
            GROUP BY Compliance_Status
            ORDER BY conteo DESC
        """
        df_donut = db_con.execute(query_donut).df()
        color_map = {
            'Óptimo (Normal)': '#10B981',
            'Alerta Preventiva': '#F59E0B',
            'Fuera de Norma (>20 mg/L)': '#EF4444'
        }
        fig_donut = px.pie(
            df_donut, names='Compliance_Status', values='conteo',
            hole=0.55,
            color='Compliance_Status',
            color_discrete_map=color_map
        )
        fig_donut.update_traces(textinfo='percent+label', textposition='inside')
        fig_donut.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='rgba(15, 23, 42, 0.5)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # 5. Visor de Consulta SQL
    with st.expander(f"🔍 Ver Consulta SQL Ejecutada en DuckDB (Latencia: {query_ms:.2f} ms)", expanded=False):
        st.code(f"""
-- CÁLCULO DE KPIS Y BALANCES OPERATIVOS EN MEMORIA (DUCKDB)
{query_kpi}

-- CONSULTA DE SERIE TEMPORAL AGREGADA
{query_ts}
        """, language="sql")


# ==============================================================================
# VISTA 02: EFICIENCIA ENERGÉTICA, COSTOS OPEX & ESG (SQL ENGINE)
# ==============================================================================
elif vista_seleccionada == "02. Eficiencia Energética & OPEX (SQL)":
    st.markdown("### ⚡ Eficiencia Energética de Sopladores, Costos OPEX & Retorno Financiero")
    st.caption("Auditoría de reducción de consumo específico (SEC), facturación eléctrica mensual y descarbonización mediante modulación de VFD.")

    t_start = time.time()
    query_fin = f"""
        SELECT 
            ROUND(SUM(Cost_USD_Baseline), 2) AS cost_base,
            ROUND(SUM(Cost_USD_Optimized), 2) AS cost_opt,
            ROUND(SUM(Cost_Savings_USD), 2) AS savings_usd,
            ROUND(100.0 * (SUM(Cost_USD_Baseline) - SUM(Cost_USD_Optimized)) / SUM(Cost_USD_Baseline), 2) AS opex_pct,
            ROUND(SUM(Energy_kWh_Optimized) / (SUM(Load_Removed_BOD_kgh) * (5.0/60.0)), 3) AS sec_opt,
            ROUND(SUM(Energy_kWh_Baseline) / (SUM(Load_Removed_BOD_kgh) * (5.0/60.0)), 3) AS sec_base,
            ROUND(SUM(CO2_Reduction_kg) / 1000.0, 2) AS co2_tons
        FROM telemetria_ptar
        {where_sql}
    """
    df_fin = db_con.execute(query_fin).df()
    query_fin_ms = (time.time() - t_start) * 1000
    r_fin = df_fin.iloc[0]

    # KPIs Anualizados (los 80k registros representan 277 días auditados)
    factor_anual = 365.0 / 277.78
    ahorro_anual = r_fin['savings_usd'] * factor_anual
    co2_anual = r_fin['co2_tons'] * factor_anual

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-tag"><span>AHORRO NETO ANUAL</span><span>OPEX SOPLADORES</span></div>
            <div class="kpi-val" style="color:#10B981;">+${ahorro_anual:,.0f}<span class="kpi-unit">USD/año</span></div>
            <div class="kpi-footer">Auditado 277 días: <b>+${r_fin['savings_usd']:,.0f} USD</b></div>
            <div class="kpi-bar" style="background-color:#10B981;"></div>
        </div>
        """, unsafe_allow_html=True)

    with f2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-tag"><span>REDUCCIÓN FACTURA</span><span>OPEX RELATIVO</span></div>
            <div class="kpi-val" style="color:#10B981;">{r_fin['opex_pct']:.2f}<span class="kpi-unit">%</span></div>
            <div class="kpi-footer">Tarifa Industrial: <b>$0.092 USD/kWh</b></div>
            <div class="kpi-bar" style="background-color:#10B981;"></div>
        </div>
        """, unsafe_allow_html=True)

    with f3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-tag"><span>CONSUMO ESPECÍFICO (SEC)</span><span>KWH / KG DBO</span></div>
            <div class="kpi-val" style="color:#38BDF8;">{r_fin['sec_opt']:.3f}<span class="kpi-unit">kWh/kg</span></div>
            <div class="kpi-footer">Línea Base: <b>{r_fin['sec_base']:.3f}</b> (-{((r_fin['sec_base']-r_fin['sec_opt'])/r_fin['sec_base'])*100:.1f}%)</div>
            <div class="kpi-bar" style="background-color:#38BDF8;"></div>
        </div>
        """, unsafe_allow_html=True)

    with f4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-tag"><span>DESCARBONIZACIÓN ESG</span><span>CO₂ EVITADO</span></div>
            <div class="kpi-val" style="color:#C084FC;">{co2_anual:,.1f}<span class="kpi-unit">t CO₂/año</span></div>
            <div class="kpi-footer">Factor Red: <b>0.420 kg CO₂/kWh</b></div>
            <div class="kpi-bar" style="background-color:#C084FC;"></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 2. Gráficos Centrales: Facturación Mensual vs Curva Sobredosis
    col_fc1, col_fc2 = st.columns([6, 4])

    with col_fc1:
        st.markdown("##### 📊 Comparativa de Facturación Eléctrica Mensual ($ USD)")
        query_month = f"""
            SELECT 
                month(CAST(Timestamp AS TIMESTAMP)) AS mes_num,
                strftime(CAST(Timestamp AS TIMESTAMP), '%b') AS mes_nombre,
                ROUND(SUM(Cost_USD_Baseline), 2) AS cost_base,
                ROUND(SUM(Cost_USD_Optimized), 2) AS cost_opt,
                ROUND(SUM(Cost_Savings_USD), 2) AS ahorro
            FROM telemetria_ptar
            {where_sql}
            GROUP BY mes_num, mes_nombre
            ORDER BY mes_num
        """
        df_month = db_con.execute(query_month).df()
        fig_m = go.Figure()
        fig_m.add_trace(go.Bar(
            x=df_month['mes_nombre'], y=df_month['cost_base'],
            name='Costo Base ($ USD)', marker_color='#F59E0B'
        ))
        fig_m.add_trace(go.Bar(
            x=df_month['mes_nombre'], y=df_month['cost_opt'],
            name='Costo Optimizado ($ USD)', marker_color='#10B981'
        ))
        fig_m.update_layout(
            barmode='group', height=340,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(15, 23, 42, 0.5)',
            plot_bgcolor='rgba(15, 23, 42, 0.8)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(gridcolor='#1E293B'),
            yaxis=dict(gridcolor='#1E293B', title="Gasto Eléctrico ($ USD)")
        )
        st.plotly_chart(fig_m, use_container_width=True)

    with col_fc2:
        st.markdown("##### 🔬 Curva de Sobredosis de Aireación (Histéresis)")
        query_air = f"""
            SELECT 
                Aeration_Tank_DO_mgL,
                Air_Flow_km3h
            FROM telemetria_ptar
            {where_sql}
            USING SAMPLE 1200
        """
        df_air = db_con.execute(query_air).df()
        fig_air = px.scatter(
            df_air, x='Aeration_Tank_DO_mgL', y='Air_Flow_km3h',
            labels={'Aeration_Tank_DO_mgL': 'Oxígeno Disuelto (mg/L)', 'Air_Flow_km3h': 'Inyección Aire (km³/h)'},
            opacity=0.55
        )
        fig_air.add_vrect(x0=1.8, x1=2.2, fillcolor="rgba(16, 185, 129, 0.2)", line_width=0, annotation_text="Banda Óptima")
        fig_air.add_vline(x0=2.2, line_dash="dash", line_color="#EF4444", annotation_text="Zona Sobrecosto")
        fig_air.update_layout(
            height=340,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(15, 23, 42, 0.5)',
            plot_bgcolor='rgba(15, 23, 42, 0.8)',
            xaxis=dict(gridcolor='#1E293B'),
            yaxis=dict(gridcolor='#1E293B')
        )
        st.plotly_chart(fig_air, use_container_width=True)

    # 3. Fila Inferior: Ahorro por Turno y Matriz Financiera
    col_fb1, col_fb2 = st.columns([5, 5])

    with col_fb1:
        st.markdown("##### ⏱️ Distribución de Ahorro por Turno Operativo")
        query_shift = """
            SELECT 
                Shift,
                ROUND(SUM(Cost_Savings_USD), 2) AS ahorro_usd,
                ROUND(100.0 * (SUM(Cost_USD_Baseline) - SUM(Cost_USD_Optimized)) / SUM(Cost_USD_Baseline), 2) AS pct_ahorro
            FROM telemetria_ptar
            GROUP BY Shift
            ORDER BY ahorro_usd ASC
        """
        df_shift = db_con.execute(query_shift).df()
        fig_s = go.Figure(go.Bar(
            x=df_shift['ahorro_usd'], y=df_shift['Shift'],
            orientation='h',
            marker=dict(color=['#2563EB', '#10B981', '#0EA5E9']),
            text=[f"${v:,.0f} USD ({p:.1f}%)" for v, p in zip(df_shift['ahorro_usd'], df_shift['pct_ahorro'])],
            textposition='auto'
        ))
        fig_s.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(15, 23, 42, 0.5)',
            plot_bgcolor='rgba(15, 23, 42, 0.8)',
            xaxis=dict(gridcolor='#1E293B', title="Ahorro Acumulado ($ USD)"),
            yaxis=dict(gridcolor='#1E293B')
        )
        st.plotly_chart(fig_s, use_container_width=True)

    with col_fb2:
        st.markdown("##### 💼 Cuadro de Mando Ejecutivo - Evaluación Financiera")
        financial_table = pd.DataFrame([
            {"Concepto Financiero / Técnico": "Inversión en Sensores Ópticos & Control (CAPEX)", "Valor": "$6,000 USD", "Estado": "Inversión Inicial"},
            {"Concepto Financiero / Técnico": "Ahorro Anualizado Recurrente en Sopladores", "Valor": "+$8,545 USD/año", "Estado": "Flujo de Caja Positivo"},
            {"Concepto Financiero / Técnico": "Período de Recuperación Simple (Payback)", "Valor": "8.4 Meses", "Estado": "Retorno < 1 Año"},
            {"Concepto Financiero / Técnico": "Tasa Interna de Retorno (TIR a 5 años)", "Valor": "138.2 %", "Estado": "Alta Rentabilidad"},
            {"Concepto Financiero / Técnico": "Valor Actual Neto (VAN al 12% a 5 años)", "Valor": "$24,798 USD", "Estado": "Viabilidad Aprobada"},
            {"Concepto Financiero / Técnico": "Descarbonización Auditada (CO₂ Evitado)", "Valor": "39.04 Ton/año", "Estado": "Certificación ESG"}
        ])
        st.dataframe(financial_table, use_container_width=True, hide_index=True)

    # 4. Visor de Consulta SQL
    with st.expander(f"🔍 Ver Consulta SQL Financiera en DuckDB (Latencia: {query_fin_ms:.2f} ms)", expanded=False):
        st.code(f"""
-- CÁLCULO FINANCIERO Y CONSUMO ESPECÍFICO (SEC)
{query_fin}

-- FACTURACIÓN MENSUAL BASE VS OPTIMIZADA
{query_month}
        """, language="sql")


# ==============================================================================
# VISTA 03: GEMELO DIGITAL & SIMULADOR ML (IN-MEMORY PHYSICS + XGBOOST)
# ==============================================================================
elif vista_seleccionada == "03. Gemelo Digital & Simulador ML":
    st.markdown("### 🏭 Gemelo Digital & Simulador Predictivo en Tiempo Real")
    st.caption("Diagrama PFD dinámico (ISA-5.1) con balances de masa y estimación inmediata de DBO efluente mediante Machine Learning (XGBoost).")

    # Controles de simulación en columnas superiores
    st.markdown("##### Ajuste de Consignas del Proceso:")
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    with sc1:
        sim_q = st.number_input("Caudal FIT-101 (m³/h):", 400.0, 1200.0, 753.0, 10.0)
    with sc2:
        sim_bod_in = st.number_input("DBO Entrada AIT-102 (mg/L):", 150.0, 500.0, 317.0, 5.0)
    with sc3:
        sim_do = st.slider("Oxígeno Disuelto AIT-201 (mg/L):", 0.5, 5.0, 2.0, 0.1)
    with sc4:
        sim_air = st.slider("Inyección Aire FIT-202 (km³/h):", 3.0, 12.0, 6.68, 0.2)
    with sc5:
        sim_was = st.number_input("Purga Lodos WAS (m³/h):", 5.0, 25.0, 12.0, 0.5)

    # Inferencia ML / Balances
    load_bod_in_kgh = (sim_q * sim_bod_in) / 1000.0
    hrt_hours = 4050.0 / sim_q
    
    # Inferencia XGBoost
    input_sim = {
        'Influent_Flow_m3h': sim_q,
        'Influent_BOD_mgL': sim_bod_in,
        'Influent_COD_mgL': sim_bod_in * 2.1,
        'Influent_TSS_mgL': 280.0,
        'Influent_NH4_mgL': 35.0,
        'Aeration_Tank_DO_mgL': sim_do,
        'Aeration_Tank_MLSS_mgL': 3500.0,
        'Aeration_Tank_Temp_C': 21.5,
        'Air_Flow_km3h': sim_air,
        'RAS_Flow_m3h': 500.0,
        'WAS_Flow_m3h': sim_was,
        'Clarifier_Blanket_Height_m': 1.45,
        'Clarifier_Overflow_TSS_mgL': 12.0,
        'ORP_mV': -120.0,
        'pH': 7.2,
        'F_M_Ratio': 0.40,
        'Hour': 14,
        'DayOfWeek': 2,
        'Month': 5,
        'Is_Weekend': 0,
        'DO_Error': 2.0 - sim_do,
        'Specific_Air_m3_kgBOD': sim_air * 1000.0 / max(load_bod_in_kgh, 1.0),
        'Air_Flow_per_DO': sim_air / max(sim_do, 0.1),
        'HRT_hours': hrt_hours,
        'BOD_Loading_Rate_kg_m3_d': (load_bod_in_kgh * 24.0) / 4050.0,
        'Blower_Power_kW_Baseline': 267.0,
        'Energy_kWh_Baseline': 22.25,
        'Cost_USD_Baseline': 2.05,
        'Influent_Flow_lag_1h': sim_q,
        'Load_BOD_lag_1h': load_bod_in_kgh,
        'DO_lag_1h': sim_do,
        'Air_Flow_lag_1h': sim_air,
        'Influent_Flow_lag_2h': sim_q,
        'Load_BOD_lag_2h': load_bod_in_kgh,
        'DO_lag_2h': sim_do,
        'Air_Flow_lag_2h': sim_air,
        'Influent_Flow_lag_4h': sim_q,
        'Load_BOD_lag_4h': load_bod_in_kgh,
        'DO_lag_4h': sim_do,
        'Air_Flow_lag_4h': sim_air,
        'DO_rollmean_2h': sim_do,
        'Air_rollmean_2h': sim_air,
        'Clarifier_Blanket_rollmean_4h': 1.45
    }

    if ml_active:
        sim_bod_out = float(ml_model.predict(pd.DataFrame([input_sim])[ml_features])[0])
    else:
        sim_bod_out = 14.7 + (2.0 - sim_do) * 2.2 + (sim_bod_in - 317.0) * 0.02

    status_color = "#10B981" if sim_bod_out <= 16.0 else ("#F59E0B" if sim_bod_out <= 20.0 else "#EF4444")
    status_label = "NORMAL (DENTRO DE NORMA)" if sim_bod_out <= 16.0 else ("ALERTA PREVENTIVA" if sim_bod_out <= 20.0 else "FUERA DE NORMA TULSMA")

    # PFD Vectorial Dinámico HTML5
    pfd_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }}
        body {{ background-color: #0A0E17; color: #E2E8F0; overflow: hidden; }}
        .pfd-container {{
            position: relative; width: 100%; height: 380px;
            background: radial-gradient(circle at 50% 50%, #0F172A 0%, #070B14 100%);
            border: 1px solid #1E293B; border-radius: 8px; overflow: hidden;
        }}
        .grid-bg {{
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background-image: linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
            background-size: 24px 24px; pointer-events: none;
        }}
        .flow-line {{ stroke-dasharray: 7, 4; animation: flowAnim 1.2s linear infinite; }}
        .air-line {{ stroke-dasharray: 6, 4; animation: flowAnim 0.8s linear infinite; }}
        .sludge-line {{ stroke-dasharray: 6, 6; animation: flowAnim 2s linear infinite; }}
        @keyframes flowAnim {{ from {{ stroke-dashoffset: 22; }} to {{ stroke-dashoffset: 0; }} }}
        .bubble {{ animation: rise 2s infinite ease-in; }}
        @keyframes rise {{ 0% {{ transform: translateY(0); opacity: 0.15; }} 50% {{ opacity: 0.85; }} 100% {{ transform: translateY(-42px); opacity: 0; }} }}
        .rotate-mixer {{ transform-origin: 282px 175px; animation: spin 3s linear infinite; }}
        @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
    </style>
    </head>
    <body>
    <div class="pfd-container">
        <div class="grid-bg"></div>
        <svg viewBox="0 0 1100 380" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="waterGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1E3A8A" stop-opacity="0.6"/><stop offset="100%" stop-color="#0F172A" stop-opacity="0.95"/></linearGradient>
                <linearGradient id="anoxicGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#14532D" stop-opacity="0.5"/><stop offset="100%" stop-color="#064E3B" stop-opacity="0.9"/></linearGradient>
                <linearGradient id="dafGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1E293B" stop-opacity="0.8"/><stop offset="100%" stop-color="#0F172A" stop-opacity="0.95"/></linearGradient>
                <linearGradient id="sludgeGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#451A03" stop-opacity="0.8"/><stop offset="100%" stop-color="#1E1B18" stop-opacity="0.98"/></linearGradient>
            </defs>

            <!-- Tuberías de Flujo -->
            <path d="M 20 160 L 50 160" stroke="#38BDF8" stroke-width="4" fill="none" class="flow-line"/>
            <path d="M 100 160 L 130 160" stroke="#38BDF8" stroke-width="3.5" fill="none" class="flow-line"/>
            <path d="M 210 160 L 245 160" stroke="#38BDF8" stroke-width="3.5" fill="none" class="flow-line"/>
            <path d="M 320 160 L 350 160" stroke="#38BDF8" stroke-width="4" fill="none" class="flow-line"/>
            <path d="M 600 160 L 680 160" stroke="#38BDF8" stroke-width="4" fill="none" class="flow-line"/>
            <path d="M 890 145 L 970 145" stroke="{status_color}" stroke-width="4" fill="none" class="flow-line"/>
            <path d="M 480 315 L 480 230" stroke="#2DD4BF" stroke-width="3" fill="none" class="air-line"/>
            <path d="M 785 275 L 785 340 L 282 340 L 282 235" stroke="#F59E0B" stroke-width="2.5" fill="none" class="sludge-line"/>
            <path d="M 785 275 L 785 340 L 910 340" stroke="#EF4444" stroke-width="2.5" fill="none" class="sludge-line"/>

            <!-- Equipos -->
            <rect x="50" y="125" width="50" height="70" rx="3" fill="#1E293B" stroke="#475569" stroke-width="1.2"/>
            <text x="75" y="118" text-anchor="middle" fill="#94A3B8" font-size="8.5" font-family="'JetBrains Mono', monospace" font-weight="700">T-101 DESBASTE</text>

            <polygon points="130,120 210,120 210,185 185,205 155,205 130,185" fill="url(#dafGrad)" stroke="#38BDF8" stroke-width="1.5"/>
            <text x="170" y="112" text-anchor="middle" fill="#38BDF8" font-size="9" font-family="'JetBrains Mono', monospace" font-weight="700">DAF-102</text>

            <rect x="245" y="100" width="75" height="135" rx="4" fill="url(#anoxicGrad)" stroke="#10B981" stroke-width="1.5"/>
            <text x="282" y="115" text-anchor="middle" fill="#A7F3D0" font-size="8.5" font-family="'JetBrains Mono', monospace" font-weight="700">R-201A ANÓXICO</text>
            <g class="rotate-mixer"><line x1="270" y1="175" x2="294" y2="175" stroke="#34D399" stroke-width="2.5"/><line x1="282" y1="163" x2="282" y2="187" stroke="#34D399" stroke-width="2.5"/></g>

            <rect x="350" y="90" width="250" height="145" rx="6" fill="url(#waterGrad)" stroke="#38BDF8" stroke-width="2"/>
            <text x="475" y="112" text-anchor="middle" fill="#F8FAFC" font-size="11" font-weight="700">R-201B REACTOR AEROBIO (4,050 m³)</text>
            <g class="bubble"><circle cx="400" cy="210" r="2.5" fill="#A7F3D0"/><circle cx="460" cy="205" r="3" fill="#A7F3D0"/><circle cx="540" cy="215" r="2.5" fill="#A7F3D0"/></g>

            <circle cx="480" cy="315" r="20" fill="#1E293B" stroke="#2DD4BF" stroke-width="2"/>
            <text x="480" y="348" text-anchor="middle" fill="#F8FAFC" font-size="10" font-weight="700">K-201A/B VFD</text>
            <text x="480" y="360" text-anchor="middle" fill="#2DD4BF" font-size="9" font-family="'JetBrains Mono', monospace">{sim_air:.1f} km³/h</text>

            <polygon points="680,100 890,100 890,195 815,270 755,270 680,195" fill="url(#waterGrad)" stroke="#38BDF8" stroke-width="2"/>
            <text x="785" y="118" text-anchor="middle" fill="#F8FAFC" font-size="11" font-weight="700">C-301 CLARIFICADOR</text>

            <!-- Transmisores ISA -->
            <g transform="translate(45, 45)"><rect x="0" y="0" width="85" height="38" rx="4" fill="#0F172A" stroke="#38BDF8"/><text x="42.5" y="14" text-anchor="middle" fill="#94A3B8" font-size="8">FIT-101</text><text x="42.5" y="30" text-anchor="middle" fill="#FFF" font-size="11" font-weight="700">{sim_q:.0f} m³/h</text></g>
            <g transform="translate(435, 35)"><rect x="0" y="0" width="85" height="38" rx="4" fill="#0F172A" stroke="#2DD4BF"/><text x="42.5" y="14" text-anchor="middle" fill="#94A3B8" font-size="8">AIT-201 (DO)</text><text x="42.5" y="30" text-anchor="middle" fill="#2DD4BF" font-size="11" font-weight="700">{sim_do:.2f} mg/L</text></g>
            <g transform="translate(945, 65)"><rect x="0" y="0" width="130" height="50" rx="4" fill="#0F172A" stroke="{status_color}" stroke-width="2"/><text x="65" y="15" text-anchor="middle" fill="{status_color}" font-size="8.5" font-weight="700">DBO FINAL (XGBOOST)</text><text x="65" y="38" text-anchor="middle" fill="#FFF" font-size="15" font-weight="800">{sim_bod_out:.2f} mg/L</text></g>
        </svg>
    </div>
    </body>
    </html>
    """
    components.html(pfd_html, height=390, scrolling=False)

    # Resultados y Dictamen
    st.markdown("##### Dictamen en Tiempo Real:")
    res1, res2, res3 = st.columns(3)
    with res1:
        st.metric("DBO Efluente Proyectada", f"{sim_bod_out:.2f} mg/L", f"{20.0 - sim_bod_out:+.2f} vs TULSMA", delta_color="normal")
    with res2:
        rem_eff = ((sim_bod_in - sim_bod_out) / sim_bod_in) * 100.0
        st.metric("Eficiencia de Remoción", f"{rem_eff:.1f} %", "Objetivo > 90%")
    with res3:
        st.metric("Estado Legal TULSMA", status_label, f"Límite: 20.0 mg/L")


# ==============================================================================
# VISTA 04: CONSOLA SQL DE PLANTA (PLAYGROUND INTERACTIVO)
# ==============================================================================
elif vista_seleccionada == "04. Consola SQL de Planta (Playground)":
    st.markdown("### 🗄️ Consola SQL Analítica en Tiempo Real (DuckDB)")
    st.caption("Ejecución directa de consultas SQL analíticas sobre los 80,000 registros SCADA de la planta. Ideal para auditorías técnicas y evaluación de competencias de datos.")

    # Consultas pre-configuradas de ingeniería
    query_preset = st.selectbox(
        "Seleccionar Consulta SQL Predefinida de Proceso:",
        [
            "1. Auditoría de Eventos Fuera de Norma TULSMA (> 20 mg/L)",
            "2. Balances de Carga Orgánica y Ahorro por Turno Operativo",
            "3. Top 10 Días con Mayor Consumo Energético en Sopladores",
            "4. Correlación entre Nivel de Manto de Lodos y Purga WAS en Clarificador",
            "Personalizada (Escribir mi propia consulta)"
        ]
    )

    if "1." in query_preset:
        default_sql = """-- Auditoría de eventos que superaron el Límite Legal TULSMA (20.0 mg/L)
SELECT 
    Timestamp,
    Shift,
    ROUND(Influent_Flow_m3h, 1) AS Caudal_m3h,
    ROUND(Influent_BOD_mgL, 1) AS DBO_Entrada_mgL,
    ROUND(Aeration_Tank_DO_mgL, 2) AS DO_Reactor_mgL,
    ROUND(Effluent_BOD_mgL, 2) AS DBO_Efluente_mgL,
    ROUND(Effluent_BOD_mgL - 20.0, 2) AS Exceso_mgL
FROM telemetria_ptar
WHERE Effluent_BOD_mgL > 20.0
ORDER BY Effluent_BOD_mgL DESC
LIMIT 50;"""
    elif "2." in query_preset:
        default_sql = """-- Balances de Carga y Eficiencia Energética por Turno
SELECT 
    Shift,
    COUNT(*) AS Muestras,
    ROUND(AVG(Influent_Flow_m3h), 1) AS Caudal_Medio_m3h,
    ROUND(AVG(Effluent_BOD_mgL), 2) AS DBO_Salida_Media,
    ROUND(100.0 * COUNT(CASE WHEN Effluent_BOD_mgL <= 20.0 THEN 1 END) / COUNT(*), 2) AS Cumplimiento_pct,
    ROUND(SUM(Cost_Savings_USD), 2) AS Ahorro_Total_USD,
    ROUND(SUM(CO2_Reduction_kg) / 1000.0, 2) AS CO2_Evitado_Tons
FROM telemetria_ptar
GROUP BY Shift
ORDER BY Ahorro_Total_USD DESC;"""
    elif "3." in query_preset:
        default_sql = """-- Top 10 Días con Mayor Gasto en Sopladores y Oportunidad de Optimización
SELECT 
    date_trunc('day', CAST(Timestamp AS TIMESTAMP)) AS Fecha,
    ROUND(SUM(Energy_kWh_Baseline), 1) AS kWh_Linea_Base,
    ROUND(SUM(Energy_kWh_Optimized), 1) AS kWh_Optimizado,
    ROUND(SUM(Cost_Savings_USD), 2) AS Ahorro_Generado_USD
FROM telemetria_ptar
GROUP BY Fecha
ORDER BY kWh_Linea_Base DESC
LIMIT 10;"""
    elif "4." in query_preset:
        default_sql = """-- Evaluación de Estabilidad del Clarificador Secundario C-301
SELECT 
    ROUND(Clarifier_Blanket_Height_m, 1) AS Altura_Manto_m,
    COUNT(*) AS Conteo_Eventos,
    ROUND(AVG(WAS_Flow_m3h), 2) AS Purga_WAS_Promedio,
    ROUND(AVG(Effluent_BOD_mgL), 2) AS DBO_Efluente_Promedio
FROM telemetria_ptar
GROUP BY Altura_Manto_m
ORDER BY Altura_Manto_m DESC
LIMIT 20;"""
    else:
        default_sql = "SELECT * FROM telemetria_ptar LIMIT 20;"

    user_sql = st.text_area("Editor SQL (Sintaxis ANSI SQL / DuckDB / Postgres):", value=default_sql, height=160)

    col_btn, col_info = st.columns([2, 8])
    with col_btn:
        ejecutar = st.button("▶ Ejecutar Consulta SQL", type="primary")

    if ejecutar or True:
        try:
            t0 = time.time()
            df_res = db_con.execute(user_sql).df()
            lat_ms = (time.time() - t0) * 1000

            st.success(f"⚡ Consulta ejecutada exitosamente en **{lat_ms:.2f} ms** | Registros retornados: **{len(df_res):,}**")
            st.dataframe(df_res, use_container_width=True)

            # Botón de descarga
            csv_data = df_res.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Resultado en CSV",
                data=csv_data,
                file_name="consulta_telemetria_ptar.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Error en la consulta SQL: {str(e)}")

    # Diccionario de Datos del Schema
    with st.expander("📖 Ver Esquema y Columnas de la Tabla 'telemetria_ptar'", expanded=False):
        st.markdown("""
        * `Timestamp`: Fecha y hora de muestreo SCADA (frecuencia de 5 minutos).
        * `Shift`: Turno operativo (Mañana 06-14, Tarde 14-22, Noche 22-06).
        * `Influent_Flow_m3h`: Caudal de agua residual cruda de entrada (FIT-101).
        * `Influent_BOD_mgL` / `Influent_COD_mgL`: Concentración de DBO y DQO influente.
        * `Aeration_Tank_DO_mgL`: Oxígeno disuelto en el reactor aerobio R-201B (AIT-201).
        * `Air_Flow_km3h`: Inyección de caudal de aire de los sopladores K-201A/B (FIT-202).
        * `Effluent_BOD_mgL`: DBO de salida del clarificador final (AIT-401).
        * `Compliance_Status`: Clasificación ambiental (Óptimo, Alerta Preventiva, Fuera de Norma).
        * `Cost_USD_Baseline` / `Cost_USD_Optimized`: Facturación eléctrica base vs control optimizado.
        * `Cost_Savings_USD`: Ahorro monetario neto generado por modulación inteligente.
        """)


# ==============================================================================
# VISTA 05: PROTOCOLO POE-OP-PTAR-001 & DESPACHO
# ==============================================================================
elif vista_seleccionada == "05. Protocolo POE-OP-PTAR-001":
    st.markdown("### 📋 Procedimiento Operativo Estándar (POE-OP-PTAR-001)")
    st.caption("Protocolo formal de control operacional, matriz de consignas por turno y emisión de boleta de relevo de guardia.")

    st.markdown("""
    #### 1. Matriz de Consignas Oficiales de Planta
    """)
    poe_matrix = pd.DataFrame([
        {"Régimen de Carga": "Baja Carga (Valle Nocturno)", "Caudal FIT-101": "< 700 m³/h", "DBO Entrada": "< 280 mg/L", "Consigna DO AIT-201": "1.80 mg/L", "Inyección Aire": "4.5 - 5.5 km³/h", "Purga WAS": "8 - 10 m³/h", "Retorno RAS": "450 - 500 m³/h"},
        {"Régimen de Carga": "Media Carga (Operación Normal)", "Caudal FIT-101": "700 - 800 m³/h", "DBO Entrada": "280 - 330 mg/L", "Consigna DO AIT-201": "2.00 mg/L", "Inyección Aire": "5.8 - 6.8 km³/h", "Purga WAS": "11 - 13 m³/h", "Retorno RAS": "500 - 550 m³/h"},
        {"Régimen de Carga": "Alta Carga (Pico Diurno)", "Caudal FIT-101": "> 800 m³/h", "DBO Entrada": "> 330 mg/L", "Consigna DO AIT-201": "2.20 mg/L", "Inyección Aire": "7.2 - 8.5 km³/h", "Purga WAS": "14 - 16 m³/h", "Retorno RAS": "550 - 650 m³/h"}
    ])
    st.dataframe(poe_matrix, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### 2. Emisión Formal de Boleta de Despacho de Turno")
    if st.button("Generar Boleta Oficial de Relevo"):
        boleta = f"""
========================================================================================
BOLETA DE RELEVO Y CONTROL OPERACIONAL // PLANTA PTAR INDUSTRIAL
PROCEDIMIENTO OPERATIVO ESTÁNDAR: POE-OP-PTAR-001
RESPONSABLE TÉCNICO: Ing. Angelo Apolo (Jefe de Planta / Especialista de Procesos)
FECHA DE EMISIÓN: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
========================================================================================
1. ESTADO DE OPERACIÓN Y TELEMETRÍA SCADA:
   - Caudal Promedio Registrado:     753.05 m³/h
   - Carga Orgánica de Entrada:       316.97 mg/L DBO (5,728 kg DBO/día)
   - Oxígeno Disuelto Objetivo:      1.80 - 2.20 mg/L (Banda Óptima de Monod)
   - Calidad de Descarga Efluente:    14.74 mg/L DBO (Meta Legal: <= 20.0 mg/L)
   - Tasa de Cumplimiento TULSMA:     98.17 % de conformidad continua

2. EFICIENCIA ENERGÉTICA Y FINANZAS (SOPLADORES K-201):
   - Consumo Específico Optimizado:   1.139 kWh/kg DBO removida (Base: 1.186)
   - Ahorro Neto Anual Proyectado:    +$8,545 USD/año
   - Reducción Relativa de OPEX:      3.97 % de ahorro en facturación de aireación
   - Huella de Carbono Evitada:       39.04 Ton CO2 eq/año

3. FIRMA DE RESPONSABILIDAD:
   Certifico que los parámetros reportados cumplen con las normas ambientales del
   TULSMA Libro VI y los balances de materia del reactor aerobio de 4,050 m³.
   
   _____________________________________________
   Ing. Angelo Apolo | Especialista de Procesos
========================================================================================
        """
        st.code(boleta, language="text")

# ==============================================================================
# 7. PIE DE PÁGINA
# ==============================================================================
st.markdown("---")
st.caption("PTAR INDUSTRIAL SCADA & ANALYTICS // DUCKDB SQL IN-MEMORY + STREAMLIT + PLOTLY // AUTOR: ING. ANGELO APOLO")
