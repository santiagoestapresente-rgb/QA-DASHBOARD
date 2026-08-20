# Medidas DAX — DiDi CX Quality Dashboard

Crea una tabla vacía llamada `_Measures` (Inicio → Escribir datos → tabla vacía) y
coloca ahí todas las medidas. Los nombres entre corchetes deben respetarse tal cual
porque las medidas se referencian entre sí.

Orden sugerido de creación: Metas → Métricas base → Variaciones → Semáforos →
Volúmenes → Defectos QA → CSAT / VOC → Análisis combinado → Recontacto entre
canales → Dispersión por canal → Recontacto por alcance → Método de score y
tipificación → Textos ejecutivos.

**El orden importa.** Power BI no acepta una medida que referencie otra que todavía
no existe, así que hay que crearlas de arriba hacia abajo. Las secciones 10, 11 y 12
tienen que estar creadas antes de la 13, porque el banner ejecutivo las usa.

---

## 1. Metas

```dax
Goal QA = LOOKUPVALUE ( dim_goal[Goal], dim_goal[Metric], "QA Score" )
```

```dax
Goal CSAT = LOOKUPVALUE ( dim_goal[Goal], dim_goal[Metric], "CSAT Score" )
```

```dax
Goal Recontact = LOOKUPVALUE ( dim_goal[Goal], dim_goal[Metric], "Recontact Rate" )
```

---

## 2. Métricas base

El QA Score ya viene calculado por auditoría en `fact_audit[QA_Score]` aplicando las
reglas del business case, así que la medida es simplemente el promedio.

```dax
QA Score = AVERAGE ( fact_audit[QA_Score] )
```

```dax
CSAT Score =
DIVIDE (
    SUM ( fact_csat[Satisfied_CNT] ),
    SUM ( fact_csat[Feedback_CNT] )
) * 100
```

```dax
Recontact Rate =
DIVIDE (
    SUM ( fact_recontact[Recontact_Volume] ),
    SUM ( fact_recontact[Contacts] )
) * 100
```

```dax
Critical Fail Rate =
DIVIDE (
    CALCULATE ( COUNTROWS ( fact_audit ), fact_audit[Has_Critical_Fail] = 1 ),
    COUNTROWS ( fact_audit )
) * 100
```

```dax
Audits Meeting Goal % =
DIVIDE (
    CALCULATE ( COUNTROWS ( fact_audit ), fact_audit[Meets_QA_Goal] = 1 ),
    COUNTROWS ( fact_audit )
) * 100
```

---

## 3. Variación contra meta

```dax
QA vs Goal = [QA Score] - [Goal QA]
```

```dax
CSAT vs Goal = [CSAT Score] - [Goal CSAT]
```

```dax
Recontact vs Goal = [Recontact Rate] - [Goal Recontact]
```

Versiones con formato para mostrar dentro de las tarjetas KPI:

```dax
QA vs Goal Label =
VAR v = [QA vs Goal]
RETURN IF ( ISBLANK ( v ), "sin datos", FORMAT ( v, "+0.0;-0.0" ) & " pp vs meta" )
```

```dax
CSAT vs Goal Label =
VAR v = [CSAT vs Goal]
RETURN IF ( ISBLANK ( v ), "sin datos", FORMAT ( v, "+0.0;-0.0" ) & " pp vs meta" )
```

```dax
Recontact vs Goal Label =
VAR v = [Recontact vs Goal]
RETURN IF ( ISBLANK ( v ), "sin datos", FORMAT ( v, "+0.00;-0.00" ) & " pp vs meta" )
```

---

## 4. Semáforos

Lógica del business case: verde si cumple, ámbar dentro de 5 pp, rojo si se aleja
más de 5 pp. En Recontact la dirección se invierte porque menos es mejor.

```dax
QA Status Color =
VAR v = [QA Score]
VAR g = [Goal QA]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( v ), "#94A3B8",
        v >= g, "#2E9B57",
        v >= g - 5, "#F2A900",
        "#D64545"
    )
```

```dax
CSAT Status Color =
VAR v = [CSAT Score]
VAR g = [Goal CSAT]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( v ), "#94A3B8",
        v >= g, "#2E9B57",
        v >= g - 5, "#F2A900",
        "#D64545"
    )
```

```dax
Recontact Status Color =
VAR v = [Recontact Rate]
VAR g = [Goal Recontact]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( v ), "#94A3B8",
        v <= g, "#2E9B57",
        v <= g + 5, "#F2A900",
        "#D64545"
    )
```

Estas tres medidas se usan en **Formato condicional → Color de fuente → Formato por
campo**, tanto en las tarjetas KPI como en las tablas de desempeño.

---

## 5. Volúmenes y comparación semana contra semana

```dax
Total Contacts = SUM ( fact_recontact[Contacts] )
```

```dax
Total Surveys = SUM ( fact_csat[Feedback_CNT] )
```

```dax
Recontact Volume = SUM ( fact_recontact[Recontact_Volume] )
```

```dax
QA Evaluations = COUNTROWS ( fact_audit )
```

```dax
QA Score PW = CALCULATE ( [QA Score], DATEADD ( dim_date[Date], -7, DAY ) )
```

```dax
CSAT Score PW = CALCULATE ( [CSAT Score], DATEADD ( dim_date[Date], -7, DAY ) )
```

```dax
Recontact Rate PW = CALCULATE ( [Recontact Rate], DATEADD ( dim_date[Date], -7, DAY ) )
```

```dax
QA Evaluations PW = CALCULATE ( [QA Evaluations], DATEADD ( dim_date[Date], -7, DAY ) )
```

```dax
Total Contacts PW = CALCULATE ( [Total Contacts], DATEADD ( dim_date[Date], -7, DAY ) )
```

```dax
Total Surveys PW = CALCULATE ( [Total Surveys], DATEADD ( dim_date[Date], -7, DAY ) )
```

