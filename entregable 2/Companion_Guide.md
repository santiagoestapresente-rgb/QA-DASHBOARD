# Companion Guide — Entregable 2
### Cómo estudiar, contar y defender el Weekly Performance Report

Esta guía no repite el reporte: te da el **hilo**, los **números que sí hay que
memorizar**, y las **respuestas a las preguntas incómodas**. Si lees solo las
secciones 1, 2 y 3 ya puedes sostener una conversación de 10 minutos con un VP.

---

## 1. La tesis en una frase

> **Estamos midiendo la calidad de la conversación, no la solución del problema.
> Por eso QA da 94.14 (meta 85) mientras el cliente califica 79.95% (meta 85) y
> vuelve a contactarnos.**

Si solo puedes decir una cosa, di esa. Todo el reporte existe para probarla.

**La versión de 20 segundos:**
"El scorecard de calidad va verde y las dos métricas que le importan al cliente
van en rojo. Revisamos si era ruido: no lo es, los procesos son estables. Revisamos
si QA predice satisfacción: no la predice, la correlación es prácticamente cero.
Hay dos huecos de medición, no uno. La rúbrica no puntúa resolución: un caso sin
resolver pero con proceso seguido saca 96.87 — eso no se le descuenta al agente;
se reporta como tasa de resolución. Y Chat, el 85.6% de la muestra, no tiene
crítico de información correcta: 372 chats no siguieron proceso y 297 de ellos
siguen en 100. Si eso valiera 0, Chat sería 80.14, bajo meta. Poner ese atributo
hace honesto el 94. No mueve CSAT por sí solo: CSAT sigue a si se resolvió."

---

## 2. Los números que debes tener en la cabeza

Son diez. Si te sabes estos diez, improvisas el resto.

| # | Número | Qué es | Por qué importa |
|---|--------|--------|-----------------|
| 1 | **94.14 / 79.95 / 5.83** | QA, CSAT, Recontacto | El titular: verde, rojo, ámbar |
| 2 | **96.87** | QA de "sin resolver pero con proceso seguido" (n=527) | No penalices al agente; reporta resolución |
| 3 | **82.7%** | Auditorías que sacan exactamente 100 | QA no discrimina: es aprobado/reprobado disfrazado de escala |
| 4 | **R² = 0.023** | Correlación QA vs CSAT sobre 45 contact reasons | Subir el **score** de QA no movería CSAT |
| 4b | **R² = 0.64** | % Resolved del auditor vs CSAT, 35 CR Lv4 (≥3 auditorías, ≥20 encuestas) | Donde el **tipo de caso** se puede cerrar, el CSAT de esa cola va bien. No es el agente ni el ticket |
| 5 | **96.01 → 80.14** | Chat hoy vs Chat si no-proceso valiera 0 (372 chats; 297 aún en 100) | El 96 de Chat es un atributo que no existe, no calidad |
| 6 | **5.83% vs 15.56%** | Recontacto oficial vs solo Phone + Live Chat | Self Help (67% de contactos, 1.22%) diluye el número |
| 7 | **49.5% vs 22.0%** | Insatisfacción que el auditor asigna a Proceso vs a Agente | No es un problema de gente |
| 8 | **19.34%** | Recontacto de "order status & delays" (QA 97.3, CSAT 64.7%) | El caso que resume todo el reporte |
| 9 | **42 agentes** | Cuartil 4 de QA (media 82.4, rango 36–92) | La población concreta de coaching |
| 10 | **27.1% en 564 encuestas** | CSAT del Agente 212 (411 clientes insatisfechos) | El outlier individual que QA nunca detectó |

**Truco de memoria:** 94-80-6 es el titular. 97 es “siguió proceso y no resolvió”
(no penalices). 80.14 es el Chat honesto. 83% saca 100. Cero correlación.

---

## 3. El hilo narrativo en 6 movimientos

El reporte está construido para que cada sección responda la objeción de la
anterior. Cuéntalo en este orden y nadie te interrumpe.

**1. El titular contradictorio.**
QA verde, CSAT rojo, recontacto ámbar. Tres métricas de la misma operación que
no pueden ser todas ciertas al mismo tiempo.

**2. "¿No será ruido de un mes?"** → *Control charts.*
Las tres métricas están dentro de límites de control. No hay causas especiales.
Es un proceso **estable**, y ese es el problema: está establemente mal centrado.
CSAT no está teniendo un mal mes, está diseñado para dar 80.

