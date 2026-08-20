# Guía de armado — DiDi CX Quality Dashboard en Power BI

Todo lo que necesitas está en la carpeta `powerbi/`:

| Archivo | Para qué sirve |
|---|---|
| `DiDi_CX_PowerBI_Model.xlsx` | Modelo estrella listo para importar, 16 hojas |
| `Medidas DAX.docx` | Todas las medidas para copiar y pegar |
| `DiDi_CX_Theme.json` | Tema con la paleta DiDi |
| `Guia de armado - Power BI.docx` | Este documento |

Las versiones `.md` de los dos documentos quedan en la misma carpeta como respaldo:
sirven si necesitas copiar código sin riesgo de que el editor cambie las comillas.

Tiempo estimado: cerca de una hora y cuarto. Los pasos 1 a 4 son mecánicos y toman
quince minutos; el resto es colocar visuales.

Antes de arrancar conviene leer la sección **Preguntas difíciles y cómo responderlas**
del final. Tres de los visuales de este documento existen solo para poder contestar
esas preguntas, y si no sabes qué preguntan, parecen decoración.

---

## Paso 1 — Importar el modelo

1. Abre Power BI Desktop y crea un archivo nuevo.
2. **Inicio → Obtener datos → Excel** y selecciona `DiDi_CX_PowerBI_Model.xlsx`.
3. En el navegador marca estas **trece** hojas:

   - `fact_audit`
   - `fact_audit_attribute`
   - `fact_csat`
   - `fact_recontact`
   - `dim_date`
   - `dim_channel`
   - `dim_cr`
   - `dim_country`
   - `dim_agent`
   - `dim_attribute`
   - `dim_goal`
   - `dim_voc_theme`
   - `dim_recontact_scope`

   No importes `Assumptions`, `Validation` ni `Control_Totals`: son documentación
   para ti, no parte del modelo. Vale la pena leer `Assumptions` completa antes de
   presentar, porque cada fila anticipa una pregunta y trae la cifra del impacto que
   tendría hacer lo contrario.

4. Pulsa **Cargar**. La carga tarda cerca de un minuto por las 76 mil filas de CSAT.

> Guarda el archivo como `DiDi_CX_Quality_Dashboard.pbix` en la carpeta `powerbi/`.

---

## Paso 2 — Aplicar el tema

**Ver → Temas → Buscar temas** y selecciona `DiDi_CX_Theme.json`.

Esto deja los fondos, bordes redondeados, tipografía Segoe UI y la paleta DiDi
aplicados por defecto, así que casi no vas a tener que tocar formato manualmente.

---

## Paso 3 — Crear las relaciones

Ve a la **vista de Modelo**. Power BI habrá detectado algunas relaciones solo;
bórralas todas primero para evitar duplicados y crea estas nueve, todas de
**uno a varios** con dirección de filtro **sencilla** (de la dimensión al hecho):

| Desde (uno) | Hacia (varios) |
|---|---|
| `dim_date[Date]` | `fact_audit[Date]` |
| `dim_date[Date]` | `fact_csat[Date]` |
| `dim_date[Date]` | `fact_recontact[Date]` |
| `dim_channel[Channel_Key]` | `fact_audit[Channel_Key]` |
| `dim_channel[Channel_Key]` | `fact_csat[Channel_Key]` |
| `dim_channel[Channel_Key]` | `fact_recontact[Channel_Key]` |
| `dim_cr[CR_Key]` | `fact_audit[CR_Key]` |
| `dim_cr[CR_Key]` | `fact_csat[CR_Key]` |
| `dim_cr[CR_Key]` | `fact_recontact[CR_Key]` |

Y estas cuatro adicionales:

| Desde (uno) | Hacia (varios) |
|---|---|
| `dim_country[Country_Code]` | `fact_audit[Country_Code]` |
| `dim_country[Country_Code]` | `fact_csat[Country_Code]` |
| `dim_agent[Agent_ID]` | `fact_audit[Agent_ID]` |
| `dim_attribute[Attribute_Key]` | `fact_audit_attribute[Attribute_Key]` |

Y una última, de hecho a hecho:

| Desde (uno) | Hacia (varios) |
|---|---|
| `fact_audit[Audit_ID]` | `fact_audit_attribute[Audit_ID]` |

### Detalle importante

`fact_audit_attribute` también trae columnas `Date`, `Channel_Key` y `CR_Key`, pero
**no las relaciones con las dimensiones**. Los filtros ya le llegan encadenados desde
`dim_date → fact_audit → fact_audit_attribute`. Si creas relaciones directas, Power BI
detecta rutas ambiguas y desactiva algunas.

`dim_country` no se relaciona con `fact_recontact` porque esa pestaña no trae país:
la columna `region_name` vale `SSL` en las catorce mil filas.

`dim_recontact_scope` **queda desconectada a propósito** y no lleva ninguna relación.
Es una tabla de tres filas que sirve de eje para comparar la tasa de recontacto en tres
alcances de canal distintos; la medida `[Recontact Rate by Scope]` arma el filtro de
canal por su cuenta según el valor de `Scope_Key`. Si Power BI le detecta una relación
automática, bórrala: con una relación activa las tres filas devolverían el mismo número.

### Marcar la tabla de fechas

Selecciona `dim_date` → **Herramientas de tabla → Marcar como tabla de fechas** →
columna `Date`. Sin este paso las medidas de comparación semanal no funcionan.

### Crear la jerarquía de motivos de contacto

El business case pide agrupar bajando por `LOB → CR Lv1 → CR Lv4`, así que esa
jerarquía tiene que existir en el modelo y no solo en la cabeza de quien lo arma.

En el panel de campos, clic derecho sobre `dim_cr[LOB]` → **Nueva jerarquía**.
Renómbrala `CR Hierarchy` y arrastra dentro, en este orden, `CR_Lv1` y `CR_Lv4`.

Con eso cualquier visual que use `dim_cr[CR Hierarchy]` en el eje permite bajar de
línea de negocio a categoría y de ahí al motivo puntual con los botones de
exploración en la esquina del visual.

Dos cosas que conviene saber antes de usarla:

- `LOB` tiene un solo valor, `Delivery`, porque la pestaña QA solo cubre esa línea.
  El nivel existe para respetar la jerarquía pedida, no porque agregue variación.
- La pestaña QA no trae `CR Lv1`. Se recupera desde la jerarquía de CSAT y, cuando el
  motivo no está en CSAT, se deduce a partir de su `CR Lv2`, que mapea uno a uno con
  `CR Lv1` sin conflictos. Así quedan 63 de 84 motivos auditados con categoría. La
  columna `CR_Lv1_Source` dice de dónde salió cada valor, y los 21 restantes aparecen
  como `Not mapped` en lugar de inventarles una categoría.

### Ocultar columnas técnicas

Oculta de la vista de informe (clic derecho → Ocultar) las columnas `*_Key` de las
tablas de hechos y `Audit_ID`. Solo generan ruido al armar visuales.

---

## Paso 4 — Crear las medidas

1. **Inicio → Escribir datos**, nombra la tabla `_Measures`, deja una columna vacía
   y pulsa Cargar. Luego borra esa columna desde el panel de campos.
2. Abre `Medidas DAX.docx` y ve creando las medidas en el orden en que aparecen
   (**Inicio → Nueva medida**, pegar, Enter).
3. La sección 7 incluye una **tabla calculada** llamada `Star Rating`; esa se crea con
   **Modelado → Nueva tabla**, no como medida.