Etiquetas de tendencia con flecha:

```dax
QA WoW Label =
VAR cur = [QA Score]
VAR prev = [QA Score PW]
VAR d = cur - prev
RETURN
    IF (
        ISBLANK ( prev ),
        "sin semana previa",
        SWITCH ( TRUE (), d > 0, "▲ ", d < 0, "▼ ", "→ " )
            & FORMAT ( ABS ( d ), "0.0" ) & " pp vs semana previa"
    )
```

```dax
Contacts WoW Label =
VAR cur = [Total Contacts]
VAR prev = [Total Contacts PW]
VAR d = DIVIDE ( cur - prev, prev )
RETURN
    IF (
        ISBLANK ( prev ) || prev = 0,
        "sin semana previa",
        SWITCH ( TRUE (), d > 0, "▲ ", d < 0, "▼ ", "→ " ) & FORMAT ( ABS ( d ), "0.0%" ) & " vs semana previa"
    )
```

```dax
Surveys WoW Label =
VAR cur = [Total Surveys]
VAR prev = [Total Surveys PW]
VAR d = DIVIDE ( cur - prev, prev )
RETURN
    IF (
        ISBLANK ( prev ) || prev = 0,
        "sin semana previa",
        SWITCH ( TRUE (), d > 0, "▲ ", d < 0, "▼ ", "→ " ) & FORMAT ( ABS ( d ), "0.0%" ) & " vs semana previa"
    )
```

```dax
Evaluations WoW Label =
VAR cur = [QA Evaluations]
VAR prev = [QA Evaluations PW]
VAR d = DIVIDE ( cur - prev, prev )
RETURN
    IF (
        ISBLANK ( prev ) || prev = 0,
        "sin semana previa",
        SWITCH ( TRUE (), d > 0, "▲ ", d < 0, "▼ ", "→ " ) & FORMAT ( ABS ( d ), "0.0%" ) & " vs semana previa"
    )
```

---

## 6. Análisis de defectos QA

`fact_audit_attribute` tiene una fila por auditoría y atributo, incluyendo aprobados
y N/A. Eso permite calcular la tasa de falla contra atributos realmente evaluados.

```dax
Attribute Fails = SUM ( fact_audit_attribute[Is_Fail] )
```

```dax
Attributes Evaluated = SUM ( fact_audit_attribute[Is_Evaluated] )
```

```dax
Attribute Fail Rate = DIVIDE ( [Attribute Fails], [Attributes Evaluated] ) * 100
```

```dax
% of Total Fails =
DIVIDE (
    [Attribute Fails],
    CALCULATE ( [Attribute Fails], REMOVEFILTERS ( dim_attribute ) )
) * 100
```

Línea acumulada del Pareto:

```dax
Cumulative % of Fails =
VAR CurrentFails = [Attribute Fails]
VAR AllAttributes =
    CALCULATETABLE (
        VALUES ( dim_attribute[Attribute_Name] ),
        REMOVEFILTERS ( dim_attribute )
    )
VAR Ranked =
    ADDCOLUMNS ( AllAttributes, "@fails", CALCULATE ( [Attribute Fails] ) )
VAR CumulativeFails =
    SUMX ( FILTER ( Ranked, [@fails] >= CurrentFails ), [@fails] )
VAR TotalFails =
    CALCULATE ( [Attribute Fails], REMOVEFILTERS ( dim_attribute ) )
RETURN
    DIVIDE ( CumulativeFails, TotalFails ) * 100
```

Impacto de cada atributo sobre el score global, en puntos porcentuales. Compara el
score promedio de las auditorías donde el atributo falló contra el promedio general,
ponderado por cuántas auditorías afecta.

```dax
Impact on QA Score pp =
VAR AffectedAudits =
    CALCULATETABLE (
        VALUES ( fact_audit_attribute[Audit_ID] ),
        fact_audit_attribute[Is_Fail] = 1
    )
VAR OverallScore = CALCULATE ( [QA Score], REMOVEFILTERS ( dim_attribute ) )
VAR ScoreWhenFailed =
    CALCULATE (
        [QA Score],
        REMOVEFILTERS ( dim_attribute ),
        TREATAS ( AffectedAudits, fact_audit[Audit_ID] )
    )
VAR ShareOfAudits =
    DIVIDE (
        COUNTROWS ( AffectedAudits ),
        CALCULATE ( COUNTROWS ( fact_audit ), REMOVEFILTERS ( dim_attribute ) )
    )
RETURN
    - ABS ( ( OverallScore - ScoreWhenFailed ) * ShareOfAudits )
```

```dax
Critical Attribute Color =
IF (
    SELECTEDVALUE ( dim_attribute[Is_Critical] ) = 1,
    "#D64545",
    "#2E6FBE"
)
```

---

## 7. CSAT y Voz del Cliente

```dax
Survey Responses = SUM ( fact_csat[Feedback_CNT] )
```

```dax
Star Responses =
SUM ( fact_csat[Star_1] ) + SUM ( fact_csat[Star_2] ) + SUM ( fact_csat[Star_3] )
    + SUM ( fact_csat[Star_4] ) + SUM ( fact_csat[Star_5] )
```

Para el gráfico de barras por estrella conviene desdoblar la tabla. Crea esta tabla
calculada (Modelado → Nueva tabla):

