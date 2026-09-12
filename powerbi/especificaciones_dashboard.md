# 📊 ESPECIFICACIONES TÉCNICAS DEL DASHBOARD DE POWER BI
## Monitoreo Operativo de PTAR, Eficiencia Energética y Cumplimiento de Efluentes

* **Archivo de Datos Oficial:** `powerbi/dataset_ptar_dashboard.csv` (80,000 registros con marcas de tiempo, turnos, semáforos y finanzas).
* **Target de Usuario:** Gerencia de Planta, Jefe de Operaciones, Supervisores de Turno e Ingenieros de Medio Ambiente.
* **Paleta de Colores Industrial:**
  * Primario (Operaciones): `#1F77B4` (Azul Técnico)
  * Ahorro / Eficiencia: `#1B9E77` (Verde Sostenible)
  * Alerta Preventiva: `#D95F02` (Naranja Precaución)
  * Incumplimiento Legal: `#D62728` (Rojo Crítico)
  * Fondo: Claro (`#F8F9FA`) con tarjetas blancas y bordes sutiles.

---

## 🧮 1. Diccionario de Fórmulas y Medidas DAX

Crea una tabla dedicada llamada `_Medidas` en Power BI e inserta las siguientes expresiones DAX:

### A. Indicadores de Calidad de Efluentes y Cumplimiento
```dax
// 1. DBO Promedio de Entrada
DBO Entrada Media = 
AVERAGE('dataset_ptar_dashboard'[Influent_BOD_mgL])

// 2. DBO Promedio de Efluente
DBO Efluente Media = 
AVERAGE('dataset_ptar_dashboard'[Effluent_BOD_mgL])

// 3. Eficiencia Promedio de Remoción de DBO (%)
Eficiencia Remocion DBO % = 
VAR BOD_In = [DBO Entrada Media]
VAR BOD_Out = [DBO Efluente Media]
RETURN
DIVIDE(BOD_In - BOD_Out, BOD_In, 0) * 100

// 4. Tasa de Cumplimiento Ambiental TULSMA (%)
Tasa Cumplimiento Ambiental % = 
VAR TotalLecturas = COUNTROWS('dataset_ptar_dashboard')
VAR CumpleNorma = CALCULATE(COUNTROWS('dataset_ptar_dashboard'), 'dataset_ptar_dashboard'[Effluent_BOD_mgL] <= 20.0)
RETURN
DIVIDE(CumpleNorma, TotalLecturas, 0) * 100

// 5. Total de Eventos Fuera de Norma (> 20 mg/L)
Eventos Fuera de Norma = 
CALCULATE(COUNTROWS('dataset_ptar_dashboard'), 'dataset_ptar_dashboard'[Effluent_BOD_mgL] > 20.0)
```

### B. Indicadores de Energía y Balances de Masa
```dax
// 6. Carga Total de DBO Removida (kg)
Carga DBO Removida kg = 
SUM('dataset_ptar_dashboard'[Load_Removed_BOD_kgh]) * (5.0 / 60.0)

// 7. Consumo Eléctrico Base Total (kWh)
Energia Base Total kWh = 
SUM('dataset_ptar_dashboard'[Energy_kWh_Baseline])

// 8. Consumo Eléctrico Optimizado Total (kWh)
Energia Optimizada Total kWh = 
SUM('dataset_ptar_dashboard'[Energy_kWh_Optimized])

// 9. Consumo Específico de Energía Actual (SEC Baseline) [kWh/kg DBO]
SEC Baseline kWh_kg = 
DIVIDE([Energia Base Total kWh], [Carga DBO Removida kg], 0)

// 10. Consumo Específico de Energía Optimizado (SEC Opt) [kWh/kg DBO]
SEC Optimizado kWh_kg = 
DIVIDE([Energia Optimizada Total kWh], [Carga DBO Removida kg], 0)
```