4. Después de crear `Star Rating`, relaciónala con `dim_date[Date]`,
   `dim_channel[Channel_Key]`, `dim_cr[CR_Key]` y `dim_country[Country_Code]`, y ordena
   la columna `Rating` por `Rating_Order` (**Herramientas de columna → Ordenar por columna**).

### Verificación rápida

Pon tres tarjetas temporales con `[QA Score]`, `[CSAT Score]` y `[Recontact Rate]` sin
ningún filtro. Deben dar exactamente:

| Medida | Valor esperado |
|---|---|
| QA Score | 94.14 |
| CSAT Score | 79.95 |
| Recontact Rate | 5.83 |

Son los tres números oficiales, y son los que tiene que ver el evaluador en la fila de
KPI. Si cuadran, el modelo está bien montado y puedes borrar las tarjetas de prueba.

La hoja `Control_Totals` del Excel ahora trae cinco filas más, que son las lecturas
alternativas que documentan los hallazgos. Cuando termines las secciones 10 a 12 de las
medidas, estas también tienen que cuadrar:

| Medida | Valor esperado | Qué es |
|---|---|---|
| `[Worst Channel QA Score]` | 83.04 | Phone, el único canal auditado bajo meta |
| `[Best Channel QA Score]` | 96.01 | Live Chat |
| `[Channels Below QA Goal]` | 1 | Cuántos canales auditados no llegan a 85 |
| `[QA Score Source Rubric]` | 86.90 | El score que trae el propio Excel, de referencia |
| `[Recontact Rate Excl Self Help]` | 15.19 | Sin autoservicio |
| `[Recontact Rate Audited Channels]` | 15.56 | Solo Phone + Live Chat |
| `[Retyped Rate %]` | 9.72 | Auditorías tipificadas a otro motivo |

Ninguna de estas reemplaza a las tres oficiales. Si alguna difiere, revisá que la
medida tenga el `REMOVEFILTERS ( dim_channel )` y que no hayas dejado un filtro de
semana puesto.

---

## Paso 5 — Configurar el lienzo

**Ver → Tamaño de página → Personalizado**, ancho `1920`, alto `1080`.
En **Ver → Ajustar página** elige *Ajustar a la página*.

Activa **Ver → Cuadrícula** y **Ajustar objetos a la cuadrícula** para alinear rápido.

Cada visual se posiciona desde el panel **Formato → General → Propiedades → Posición**
escribiendo las coordenadas exactas que aparecen abajo.

---

## Paso 6 — Página 1: CX Quality Overview

Renombra la página como `CX Quality Overview`.

### 6.1 Barra lateral

Inserta un **rectángulo** (Insertar → Formas → Rectángulo):

- Posición `x=0, y=0`, tamaño `210 × 1080`
- Relleno `#0B1F33`, sin borde, sin sombra

Encima coloca cuadros de texto (Insertar → Cuadro de texto):

| Contenido | Posición | Formato |
|---|---|---|
| `DiDi` | `x=16, y=20, w=178, h=32` | Segoe UI Bold 22, color `#FF6600` |
| `CX QUALITY DASHBOARD` | `x=16, y=52, w=178, h=20` | Segoe UI Semibold 9, color `#FFFFFF` |
| `CX Service Operations` | `x=16, y=76, w=178, h=18` | Segoe UI 9, color `#94A3B8` |
| `FILTROS` | `x=16, y=112, w=178, h=16` | Segoe UI Semibold 8, color `#64748B` |

Añade una línea separadora: rectángulo `x=16, y=102, w=178, h=1`, relleno `#1E3A52`.

### 6.2 Segmentaciones

Siete segmentaciones, todas con estilo **Lista desplegable**
(Formato → Configuración de segmentación → Opciones → Estilo).

| Campo | Posición |
|---|---|
| `dim_date[Week]` | `x=16, y=134, w=178, h=52` |
| `dim_channel[Channel_Name]` | `x=16, y=190, w=178, h=52` |
| `fact_audit[LOB]` | `x=16, y=246, w=178, h=52` |
| `dim_cr[CR_Lv4]` | `x=16, y=302, w=178, h=52` |
| `fact_audit[Requester]` | `x=16, y=358, w=178, h=52` |
| `dim_country[Country_Name]` | `x=16, y=414, w=178, h=52` |
| `dim_agent[Agent_ID]` | `x=16, y=470, w=178, h=52` |

En la segmentación de canal, filtra el visual a `dim_channel[Has_QA] = 1` si prefieres
mostrar solo los canales auditados, o déjala completa para poder analizar recontacto
en autoservicio. Recomiendo dejarla completa y explicarlo en la entrevista.

**Semana por defecto.** El business case habla de una semana de operación y el dataset
trae cuatro (W19 a W22). Guarda el archivo con esa misma semana seleccionada en la
segmentación, porque el documento pide consistencia entre los dos entregables y el
evaluador va a comparar cifras entre el reporte y el dashboard. Quitar el filtro
sigue mostrando el mes completo, y las medidas `PW` comparan contra la semana previa,
así que la comparación funciona con una sola semana seleccionada.

Para que cuadren, estas son las cifras por semana:

| Semana | QA Score | CSAT | Recontacto |
|---|---|---|---|
| W19 | 92.36 | 79.19 | 6.04 |
| W20 | 94.85 | 80.15 | 5.98 |
| W21 | 94.17 | 81.02 | 5.81 |
| W22 | 95.46 | 79.45 | 5.26 |
| Período completo | 94.14 | 79.95 | 5.83 |

Ojo con esto: los tres números de control del paso 4 (94.14, 79.95 y 5.83) son los del
período completo, así que verifica el modelo **sin filtro de semana** y recién después
aplica el filtro que corresponda.

### 6.3 Metas y fuentes en la barra lateral

Cuadros de texto:

| Contenido | Posición |
|---|---|
| `METAS DE CALIDAD` | `x=16, y=800, w=178, h=16` |
| `QA Score ≥ 85%` / `CSAT Score ≥ 85%` / `Recontact Rate ≤ 5.44%` | `x=16, y=820, w=178, h=60` |
| `FUENTES DE DATOS` | `x=16, y=900, w=178, h=16` |
| `QA Data` / `CSAT Data` / `Recontact Data` | `x=16, y=920, w=178, h=54` |

Formato: títulos en Segoe UI Semibold 8 color `#64748B`, contenido en Segoe UI 9
color `#CBD5E1`.

### 6.4 Encabezado

| Elemento | Posición | Contenido |
|---|---|---|
| Cuadro de texto | `x=226, y=16, w=700, h=34` | `CX QUALITY OVERVIEW` en Segoe UI Bold 24, color `#1A1A1A` |
| Tarjeta | `x=226, y=52, w=700, h=28` | Medida `[Period Label]`, precedida del texto fijo en el título |
| Tarjeta | `x=1500, y=16, w=250, h=30` | Medida `[Data As Of]`, alineada a la derecha |
| Botón | `x=1770, y=16, w=132, h=30` | Texto `Restablecer filtros` |

Para el subtítulo completo puedes usar una tarjeta con esta medida auxiliar:

```dax
Header Subtitle = "Análisis semanal de CX Service Operations  |  " & [Period Label]
```

En todas las tarjetas del encabezado desactiva el fondo y el borde
(Formato → General → Efectos → Fondo: desactivado, Borde: desactivado).