```dax
Star Rating =
UNION (
    SELECTCOLUMNS ( fact_csat, "Date", fact_csat[Date], "Channel_Key", fact_csat[Channel_Key], "CR_Key", fact_csat[CR_Key], "Country_Code", fact_csat[Country_Code], "Rating", "1 Star",  "Rating_Order", 1, "Responses", fact_csat[Star_1] ),
    SELECTCOLUMNS ( fact_csat, "Date", fact_csat[Date], "Channel_Key", fact_csat[Channel_Key], "CR_Key", fact_csat[CR_Key], "Country_Code", fact_csat[Country_Code], "Rating", "2 Stars", "Rating_Order", 2, "Responses", fact_csat[Star_2] ),
    SELECTCOLUMNS ( fact_csat, "Date", fact_csat[Date], "Channel_Key", fact_csat[Channel_Key], "CR_Key", fact_csat[CR_Key], "Country_Code", fact_csat[Country_Code], "Rating", "3 Stars", "Rating_Order", 3, "Responses", fact_csat[Star_3] ),
    SELECTCOLUMNS ( fact_csat, "Date", fact_csat[Date], "Channel_Key", fact_csat[Channel_Key], "CR_Key", fact_csat[CR_Key], "Country_Code", fact_csat[Country_Code], "Rating", "4 Stars", "Rating_Order", 4, "Responses", fact_csat[Star_4] ),
    SELECTCOLUMNS ( fact_csat, "Date", fact_csat[Date], "Channel_Key", fact_csat[Channel_Key], "CR_Key", fact_csat[CR_Key], "Country_Code", fact_csat[Country_Code], "Rating", "5 Stars", "Rating_Order", 5, "Responses", fact_csat[Star_5] )
)
```

Relaciona `Star Rating` con `dim_date`, `dim_channel`, `dim_cr` y `dim_country`, y
ordena la columna `Rating` por `Rating_Order`.

```dax
Star Responses Count = SUM ( 'Star Rating'[Responses] )
```

```dax
Star Share % =
DIVIDE (
    [Star Responses Count],
    CALCULATE ( [Star Responses Count], REMOVEFILTERS ( 'Star Rating'[Rating] ) )
) * 100
```

```dax
Star Bar Color =
SWITCH (
    SELECTEDVALUE ( 'Star Rating'[Rating_Order] ),
    5, "#2E9B57",
    4, "#2E9B57",
    3, "#F2A900",
    2, "#D64545",
    1, "#D64545",
    "#94A3B8"
)
```

Temas de la voz del cliente en encuestas negativas:

```dax
Negative VOC Mentions =
CALCULATE (
    COUNTROWS ( fact_csat ),
    fact_csat[Is_Negative_Survey] = 1,
    NOT fact_csat[VOC_Theme] IN { "Not classified" }
)
```

```dax
Negative VOC Share % =
DIVIDE (
    [Negative VOC Mentions],
    CALCULATE ( [Negative VOC Mentions], REMOVEFILTERS ( fact_csat[VOC_Theme] ) )
) * 100
```

---

## 8. Análisis combinado por motivo de contacto

Detecta los CR Lv4 donde varias métricas fallan al mismo tiempo.

```dax
CR Risk Pattern =
VAR qa = [QA Score]
VAR cs = [CSAT Score]
VAR rc = [Recontact Rate]
VAR flags =
    FILTER (
        {
            ( IF ( NOT ISBLANK ( qa ) && qa < [Goal QA], "QA bajo" ) ),
            ( IF ( NOT ISBLANK ( cs ) && cs < [Goal CSAT], "CSAT bajo" ) ),
            ( IF ( NOT ISBLANK ( rc ) && rc > [Goal Recontact], "Recontacto alto" ) )
        },
        NOT ISBLANK ( [Value] )
    )
RETURN
    IF (
        COUNTROWS ( flags ) = 0,
        "Dentro de meta",
        CONCATENATEX ( flags, [Value], " + " )
    )
```

```dax
CR Risk Count =
VAR qa = [QA Score]
VAR cs = [CSAT Score]
VAR rc = [Recontact Rate]
RETURN
    IF ( NOT ISBLANK ( qa ) && qa < [Goal QA], 1, 0 )
        + IF ( NOT ISBLANK ( cs ) && cs < [Goal CSAT], 1, 0 )
        + IF ( NOT ISBLANK ( rc ) && rc > [Goal Recontact], 1, 0 )
```

```dax
CR Risk Color =
SWITCH (
    [CR Risk Count],
    3, "#D64545",
    2, "#F2A900",
    1, "#FF6600",
    "#2E9B57"
)
```

Úsala como filtro visual (`CR Risk Count` es mayor o igual a 2) en la tabla de
análisis combinado para quedarte solo con los casos críticos.

---

## 9. Recontacto entre canales

La pestaña Recontact guarda el canal del contacto anterior. Eso permite responder la
pregunta del business case sobre dónde vuelve a contactar el cliente y qué revela
sobre la calidad de la resolución: seis de cada diez recontactos llegan por un canal
distinto al original, así que el problema no es solo cuántos vuelven sino por dónde.

```dax
Cross-Channel Recontacts =
CALCULATE ( [Recontact Volume], fact_recontact[Is_Cross_Channel] = 1 )
```

```dax
Cross-Channel Recontact % =
DIVIDE ( [Cross-Channel Recontacts], [Recontact Volume] ) * 100
```

Participación de cada ruta sobre el total de recontactos del período. Quita los
filtros de las dos puntas de la ruta para que el denominador sea siempre el total.

```dax
Route Share of Recontacts % =
DIVIDE (
    [Recontact Volume],
    CALCULATE (
        [Recontact Volume],
        REMOVEFILTERS ( fact_recontact[Prev_Channel_Name] ),
        REMOVEFILTERS ( fact_recontact[Contact_Route] ),
        REMOVEFILTERS ( dim_channel )
    )
) * 100
```

Escalamiento desde autoservicio: contactos que empezaron en un canal sin agente y
terminaron en Phone o Live Chat. Es la señal más directa de una brecha de proceso,
porque el cliente intentó resolver solo y no pudo.

```dax
Self-Service Escalation Volume =
CALCULATE (
    [Recontact Volume],
    fact_recontact[Prev_Channel_Name] IN { "Self Help", "GPTBot", "Help Center" },
    dim_channel[Has_QA] = 1
)
```

