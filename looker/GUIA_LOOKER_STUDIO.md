# Looker Studio — una hoja por KPI

Archivo: `looker/DiDi_CX_Looker_Data.xlsx`

| Hoja | Para qué |
|---|---|
| `PAGINA1` | **Página 1 completa**: tarjetas + líneas + filtros Canal y Semana |
| `TOTALES` | Tarjetas fijas 94.14 / 79.95 / 5.83 (no se mueven con filtros) |
| `QA` / `CSAT` / `Recontact` | Página 2: Pareto, control chart, tenure, VOC |
| `CORTES` | Qué filtro existe en cada KPI |
| `COMO_USAR` | Mapa vista → gráfico |

En cada hoja KPI hay una columna `Vista`. **Cada gráfico de página 2 se filtra a una sola Vista.**

---

## Filtros en la página 1 (Canal y Semana)

Looker no tiene un “slicer” mágico para todo el informe. Un control solo mueve gráficos que usan **la misma fuente**. Por eso la página 1 usa solo la hoja `PAGINA1`.

### 1. Añadí la fuente

Recurso → Administrar fuentes de datos añadidas → Añadir → Google Sheets → pestaña **`PAGINA1`**.

### 2. Poné los dos controles (arriba a la derecha, sobre el navy)

Menú **Insertar → Control** (en inglés: *Insert → Control*):

| Control | Tipo | Fuente | Campo de control |
|---|---|---|---|
| Canal | Lista desplegable (*Drop-down list*) | `PAGINA1` | `Channel` |
| Semana | Lista desplegable | `PAGINA1` | `Week` |

Clic en el control → panel derecho **Configuración**:

- Fuente de datos = `PAGINA1`
- Campo de control = `Channel` o `Week`
- Dejá **todos los valores** por defecto (no fuerces un valor). Así, sin tocar nada, ves el periodo completo.

Estilo: fondo blanco, texto navy, borde `#D9DDE3`.

### 3. Los gráficos de esa página también tienen que ser `PAGINA1`

Si las tarjetas salen de `TOTALES`, **no se van a mover** al filtrar. Cambiá la fuente a `PAGINA1`.

**Campos calculados** (en la fuente `PAGINA1`, clic en Añadir un campo):

```
QA Score
SUM(QA_Score_Sum) / SUM(QA_Evaluations)
```

```
CSAT Score
SUM(Satisfied) / SUM(Feedback) * 100
```

```
Recontact Rate
SUM(Recontacts) / SUM(Contacts) * 100
```

Tipo: Número → 1 o 2 decimales. Sin esos campos, Looker promedia tasas de Phone con Self Help y el número queda mal.

| Visual | Dimensión | Métrica |
|---|---|---|
| Tarjeta QA | — | `QA Score` (calculado). Comparación: `QA_Goal` |
| Tarjeta CSAT | — | `CSAT Score` |
| Tarjeta Recontact | — | `Recontact Rate` |
| Línea semanal | `Week` | las 3 métricas calculadas |
| Barras canal | `Channel` | las 3 métricas calculadas |

Sin filtro: **94.14 / 79.95 / 5.83**.  
Canal = Phone: QA baja (~83) y Recontact sube.  
Canal = Self Help: casi no hay QA; Recontact ~1.2%.

### Si un gráfico no se filtra

1. Seleccioná el gráfico → Configuración → Fuente = `PAGINA1` (la misma que el desplegable).
2. El control tiene que estar **en la misma página**.
3. No uses un filtro de gráfico que fije `Channel` o `Week`: pelearía con el desplegable.

Página 2 (Pareto, I-chart, tenure) se queda en las hojas `QA` / `CSAT` / `Recontact`. Esos filtros de página 1 **no** los mueven: el Pareto no es grano semana×canal.

---

## 0. Subir datos

1. Drive (Gmail) → subí `DiDi_CX_Looker_Data.xlsx`.
2. Clic derecho → **Abrir con → Hojas de cálculo de Google**.
3. No edites celdas.

---

## 1. Informe + fuentes

Looker Studio → **Crear → Informe** → Google Sheets → esa Sheet.

Añadí estas pestañas como fuentes (Recurso → Administrar fuentes → Añadir):

`PAGINA1`, `TOTALES`, `QA`, `CSAT`, `Recontact`

En `QA` / `CSAT` / `Recontact`, si `Date` quedó como texto: clic → tipo **Fecha**.

Tema: fondo `#F5F6F8`, acento `#FF6600`, texto `#1A1A1A`.
Lienzo: 1600 × 900.

---

## 2. Cómo se arma un gráfico (siempre igual)