**3. "¿Entonces dónde falla?"** → *Pareto por canal, atributo y contact reason.*
Phone está en 83.04 pero es solo 14.4% de la muestra auditada, así que no mueve
el promedio. Phone ya mide información completa y correcta (crítico). Chat no:
los defectos que sí se ven están en el saludo, y 372 chats no siguieron proceso
con 297 aún en 100. Si eso fuera crítico, Chat sería 80.14.

**4. "¿Y no será que los agentes son malos?"** → *Sección People + Ishikawa.*
Los cuartiles 1, 2 y 3 de QA están en 99.9, 98.8 y 94.9: tres cuartas partes de
la fuerza laboral es estadísticamente idéntica. Un 100 de Chat no prueba que la
gente esté bien: el instrumento no ve process-fail. CSAT sí separa: va de 27% a
97%. El hueco de CSAT no es gente: el auditor asigna 49.5% de la insatisfacción
a Proceso contra 22.0% al agente.

**5. "Pruébamelo con un caso."** → *Análisis combinado + resolución vs CSAT.*
"order status & delays": QA 97.3, CSAT 64.7%, recontacto 19.34%. El agente ejecuta
un guion sin ETA. Al lado: las colas que **sí se pueden cerrar** (wrong / incomplete /
inedible / damaged) tienen CSAT ≥ 85; fraud / fee / modify no se pueden y son los
blockers. Los 5 whys de las 699 no resueltas dicen política o tools, no saludo.

**6. "¿Qué hago el lunes?"** → *Plan de control + action plans.*
Dos palancas, no una. Reportar la **tasa de resolución (auditoría)** y exigir
dueño en cada no resuelto (eso puede mover CSAT). Añadir en Chat el crítico de
información correcta / KB que Phone ya tiene (eso hace honesto el 96; no mueve
CSAT solo). Rebalancear la muestra a 30% Phone, ETA en vivo, coaching a los 42
agentes del Q4. Cada acción con dueño, fecha y severidad del problema.

---

## 4. Guion por lámina (una línea cada una)

| # | Lámina | Lo único que tienes que decir |
|---|--------|------------------------------|
| 2 | Scope | "Cuatro fuentes, un mes, 2,460 auditorías sobre 994 mil contactos — la muestra auditada es 0.25%." |
| 3 | Executive summary | "Una verde, una roja, una ámbar. La verde es la que no deberías creer." |
| 4 | Hallazgo crítico | "Dos huecos: 96.87 no se penaliza; Chat sin crítico de info sería 80.14." |
| 5 | Control charts | "Estable no significa bueno: significa que va a volver a pasar." |
| 7 | QA por canal | "Chat no está 'mejor': no mide info correcta. Phone sí, y el cliente lo premia." |
| 8 | QA Phone | "Un atributo, Time management, es dos tercios de los defectos. Info correcta ya es crítico." |
| 9 | QA Live Chat | "372 no siguieron proceso; 297 aún en 100. Si valieran 0, Chat sería 80.14." |
| 10 | Defectos | "7 de 17 atributos, 83% de las fallas. Y 83% de las auditorías dan 100." |
| 11 | QA por CR | "Todas las razones rojas son pedidos no entregados o cobros disputados." |
| 13 | CSAT | "75.7% da 5 estrellas y 16.5% da 1: no hay término medio, hay dos poblaciones." |
| 14 | Voz del cliente | "35% de los comentarios negativos son 'no me resolvieron' o 'no me devolvieron'. Actitud del agente: 4.3%." |
| 16 | Recontacto | "5.83% es real pero engañoso: Self Help es 67% del volumen a 1.22%." |
| 17 | Recontacto por CR | "Los peores en repetición sacan 93–98 en QA. Ese es el punto." |
| 19 | Cuartiles de agentes | "QA no separa agentes; un 100 de Chat no prueba que la gente esté bien. Foco: 42 en Q4." |
| 20 | Supervisores | "15 de 16 equipos pasan QA, solo 1 pasa CSAT. No es un agente, es el sistema." |
| 22 | Análisis combinado | "Verde en QA, rojo en CSAT y rojo en recontacto, en la misma fila." |
| 22b | Resolución vs CSAT | "Árbol CR padre → SUB_CR hijo. Resolved ≥70 y CSAT ≥85 semaforizados igual que el resto del deck." |
| 22c | 5 whys | "699 no resueltas (política/tools; la tabla suma 699). 1,415 resueltas: reembolso, explicación o reporte. CR-mix CSAT 70.9 vs 52.1 — no hay CSAT de esos tickets." |
| 23 | Ishikawa | "Medición = el QA mentiroso (R² 0.023). Proceso = 527/699 NR siguieron proceso; 5-whys política/tools. El dueño CSAT es el CR padre, no el tag anidado." |
| 24 | Plan de control | "Reportar resolución por CR/SUB_CR (palanca CSAT). Crítico de info en Chat (palanca QA honesto)." |
| 26-27 | Action plans | "Doce acciones, con dueño y fecha. La severidad califica el problema, no el avance." |