```dax
Self-Service Escalation % =
DIVIDE ( [Self-Service Escalation Volume], [Recontact Volume] ) * 100
```

```dax
Top Contact Route =
VAR ranked =
    TOPN (
        1,
        ADDCOLUMNS (
            ALL ( fact_recontact[Contact_Route] ),
            "@vol", CALCULATE ( [Recontact Volume] )
        ),
        [@vol], DESC
    )
RETURN CONCATENATEX ( ranked, fact_recontact[Contact_Route] )
```

---

## 10. Dispersión de QA entre canales

El QA Score global cumple la meta, pero eso no significa que todos los canales la
cumplan. Live Chat concentra el 85.6% de las auditorías, así que el promedio
ponderado se apoya casi por completo en ese canal y Phone queda tapado: 96.01 contra
83.04, con la meta en 85. Estas medidas hacen visible la brecha en lugar de dejarla
enterrada en el promedio.

Todas recorren la misma tabla virtual de canales auditados con su score y su volumen.
La repetición es inevitable porque una medida no puede devolver una tabla; lo
importante es que el filtro `[@n] > 0` esté siempre, para que un canal sin auditorías
en el período seleccionado no se cuele como el peor con un valor en blanco.

```dax
Worst Channel QA Score =
VAR Channels =
    FILTER (
        ADDCOLUMNS (
            CALCULATETABLE ( VALUES ( dim_channel[Channel_Name] ), dim_channel[Has_QA] = 1 ),
            "@qa", CALCULATE ( [QA Score] ),
            "@n", CALCULATE ( [QA Evaluations] )
        ),
        [@n] > 0
    )
RETURN MINX ( Channels, [@qa] )
```

```dax
Best Channel QA Score =
VAR Channels =
    FILTER (
        ADDCOLUMNS (
            CALCULATETABLE ( VALUES ( dim_channel[Channel_Name] ), dim_channel[Has_QA] = 1 ),
            "@qa", CALCULATE ( [QA Score] ),
            "@n", CALCULATE ( [QA Evaluations] )
        ),
        [@n] > 0
    )
RETURN MAXX ( Channels, [@qa] )
```

```dax
Channel QA Spread pp = [Best Channel QA Score] - [Worst Channel QA Score]
```

Reemplaza la medida `[Worst Channel]` de la versión anterior. Ahora descarta los
canales sin auditorías y devuelve el nombre del peor.

```dax
Worst Channel =
VAR Channels =
    FILTER (
        ADDCOLUMNS (
            CALCULATETABLE ( VALUES ( dim_channel[Channel_Name] ), dim_channel[Has_QA] = 1 ),
            "@qa", CALCULATE ( [QA Score] ),
            "@n", CALCULATE ( [QA Evaluations] )
        ),
        [@n] > 0
    )
RETURN CONCATENATEX ( TOPN ( 1, Channels, [@qa], ASC ), dim_channel[Channel_Name], ", " )
```

```dax
Worst Channel Evaluations =
VAR Channels =
    FILTER (
        ADDCOLUMNS (
            CALCULATETABLE ( VALUES ( dim_channel[Channel_Name] ), dim_channel[Has_QA] = 1 ),
            "@qa", CALCULATE ( [QA Score] ),
            "@n", CALCULATE ( [QA Evaluations] )
        ),
        [@n] > 0
    )
RETURN MAXX ( TOPN ( 1, Channels, [@qa], ASC ), [@n] )
```

```dax
Worst Channel Gap vs Goal = [Worst Channel QA Score] - [Goal QA]
```

```dax
Channels Below QA Goal =
VAR goalQA = [Goal QA]
VAR Channels =
    FILTER (
        ADDCOLUMNS (
            CALCULATETABLE ( VALUES ( dim_channel[Channel_Name] ), dim_channel[Has_QA] = 1 ),
            "@qa", CALCULATE ( [QA Score] ),
            "@n", CALCULATE ( [QA Evaluations] )
        ),
        [@n] > 0
    )
RETURN COUNTROWS ( FILTER ( Channels, [@qa] < goalQA ) ) + 0
```

Participación de cada canal en la muestra de auditoría. Es la medida que explica *por
qué* el promedio global no refleja a Phone, y va en la tabla de desempeño por canal.

```dax
Channel Share of Audits % =
DIVIDE (
    [QA Evaluations],
    CALCULATE ( [QA Evaluations], REMOVEFILTERS ( dim_channel ) )
) * 100
```

```dax
Largest Channel Share of Audits % =
VAR Channels =
    FILTER (
        ADDCOLUMNS (
            CALCULATETABLE ( VALUES ( dim_channel[Channel_Name] ), dim_channel[Has_QA] = 1 ),
            "@n", CALCULATE ( [QA Evaluations] )
        ),
        [@n] > 0
    )
RETURN DIVIDE ( MAXX ( Channels, [@n] ), SUMX ( Channels, [@n] ) ) * 100
```

Promedio simple entre canales, sin ponderar por volumen. **Es una medida de
diagnóstico, no un KPI:** sirve para mostrar en la entrevista cuánto del 94.14 viene
del peso de Live Chat y nada más. Nunca la pongas en la fila de KPI.

```dax
QA Score Simple Channel Average =
VAR Channels =
    FILTER (
        ADDCOLUMNS (
            CALCULATETABLE ( VALUES ( dim_channel[Channel_Name] ), dim_channel[Has_QA] = 1 ),
            "@qa", CALCULATE ( [QA Score] ),
            "@n", CALCULATE ( [QA Evaluations] )
        ),
        [@n] > 0
    )
RETURN AVERAGEX ( Channels, [@qa] )
```

Texto largo para el tooltip y para la página de QA Deep Dive:

```dax
Worst Channel Alert =
VAR below = [Channels Below QA Goal]
VAR worst = [Worst Channel]
VAR score = [Worst Channel QA Score]
VAR goalQA = [Goal QA]
VAR n = [Worst Channel Evaluations]
RETURN
    IF (
        below = 0,
        "Todos los canales auditados cumplen la meta. Dispersión de "
            & FORMAT ( [Channel QA Spread pp], "0.0" ) & " pp entre el mejor y el peor.",
        worst & " está en " & FORMAT ( score, "0.0" ) & "% contra una meta de "
            & FORMAT ( goalQA, "0" ) & "%: " & FORMAT ( score - goalQA, "+0.0;-0.0" )
            & " pp sobre " & FORMAT ( n, "#,0" ) & " auditorías. El global se sostiene porque "
            & "el canal de mayor volumen concentra "
            & FORMAT ( [Largest Channel Share of Audits %], "0" ) & "% de la muestra."
    )
```

Indicador corto para la tarjeta de KPI. Devuelve cadena vacía cuando no hay nada que
señalar, así que el objeto desaparece solo y no ocupa espacio cuando todo está en meta.

```dax
QA Dispersion Alert =
VAR below = [Channels Below QA Goal]
VAR spread = [Channel QA Spread pp]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( [QA Score] ), "",
        below > 0,
            "⚠ " & [Worst Channel] & " " & FORMAT ( [Worst Channel QA Score], "0.0" ) & "%",
        spread >= 5, "⚠ " & FORMAT ( spread, "0.0" ) & " pp entre canales",
        ""
    )
```

```dax
QA Dispersion Color =
SWITCH (
    TRUE (),
    [Channels Below QA Goal] > 0, "#D64545",
    [Channel QA Spread pp] >= 5, "#F2A900",
    "#94A3B8"
)
```

Desglose completo para el tooltip, una línea por canal ordenada de peor a mejor:

```dax
QA Channel Breakdown =
VAR Channels =
    FILTER (
        ADDCOLUMNS (
            CALCULATETABLE ( VALUES ( dim_channel[Channel_Name] ), dim_channel[Has_QA] = 1 ),
            "@qa", CALCULATE ( [QA Score] ),
            "@n", CALCULATE ( [QA Evaluations] )
        ),
        [@n] > 0
    )
RETURN
    CONCATENATEX (
        Channels,
        dim_channel[Channel_Name] & ": " & FORMAT ( [@qa], "0.0" ) & "%  (n="
            & FORMAT ( [@n], "#,0" ) & ",  " & FORMAT ( [@qa] - [Goal QA], "+0.0;-0.0" )
            & " pp vs meta)",
        UNICHAR ( 10 ),
        [@qa], ASC
    )
```

```dax
Worst Channel Top Failing Attribute =
VAR worst = [Worst Channel]
RETURN
    CALCULATE (
        [Top Failing Attribute],
        REMOVEFILTERS ( dim_channel ),
        dim_channel[Channel_Name] = worst
    )
```

---

## 11. Recontacto por alcance de canal

La tasa oficial se calcula sobre los doce canales, y ahí está el problema de lectura:
Self Help aporta el 67% del denominador con una tasa de apenas 1.22%, así que arrastra
el total hacia abajo. Presentar 5.83% contra una meta de 5.44% como "apenas 0.39 pp
arriba" solo es correcto si la meta se definió sobre todos los canales incluyendo bots
y autoservicio, y el business case no lo dice.

**El total oficial sigue siendo 5.83% y es el KPI de la página 1.** Lo que sigue es
contexto complementario, no un reemplazo.

Las tres medidas de alcance quitan el filtro de `dim_channel` y lo vuelven a aplicar
ellas mismas, así que no reaccionan a la segmentación de canal. Es intencional: el
punto es comparar alcances fijos.

```dax
Recontact Rate Audited Channels =
CALCULATE (
    [Recontact Rate],
    REMOVEFILTERS ( dim_channel ),
    dim_channel[Has_QA] = 1
)
```

```dax
Recontact Rate Excl Self Help =
CALCULATE (
    [Recontact Rate],
    REMOVEFILTERS ( dim_channel ),
    dim_channel[Channel_Name] <> "Self Help"
)
```

```dax
Self Help Recontact Rate =
CALCULATE (
    [Recontact Rate],
    REMOVEFILTERS ( dim_channel ),
    dim_channel[Channel_Name] = "Self Help"
)
```

```dax
Self Help Share of Contacts % =
DIVIDE (
    CALCULATE (
        [Total Contacts],
        REMOVEFILTERS ( dim_channel ),
        dim_channel[Channel_Name] = "Self Help"
    ),
    CALCULATE ( [Total Contacts], REMOVEFILTERS ( dim_channel ) )
) * 100
```

```dax
Recontact Audited vs Goal = [Recontact Rate Audited Channels] - [Goal Recontact]
```

```dax
Recontact Audited Status Color =
VAR v = [Recontact Rate Audited Channels]
VAR g = [Goal Recontact]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( v ), "#94A3B8",
        v <= g, "#2E9B57",
        v <= g + 5, "#F2A900",
        "#D64545"
    )
```

`dim_recontact_scope` es una tabla desconectada de tres filas que viene en el Excel del
modelo. **No la relaciones con nada:** la medida resuelve el filtro de canal por su
cuenta según `Scope_Key`. Eso es lo que permite poner los tres alcances en un solo
visual.

```dax
Recontact Rate by Scope =
SWITCH (
    SELECTEDVALUE ( dim_recontact_scope[Scope_Key] ),
    "all", CALCULATE ( [Recontact Rate], REMOVEFILTERS ( dim_channel ) ),
    "ex_self_help", [Recontact Rate Excl Self Help],
    "audited", [Recontact Rate Audited Channels],
    BLANK ()
)
```