Línea inferior del encabezado: rectángulo `x=226, y=88, w=1676, h=1`, relleno `#D9DDE3`.

### 6.5 Fila de KPI

Seis tarjetas de `271 × 150`, con separación de 10 px:

| Tarjeta | x | Medida principal | Etiqueta | Color |
|---|---|---|---|---|
| QA Score | 226 | `[QA Score]` | `[QA vs Goal Label]` | `[QA Status Color]` |
| CSAT Score | 507 | `[CSAT Score]` | `[CSAT vs Goal Label]` | `[CSAT Status Color]` |
| Recontact Rate | 788 | `[Recontact Rate]` | `[Recontact vs Goal Label]` | `[Recontact Status Color]` |
| Total Contacts | 1069 | `[Total Contacts]` | `[Contacts WoW Label]` | fijo `#2E6FBE` |
| Total Surveys | 1350 | `[Total Surveys]` | `[Surveys WoW Label]` | fijo `#2E6FBE` |
| QA Evaluations | 1631 | `[QA Evaluations]` | `[Evaluations WoW Label]` | fijo `#2E6FBE` |

Todas en `y=100`.

Cada tarjeta se compone de tres objetos superpuestos. Arma la primera completa y
luego cópiala con Ctrl+C / Ctrl+V cambiando solo las medidas:

1. **Tarjeta principal** — `x=226, y=100, w=271, h=100`, campo `[QA Score]`.
   Título activado con el texto `QA SCORE`, alineado a la izquierda.
   Etiqueta de datos en Segoe UI Bold 26.
2. **Tarjeta de variación** — `x=238, y=178, w=247, h=22`, campo `[QA vs Goal Label]`.
   Fondo y borde desactivados, tamaño 10.
   En **Formato → Etiqueta de datos → Color → fx** elige *Formato por campo* y
   selecciona `[QA Status Color]`. Así el texto se pinta verde, ámbar o rojo solo.
3. **Minigráfico** — gráfico de líneas `x=238, y=202, w=247, h=42`.
   Eje `dim_date[Date_Label]`, valores `[QA Score]`.
   Desactiva ejes, leyenda, títulos, cuadrícula, fondo y borde. Grosor de línea 2.

> Si tu versión de Power BI tiene la **tarjeta nueva** (icono con varias cifras),
> puedes resolver los tres objetos en uno solo: acepta varios campos, etiquetas de
> referencia y minigráfico integrado. Es más rápido, pero el resultado visual es
> equivalente.

Para diferenciar las tres primeras tarjetas —que son las métricas del business case—
añade encima de cada una un rectángulo de `271 × 3` en `y=100` con relleno `#FF6600`.

### 6.5.1 Indicador de dispersión en la tarjeta de QA

El QA Score global es 94.14 y el semáforo queda verde, pero Phone está en 83.04 contra
una meta de 85. Es el hallazgo más importante del dashboard y sin esto no se ve en
ninguna parte de la página 1.

Probé tres caminos y este es el que menos ensucia el diseño: **un cuarto objeto sobre
la tarjeta de QA que solo aparece cuando hay algo que señalar.** La medida
`[QA Dispersion Alert]` devuelve cadena vacía cuando todos los canales cumplen y la
dispersión es menor a 5 pp, así que en un período sano el indicador desaparece solo y la
tarjeta se ve igual que las otras cinco. No hay que condicionar visibilidad ni armar
marcadores.

**Tarjeta de alerta** — `x=380, y=104, w=113, h=16`, campo `[QA Dispersion Alert]`.

- Fondo, borde y sombra desactivados; título desactivado
- Etiqueta de datos en Segoe UI Semibold 7.5, alineada a la derecha
- **Formato → Etiqueta de datos → Color → fx → Formato por campo → `[QA Dispersion Color]`**
- Desactiva el ajuste de texto para que nunca empuje la cifra principal

Con los datos actuales muestra `⚠ Phone 83.0%` en rojo, arriba a la derecha de la
tarjeta, sin tocar el número grande ni la etiqueta de variación.

El texto corto alcanza para que salte a la vista, pero no para explicarlo. El detalle va
en un tooltip de página, que es el paso 6.9.

Lo que **no** hice, y conviene poder justificarlo si te lo preguntan: no toqué
`[QA Status Color]` para que se ponga ámbar cuando un canal está bajo meta. El semáforo
de la tarjeta tiene que responder a la métrica que la tarjeta muestra —el global, que
sí cumple— porque si lo pinto de ámbar con un valor de 94.14 al lado, la tarjeta se
contradice sola y el evaluador pierde la confianza en el resto de los semáforos. La
dispersión es información distinta y va en un objeto distinto.

### 6.6 Fila de análisis principal

**Panel A — Metrics Trend (Daily)**
Gráfico de **líneas**, `x=226, y=262, w=700, h=310`.

- Eje X: `dim_date[Date_Label]`
- Valores: `[QA Score]`, `[CSAT Score]`
- Eje Y secundario: `[Recontact Rate]`
- Título: `METRICS TREND — DAILY`
- Colores: QA `#2E9B57`, CSAT `#2E6FBE`, Recontact `#D64545`
- Eje Y principal fijo de 0 a 100, secundario de 0 a 10
- En **Analytics** agrega dos líneas constantes punteadas en `85` (eje principal) y
  `5.44` (eje secundario), color `#CBD5E1`
- Leyenda arriba a la izquierda

Los dos ejes separados son deliberados: recontacto se mueve entre 5 y 6 por ciento
mientras QA y CSAT viven cerca de 80 a 95, y compartir escala aplastaría la línea roja.

**Panel B — Performance by Channel y por Requester**
Dos **tablas** apiladas.

Tabla superior, `x=938, y=262, w=480, h=170`:

- Filas: `dim_channel[Channel_Name]`
- Columnas: `[QA Score]`, `[QA vs Goal]`, `[QA Evaluations]`,
  `[Channel Share of Audits %]`, `[CSAT Score]`, `[CSAT vs Goal]`,
  `[Recontact Rate]`, `[Recontact vs Goal]`
- Filtro del visual: `dim_channel[Has_QA] = 1` para dejar solo Phone y Live Chat
- Activa **Total** para que aparezca la fila Overall
- Formato condicional de color de fuente en cada columna `vs Goal` usando
  *Formato por campo* con las medidas de color correspondientes
- Ordena ascendente por `[QA Score]` para que Phone quede arriba
- Título: `PERFORMANCE BY CHANNEL`

Las dos columnas de volumen son la parte importante y no estaban antes. Sin ellas la
tabla muestra que Phone saca 83.04 y Live Chat 96.01, pero no explica por qué el total
da 94.14 y no algo cerca del medio: Live Chat es el 85.6% de las auditorías, así que el
promedio ponderado se apoya casi entero en ese canal. Con las cuatro columnas juntas la
lectura se sostiene sola y no hace falta que la expliques de memoria.

Poner Phone en la primera fila es deliberado. Es el único canal bajo meta y la fila
`Overall` de abajo va a mostrar 94.14 en verde, así que el contraste entre las dos
queda a la vista en el mismo visual.

Tabla inferior, `x=938, y=440, w=480, h=132`:

- Filas: `fact_audit[Requester]`
- Columnas: `[QA Score]`, `[CSAT Score]`, `[Recontact Rate]`
- Título: `PERFORMANCE BY REQUESTER TYPE`

