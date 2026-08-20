# DiDi CX QA Dashboard

Dashboard interactivo para el Business Case CX Quality Analyst.
**Todos los datos provienen del archivo Business Case.xlsx** (tabs QA, CSAT, Recontact).

## Correr localmente

```powershell
cd C:\Users\PC\Documents\DIDI
pip install -r requirements.txt
streamlit run app.py
```

## Datos

La app lee el **snapshot parquet versionado en `data/packaged/`** (0,8 MB, 9 tablas).
Si ese snapshot no existe, reconstruye el modelo desde `data/Business Case.xlsx`.
Todas las rutas son relativas al proyecto, así que funciona igual en local y en la nube.

Si cambias el Excel fuente, regenera el snapshot:

```powershell
python scripts\build_data_artifact.py     # reconstruye data/packaged/*.parquet
python scripts\smoke_test_deploy.py       # valida filas y totales de control
python scripts\smoke_test_app.py          # ejecuta app.py completo sin navegador
```

Totales de control del dataset completo: QA Score **94,14** · CSAT **79,95** ·
Recontact Rate **5,83**.

## Despliegue

Ver [DEPLOY.md](DEPLOY.md) para publicar en Streamlit Community Cloud con repositorio
privado y acceso restringido por correo (el Business Case es confidencial).

## Estructura

```
DIDI/
├── app.py                      # UI Streamlit
├── config.py                   # Metas, colores DiDi y rutas de datos
├── DEPLOY.md                   # Guía de despliegue
├── modules/
│   ├── data_loader.py          # Snapshot parquet + fallback al Excel
│   ├── kpis.py                 # Cálculo de métricas
│   ├── charts.py               # Gráficos Plotly
│   └── recommendations.py      # Recomendaciones (solo datos reales)
├── scripts/
│   ├── build_data_artifact.py  # Genera data/packaged/*.parquet
│   ├── smoke_test_deploy.py    # Verifica la capa de datos
│   └── smoke_test_app.py       # Verifica el render completo de app.py
└── data/
    ├── packaged/               # Snapshot parquet (se despliega con el repo)
    ├── Business Case.xlsx      # Fuente original (fallback)
    └── cache/                  # Caché local, ignorado por git
```

## Secciones

| Página | Contenido |
|--------|-----------|
| **Overview** | 3 KPIs vs meta, volúmenes diarios, WoW, canal, requester, combined CR, action plan |
| **QA Score** | Críticos vs no críticos, Phone/Live Chat, Pareto, CR, tenure, Special project, Type of audit, AHT, supervisor, agentes |
| **CSAT** | Estrellas, VOC, segmentación, user_tenure, Business Type |
| **Recontact** | Tasa oficial, alcance (Self Help diluye), Pareto CR, canal |

## Nota importante

No hay datos simulados. El módulo de "Plan de Acción" genera recomendaciones
basadas en hallazgos reales (scores bajo meta, errores frecuentes, CRs problemáticos).