---

## 5. Las 7 herramientas de calidad — qué es y por qué la usaste

Te lo van a preguntar porque el caso las pide explícitamente. Respuesta corta y
la razón de uso:

| Herramienta | Qué es en una frase | Dónde está y para qué |
|-------------|---------------------|----------------------|
| **Check sheet** | Formato estructurado para recolectar datos de forma consistente | Lámina 2: las cuatro fuentes, su grano y su volumen |
| **Pareto** | El 80% del efecto viene del 20% de las causas | Defectos QA, Phone, Chat y recontacto: prioriza dónde invertir |
| **Histograma** | La forma de la distribución, no solo el promedio | Lámina 10: revela que QA es bimodal (0 o 100), no una escala |
| **Control chart** | Separa variación normal de causas especiales | Lámina 5: prueba que el problema es sistémico, no un mal mes |
| **Scatter / correlación** | Mide si dos variables se mueven juntas | Lámina 4 (el gráfico) y 14 (las cifras): QA no predice CSAT, R² 0.023 |
| **Ishikawa** | Organiza las causas en familias para no saltar a conclusiones | Lámina 23: Medición (el QA mentiroso) y Proceso (CR padre / SUB_CR hijo + 5-whys) |
| **Flowchart** | Dibuja el proceso para ver dónde se rompe el circuito | Lámina 24: clasifica en CR/SUB_CR y verifica el CSAT de ese padre |

**Si te preguntan "¿por qué un control chart y no una línea de tendencia?"**
"Porque una línea de tendencia me dice si subió o bajó; el control chart me dice
si ese cambio es señal o ruido. Sin eso, reaccionaría a variación normal."

---

## 6. Cómo explicar lo técnico en simple

| Si dices esto… | Di mejor esto |
|----------------|---------------|
| "R² de 0.023" | "Si me das el QA de una razón de contacto, no puedo adivinar su CSAT. Son dos cosas distintas." |
| "Está dentro de límites de control" | "Esto no fue un mal mes. Es lo que el proceso produce siempre. Va a volver a pasar." |
| "Distribución bimodal" | "No hay agentes 'regulares'. O sacan 100 o sacan 0. La escala del 1 al 100 es ficticia." |
| "Cuartil 4" | "El 25% de abajo. Son 42 personas con nombre y apellido, no un porcentaje." |
| "Dilución del denominador" | "El número global se ve bien porque metimos el autoservicio, que casi nunca genera repetición." |
| "FCR" | "Eso es 100 menos recontacto. No es '¿se resolvió el caso?'. El FCR oficial se ve bien porque el recontacto oficial está diluido por Self Help." |
| "Correlación no implica causalidad" | "Esto es una hipótesis, no una prueba. La prueba es que el número se mueva cuando cambiemos el proceso." |

---

## 7. Las preguntas que te van a hacer

**"Si QA está en 94, ¿por qué debería preocuparme?"**
Porque 94 no significa clientes satisfechos. Un caso donde el agente siguió todo
el proceso y **no resolvió** promedia 96.87 — eso no se le cobra al agente; se
reporta como resolución. El 94 además está inflado por Chat: 85.6% de la muestra,
sin crítico de información correcta, con 297 de 372 process-fails aún en 100. Si
eso valiera 0, Chat sería 80.14.

**"¿No será que la meta de CSAT es muy alta?"**
Podría ser, pero el argumento no depende de la meta. Depende de que el 16.5% de
los clientes da 1 estrella y de que el 35% de los comentarios negativos digan
"no me resolvieron" o "no me devolvieron el dinero". Eso es independiente de
dónde pongas la meta.

**"¿La muestra de auditorías es suficiente?"**
2,460 auditorías sobre 994 mil contactos es 0.25%. Es suficiente para detectar
patrones de atributo, y **no** es suficiente para juzgar razones de contacto
individuales con pocos casos. Por eso marco explícitamente los n bajos, y por eso
una de las acciones es rebalancear la muestra a 30% Phone.

**"Estás actuando sobre un n=4 en Market Place."**
Correcto, y está señalado en el reporte. La acción de Market Place lleva una nota
de baja confianza: pide 20+ auditorías antes de comprometer recursos. La incluí
porque el CSAT de Market Place sí tiene volumen (3,489 encuestas), pero la
evidencia de QA no.