En el dataset esta tabla devuelve una sola fila, `Customer`, porque no existen las
categorías Rider, Driver ni Merchant. Es un hallazgo válido: agrega debajo un cuadro
de texto pequeño que lo diga en lugar de inventar segmentos.

**Panel C — Recontact by CR Lv4**
Gráfico de **anillo**, `x=1430, y=262, w=472, h=310`.

- Leyenda: `dim_cr[CR_Lv4]`
- Valores: `[Recontact Volume]`
- Filtro: **N superior**, 6 elementos por el mismo valor
- Etiquetas de detalle: porcentaje del total
- Título: `RECONTACT VOLUME BY CR LV4`

### 6.7 Segunda fila de análisis

**Panel D — Top Failing QA Attributes**
Gráfico de **barras agrupadas** horizontal, `x=226, y=584, w=700, h=340`.

- Eje Y: `dim_attribute[Attribute_Name]`
- Eje X: `[% of Total Fails]`
- Filtro: N superior, 8 elementos por `[Attribute Fails]`
- Orden descendente por `[Attribute Fails]`
- Color de datos con **fx → Formato por campo → `[Critical Attribute Color]`**, que
  pinta de rojo los atributos críticos y de azul el resto
- Información sobre herramientas: agrega `[Attribute Fail Rate]` y `[Impact on QA Score pp]`
- Título: `TOP FAILING QA ATTRIBUTES`

Debajo, cuadro de texto en `x=238, y=898, w=676, h=18`, Segoe UI cursiva 8, color
`#94A3B8`:

> Un fallo en cualquier atributo crítico deja la interacción en cero puntos. Las barras rojas son atributos críticos.

**Panel E — QA Score by CR Lv4**
Gráfico de **barras agrupadas** horizontal, `x=938, y=584, w=480, h=340`.

- Eje Y: la jerarquía `dim_cr[CR Hierarchy]` completa, no la columna suelta.
  Baja el visual hasta el nivel `CR_Lv4` con el botón de doble flecha para que abra
  mostrando el motivo puntual; los botones de exploración quedan disponibles para
  subir a `CR Lv1` durante la presentación y mostrar qué categoría concentra el
  problema antes de aterrizar en el motivo
- Eje X: `[QA Score]`
- Filtro: N inferior, 10 elementos por `[QA Score]`, más un filtro
  `[QA Evaluations] >= 3` para evitar motivos con una sola auditoría
- Orden ascendente: los peores arriba
- Color con **fx → Formato por campo → `[QA Status Color]`**
- En **Analytics** agrega una línea constante en `85`, color `#64748B`, punteada,
  con etiqueta `Meta 85%`
- Eje X fijo de 0 a 100
- Título: `QA SCORE BY CONTACT REASON (CR LV4)`

**Panel F — CSAT y voz del cliente**
Dos visuales dentro del mismo bloque.

Gráfico de **barras** horizontal, `x=1430, y=584, w=472, h=180`:

- Eje Y: `'Star Rating'[Rating]`
- Eje X: `[Star Share %]`
- Color con **fx → Formato por campo → `[Star Bar Color]`**
- Título: `CSAT BY STAR RATING`

**Tabla**, `x=1430, y=772, w=472, h=152`:

- Filas: `fact_csat[VOC_Theme]`
- Columnas: `[Negative VOC Share %]`, `[Negative VOC Mentions]`
- Filtro: excluir `Not classified`, N superior 6 por menciones
- Título: `TOP THEMES IN NEGATIVE FEEDBACK (1–3 ★)`

### 6.8 Banner ejecutivo

Rectángulo de fondo: `x=226, y=936, w=1676, h=104`, relleno `#0B1F33`,
esquinas redondeadas 10, sin borde.

Encima:

| Elemento | Posición | Contenido |
|---|---|---|
| Rectángulo | `x=246, y=956, w=26, h=26` | Relleno `#FF6600`, radio 5 |
| Texto | `x=250, y=958, w=20, h=20` | `!` en blanco, negrita, centrado |
| Texto | `x=286, y=952, w=300, h=14` | `KEY OPERATIONAL INSIGHT`, Segoe UI Semibold 8, color `#FF6600` |
| Tarjeta | `x=286, y=966, w=1400, h=24` | Medida `[Key Operational Insight]`, Segoe UI 11, color `#E2E8F0` |
| Texto | `x=286, y=992, w=300, h=14` | `RECOMMENDED ACTION`, Segoe UI Semibold 8, color `#FF6600` |
| Tarjeta | `x=286, y=1006, w=1400, h=22` | Medida `[Recommended Action]`, Segoe UI 10, color `#E2E8F0` |

En las dos tarjetas desactiva fondo, borde y sombra, y activa el ajuste de texto.

Con el período completo sin filtros, el banner tiene que abrir hablando de Phone, no de
recontacto. La primera rama de `[Key Operational Insight]` es el caso "un canal está
bajo meta aunque el global no lo esté", y va primero porque es el único hallazgo que no
se ve en ninguna tarjeta de KPI: los incumplimientos globales ya se anuncian solos con
el semáforo en ámbar o rojo. Si al filtrar una semana el banner cambia de tema, es
porque cambió qué está fallando; eso es lo que tiene que hacer.

### 6.9 Tooltip de página para la tarjeta de QA

El indicador del paso 6.5.1 avisa que hay dispersión, pero no la explica. El detalle va
en una página de tooltip, que es la forma limpia de agregar profundidad sin gastar
lienzo: aparece al pasar el mouse por la tarjeta y no ocupa nada mientras no se use.

1. Nueva página, nómbrala `Tooltip — QA por canal`.
2. **Formato de página → Información de página → Permitir su uso como información
   sobre herramientas: activado.**
3. **Formato de página → Tamaño de lienzo → Tipo: Información sobre herramientas**, y
   ajusta a `340 × 260`.
4. Marca la página como oculta (clic derecho en la pestaña → Ocultar página).

Dentro pon tres objetos:

| Elemento | Posición | Contenido |
|---|---|---|
| Cuadro de texto | `x=12, y=10, w=316, h=16` | `QA SCORE POR CANAL`, Segoe UI Semibold 9, color `#64748B` |
| Tabla | `x=12, y=30, w=316, h=110` | Filas `dim_channel[Channel_Name]`, columnas `[QA Score]`, `[QA vs Goal]`, `[QA Evaluations]`, `[Channel Share of Audits %]`. Filtro `dim_channel[Has_QA] = 1`, orden ascendente por `[QA Score]`, color de fuente de `[QA vs Goal]` atado a `[QA Status Color]` |
| Tarjeta | `x=12, y=148, w=316, h=100` | Medida `[Worst Channel Alert]`, Segoe UI 9, ajuste de texto activado, fondo y borde desactivados |

Después selecciona la **tarjeta principal de QA Score** de la página 1 y ve a
**Formato → General → Información sobre herramientas → Tipo: Página de informe →
Página: `Tooltip — QA por canal`**. Repite en el minigráfico de la misma tarjeta para
que el tooltip aparezca en todo el bloque.

Alternativa si preferís no usar tooltips: la misma tabla entra en la página 2 como
visual fijo. Es más robusto para presentar en PDF, pero gasta espacio en una página que
ya está cargada. Yo dejaría el tooltip y además la tabla de la página 2, que es lo que
está armado más abajo.

---

## Paso 7 — Páginas de profundidad

El resto del análisis no cabe en una sola página sin saturarla, así que va en tres
páginas adicionales. Copia la barra lateral y el encabezado de la página 1 en cada una
para mantener la consistencia, y sincroniza las segmentaciones
(**Ver → Sincronizar segmentaciones**, marca las cuatro páginas en visible y sincronizado).

