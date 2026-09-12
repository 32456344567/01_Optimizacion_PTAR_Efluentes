# Información Oficial del Conjunto de Datos: PTAR & Efluentes

* **Nombre del Dataset:** Wastewater Treatment Time Series
* **Origen / Autor:** Dr. Sayed (Kaggle)
* **Licencia:** CC0: Public Domain
* **Enlace Oficial:** https://www.kaggle.com/datasets/drsayed/wastewater-treatment-time-series

---

## 1. Resumen Ejecutivo y Contexto
Datos reales de sensores en series temporales provenientes de una planta de tratamiento de aguas residuales municipales e industriales mediante el proceso de **lodos activados** (activated sludge process). El conjunto de datos está preparado para la **monitorización continua del proceso, detección de anomalías y pronóstico multivariable**.

Todos los valores están expresados rigurosamente en **unidades métricas internacionales** ($mg/L$, $m^3/h$, $km^3/h$, $mV$, $^\circ C$).

La variable objetivo (*Target*) para modelado predictivo y cumplimiento ambiental es: **`Effluent_BOD_mgL`**.

---

## 2. Características del Dataset
* **Volumen de Filas:** 80,000 registros continuos.
* **Columnas:** 18 (1 marca temporal + 16 características operativas + 1 variable objetivo).
* **Frecuencia Temporal:** Lecturas continuas con marcas de tiempo `YYYY-MM-DD HH:MM:SS`.

---

## 3. Diccionario Detallado de Variables

| # | Nombre de Variable | Descripción Técnica del Parámetro | Rango Típico (Métrico) | Rol Operativo en Planta |
|---|---|---|---|---|
| — | **`Timestamp`** | Fecha y hora exacta de la lectura | `YYYY-MM-DD HH:MM:SS` | Índice temporal |
| 1 | **`Influent_Flow_m3h`** | Caudal de agua residual cruda que ingresa a la planta | 200 – 1200 $m^3/h$ | Carga hidráulica de entrada |
| 2 | **`Influent_BOD_mgL`** | Demanda Bioquímica de Oxígeno en agua cruda | 120 – 450 $mg/L$ | Carga orgánica biodegradable |
| 3 | **`Influent_COD_mgL`** | Demanda Química de Oxígeno en agua cruda | 250 – 900 $mg/L$ | Carga contaminante total |
| 4 | **`Influent_TSS_mgL`** | Sólidos Suspendidos Totales a la entrada | 100 – 500 $mg/L$ | Contenido de sólidos en suspensión |
| 5 | **`Influent_NH4_mgL`** | Concentración de amonio a la entrada | 15 – 60 $mg/L$ | Carga de nitrógeno amoniacal |
| 6 | **`Aeration_Tank_DO_mgL`** | Oxígeno Disuelto en el reactor biológico | 0.5 – 4.5 $mg/L$ | Control del proceso de aireación |
| 7 | **`Aeration_Tank_MLSS_mgL`**| Sólidos Suspendidos en Licor Mezcla | 2000 – 5000 $mg/L$ | Concentración de biomasa activa |
| 8 | **`Aeration_Tank_Temp_C`** | Temperatura en el tanque de aireación | 10 – 28 $^\circ C$ | Cinética de crecimiento bacteriano |
| 9 | **`Air_Flow_km3h`** | Flujo de aire inyectado a los difusores | 2.0 – 12.0 $km^3/h$ | **Consumo de energía de sopladores** |
| 10 | **`RAS_Flow_m3h`** | Caudal de recirculación de lodos activos | 150 – 800 $m^3/h$ | Retorno de biomasa al reactor |
| 11 | **`WAS_Flow_m3h`** | Caudal de purga de lodos excedentes | 2.0 – 20.0 $m^3/h$ | Control de la edad del lodo (SRT) |
| 12 | **`Clarifier_Blanket_Height_m`**| Altura del manto de lodos en clarificador | 0.3 – 2.5 $m$ | Eficiencia de decantación secundaria |
| 13 | **`Clarifier_Overflow_TSS_mgL`**| Sólidos suspendidos en vertedero de salida | 5 – 40 $mg/L$ | Arrastre de biomasa en efluente |
| 14 | **`ORP_mV`** | Potencial de Óxido-Reducción | -200 a +200 $mV$ | Estado anóxico vs. aeróbico |
| 15 | **`pH`** | Potencial de hidrógeno en el licor mezcla | 6.5 – 8.0 | Estabilidad del medio biológico |
| 16 | **`F_M_Ratio`** | Relación Alimento / Microorganismo | 0.05 – 0.40 $kg/kg\cdot d$ | Balance nutricional de bacterias |
| 17 | **`Effluent_BOD_mgL`** | **DBO final en el efluente tratado (TARGET)** | **2 – 25 $mg/L$** | **Cumplimiento de norma ambiental** |

---

## 4. Dinámicas Físicas y Químicas Registradas en los Datos
El autor del conjunto de datos destaca 5 comportamientos dinámicos reales de piso de planta que se deben considerar en el análisis:
1. **Patrón diurno de 24 horas:** Fuertes oscilaciones cíclicas de caudal (`Influent_Flow_m3h`) y carga contaminante vinculadas a los turnos de actividad de la planta.
2. **Eventos de lluvia / dilución:** Caídas bruscas en la concentración de entrada por aportes pluviales o lavados de planta, que alteran la relación $F/M$.
3. **Lazos de control oscilatorios en DO:** Dinámica de control PID/encendido de sopladores que generan fluctuaciones periódicas en el oxígeno disuelto.
4. **Inercia biológica (Edad del Lodo):** La purga de lodos (`WAS_Flow_m3h`) tarda aproximadamente 10 días en reflejar su impacto completo sobre la concentración de sólidos en licor mezcla (`MLSS`).
5. **Efecto estacional de temperatura:** La temperatura del agua modula directamente la velocidad de degradación biológica de la DBO.

---

## 5. Archivo Esperado en esta Carpeta
* Coloca aquí el archivo CSV descargado de Kaggle (por ejemplo: `wastewater_treatment.csv` o similar).