**"¿Recontacto está en meta o no?"**
Las dos cosas, y hay que reportar ambas. Oficial 5.83% contra meta 5.44%: casi en
meta. Pero Self Help es 67% del volumen con 1.22% de repetición y arrastra el
promedio. En los canales donde hay un humano, la tasa es 15.56% — casi tres veces
la meta. El número oficial sirve para el contrato; el auditado sirve para decidir.

**"¿Por qué Phone tiene peor QA pero mejor CSAT que Chat?"**
Porque cada canal se puntúa con su propia rúbrica. Phone tiene 12 atributos e
incluye **información completa y correcta** como crítico. Chat tiene 8, de
etiqueta, y no pregunta si se dio la info bien ni si se siguió el KB. Phone es
castigado por la rúbrica y premiado por el cliente. El 96 de Chat no es calidad
mejor: es un hueco de medición.

**"Si ponemos el crítico de info en Chat, ¿sube CSAT y baja recontacto?"**
No por sí solo. Ese atributo hace honesto el QA (96 → 80). CSAT y recontacto
siguen a **si se resolvió**, no a si se siguió el proceso. A nivel CR Lv4,
% Resolved vs CSAT da R² 0.64 (n=35, piso ≥3 auditorías y ≥20 encuestas). Eso es
**case mix**, no “el agente que resuelve deja feliz al cliente”: a nivel agente
Chat el R² es ~0, y no hay cruce al mismo ticket. Wrong / incomplete / inedible /
damaged se cierran y el CSAT va ≥ 85. Fraud, delivery fee, modify, pago al courier
no se cierran y son los blockers. Los 5 whys de las 699 no resueltas (campo IA,
no KPI) caen en política que no deja reembolsar o en “no hay herramienta, hay que
escalar”. Cuando sí se resolvió, el 5 why nombra reembolso confirmado, explicación
o un reporte/tool. Order status es la excepción: se marca Resolved y el CSAT sigue
~67 — cerrar el chat no es el outcome. La palanca de cliente es resolución + tools
(ETA, reembolso). No prometas que el atributo de Chat mueve CSAT.

**"¿Quién es el responsable, entonces?"**
El grano es el CR padre y su SUB_CR hijo, no el agente y no el tag Dissatisfaction_Owner
(ese tag solo existe cuando Dissatisfaction = Yes, ~4% de las auditorías). De las 699
no resueltas, 527 siguieron proceso: el 5 why nombra política o tools. El crítico de
Chat sigue siendo coaching/rúbrica: las 372 que no siguieron proceso son gente, y hoy
el score no las ve. No uses el 96 para exonerar agentes ni para explicar CSAT.

**"¿A quién le hago coaching el lunes?"**
A 42 agentes: el cuartil 4 de QA, que promedia 82.4. Cinco supervisores concentran
14 de los 26 agentes bajo meta, así que arrancas por ahí. Y un caso individual
merece nombre: el Agente 212, con 27.1% de CSAT en 564 encuestas — 411 clientes
insatisfechos, 2.7% de toda la insatisfacción del mes, y ninguna auditoría lo marcó.

**"¿No es injusto rankear agentes con 5 auditorías?"**
Por eso el ranking usa un umbral mínimo (5 auditorías para QA, 20 encuestas para
CSAT) y la priorización usa "impacto de coaching" = puntos bajo meta × auditorías.
Así una muestra chica no puede superar a una brecha persistente.

**"¿Cuánto cuesta esto?"**
Reportar resolución es gratis: el auditor ya lo captura. El crítico de info en
Chat es un cambio de rúbrica (QA Lead), no un proyecto de producto. El ETA en
vivo sí requiere producto. Orden: primero reportar si se resolvió y puntuar info
en Chat; después tools, porque sin medición no sabes si lo demás funcionó.

**"¿Buen FCR y mal recontacto? ¿No es lo mismo?"**
En este dashboard, sí son el mismo número al revés: FCR = 100 − recontacto.
FCR oficial 94.17% es exactamente recontacto oficial 5.83%. Se ve “bueno”
porque Self Help (67% del volumen, 1.22% de repetición) arrastra el promedio.
En Phone + Chat el recontacto es 15.56%, o sea FCR ~84%. Ninguno de los dos
es la tasa de resolución del auditor (66.9%): esa pregunta si el caso se cerró,
no si el cliente volvió.