1. Insertar el visual.
2. Fuente = la hoja del KPI (`QA` o `CSAT` o `Recontact`).
3. **Filtro del gráfico** → `Vista` igual a la vista de la tabla de abajo.
4. Dimensión = `Week` / `Date` / `Channel` / `Tenure` / `Categoria` (lo que diga X).
5. Métrica = `Valor` (agregación **Promedio** o **MAX**, nunca Suma, salvo Paretos que sí son conteos).
6. Meta = campo `Meta` (línea de referencia) o segunda métrica.

Para scorecards de periodo en página 2 usá `TOTALES` (no se filtran). En página 1 usá `PAGINA1` + campos calculados.

---

## 3. Tres tarjetas

**Página 1** (se mueven con Canal / Semana): fuente `PAGINA1`, métricas calculadas `QA Score` / `CSAT Score` / `Recontact Rate`. Comparación: `QA_Goal` / `CSAT_Goal` / `Recontact_Goal`.

**Si querés tarjetas fijas** (siempre 94.14 / 79.95 / 5.83): fuente `TOTALES`.

Recontact: más bajo es mejor. Sin filtro tienen que leer **94.14 / 79.95 / 5.83**.

---

## 4. Vistas por hoja

### Hoja `QA` — meta 85

| Vista | Gráfico | X | Y |
|---|---|---|---|
| `00_Scorecard` | Tarjeta (si no usás TOTALES) | — | Valor |
| `01_WoW_semanal` | Línea | Week | Valor + Meta. Etiqueta `WoW_pp` |
| `02_WoW_por_canal` | Línea + filtro Channel | Week | Valor |
| `03_Tendencia_diaria` | Línea | Date | Valor |
| `04_Por_canal` | Barras | Channel | Valor. Phone queda bajo 85 |
| `05_Por_tenure_agente` | Barras | Tenure | Valor. **Solo QA** |
| `06_Control_chart` | Series | Date | Valor, CL, UCL, LCL, Meta |
| `07_Pareto_atributos` | Combinado | Categoria | Valor (barras, Suma) + Cum_Pct (línea 0–100) |
| `08_Histograma` | Barras | Categoria | n |
| `09_Por_CR_Lv4` | Barras | Categoria | Valor |
| `10_Atributos_por_canal` | Barras + filtro Channel | Categoria | Valor |
| `11_Por_agente_n5` | Tabla | Categoria = Agent | Valor. n ≥ 5 |

### Hoja `CSAT` — meta 85

| Vista | Gráfico | X | Y |
|---|---|---|---|
| `01_WoW_semanal` | Línea | Week | Valor + Meta |
| `02_WoW_por_canal` | Línea + filtro Channel | Week | Valor |
| `04_Por_canal` | Barras | Channel | Valor |
| `05_Por_tenure_CSAT` | Barras | Tenure | Valor. **No es el tenure de QA** (`user_tenure`, ~81% `other`) |
| `06_Control_chart` | Series | Date | Valor, CL, UCL, LCL, Meta |
| `07_Por_estrellas` | Barras | Categoria | Valor o Cum_Pct |
| `08_VOC_negativo` | Barras | Categoria | Valor |
| `09_Por_CR_Lv4` | Barras | Categoria | Valor. Mín. 20 encuestas |

### Hoja `Recontact` — meta 5.44 (más bajo es mejor)

| Vista | Gráfico | X | Y |
|---|---|---|---|
| `01_WoW_semanal` | Línea | Week | Valor + Meta |
| `02_WoW_por_canal` | Línea + filtro Channel | Week | Valor. Self Help vs Phone vs Live Chat |
| `04_Por_canal` | Barras | Channel | Valor. Self Help diluye el 5.83 |
| `05_Control_chart` | Series | Date | Valor, CL, UCL, LCL, Meta |
| `06_Pareto_CR` | Combinado | Categoria | Valor (Suma) + Cum_Pct |
| `07_Por_alcance` | Barras | Categoria | Valor. Oficial 5.83 vs Phone+Chat ~15.56 |

---

## 5. Filtros (no mezclar taxonomías)

Un control desplegable de `Channel` en la fuente `QA` **no** mueve CSAT ni Recontact. En Looker el control filtra solo gráficos de la misma fuente, o lo asignás a página.

Tenure de QA (`05_Por_tenure_agente`) y tenure de CSAT (`05_Por_tenure_CSAT`) son campos distintos. No los juntes.

Recontact no tiene tenure.

---

## 6. Compartir

**Compartir → Cualquier usuario con el enlace → Lector.**

Antes de mandar el link: las tres tarjetas dicen **94.14 / 79.95 / 5.83**.