### C. Indicadores Financieros y ESG
```dax
// 11. Costo Eléctrico Línea Base ($ USD)
Costo Base USD = 
SUM('dataset_ptar_dashboard'[Cost_USD_Baseline])

// 12. Costo Eléctrico Optimizado ($ USD)
Costo Optimizado USD = 
SUM('dataset_ptar_dashboard'[Cost_USD_Optimized])

// 13. Ahorro Económico Neto Generado ($ USD)
Ahorro Neto USD = 
[Costo Base USD] - [Costo Optimizado USD]

// 14. Porcentaje de Reducción en Gasto Eléctrico (%)
Ahorro OPEX % = 
DIVIDE([Ahorro Neto USD], [Costo Base USD], 0) * 100

// 15. Emisiones de CO2 Evitadas (Toneladas métricas)
CO2 Evitado Tons = 
(SUM('dataset_ptar_dashboard'[CO2_Reduction_kg])) / 1000.0
```

---

## 🖥️ 2. Arquitectura de Páginas del Dashboard

### Vista 1: Control de Operaciones y Cumplimiento (Piso de Planta / SCADA)
* **Encabezado:** Logo de la empresa, selector de fechas y segmentador de turno (`Shift`: Mañana, Tarde, Noche).
* **Fila Superior de KPIs (Cards):**
  1. `[Caudal Medio Entrada]` ($m^3/h$)
  2. `[DBO Entrada Media]` ($mg/L$)
  3. `[DBO Efluente Media]` ($mg/L$) con formato condicional (Verde si $\le 16$, Amarillo si $16-20$, Rojo si $> 20$).
  4. `[Tasa Cumplimiento Ambiental %]` (Meta: $> 99.0\%$).
* **Panel Central (Gráfico de Líneas Temporal):**
  * Eje X: `Timestamp`.
  * Eje Y: `Effluent_BOD_mgL` y `Aeration_Tank_DO_mgL`.
  * Línea de referencia constante: `20.0 mg/L` (Color Rojo discontinua).
* **Panel Inferior Izquierdo (Sedimentador Secundario):**
  * Gráfico de dispersión: Altura de Manto (`Clarifier_Blanket_Height_m`) vs Purga (`WAS_Flow_m3h`).
* **Panel Inferior Derecho (Distribución de Cumplimiento):**
  * Gráfico de Donut: `Compliance_Status` ('Óptimo', 'Alerta Preventiva', 'Fuera de Norma').

---

### Vista 2: Eficiencia Energética, Costos y Sostenibilidad ESG (Vista Gerencial)
* **Fila Superior de KPIs (Cards Financieras):**
  1. `[Ahorro Neto USD]` (Valor destacado: **+$8,545 USD/año**).
  2. `[Ahorro OPEX %]` (Meta: **~4.0% de reducción en utilidades**).
  3. `[SEC Baseline kWh_kg]` vs `[SEC Optimizado kWh_kg]` (Mejora de $1.186$ a $1.139$).
  4. `[CO2 Evitado Tons]` (**39.0 Toneladas de CO2 eq/año**).
* **Panel Central Izquierdo (Comparativa Mensual):**
  * Gráfico de columnas agrupadas: `Month` en Eje X.
  * Barras: `[Costo Base USD]` (Naranja) vs `[Costo Optimizado USD]` (Verde).
* **Panel Central Derecho (Curva de Sobredosis de Aireación):**
  * Gráfico de dispersión / burbujas: `Aeration_Tank_DO_mgL` vs `Air_Flow_km3h`, destacando la meseta de ahorro cuando $DO$ está en la banda óptima ($1.8 - 2.2\ mg/L$).
* **Panel Inferior (Distribución de Ahorro por Turno):**
  * Gráfico de barras horizontales: Ahorro generado en Turno Noche, Turno Mañana y Turno Tarde.

---

## 📑 3. Generación del Tablero PBIX
1. Conectar Power BI Desktop al archivo procesado: `powerbi/dataset_ptar_dashboard.csv`.
2. Crear la tabla `_Medidas` e incorporar las 15 expresiones DAX detalladas arriba.
3. Configurar la vista SCADA de Operación y la vista Ejecutiva de Costos/ESG según el layout.
4. Guardar el archivo en: `powerbi/dashboard_ptar_operaciones.pbix`.