### Página 2 — QA Deep Dive

| Visual | Tipo | Contenido |
|---|---|---|
| Pareto de defectos | Columnas y líneas | Eje `dim_attribute[Attribute_Name]`, columnas `[Attribute Fails]`, línea `[Cumulative % of Fails]` en eje secundario de 0 a 100 |
| QA por canal | Tabla | Filas `dim_channel[Channel_Name]`, columnas `[QA Score]`, `[QA vs Goal]`, `[Critical Fail Rate]`, `[QA Evaluations]` |
| Atributos por canal | Matriz | Filas `dim_attribute[Attribute_Name]`, columnas `dim_channel[Channel_Name]`, valores `[Attribute Fail Rate]` |
| Atributos por motivo | Matriz | Filas `dim_cr[CR_Lv4]`, columnas `dim_attribute[Attribute_Name]`, valores `[Attribute Fails]` |
| Impacto en el score | Tabla | Filas `dim_attribute[Attribute_Name]`, columnas `[Attribute Fails]`, `[% of Total Fails]`, `[Impact on QA Score pp]` |
| Desempeño por agente | Tabla | Filas `dim_agent[Agent_ID]`, `dim_agent[Supervisor_ID]`, `dim_agent[Tenure_Cohort]`, columnas `[QA Score]`, `[QA Evaluations]`, `[Critical Fail Rate]`, filtrada a `[QA Evaluations] >= 5` |
| Atributos por agente | Matriz | Filas `dim_agent[Agent_ID]`, columnas `dim_attribute[Attribute_Name]`, valores `[Attribute Fails]`, filtrada a `[Attribute Fails] >= 1` |

En la matriz de atributos por canal vas a ver celdas vacías: es correcto, porque
Phone y Live Chat usan listas de atributos distintas y nunca se mezclan.

#### Bloque de brecha entre canales

Estos cuatro objetos son los que sostienen el hallazgo principal cuando el evaluador
baja de la página 1 a pedir el detalle.

| Visual | Tipo | Contenido |
|---|---|---|
| Alerta de canal | Tarjeta | Medida `[Worst Channel Alert]`, ajuste de texto activado, ancho completo del bloque |
| Brecha por canal | Barras horizontales | Eje `dim_channel[Channel_Name]` filtrado a `Has_QA = 1`, valor `[QA Score]`, línea constante en `85` con etiqueta `Meta 85%`, color con **fx → `[QA Status Color]`** |
| Dispersión | Tarjetas | `[Channel QA Spread pp]` y `[Channels Below QA Goal]` |
| Efecto del peso | Tarjetas | `[QA Score]` y `[QA Score Simple Channel Average]`, con un cuadro de texto abajo que aclare qué es cada una |

El par de tarjetas del último visual es el que cierra la discusión: 94.14 es el promedio
real y 89.53 es lo que daría si los dos canales pesaran igual. La diferencia es el efecto
del volumen de Live Chat, y tenerlo como número evita la sensación de que el promedio se
eligió para que quedara bien. Ponele al lado un cuadro de texto que diga que la primera
es la métrica oficial y la segunda solo sirve para medir el sesgo de la mezcla, porque
sueltas se pueden confundir.

#### Tipificación del motivo de contacto

`CR_registrada` es el motivo con el que se abrió la interacción y `CR_correcta` el que el
auditor determinó que correspondía. La diferencia entre las dos es un hallazgo de negocio
aprovechable, pero hay que medirla bien.

| Visual | Tipo | Contenido |
|---|---|---|
| Estado de tipificación | Anillo | Leyenda `fact_audit[CR_Typing_Status]`, valores `[QA Evaluations]`, etiquetas con porcentaje del total |
| Impacto en calidad | Tarjetas | `[Retyped Rate %]`, `[Retyping QA Gap pp]` |
| Nota | Tarjeta | Medida `[Retyping Note]`, ajuste de texto activado |
| Confusiones más frecuentes | Matriz | Filas `fact_audit[CR_Registered_Raw]`, columnas `dim_cr[CR_Lv4]`, valores `[QA Evaluations]`, filtro del visual `fact_audit[Is_Retyped_CR] = 1`, formato condicional de fondo en escala de color |

Cuidado con esto, porque es fácil quedar mal: comparar las dos columnas como texto crudo
da un 47.20% de diferencias, y es tentador presentarlo como "casi la mitad de las
interacciones se tipifica mal". No es cierto. El 37.48% de esas diferencias es solo
mayúsculas y espacios —`incomplete order` contra `Incomplete order`— porque las dos
columnas no comparten convención de escritura. La tipificación realmente incorrecta, la
que manda la interacción a otro motivo, es del **9.72%**. El anillo muestra las tres
categorías separadas justamente para que la cifra que se lee sea la correcta.

Un 9.72% sigue siendo material: una de cada diez interacciones se tipifica a un motivo
distinto del que correspondía, y eso desvía todo el análisis por CR Lv4 además del
enrutamiento del caso. Las auditorías mal tipificadas promedian 91.97 de QA contra 94.38
del resto, así que el error de tipificación viaja junto con interacciones de peor calidad.
La matriz de confusiones es la que da material para el plan de acción, porque muestra qué
pares de motivos se confunden entre sí.

No armes nada sobre `SUB_CR_registrada` contra `SUB_CR_correcta`: difieren en el 99.88%
de las filas, lo que indica que las dos columnas usan taxonomías distintas y no que la
operación se equivoque siempre. No es medible con lo que hay.

#### Nuestro score contra el del Excel

| Visual | Tipo | Contenido |
|---|---|---|
| Comparación de método | Tarjetas | `[QA Score]`, `[QA Score Source Rubric]`, `[QA Score Method Gap pp]`, `[Score Agreement %]` |
| Explicación | Tarjeta | Medida `[Scoring Method Note]`, ajuste de texto activado |
| Adherencia al proceso | Barras | Eje `fact_audit[Process_Adherence]`, valor `[QA Evaluations]` |
| Auditorías limpias con score 0 en el origen | Tarjeta | Medida `[All Attributes Pass Scored Zero by Source]` |

Rotula la tarjeta de `[QA Score]` como `SCORE OFICIAL (BUSINESS CASE)` y la de
`[QA Score Source Rubric]` como `SCORE DEL ORIGEN (REFERENCIA)`. Sin esos rótulos las dos
cifras juntas son una ambigüedad, y la ambigüedad en una tarjeta de KPI es peor que no
mostrar el dato. El detalle de por qué difieren está en la sección de preguntas difíciles
del final.

Las dos matrices nuevas son las que responden la parte del business case sobre qué
patrones aparecen entre agentes y motivos de contacto, no solo cuáles son los
atributos con más fallas en total. En la de motivos conviene aplicar formato
condicional de fondo en escala de color sobre `[Attribute Fails]` y filtrar a los
20 motivos que acumulan diez fallas o más; por debajo de eso el patrón es ruido.
En la de agentes, la lectura útil es la columna: si un mismo atributo se repite en
muchos agentes es un problema de proceso o de capacitación, y si se concentra en unos
pocos es un caso de coaching individual.

### Página 3 — CSAT y voz del cliente