```dax
Contacts by Scope =
SWITCH (
    SELECTEDVALUE ( dim_recontact_scope[Scope_Key] ),
    "all", CALCULATE ( [Total Contacts], REMOVEFILTERS ( dim_channel ) ),
    "ex_self_help",
        CALCULATE (
            [Total Contacts],
            REMOVEFILTERS ( dim_channel ),
            dim_channel[Channel_Name] <> "Self Help"
        ),
    "audited",
        CALCULATE ( [Total Contacts], REMOVEFILTERS ( dim_channel ), dim_channel[Has_QA] = 1 ),
    BLANK ()
)
```

```dax
Scope vs Goal by Scope = [Recontact Rate by Scope] - [Goal Recontact]
```

```dax
Recontact Scope Note =
"Oficial (12 canales): "
    & FORMAT ( CALCULATE ( [Recontact Rate], REMOVEFILTERS ( dim_channel ) ), "0.00" )
    & "%   |   sin Self Help: " & FORMAT ( [Recontact Rate Excl Self Help], "0.00" )
    & "%   |   solo canales auditados: "
    & FORMAT ( [Recontact Rate Audited Channels], "0.00" ) & "%. "
    & "Self Help aporta " & FORMAT ( [Self Help Share of Contacts %], "0" )
    & "% del denominador con una tasa de " & FORMAT ( [Self Help Recontact Rate], "0.00" )
    & "%, así que diluye el total. La meta de "
    & FORMAT ( [Goal Recontact], "0.00" ) & "% no especifica sobre qué canales se definió."
```

El modelo marca en `fact_recontact[Data_Quality_Flag]` las 111 filas donde el volumen
de recontacto supera los contactos —todas de GPTBot— y las 249 con cero contactos.
Esta medida cuantifica cuánto cambiaría el total si se excluyeran, para poder
responderlo con un número en lugar de una intuición.

```dax
Recontact Rate Excl Anomalies =
CALCULATE ( [Recontact Rate], fact_recontact[Data_Quality_Flag] = "OK" )
```

```dax
Recontact Anomaly Impact pp = [Recontact Rate Excl Anomalies] - [Recontact Rate]
```

```dax
Recontact Anomaly Rows =
CALCULATE ( COUNTROWS ( fact_recontact ), fact_recontact[Data_Quality_Flag] <> "OK" )
```

---

## 12. Método de score y calidad de la tipificación

### Nuestro score contra el del origen

La pestaña QA trae su propia columna de score, `Score_end_user`, con un promedio de
86.90 contra nuestros 94.14. No es un error de ninguno de los dos: el origen usa una
rúbrica ponderada por atributo y el business case dicta −10 plano por cada falla no
crítica. Nosotros seguimos la regla del business case, y estas medidas permiten
mostrar las dos lecturas lado a lado sin ambigüedad sobre cuál es la oficial.

```dax
QA Score Source Rubric = AVERAGE ( fact_audit[Source_Score_End_User] )
```

```dax
QA Score Method Gap pp = [QA Score] - [QA Score Source Rubric]
```

```dax
Source Score vs Goal = [QA Score Source Rubric] - [Goal QA]
```

```dax
Score Agreement % =
DIVIDE (
    CALCULATE ( COUNTROWS ( fact_audit ), fact_audit[Score_Matches_Source] = 1 ),
    COUNTROWS ( fact_audit )
) * 100
```

```dax
Scoring Method Note =
"Score oficial (regla del business case, -10 por falla no crítica): "
    & FORMAT ( [QA Score], "0.00" ) & "% (" & FORMAT ( [QA vs Goal], "+0.00;-0.00" )
    & " pp vs meta).   Score del origen (columna Score_end_user, rúbrica ponderada por atributo): "
    & FORMAT ( [QA Score Source Rubric], "0.00" ) & "% ("
    & FORMAT ( [Source Score vs Goal], "+0.00;-0.00" ) & " pp vs meta).   Coinciden en "
    & FORMAT ( [Score Agreement %], "0.00" ) & "% de las auditorías. "
    & "Las dos superan la meta; el dashboard reporta la del business case."
```

### Adherencia al proceso

El origen penaliza que el agente no siga el proceso, y eso no está representado en
ninguna de las columnas de atributos. Por eso hay 151 auditorías de Live Chat que
aprueban los ocho atributos y el origen igual les pone 0. Esta es la evidencia de que
ningún score reconstruido solo desde las columnas W–AP puede reproducir el del origen.

```dax
Process Not Followed % =
DIVIDE (
    CALCULATE ( COUNTROWS ( fact_audit ), fact_audit[Process_Adherence] = "Did not follow process" ),
    CALCULATE ( COUNTROWS ( fact_audit ), fact_audit[Process_Adherence] <> "Not assessed" )
) * 100
```

```dax
All Attributes Pass Scored Zero by Source =
CALCULATE (
    COUNTROWS ( fact_audit ),
    fact_audit[NonCritical_Fails] = 0,
    fact_audit[Has_Critical_Fail] = 0,
    fact_audit[Source_Score_End_User] = 0
)
```

### Calidad de la tipificación

`CR_registrada` y `CR_correcta` difieren como texto crudo en el 47.20% de las
auditorías, pero el 37.48% de eso es solo diferencia de mayúsculas. La tipificación
realmente incorrecta —la que manda la interacción a otro motivo de contacto— es del
9.72%. `fact_audit[CR_Typing_Status]` separa los tres casos, así que el ruido
ortográfico nunca se reporta como error de tipificación.

```dax
Retyped Audits = CALCULATE ( COUNTROWS ( fact_audit ), fact_audit[Is_Retyped_CR] = 1 )
```

```dax
Retyped Rate % = DIVIDE ( [Retyped Audits], COUNTROWS ( fact_audit ) ) * 100
```

```dax
QA Score When Retyped = CALCULATE ( [QA Score], fact_audit[Is_Retyped_CR] = 1 )
```