**"¿No está ya en el formulario si se resolvió?"**
Sí. El form pregunta “¿se le brindó solución a la solicitud?” y también si se
siguió el proceso. Ninguno de los dos entra al score. Un caso sin resolver y con
proceso seguido sigue sacando 96.87: hay que reportar la tasa de resolución y no
bajarle el 100 al agente cuando el dueño es proceso. Lo que Chat **no** tiene es
un atributo puntuado de información correcta: eso sí hay que agregarlo a la
rúbrica, no solo reportar el dropdown.

**"¿Cuál es el CSAT de las 1,415 resueltas?"**
No existe a nivel ticket: no hay cruce auditoría ↔ encuesta. Lo más cercano es el
CSAT oficial del CR de cada auditoría, promediado: **70.9%** en resueltas vs
**52.1%** en no resueltas. El 79.95% oficial es ponderado por encuestas, no por
auditorías. Si alguien pide “el CSAT de esas 1,415”, la respuesta es esa distinción.

**"Refund status: ¿98.4 o 90.6?"**
Los dos. 98.4 es Live Chat (n=45). 76.4 es Phone (n=25). 90.6 es el mismo CR unido
por mayúsculas (la misma regla que Incomplete order = incomplete order). Combined
ahora muestra n=70 para que no parezca que el número “se movió”.

**"¿Cómo sé que tu plan funcionó?"**
Lámina 24: la correlación QA–CSAT debe subir de R² 0.023 a ≥0.25 en dos trimestres
(eso es la palanca de rúbrica). Resolved vs CSAT en CR ya está en R² 0.64: hay que
mantenerlo ≥0.50, no sustituir el 0.023. CSAT a 85, recontacto auditado a 10%, y
la muestra de Phone de 14.4% a 30%.

**"¿Qué pasa si no hacemos nada?"**
El proceso es estable, así que la predicción es fácil: el mes que viene el QA
vuelve a dar ~94, CSAT vuelve a dar ~80, y "order status & delays" vuelve a
generar cerca de 7,680 contactos repetidos.

---

## 8. Los límites — dilos tú primero

Reconocer las debilidades antes de que las encuentren es lo que separa un análisis
de una presentación de ventas.

- **Un solo mes.** No hay estacionalidad ni comparación año contra año.
- **0.25% de cobertura de auditoría.** Sirve para patrones, no para juzgar casos aislados.
- **El cruce entre fuentes es parcial.** Solo 45 contact reasons tienen QA, CSAT y
  recontacto a la vez; sobre esos 45 se calcula la correlación.
- **11.7% de las encuestas no se pueden mapear a un supervisor.** Los cortes por
  equipo excluyen ese volumen.
- **Delivery es la única línea de negocio en los datos**, por eso los planes se
  cortan por Business Type y no por LOB.
- **80.14 es un contrafactual, no el score oficial.** Asume que “no siguió
  proceso” en Chat se puntuaría como crítico (0). El QA oficial de Chat sigue
  siendo 96.01.
- **Las causas del Ishikawa son hipótesis con evidencia, no causalidad probada.**
  La prueba viene del experimento: cambiar el proceso y ver si el número se mueve.

---

## 9. Plan de tiempo

**Versión 3 minutos (ascensor)**
Tesis → el 96.87 (no penalices) → el 80.14 de Chat (atributo que falta) → dos
palancas: resolución para CSAT, crítico de info en Chat para un QA honesto.
No abras el deck.

**Versión 10 minutos (reunión de equipo)**
Láminas 3, 4, 5, 7, 9, 22, 24. Executive summary, hallazgo crítico, estabilidad,
canal, Chat 80.14, el caso combinado, el plan.

**Versión 25 minutos (comité)**
Los 6 movimientos completos con las láminas del guion de la sección 4. Reserva los
últimos 8 minutos para preguntas: van a venir de la sección 7.

---

## 10. Checklist de estudio

Marca cuando puedas hacerlo **sin mirar**:

- [ ] Decir la tesis en una frase.
- [ ] Recitar los tres KPI con su meta y su color.
- [ ] Explicar por qué 96.87 es el número de resolución (no penalices) y 80.14 el de Chat.
- [ ] Explicar qué es un control chart y por qué lo usaste.
- [ ] Explicar la inversión Phone/Chat y por qué Chat 96 no es calidad.
- [ ] Decir por qué el crítico de Chat no mueve CSAT por sí solo.
- [ ] Dar los dos números de recontacto y por qué son distintos.
- [ ] Nombrar la población de coaching (42 agentes, Q4) y el outlier (Agente 212).
- [ ] Contar el caso de "order status & delays" con sus cuatro cifras.
- [ ] Decir las tres primeras acciones con su dueño.
- [ ] Nombrar tres límites del análisis antes de que te los pregunten.