| Visual | Tipo | Contenido |
|---|---|---|
| Distribución de estrellas | Barras | `'Star Rating'[Rating]` con `[Star Responses Count]` |
| CSAT por canal | Barras | `dim_channel[Channel_Name]` con `[CSAT Score]`, línea constante en 85 |
| CSAT por motivo | Barras | `dim_cr[CR_Lv4]`, N inferior 10 por `[CSAT Score]`, filtrado a `[Survey Responses] >= 20` |
| CSAT por país | Barras | `dim_country[Country_Name]` con `[CSAT Score]` |
| CSAT por tipo de negocio | Tabla | Filas `fact_csat[Business_Type]`, columnas `[CSAT Score]`, `[CSAT vs Goal]`, `[Survey Responses]`, con el color de fuente de la variación atado a `[CSAT Status Color]` |
| Temas negativos | Barras | `fact_csat[VOC_Theme]` con `[Negative VOC Mentions]` |
| Comentarios | Tabla | `fact_csat[VOC_Text]`, `fact_csat[VOC_Theme]`, `dim_cr[CR_Lv4]`, filtrada a encuestas negativas |

El filtro de volumen mínimo evita que un motivo con tres encuestas aparezca como el
peor del mes. Es el mismo criterio que aplicarías en un reporte real.

La tabla por tipo de negocio es la que sostiene los planes de acción por línea de
negocio del reporte escrito. `Business_Type` es la única dimensión de negocio con
variación real en el dataset —`LOB` es siempre Delivery— y separa Food, Full Service,
Market Place, Pickup y Other. Ahí aparece el contraste más fuerte de toda la página:
Food y Full Service rondan el 80% con decenas de miles de encuestas, mientras que
Other cae a la mitad con quinientas y pico. Pickup tiene 35 respuestas, así que
menciónalo como no concluyente en lugar de tratarlo como un hallazgo.

### Página 4 — Recontacto y análisis combinado

| Visual | Tipo | Contenido |
|---|---|---|
| Recontacto por alcance | Barras | Ver el bloque de abajo |
| Recontacto por motivo | Barras | `dim_cr[CR_Lv4]` con `[Recontact Rate]`, N superior 10 por volumen, línea constante en 5.44 |
| Recontacto por canal | Barras | `dim_channel[Channel_Name]` con `[Recontact Rate]` y `[Total Contacts]` |
| Ruta del recontacto | Matriz | Filas `fact_recontact[Prev_Channel_Name]`, columnas `dim_channel[Channel_Name]`, valores `[Recontact Volume]` con formato condicional de fondo en escala de color |
| Rutas principales | Barras | Eje `fact_recontact[Contact_Route]`, valor `[Route Share of Recontacts %]`, N superior 8 por `[Recontact Volume]` |
| Cambio de canal | Tarjetas | `[Cross-Channel Recontact %]` y `[Self-Service Escalation %]` |
| Análisis combinado | Tabla | Filas `dim_cr[CR_Lv4]`, columnas `[CR Risk Pattern]`, `[QA Score]`, `[QA vs Goal]`, `[CSAT Score]`, `[CSAT vs Goal]`, `[Recontact Rate]`, `[Recontact vs Goal]`, `[Total Contacts]`. Filtro del visual `[CR Risk Count] >= 2`, ordenada por `[Total Contacts]` descendente |
| QA contra CSAT | Dispersión | Eje X `[QA Score]`, eje Y `[CSAT Score]`, detalles `dim_cr[CR_Lv4]`, tamaño `[Survey Responses]`. Activa la línea de tendencia en Analytics |
| Hipótesis | Tarjeta | Medida `[Root Cause Hypothesis]` |
| Plan de acción | Tabla | Ver nota abajo |

#### Bloque de alcance del denominador

Este es el bloque que hay que armar primero en la página, arriba a la izquierda, porque
cambia cómo se lee todo lo demás.

La tasa oficial es 5.83% contra una meta de 5.44%: apenas 0.39 pp arriba, que suena a
problema menor. Pero el denominador incluye los doce canales, y **Self Help aporta el 67%
de los contactos con una tasa de recontacto de 1.22%**. Un canal donde el cliente se
atiende solo, con muchísimo volumen y casi ningún recontacto, arrastra el total hacia
abajo. Medida solo sobre los canales que QA audita, la tasa es 15.56%.

| Visual | Tipo | Contenido |
|---|---|---|
| Tasa por alcance | Barras horizontales | Eje `dim_recontact_scope[Scope_Name]`, valor `[Recontact Rate by Scope]`, línea constante en `5.44` con etiqueta `Meta 5.44%` |
| Volumen por alcance | Tooltip del visual anterior | Agrega `[Contacts by Scope]` y `[Scope vs Goal by Scope]` a Información sobre herramientas |
| Tasa en canales auditados | Tarjeta | `[Recontact Rate Audited Channels]` con `[Recontact Audited vs Goal]` abajo, color de fuente atado a `[Recontact Audited Status Color]` |
| Dilución | Tarjeta | Medida `[Recontact Scope Note]`, ajuste de texto activado, ancho completo |
| Peso del autoservicio | Tarjetas | `[Self Help Share of Contacts %]` y `[Self Help Recontact Rate]` |

En el eje ordena por `dim_recontact_scope[Scope_Order]` (**Herramientas de columna →
Ordenar por columna**) para que el alcance oficial quede siempre primero. La barra de
`Los 12 canales (oficial)` es la única que queda cerca de la línea de meta; las otras dos
se van a 15 y pico, y ese salto visual es todo el argumento.

Tres cosas que hay que tener claras al presentar esto:

- **El KPI de la página 1 no se toca.** 5.83% sigue siendo el número oficial y es el que
  va en la tarjeta. Este bloque es contexto, no un reemplazo, y presentarlo como
  corrección sería pasarse de la raya: la meta puede haberse definido perfectamente sobre
  todos los canales.
- **Lo que no sabemos es sobre qué canales se fijó la meta de 5.44%.** El business case da
  el número sin decirlo. Por eso las tres barras se comparan contra la misma línea y el
  visual no inventa una segunda meta.
- **Las medidas de alcance ignoran la segmentación de canal a propósito.** Si filtrás
  Phone en la barra lateral, este visual no cambia. Es correcto: compara alcances fijos.
  Vale aclararlo con un cuadro de texto chico debajo para que no parezca un visual roto.

También conviene tener a mano `[Recontact Anomaly Impact pp]`: el modelo marca 111 filas
donde el volumen de recontacto supera los contactos, todas de GPTBot, y 249 filas con cero
contactos. Excluirlas mueve la tasa −0.14 pp, así que se quedan y el total sigue siendo
reproducible desde la fuente. Si te preguntan por la calidad del dato, la respuesta es un
número, no un encogimiento de hombros.

Un detalle si llegás a poner `fact_recontact[Data_Quality_Flag]` en un visual: las dos
condiciones se solapan en 59 filas, porque una fila con cero contactos y algo de volumen
cumple las dos. El flag asigna primero `Zero contacts recorded`, así que la etiqueta
`Recontact volume exceeds contacts` muestra 52 y no 111. Son 301 filas distintas en total
sobre 14.095. El conteo crudo de 111 y el de la etiqueta no tienen por qué coincidir, y
`[Recontact Anomaly Rows]` devuelve las 301.

#### Ruta del recontacto

