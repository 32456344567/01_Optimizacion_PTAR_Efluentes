# Optimización Operativa de PTAR y Eficiencia Energética en Sistemas de Aireación

**Ingeniería de Procesos, Balances de Materia y Control de Efluentes**  
**Autor:** Ing. Angelo Apolo | Especialista en Operaciones, Procesos y Utilidades Industriales  

---

## 📌 1. Descripción del Proceso y Contexto Operativo
El presente proyecto aborda la optimización técnica y operativa de una **Planta de Tratamiento de Aguas Residuales (PTAR)** industrial/municipal basada en el proceso de **lodos activados de mezcla completa** ($4,050\text{ m}^3$) y clarificación secundaria. 

La planta procesa un caudal medio de **$753\text{ m}^3\text{/h}$** con una carga orgánica de entrada de **$5,670\text{ kg DBO/día}$** ($317\text{ mg/L}$ DBO y $666\text{ mg/L}$ DQO medios). 

El principal desafío operativo de este tipo de instalaciones reside en el **sistema de sopladores de aireación**, el cual representa entre el **$50\%$ y $65\%$ del consumo eléctrico total de utilidades**. Históricamente, la planta operaba bajo una consigna conservadora de sobre-aireación constante ($DO > 2.5 - 3.5\text{ mg/L}$) por temor a sanciones ambientales del Ministerio de Ambiente (normativa **TULSMA Libro VI Anexo 1: DBO $\le 20\text{ mg/L}$**). 

A pesar del elevado consumo energético, la planta experimentaba **$1,465$ eventos de descarga fuera de norma** ($1.83\%$ del tiempo operativo) debido a la incapacidad del sistema para anticipar las fluctuaciones diurnas de carga contaminante (turnos de producción a las 06:00 y 18:00).

```mermaid
flowchart LR
    A[Afluente Crudo<br/>Q = 753 m³/h<br/>DBO = 317 mg/L] --> T[Pre-tratamiento T-101<br/>Tamiz / Desbaste Grueso]
    T --> DAF[Físico-Químico DAF-102<br/>Flotación Aire Disuelto<br/>Remoción Grasas ≥ 85%]
    DAF -->|Lodo Flotado| L1[Gestión Lodos DAF]
    DAF --> AN[Selector Anóxico R-201A<br/>Pre-desnitrificación<br/>NO₃⁻ → N₂↑]
    AN --> B[Reactor Aerobio R-201B<br/>V = 4,050 m³<br/>MLSS = 3,500 mg/L]
    B --> C[Clarificador Secundario C-301<br/>Decantación de Biomasa]
    C --> D[Efluente Tratado<br/>Norma TULSMA Tabla 9<br/>DBO ≤ 20 mg/L]
    C -->|Recirculación RAS| AN
    C -->|Purga WAS| E[Tratamiento de Lodos]
    F[Sopladores Centrífugos K-201<br/>VFD Modulado // Consumo Crítico] -->|Inyección Aire| B
```

---

## 🔬 2. Metodología de Ingeniería Aplicada

Se implementó una reestructuración operativa basada en la metodología industrial **DMAIC**:

1. **Define & Measure (Balances de Materia):**
   * Auditoría de $80,000$ registros continuos de sensores SCADA a intervalos de 5 minutos.
   * Determinación de parámetros de proceso: Tiempo de Retención Hidráulico ($HRT = 5.38\text{ horas}$), relación Alimento/Microorganismo ($F/M = 0.40\text{ kg DBO/kg MLSS}\cdot\text{d}$) y eficiencia media de remoción ($95.28\%$).
2. **Analyze (Cinética y Lag Analysis):**
   * Análisis de correlación cruzada temporal (*Cross-Correlation*) para medir la inercia del reactor.
   * Modelado de la curva de transferencia de oxígeno: comprobación experimental de la saturación bacteriana de Monod ($K_{DO} \approx 0.2 - 0.5\text{ mg/L}$). Se demostró que operar con $DO > 2.2\text{ mg/L}$ exige un $+35\%$ de caudal de sopladores con una ganancia marginal de remoción inferior a $0.9\text{ mg/L}$ de DBO.
3. **Improve (Sensor Virtual & Optimización de Setpoints):**
   * Dado que los análisis de laboratorio demoran 5 días ($DBO_5$), se desarrolló un **Sensor Virtual (XGBoost Regressor)** con retardos temporales ($1\text{h}, 2\text{h}, 4\text{h}$) que estima la calidad del efluente en tiempo real ($MAE = 1.62\text{ mg/L}$).
   * Redefinición de la consigna óptima de oxígeno disuelto en **$1.8 - 2.2\text{ mg/L}$**, reduciendo la velocidad de los sopladores mediante modulación del variador de frecuencia (VFD).
4. **Control (Estandarización de Planta):**
   * Elaboración del Procedimiento Operativo Estándar formal (`POE-OP-PTAR-001`) con matriz de consignas por turno de operación.
   * Modelo dimensional y medidas DAX para supervisión en Power BI y desarrollo de un Gemelo Digital interactivo en Streamlit.

---

## 📊 3. Resultados Cuantitativos e Impacto Económico

Los resultados anualizados para una tarifa eléctrica industrial estándar de **$\$0.092\text{ USD/kWh}$** se resumen a continuación:

| Indicador Clave de Proceso | Línea Base (Histórica) | Escenario Optimizado | Impacto Técnico / Económico |
|---|:---:|:---:|:---:|
| **Gasto Eléctrico en Sopladores** | $\$215,266\text{ USD/año}$ | $\$206,721\text{ USD/año}$ | **$\mathbf{-\$8,545.23\text{ USD/año}}$ de ahorro neto recurrente** |
| **Consumo Eléctrico de Aireación** | $2,339,852\text{ kWh/año}$ | $2,246,970\text{ kWh/año}$ | **$92,883\text{ kWh/año}$ de energía eléctrica ahorrada** |
| **Consumo Específico (SEC)** | $1.186\text{ kWh/kg DBO}$ | $1.139\text{ kWh/kg DBO}$ | **$+3.97\%$ de mejora en eficiencia energética** |
| **Banda de Oxígeno Disuelto (DO)** | $> 2.5 - 3.5\text{ mg/L}$ | **$1.8 - 2.2\text{ mg/L}$** | **Operación en rango óptimo de Monod** |
| **Cumplimiento Ambiental (TULSMA)** | $122\text{ horas/año}$ fuera de norma | $100\%$ bajo control | **Riesgo legal y multas mitigados a cero** |
| **Reducción de Huella de Carbono** | — | $-39.01\text{ t CO}_2\text{ eq/año}$ | **$39.01\text{ Toneladas de CO}_2$ evitadas al año** |
| **Inversión Requerida (CAPEX)** | — | $\$0\text{ USD}$ (Ajustes SCADA / POE) | **Retorno Inmediato (Payback = 0 meses)** |

---

## 🖥️ 4. Dashboards Ejecutivos de Business Intelligence (Power BI)

El proyecto cuenta con un sistema de doble panel de nivel ejecutivo desarrollado bajo estándares de visualización industrial **ISA-101**, integrando telemetría de planta en tiempo real con auditoría de costos y cumplimiento legal.

### Vista 01: Supervisión SCADA, Control de Operaciones y Calidad de Efluentes
Monitoreo continuo de caudal influyente ($753.05\text{ m}^3\text{/h}$), carga orgánica ($316.97\text{ mg/L}$ DBO), calidad de descarga ($14.74\text{ mg/L}$ DBO) y tasa de cumplimiento del límite máximo permisible TULSMA Libro VI ($98.17\%$).

![Dashboard Vista 01 - Operaciones SCADA](powerbi/capturas_dashboard/dashboard_page_01_operaciones_scada.png)

### Vista 02: Eficiencia Energética, Costos OPEX y Sostenibilidad ESG
Cuadro de mando para la gerencia de planta y directores de operaciones: desglose mensual de facturación eléctrica ($206,721\text{ USD}$ optimizado vs $\$215,266\text{ USD}$ base), ahorro neto anualizado ($+\$8,545\text{ USD}$), curva de histéresis de sobredosis de aireación y descarbonización auditada ($39.04\text{ Ton CO}_2\text{ eq/año}$).

![Dashboard Vista 02 - Eficiencia Energética y Costos](powerbi/capturas_dashboard/dashboard_page_02_energia_opex_esg.png)

---

## 📁 5. Estructura del Repositorio

```text
├── data/
│   ├── README_DATA.md                     # Diccionario técnico y rangos de sensores
│   └── wwtp_time_series_data.csv          # Serie temporal de 80,000 registros (5 min)
├── notebooks/
│   ├── 01_eda_balances_masa.ipynb         # Balances de materia, HRT, cargas diurnas y lags
│   ├── 02_optimizacion_energia.ipynb      # Curva de aireación, setpoint óptimo y Sensor Virtual
│   └── 03_calculo_roi_financiero.ipynb    # Modelado financiero, ROI, SEC y métricas ESG
├── src/
│   ├── modelo_ptar_xgboost.joblib         # Modelo serializado de inferencia
│   └── features_ptar.joblib               # Esquema de características de entrada
├── app/
│   ├── app.py                             # Gemelo Digital / Simulador en Streamlit y Plotly
│   ├── requirements.txt                   # Dependencias para despliegue web
│   └── Procfile                           # Configuración de ejecución en producción (Railway)
├── powerbi/
│   ├── background_pagina_01.png           # Plantilla Canvas Background 1920x1080 (Operaciones)
│   ├── background_pagina_02.png           # Plantilla Canvas Background 1920x1080 (Energía y OPEX)
│   ├── capturas_dashboard/                # Capturas de alta definición del tablero final
│   ├── dataset_ptar_dashboard.csv         # Dataset procesado para Business Intelligence
│   └── especificaciones_dashboard.md     # Medidas DAX y arquitectura de pantallas SCADA
└── entregables_planta/
    └── POE_Control_Operativo_PTAR.md      # Procedimiento Operativo Estándar POE-OP-PTAR-001
```

---

## 💻 5. Instrucciones de Ejecución Local

### Prerrequisitos
Tener instalado Python 3.10 o superior y un gestor de entornos virtuales.

```bash
# 1. Clonar el repositorio
git clone https://github.com/32456344567/01_Optimizacion_PTAR_Efluentes.git
cd 01_Optimizacion_PTAR_Efluentes

# 2. Instalar dependencias
pip install -r app/requirements.txt

# 3. Iniciar el simulador interactivo (Gemelo Digital)
streamlit run app/app.py
```

---
*Documentación técnica de ingeniería desarrollada por Ing. Angelo Apolo.*
