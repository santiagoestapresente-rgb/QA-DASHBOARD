# DiDi CX Performance Dashboard — Deploy Guide

## Entregable 1: Performance Dashboard

Dashboard interactivo con slicers para el Business Case de CX Quality Analyst.

### KPIs de la semana (W19)

| Métrica | Valor | Meta | Estado |
|---------|-------|------|--------|
| QA Score | 94.14 | ≥ 85 | 🟢 |
| CSAT | 79.95% | ≥ 85% | 🔴 |
| Recontact Rate | 5.83% | ≤ 5.44% | 🟡 |

---

## Opción A — Streamlit Cloud (1 link gratis) ⭐ Recomendada

### Paso 1: Subir a GitHub

```bash
cd C:\Users\PC\Documents\DIDI
git init
git add .
git commit -m "DiDi CX Performance Dashboard"
git remote add origin https://github.com/TU_USUARIO/didi-cx-dashboard.git
git push -u origin main
```

### Paso 2: Deploy en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Conecta tu cuenta de GitHub
3. Selecciona el repo `didi-cx-dashboard`
4. Main file: `app.py`
5. Click **Deploy**

Obtendrás un link como: `https://didi-cx-dashboard.streamlit.app`

### Paso 3: Editar datos

Para actualizar el dashboard con datos nuevos:

1. Reemplaza el Excel en `c:\Users\PC\Downloads\Business Case.xlsx`
2. Ejecuta: `python scripts/process_data.py`
3. Haz commit y push de los CSVs actualizados en `data/`
4. Streamlit Cloud se redeploya automáticamente

---

## Opción B — Looker Studio + Google Sheets (editable en vivo)

Si prefieres que cualquier persona edite datos directamente en Sheets:

1. Abre [Google Sheets](https://sheets.google.com)
2. Importa `data/DiDi_CX_Dashboard_Data.xlsx` (File → Import)
3. Ve a [Looker Studio](https://lookerstudio.google.com)
4. Create → Report → Google Sheets connector
5. Selecciona cada pestaña como fuente de datos
6. Crea visualizaciones con filtros (slicers) por Channel, Country, CR Lv4
7. Share → "Anyone with the link can view"

**Ventaja:** Editas Google Sheets y el dashboard se actualiza al instante.

---

## Correr localmente

```powershell
cd C:\Users\PC\Documents\DIDI
python -m pip install -r requirements.txt
python scripts/process_data.py
streamlit run app.py
```

Abre: `http://localhost:8501`

---

## Estructura del proyecto

```
DIDI/
├── app.py                          # Dashboard Streamlit
├── requirements.txt
├── scripts/
│   └── process_data.py             # Pipeline ETL + métricas
├── data/
│   ├── kpi_summary.csv             # KPIs vs goals
│   ├── qa_by_channel.csv           # QA por canal
│   ├── qa_by_cr.csv                # QA por CR Lv4
│   ├── qa_attributes.csv           # Defectos por atributo
│   ├── csat_by_cr.csv              # CSAT por CR Lv4
│   ├── csat_by_business_type.csv   # CSAT por Business Type
│   ├── recontact_by_cr.csv         # Recontact por CR Lv4
│   ├── combined_analysis.csv       # Análisis cruzado
│   ├── voc_sample.csv              # Voice of Customer
│   └── DiDi_CX_Dashboard_Data.xlsx # Master editable
```

---

## Secciones del dashboard (cumple requisitos del PDF)

| Requisito PDF | Sección del Dashboard |
|---------------|----------------------|
| Overall performance vs goals | Overview — KPI cards |
| QA by channel, CR, attributes | QA Analysis (3 tabs) |
| CSAT segmented + VOC | CSAT / VOC (3 tabs) |
| Recontact patterns | Recontact |
| Combined metric insight | Combined Insights |
| Slicers/filters | Sidebar: Channel, Country, CR Lv4 |

---

## Notas técnicas

- QA Score calculado con fórmula del PDF (no se usa `Score_end_user` directamente)
- Phone attrs: cols W–AH · Live Chat attrs: cols AI–AP
- Critical fail = score 0 · Non-critical fail = −10 pts · N/A (2) excluido
- Colores DiDi: `#FF6600`, `#1A1A1A`, `#FFFFFF`
- Semáforo: 🟢 at/above goal · 🟡 within 5pp · 🔴 >5pp below goal