Los tres visuales de ruta son los que contestan la pregunta del business case sobre
dónde vuelve a contactar el cliente y qué dice eso del proceso. El dato duro: el 61%
de los recontactos llega por un canal distinto al original, y la segunda ruta más
grande de todas es Self Help hacia Live Chat, con 16.180 contactos y un 28% del total.
Sumando todas las rutas que salen de un canal sin agente hacia Phone o Live Chat, el
38% de los recontactos son escalamientos desde autoservicio: el cliente intentó
resolver solo, no pudo, y terminó ocupando a un agente. Eso no es un problema de
calidad de la atención sino de cobertura del autoservicio, y es un hallazgo distinto
al que se ve mirando solo la tasa de recontacto.

En la matriz, la diagonal es el recontacto dentro del mismo canal —39% del total— y
todo lo que queda fuera de la diagonal es traspaso entre canales. Vale la pena dejarla
con formato condicional de fondo para que las celdas gruesas salten a la vista sin
tener que leer los números.

La dispersión solo tiene sentido sobre los motivos que existen en las tres pestañas.
Aplica el filtro `dim_cr[Coverage] = "All three metrics"`; son 46 de 110 motivos y
está documentado en la hoja `Assumptions`.

Junto a la línea de tendencia añade un cuadro de texto aclarando que se trata de una
asociación observada entre motivos de contacto, no de una relación causal.

**Plan de acción.** Es el único contenido que no sale de una medida, porque son
decisiones tuyas derivadas de los hallazgos. Crea una tabla manual con
**Inicio → Escribir datos**, nómbrala `Action Plan` con las columnas `Hallazgo`,
`Acción`, `Responsable`, `Prioridad` y `Plazo`, y llénala con lo que muestren los
visuales. Redáctalo después de armar todo, cuando ya veas los números finales.

---

## Paso 8 — Botón de restablecer filtros

1. **Ver → Marcadores → Agregar** sin ningún filtro aplicado. Nómbralo `Reset`.
2. Clic derecho en el marcador → desmarca *Datos* y deja marcado *Filtros actuales*
   y *Todos los objetos visuales*.
3. Selecciona el botón del encabezado → **Formato → Acción → Tipo: Marcador →
   Marcador: Reset**.

---

## Paso 9 — Revisión final

- [ ] Los tres números de control cuadran: 94.14, 79.95 y 5.83
- [ ] Las siete medidas de la tabla de verificación ampliada también cuadran
- [ ] Todas las segmentaciones filtran los visuales de la página
- [ ] Recontacto no reacciona al filtro de país, y sabes explicar por qué
- [ ] Los semáforos usan las medidas de color y no colores fijos
- [ ] Las líneas de meta aparecen en tendencia, QA por motivo y recontacto por motivo
- [ ] Ningún visual muestra el mensaje de más datos necesarios
- [ ] El banner ejecutivo abre hablando de Phone sin filtros aplicados
- [ ] El indicador de dispersión muestra `⚠ Phone 83.0%` en rojo sobre la tarjeta de QA
- [ ] El tooltip de la tarjeta de QA abre y muestra los dos canales ordenados
- [ ] `dim_recontact_scope` no tiene ninguna relación en la vista de modelo
- [ ] El visual de alcance muestra tres barras distintas y no tres veces 5.83
- [ ] Las tarjetas de score llevan rótulo de cuál es la oficial y cuál la de referencia
- [ ] El panel E sube y baja por la jerarquía `LOB → CR Lv1 → CR Lv4`
- [ ] La matriz de ruta suma lo mismo que el volumen total de recontacto
- [ ] El archivo queda guardado con `W22` seleccionada en la segmentación de semana

---

## Limitaciones del dataset

Anótalas para la entrevista: reconocer los límites de los datos es parte del trabajo
de un analista de calidad, y aquí hay doce que vale la pena mencionar.

| Tema | Situación |
|---|---|
| Tipo de solicitante | Todas las filas son `Customer`. No hay Rider, Driver ni Merchant. |
| Línea de negocio | La pestaña QA solo contiene `Delivery`, así que el nivel `LOB` de la jerarquía no aporta variación. El corte de negocio con variación real es `Business_Type` en CSAT. |
| CR Lv1 | La pestaña QA no lo trae. Se recupera desde CSAT y se deduce por `CR Lv2` donde falta; quedan 63 de 84 motivos auditados con categoría y 21 como `Not mapped`. El 5.9% de las auditorías no obtiene nivel. |
| País en recontacto | `region_name` vale `SSL` siempre, así que no se puede abrir por mercado. |
| Cobertura de canales | Recontacto cubre doce canales; QA solo audita Phone y Live Chat. |
| Muestra de Phone | Phone son 355 de 2.460 auditorías (14.4%), así que su score se mueve sobre una base mucho más chica que Live Chat. |
| Motivos comparables | Solo 46 de 110 motivos existen en las tres pestañas, y el 19.1% de las auditorías no tiene contraparte en CSAT. |
| Texto de la encuesta | `open_question` viene como `Other` en el 89.3% de las filas; los temas salen del 10.7% restante. |
| Duplicados en CSAT | 5.954 filas redundantes (7.76%) dentro de 10.752 filas byte-idénticas, todas con `Feedback CNT = 1`. Se mantienen; deduplicar daría 78.57%. |
| Anomalías de recontacto | 111 filas con volumen mayor a los contactos, todas de GPTBot, y 249 con cero contactos; 301 filas distintas porque las dos condiciones se solapan. Impacto de −0.14 pp si se excluyeran. |
| Score del origen | La columna `Score_end_user` del Excel promedia 86.90 contra los 94.14 del cálculo del business case, porque usa una rúbrica ponderada. |
| Adherencia al proceso | El origen la penaliza pero no está en las columnas de atributos, así que ningún score reconstruido desde ellas puede reproducir el del origen. |

Todas están documentadas en la hoja `Assumptions` del Excel del modelo, con la cifra del
impacto que tendría resolverlas de otra manera. La hoja se regenera desde los datos en
cada corrida de `build_powerbi_model.py`, así que los números de esa tabla y los de esta
no se pueden desincronizar.

---

## Preguntas difíciles y cómo responderlas

Tres preguntas pueden desarmar la presentación si llegan sin preparación. Las tres tienen
respuesta con datos, y los visuales que las sostienen ya están en el dashboard.

### «El QA Score da 94 y la meta es 85. ¿Entonces no hay nada que arreglar?»

Sí hay, y es el hallazgo principal. El 94.14 es un promedio ponderado y los dos canales
auditados están a 13 puntos de distancia:

| Canal | QA Score | Auditorías | Contra meta |
|---|---|---|---|
| Live Chat | 96.01 | 2.105 (85.6%) | +11.01 pp |
| Phone | 83.04 | 355 (14.4%) | **−1.96 pp** |
| Global | 94.14 | 2.460 | +9.14 pp |

Live Chat es el 85.6% de la muestra, así que el promedio se apoya casi entero en ese canal
y Phone queda tapado. Si los dos pesaran igual, el score sería 89.53. Phone es el único
canal bajo meta y es el que necesita plan de acción.

Muéstralo con el indicador de la tarjeta de QA, el tooltip por canal y el bloque de brecha
de la página 2. El banner ejecutivo lo dice solo, sin filtros aplicados.

La segunda mitad de la respuesta es que la muestra de Phone es chica: 355 auditorías
contra 2.105. Antes de sacar conclusiones fuertes hay que ampliar la cobertura de auditoría
en ese canal, y eso también es una acción concreta.

### «El recontacto está en 5.83% contra 5.44%. ¿0.39 pp es todo el problema?»