```dax
QA Score When Typed Right = CALCULATE ( [QA Score], fact_audit[Is_Retyped_CR] = 0 )
```

```dax
Retyping QA Gap pp = [QA Score When Typed Right] - [QA Score When Retyped]
```

```dax
Retyping Note =
FORMAT ( [Retyped Rate %], "0.00" ) & "% de las auditorías se tipificó a un motivo distinto "
    & "del correcto (" & FORMAT ( [Retyped Audits], "#,0" ) & " de "
    & FORMAT ( COUNTROWS ( fact_audit ), "#,0" ) & "). Esas interacciones promedian "
    & FORMAT ( [QA Score When Retyped], "0.0" ) & "% de QA contra "
    & FORMAT ( [QA Score When Typed Right], "0.0" ) & "% del resto, una brecha de "
    & FORMAT ( [Retyping QA Gap pp], "0.0" ) & " pp. Una tipificación errada desvía el análisis "
    & "por motivo y el enrutamiento del caso."
```

---

## 13. Textos ejecutivos dinámicos

```dax
Period Label =
VAR minDate = MIN ( dim_date[Date] )
VAR maxDate = MAX ( dim_date[Date] )
RETURN FORMAT ( minDate, "dd mmm" ) & " – " & FORMAT ( maxDate, "dd mmm yyyy" )
```

```dax
Data As Of = "Datos al " & FORMAT ( MAX ( dim_date[Date] ), "dd mmm yyyy" )
```

```dax
Worst Metric =
VAR gapQA = [Goal QA] - [QA Score]
VAR gapCSAT = [Goal CSAT] - [CSAT Score]
VAR gapRC = [Recontact Rate] - [Goal Recontact]
VAR worst = MAXX ( { gapQA, gapCSAT, gapRC }, [Value] )
RETURN
    SWITCH (
        TRUE (),
        worst <= 0, "Todas las métricas en meta",
        worst = gapQA, "QA Score",
        worst = gapCSAT, "CSAT Score",
        "Recontact Rate"
    )
```

```dax
Top Failing Attribute =
VAR ranked =
    TOPN (
        1,
        ADDCOLUMNS (
            ALL ( dim_attribute[Attribute_Name] ),
            "@fails", CALCULATE ( [Attribute Fails] )
        ),
        [@fails], DESC
    )
RETURN CONCATENATEX ( ranked, dim_attribute[Attribute_Name] )
```

```dax
Top Recontact Reason =
VAR ranked =
    TOPN (
        1,
        ADDCOLUMNS (
            ALL ( dim_cr[CR_Lv4] ),
            "@vol", CALCULATE ( [Recontact Volume] )
        ),
        [@vol], DESC
    )
RETURN CONCATENATEX ( ranked, dim_cr[CR_Lv4] )
```

```dax
Top Negative VOC Theme =
VAR ranked =
    TOPN (
        1,
        ADDCOLUMNS (
            ALL ( fact_csat[VOC_Theme] ),
            "@mentions", CALCULATE ( [Negative VOC Mentions] )
        ),
        [@mentions], DESC
    )
RETURN CONCATENATEX ( ranked, fact_csat[VOC_Theme] )
```

`[Worst Channel]` está definida en la sección 10 junto con el resto de las medidas de
dispersión por canal.

### Banner ejecutivo del pie de página

El orden del `SWITCH` es una decisión de criterio, no un detalle de implementación.
La primera rama es el caso que ningún KPI muestra por sí solo: **un canal está bajo
meta aunque el global no lo esté.** Va primero justamente porque es el hallazgo que el
promedio esconde; los incumplimientos globales ya se ven en su propia tarjeta con el
semáforo en ámbar o rojo, mientras que este no se ve en ninguna parte del dashboard si
no se dice explícitamente.

Las ramas siguientes mantienen el orden anterior, pero la de recontacto ahora aclara
el alcance del denominador en lugar de presentar los 0.39 pp sin contexto.

```dax
Key Operational Insight =
VAR qa = [QA Score]
VAR goalQA = [Goal QA]
VAR rc = [Recontact Rate]
VAR goalRC = [Goal Recontact]
VAR cs = [CSAT Score]
VAR goalCS = [Goal CSAT]
VAR belowChannels = [Channels Below QA Goal]
VAR worstCh = [Worst Channel]
VAR worstScore = [Worst Channel QA Score]
VAR worstN = [Worst Channel Evaluations]
VAR rcAudited = [Recontact Rate Audited Channels]
VAR topReason = [Top Recontact Reason]
VAR topAttr = [Top Failing Attribute]
VAR topTheme = [Top Negative VOC Theme]
RETURN
    SWITCH (
        TRUE (),
        belowChannels > 0 && qa >= goalQA,
            "El QA Score global cumple la meta con " & FORMAT ( qa, "0.0" ) & "%, pero "
                & worstCh & " está en " & FORMAT ( worstScore, "0.0" ) & "% sobre "
                & FORMAT ( worstN, "#,0" ) & " auditorías: "
                & FORMAT ( worstScore - goalQA, "+0.0;-0.0" ) & " pp contra la meta de "
                & FORMAT ( goalQA, "0" ) & "%. El promedio global lo esconde porque el canal de "
                & "mayor volumen concentra " & FORMAT ( [Largest Channel Share of Audits %], "0" )
                & "% de la muestra. En ese canal el atributo que más falla es "
                & [Worst Channel Top Failing Attribute] & ".",
        qa < goalQA,
            "El QA Score está en " & FORMAT ( qa, "0.0" ) & "% contra una meta de "
                & FORMAT ( goalQA, "0.0" ) & "%, y el canal más rezagado es " & worstCh & " con "
                & FORMAT ( worstScore, "0.0" ) & "%. El atributo que concentra más fallas es "
                & topAttr & ".",
        rc > goalRC,
            "La tasa de recontacto está en " & FORMAT ( rc, "0.00" ) & "% contra una meta de "
                & FORMAT ( goalRC, "0.00" ) & "% sobre los 12 canales, pero medida solo sobre los "
                & "canales que QA audita sube a " & FORMAT ( rcAudited, "0.00" )
                & "%, porque el autoservicio diluye el denominador. El motivo que más recontactos "
                & "genera es " & topReason & ", y " & FORMAT ( [Cross-Channel Recontact %], "0" )
                & "% llega por un canal distinto al original (" & [Top Contact Route]
                & " es la ruta más frecuente).",
        cs < goalCS,
            "El CSAT cerró en " & FORMAT ( cs, "0.0" ) & "% frente a la meta de "
                & FORMAT ( goalCS, "0.0" )
                & "%. El tema más mencionado en la retroalimentación negativa es " & topTheme & ".",
        "Las tres métricas están dentro de meta y ningún canal auditado queda por debajo. "
            & "El atributo con más fallas sigue siendo " & topAttr & "."
    )
```

```dax
Recommended Action =
VAR qa = [QA Score]
VAR goalQA = [Goal QA]
VAR rc = [Recontact Rate]
VAR goalRC = [Goal Recontact]
VAR cs = [CSAT Score]
VAR goalCS = [Goal CSAT]
VAR belowChannels = [Channels Below QA Goal]
VAR worstCh = [Worst Channel]
RETURN
    SWITCH (
        TRUE (),
        belowChannels > 0 && qa >= goalQA,
            "Abrir un plan de coaching focalizado en " & worstCh & " sobre "
                & [Worst Channel Top Failing Attribute]
                & ", y ampliar la muestra de auditoría de ese canal: hoy es demasiado chica frente "
                & "al resto para sostener una conclusión firme. Reportar QA por canal, no solo el global.",
        qa < goalQA,
            "Incluir " & [Top Failing Attribute] & " como tema principal de la próxima sesión de "
                & "calibración, empezando por " & worstCh & ".",
        rc > goalRC,
            "Revisar de punta a punta la ruta de resolución y el manejo de escalamientos en "
                & [Top Recontact Reason] & ", y confirmar con el dueño de la métrica sobre qué "
                & "canales se definió la meta de " & FORMAT ( goalRC, "0.00" )
                & "% antes de declarar la brecha cerrada.",
        cs < goalCS,
            "Validar los flujos de resolución y compensación asociados a " & [Top Negative VOC Theme]
                & " junto con el dueño del proceso.",
        "Mantener el monitoreo sobre " & [Top Failing Attribute] & " y sostener la cadencia de calibración."
    )
```

```dax
Root Cause Hypothesis =
VAR rc = [Recontact Rate]
VAR goalRC = [Goal Recontact]
VAR escal = [Self-Service Escalation %]
VAR belowChannels = [Channels Below QA Goal]
RETURN
    "Hipótesis: "
        & IF (
            rc > goalRC,
            "el recontacto elevado junto con las fallas en " & [Top Failing Attribute]
                & " sugiere una brecha en la ejecución de la resolución o en el escalamiento. ",
            "las fallas concentradas en " & [Top Failing Attribute]
                & " podrían estar limitando el desempeño de calidad. "
        )
        & IF (
            belowChannels > 0,
            "La brecha se concentra en " & [Worst Channel] & " ("
                & FORMAT ( [Worst Channel QA Score], "0.0" ) & "% contra "
                & FORMAT ( [Best Channel QA Score], "0.0" ) & "% del mejor canal), lo que apunta a "
                & "una causa específica de ese canal —guion, herramienta o capacitación— y no a un "
                & "problema transversal de la operación. ",
            ""
        )
        & IF (
            escal >= 10,
            FORMAT ( escal, "0" ) & "% de los recontactos vienen de un canal de autoservicio hacia un agente, "
                & "lo que apunta a contenido de autoayuda insuficiente para esos motivos. ",
            ""
        )
        & "Patrón observado en los datos, no causalidad confirmada."
```

---

## 14. Notas de uso

- Marca `dim_date` como tabla de fechas (**Modelado → Marcar como tabla de fechas**,
  columna `Date`). Sin eso las medidas `PW` no funcionan.
- Las medidas `PW` comparan contra la misma ventana siete días atrás. Con una sola
  semana seleccionada devuelven la semana anterior completa.
- `Recontact Rate` no responde al filtro de país porque la pestaña Recontact no trae
  esa dimensión. Está documentado en la hoja `Assumptions` del modelo.
- Formatea `QA Score`, `CSAT Score` y `Recontact Rate` como número decimal con un
  decimal (dos para recontacto) y sufijo `%` desde el panel de formato, no
  multiplicando de nuevo.
- **Toda medida de tasa es una razón de sumas,** nunca un promedio de razones. En la
  pestaña Recontact las filas son cubetas preagregadas de tamaños muy distintos, así
  que promediar las tasas por fila devolvería 40.51% en lugar de 5.83%. La única
  excepción deliberada es `QA Score`, donde la unidad de análisis es la auditoría y el
  promedio simple de los scores por auditoría es lo correcto.
- `dim_recontact_scope` no se relaciona con ninguna tabla. Si Power BI la detecta y
  crea una relación automática, bórrala: las medidas de alcance resuelven el filtro de
  canal por su cuenta y una relación activa las rompería.
- Las medidas de alcance de recontacto y las de dispersión por canal ignoran a
  propósito la segmentación de canal, porque comparan alcances fijos. El resto de las
  medidas sí responde a todos los filtros.
- `[QA Score Simple Channel Average]` es diagnóstica. Sirve para explicar el efecto del
  peso de Live Chat sobre el promedio; no la uses como KPI ni la muestres junto a las
  metas.