Depende de sobre qué canales se definió la meta, y el business case no lo dice. La tasa
oficial abarca los doce canales, incluidos bots y autoservicio:

| Alcance | Tasa | Contactos |
|---|---|---|
| Los 12 canales (lo que se reporta) | 5.83% | 994.591 |
| Excluyendo Self Help | 15.19% | 327.941 |
| Solo Phone + Live Chat | 15.56% | 293.300 |

Self Help aporta el 67% del denominador con una tasa de 1.22%. Es un canal donde el
cliente se resuelve solo, con volumen enorme y casi ningún recontacto, así que diluye el
total. Sobre los canales que QA audita —los que tienen un agente atendiendo— la tasa es
15.56%, casi el triple.

La respuesta correcta no es «entonces el número real es 15.56%». Es que **5.83% es el
número oficial y se reporta como tal**, y que la comparación contra meta solo es
interpretable si se sabe sobre qué canales se fijó la meta. Eso es una pregunta para el
dueño de la métrica, y el dashboard muestra las tres lecturas para poder hacerla con datos
en la mano.

El visual es el bloque de alcance de la página 4.

### «El Excel ya trae un score en la columna V y da 86.90. ¿Por qué el tuyo da 94.14?»

Porque el business case especifica una regla y el origen usa otra. La regla del documento
es 100 puntos base, cero si falla un atributo crítico y −10 plano por cada falla no
crítica. El origen, reconstruido desde las filas con una sola falla, pondera cada atributo:

| Deducción | Atributos |
|---|---|
| −3 | `nombre_de_usuario` |
| −5 | `presentacion`, `Saludo_e_identificacion`, `Personalizacion` |
| −15 | `Actitud_de_servicio`, `Calidad_del_sondeo`, `Recurrencia_de_informacion` |
| −20 | `manejo_del_tiempo`, `Calidad_de_comunicacion` |
| −30 | `comunicacion_efectiva` |

Los dos métodos coinciden en el 81.22% de las auditorías y difieren en 462. Las
deducciones ponderadas son en promedio más duras que el −10 plano, así que el score del
origen sale más bajo. **Las dos cifras superan la meta**: +1.90 pp el del origen contra
+9.14 pp el nuestro, así que la conclusión de negocio no cambia.

Hay una parte que no se puede reconciliar, y conviene decirla antes de que la encuentren:
151 auditorías de Live Chat aprueban los ocho atributos y el origen igual las califica con
0. El 67.5% de ellas está marcada como «el agente no siguió el proceso» en una pregunta
aparte del formulario, contra el 11.6% entre las que sí sacan 100. El origen penaliza
adherencia a proceso, y eso no está representado en las columnas de atributos. Por lo tanto
**ningún score reconstruido solo desde esas columnas puede reproducir el del origen**, y no
es un error del cálculo sino una diferencia de alcance del instrumento.

Por eso el modelo trae las dos: `fact_audit[QA_Score]` es el oficial porque sigue la regla
del business case al pie de la letra, y `fact_audit[Source_Score_End_User]` viaja al lado
para poder mostrar la comparación. Los visuales están en la página 2, con rótulos
explícitos de cuál es cuál.

### Preguntas más cortas

| Pregunta | Respuesta |
|---|---|
| ¿Por qué no deduplicaste CSAT? | Las 5.954 filas redundantes son encuestas reales de clientes distintos que coinciden en día, agente, motivo y calificación; nada en la pestaña identifica al encuestado. Deduplicar daría 78.57%, −1.39 pp. |
| El PDF dice `Total Feedback CNT` y la columna se llama `Feedback CNT`. | Son lo mismo. La suma de los cinco niveles de estrella iguala `Feedback CNT` en las 76.754 filas, así que el denominador está confirmado. |
| ¿El valor 2 en los atributos es «no aplica»? | En este dataset no. Los 28.100 valores 2 son exactamente las celdas del canal ajeno (355×8 + 2.105×12) y ninguna auditoría marca 2 dentro de su propio canal. Toda auditoría califica el 100% de los atributos que le corresponden. |
| ¿Cuántas interacciones se tipifican mal? | El 9.72%. Comparar las columnas como texto crudo da 47.20%, pero el 37.48% de eso es solo diferencia de mayúsculas entre las dos convenciones de escritura. |
| ¿Las tasas son promedios de porcentajes? | No, todas son razón de sumas. En recontacto promediar las tasas por fila daría 40.51% en lugar de 5.83%, porque las filas son cubetas de tamaños muy distintos. |

---

## Cobertura del business case

Dónde queda resuelto cada punto que pide el documento, por si te lo preguntan en la
presentación.

| Lo que pide el business case | Dónde está |
|---|---|
| Las tres métricas contra su meta | Fila de KPI de la página 1, con semáforo verde / ámbar / rojo |
| Desglose por canal | `Performance by Channel` en la página 1 con volumen y participación, el tooltip de la tarjeta de QA, y el bloque de brecha entre canales de la página 2 |
| Que un canal bajo meta no quede tapado por el promedio | Indicador de dispersión en la tarjeta de QA, `[Worst Channel Alert]` y la primera rama del banner ejecutivo |
| Sensibilidad de la tasa de recontacto al alcance de canales | Bloque de alcance del denominador en la página 4, con `dim_recontact_scope` |
| Trazabilidad del método de cálculo del score | Comparación contra `Score_end_user` en la página 2 y la hoja `Assumptions` |
| Calidad de la tipificación del motivo de contacto | Bloque de tipificación de la página 2, con la matriz de confusiones |
| Desglose por motivo de contacto | Panel E de la página 1 y las páginas 2, 3 y 4 |
| Desglose por tipo de solicitante | `Performance by Requester Type`, con la nota de que solo existe `Customer` |
| Agrupar bajando `LOB → CR Lv1 → CR Lv4` | Jerarquía `CR Hierarchy` en `dim_cr`, usada con exploración en el panel E |
| Atributos con mayor concentración de defectos | `Top Failing QA Attributes` y el Pareto de la página 2 |
| Impacto de cada atributo sobre el score | `[Impact on QA Score pp]` en la tabla de impacto de la página 2 |
| Patrones de atributos entre agentes y motivos | Las dos matrices nuevas de la página 2 |
| CSAT segmentado por las variables que explican la varianza | Página 3: canal, motivo, país y tipo de negocio |
| Voz del cliente y drivers de insatisfacción | Temas negativos y tabla de comentarios de la página 3 |
| Correlación entre CSAT y QA | Dispersión QA contra CSAT de la página 4, con línea de tendencia |
| Dónde vuelve a contactar el cliente | Recontacto por motivo y por canal, más los tres visuales de ruta de la página 4 |
| Qué señala el recontacto sobre la resolución | Matriz de ruta, `[Cross-Channel Recontact %]` y `[Self-Service Escalation %]` |
| Un insight que conecte dos o más métricas | Tabla de análisis combinado filtrada a `[CR Risk Count] >= 2` |
| Hipótesis de causa raíz | `[Root Cause Hypothesis]` y el banner ejecutivo de la página 1 |
| Semáforo verde / ámbar / rojo | Las medidas de color de la sección 4 de las medidas DAX |
| Colores de marca DiDi | `DiDi_CX_Theme.json` |
| Supuestos sobre datos incompletos | Hoja `Assumptions` del modelo y la tabla de limitaciones de arriba |

Lo único que el documento pide y no vive en el `.pbix` es el **reporte semanal
escrito**, que es el segundo entregable y va en Word o PDF aparte.
