import {
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  LineChart,
  PieChart,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
  useCanvasState,
} from "cursor/canvas";

type Tab = "lectura" | "canales" | "motivos" | "equipo";

const SOURCE =
  "Fuente: Business Case mayo 2026 · Market = All · Week = todas · Day = All · fórmulas oficiales (no promedios de tasas).";

export default function HistoriaMayoCx() {
  const [tab, setTab] = useCanvasState<Tab>("tab", "lectura");

  return (
    <Stack gap={20}>
      <Stack gap={6}>
        <H1>Qué cuentan estos números</H1>
        <Text tone="secondary">
          Mayo 2026 · 2,460 evaluaciones QA · 77,266 encuestas CSAT · 994,591
          contactos. La lectura es de interpretación, no cambia las fórmulas
          del dashboard.
        </Text>
      </Stack>

      <Callout tone="warning" title="La tesis en una frase">
        QA dice que el agente hizo el proceso bien. El cliente dice que no se
        resolvió. El Recontact oficial casi cumple porque Self Help diluye el
        mix: dos de cada tres contactos ni siquiera pasan por un agente
        auditado.
      </Callout>

      <Grid columns={3} gap={16}>
        <Stat value="94.14" label="QA vs meta 85 · verde +9.14" tone="success" />
        <Stat value="79.95%" label="CSAT vs meta 85% · rojo −5.05" tone="danger" />
        <Stat value="5.83%" label="Recontact vs 5.44% · ámbar +0.39" tone="warning" />
      </Grid>

      <Row gap={8} wrap>
        <Pill active={tab === "lectura"} onClick={() => setTab("lectura")}>
          La historia
        </Pill>
        <Pill active={tab === "canales"} onClick={() => setTab("canales")}>
          Canales
        </Pill>
        <Pill active={tab === "motivos"} onClick={() => setTab("motivos")}>
          Motivos de contacto
        </Pill>
        <Pill active={tab === "equipo"} onClick={() => setTab("equipo")}>
          Agentes y tenure
        </Pill>
      </Row>

      {tab === "lectura" && <Lectura />}
      {tab === "canales" && <Canales />}
      {tab === "motivos" && <Motivos />}
      {tab === "equipo" && <Equipo />}

      <Text size="small" tone="tertiary">
        {SOURCE}
      </Text>
    </Stack>
  );
}

function Lectura() {
  return (
    <Stack gap={20}>
      <H2>Tres KPIs, tres historias distintas</H2>
      <Text>
        El promedio global es engañoso si se lee como “la operación está
        bien”. QA está holgado. CSAT es el miss real: 5.05 puntos bajo la
        meta, justo fuera de la banda ámbar de 5 puntos. Recontact está a
        0.39 puntos de 5.44% —cerca en el encabezado, lejos en los canales
        vivos.
      </Text>

      <Grid columns="1.2fr 1fr" gap={20} align="start">
        <Stack gap={8}>
          <H3>CSAT no es tibio: está polarizado</H3>
          <Text>
            De 77,266 encuestas, 80.0% son 4★ o 5★ (meta 85%). El hueco son
            ~3,900 encuestas. No es un mar de 3★: el 16.5% del universo es
            1★ (12,753). El 82% de los insatisfechos son 1★, no 2★/3★.
            Convertir ~31% de esas 1★ a 4–5★ cierra la meta.
          </Text>
          <Text tone="secondary">
            VOC en comentarios negativos: Refund / compensation not received
            (754), No solution provided (664), Driver behavior (435). El
            cliente habla de resultado (reembolso, solución, conductor), no
            de saludo ni de script.
          </Text>
        </Stack>
        <Stack gap={8}>
          <Text size="small" tone="secondary" weight="semibold">
            Mix de estrellas · % de encuestas
          </Text>
          <PieChart
            donut
            size={220}
            data={[
              { label: "5 Stars (75.7%)", value: 58486, tone: "success" },
              { label: "4 Stars (4.3%)", value: 3292, tone: "info" },
              { label: "3 Stars (2.3%)", value: 1793, tone: "warning" },
              { label: "2 Stars (1.2%)", value: 942, tone: "neutral" },
              { label: "1 Star (16.5%)", value: 12753, tone: "danger" },
            ]}
          />
          <Text size="small" tone="tertiary">
            CSAT oficial = (4★+5★) / Feedback CNT. 61,778 satisfechos de
            77,266.
          </Text>
        </Stack>
      </Grid>

      <Divider />

      <H2>QA 94 no es “todos en 94”</H2>
      <Text>
        El histograma es bimodal. El 82.7% de las auditorías sacan 100. El
        4.5% sacan 0 (critical fail: 110 de 2,460). El 17.3% tiene al menos
        un fail (426 auditorías). El 94.14 es un promedio de muchos
        perfectos y una cola fatal corta —no un centro de masa en 94.
      </Text>
      <BarChart
        categories={["0 (fail crítico)", "70", "80", "90", "100"]}
        series={[
          {
            name: "Auditorías",
            data: [110, 2, 21, 293, 2034],
            tone: "info",
          },
        ]}
        height={200}
        yMax={2200}
      />
      <Text size="small" tone="tertiary">
        Distribución de QA Score · n = 2,460 · mayo 2026. Un fail crítico
        pone el score en 0; el resto parte de 100 y resta 10 por atributo.
      </Text>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader trailing="volumen">Time management</CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text>
                133 fails (25.7% de los fails). Impacto en el promedio: −1.2
                pp. Es el atributo más frecuente, no crítico.
              </Text>
              <Text size="small" tone="secondary">
                Greeting and identification: 96 fails (−0.42 pp). Coaching
                de proceso, no de riesgo.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing="letalidad">Service availability</CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text>
                Solo 46 fails, pero −1.76 pp en el promedio global —el
                mayor impacto. Es CRITICAL: un fail tumba el score a 0.
              </Text>
              <Text size="small" tone="secondary">
                Service attitude: 71 fails CRITICAL (−0.57 pp). Complete and
                correct information: 28 fails CRITICAL (−1.07 pp). Pocas
                veces, caro.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <H2>El tiempo: QA estable, CSAT atascado, Recontact sí bajó</H2>
      <Grid columns={2} gap={16}>
        <Stack gap={8}>
          <Text size="small" tone="secondary" weight="semibold">
            QA Score y CSAT por semana (%)
          </Text>
          <LineChart
            categories={["W19", "W20", "W21", "W22"]}
            series={[
              { name: "QA Score", data: [92.4, 94.9, 94.2, 95.5], tone: "success" },
              { name: "CSAT", data: [79.2, 80.1, 81.0, 79.4], tone: "danger" },
            ]}
            valueSuffix="%"
            beginAtZero={false}
            yMin={75}
            yMax={100}
            height={220}
            referenceLines={[{ value: 85, label: "Meta 85", tone: "neutral" }]}
            showValues
          />
          <Text size="small" tone="tertiary">
            W18 no tiene QA (auditorías arrancan W19; CSAT esa semana: 79.8%).
            CSAT nunca cruza 85. W22: QA en máximo del mes y CSAT vuelve a rojo.
          </Text>
        </Stack>
        <Stack gap={8}>
          <Text size="small" tone="secondary" weight="semibold">
            Recontact Rate por semana (%)
          </Text>
          <LineChart
            categories={["W18", "W19", "W20", "W21", "W22"]}
            series={[
              { name: "Recontact", data: [6.33, 6.04, 5.98, 5.81, 5.26], tone: "warning" },
            ]}
            valueSuffix="%"
            beginAtZero={false}
            yMin={5}
            yMax={7}
            height={220}
            referenceLines={[{ value: 5.44, label: "Meta 5.44", tone: "success" }]}
            showValues
          />
          <Text size="small" tone="tertiary">
            Mejora de 6.33% a 5.26% (W22 ya bajo meta). FCR derivado oficial
            = 100 − Recontact; no tiene meta de negocio.
          </Text>
        </Stack>
      </Grid>

      <Callout tone="info" title="Qué no se puede concluir">
        Bajar Recontact en W22 no levantó CSAT (cayó a 79.4%). Resolver a la
        primera y que el cliente se sienta bien no es el mismo mecanismo este
        mes. QA alto tampoco predice CSAT: el mes termina con el QA más alto
        y el CSAT otra vez en rojo.
      </Callout>
    </Stack>
  );
}

function Canales() {
  return (
    <Stack gap={20}>
      <H2>La inversión Phone vs Live Chat</H2>
      <Text>
        Live Chat es el 85.6% de las auditorías y arrastra el QA global a
        verde. Phone es el 14.4% y está bajo meta. CSAT hace lo contrario:
        Phone cumple, Chat no. Si se coachingea “calidad” mirando solo el
        94.14, se entrena el canal que ya pasa QA y se ignora el que genera
        el CSAT bajo.
      </Text>

      <BarChart
        categories={["Live Chat", "Phone"]}
        series={[
          { name: "QA Score", data: [96.01, 83.04], tone: "success" },
          { name: "CSAT", data: [77.55, 86.26], tone: "danger" },
          { name: "Recontact", data: [15.99, 13.47], tone: "warning" },
        ]}
        valueSuffix=""
        height={240}
        yMax={110}
        referenceLines={[{ value: 85, label: "Meta QA/CSAT 85", tone: "neutral" }]}
        showValues
      />
      <Text size="small" tone="tertiary">
        QA y CSAT en la misma escala 0–100. Recontact es % (15.99 y 13.47),
        no comparable en magnitud con 85 —se muestra para ver que ambos
        canales vivos están ~3× sobre 5.44%. Chat: 2,105 evals / 55,962
        encuestas / 243,626 contactos. Phone: 355 / 21,304 / 49,674.
      </Text>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader trailing="QA verde · CSAT rojo">Live Chat</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                QA 96.01 (n=2,105). CSAT 77.55 (−7.45 vs meta). Recontact
                15.99% sobre 243,626 contactos —el mayor volumen de
                recontactos vivos (38,961).
              </Text>
              <Text size="small" tone="secondary">
                Lectura: el rubric se cumple; el ticket no cierra el problema
                del cliente (status, cargo, refund). Coaching de script aquí
                tiene poco ROI.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing="QA rojo · CSAT verde">Phone</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text>
                QA 83.04 (n=355, −2.0 vs 85) —único canal auditado bajo meta.
                CSAT 86.26 (cumple). Recontact 13.47% sobre 49,674 contactos.
              </Text>
              <Text size="small" tone="secondary">
                Lectura: el teléfono falla atributos de proceso (tiempo,
                saludo) que el auditor ve y el cliente, en media, perdona.
                Aquí sí hay caso de coaching QA.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <H2>Recontact 5.83% es un mix, no un resultado de agentes</H2>
      <Text>
        Self Help es el 67.0% de los 994,591 contactos, con Recontact 1.22%.
        Eso empuja el oficial a 5.83%. Sin Self Help el rate es 15.19%. En
        Phone + Live Chat (el universo que QA puede tocar) es 15.56% —casi
        10 puntos sobre la meta 5.44%.
      </Text>

      <BarChart
        horizontal
        categories={[
          "All 12 channels (oficial)",
          "Excluding Self Help",
          "Phone + Live Chat only",
        ]}
        series={[
          { name: "Recontact Rate", data: [5.83, 15.19, 15.56], tone: "warning" },
        ]}
        valueSuffix="%"
        height={180}
        referenceLines={[{ value: 5.44, label: "Meta 5.44", tone: "success" }]}
        showValues
      />
      <Text size="small" tone="tertiary">
        Scopes de Recontact · Σ Recontact Volume / Σ Contacts. Nunca
        promediar tasas de fila. Self Help: 666,650 contactos · 8,154
        recontactos.
      </Text>

      <Table
        headers={["Canal", "Contactos", "Share", "Recontact", "vs 5.44%"]}
        columnAlign={["left", "right", "right", "right", "right"]}
        rowTone={["success", "danger", "warning", "warning", "warning"]}
        rows={[
          ["Self Help", "666,650", "67.0%", "1.22%", "−4.22"],
          ["Live Chat", "243,626", "24.5%", "15.99%", "+10.55"],
          ["Phone", "49,674", "5.0%", "13.47%", "+8.03"],
          ["GPTBot", "19,508", "2.0%", "13.73%", "+8.29"],
          ["Help Center", "12,224", "1.2%", "7.70%", "+2.26"],
        ]}
        striped
      />
      <Text size="small" tone="tertiary">
        FCR derivado oficial ≈ 94.17% (100 − 5.83). En Phone+Chat ≈ 84.4%.
        Usar el FCR global para decir “resolvemos a la primera” mezcla
        self-service con agentes.
      </Text>

      <Callout tone="danger" title="Implicación operativa">
        El 5.83 ámbar no se arregla pidiendo a los agentes “menos
        recontacto” en abstracto. El palanca de volumen está en Live Chat
        (38,961 recontactos) y en tres Contact reason Lv4 de status / cargo /
        refund. Self Help ya está “barato”; no es el problema.
      </Callout>
    </Stack>
  );
}

function Motivos() {
  return (
    <Stack gap={20}>
      <H2>Los mismos tres motivos empujan CSAT y Recontact</H2>
      <Text>
        No es un long-tail de 80 reasons. Status del pedido, cargo de
        cancelación y refund concentran insatisfacción y recontacto. En esos
        CRs el QA suele estar verde: el agente “pasa el audit” y el cliente
        vuelve. Eso apunta a política, herramienta o promesa —no a un hueco
        masivo de skill.
      </Text>

      <BarChart
        horizontal
        categories={[
          "order status / delay info",
          "cancellation charge/debt",
          "order status & delays",
          "don't want the order",
          "refund status",
          "incomplete order",
        ]}
        series={[
          {
            name: "Encuestas insatisfechas (1–3★)",
            data: [3189, 1951, 1800, 1229, 1181, 874],
            tone: "danger",
          },
        ]}
        height={240}
      />
      <Text size="small" tone="tertiary">
        Top Contact reason Lv4 por volumen insatisfecho · CSAT mayo 2026.
        “don't want the order” y “incomplete order” tienen CSAT alto (88.3 y
        89.4): mucho volumen, poca queja.
      </Text>

      <Table
        headers={[
          "Contact reason Lv4 (detail)",
          "CSAT",
          "Insatisfechos",
          "Recontact",
          "QA",
          "Patrón",
        ]}
        columnAlign={["left", "right", "right", "right", "right", "left"]}
        rowTone={["danger", "danger", "danger", "neutral", "danger", "warning"]}
        striped
        rows={[
          [
            "user request order status or delay information",
            "67.8%",
            "3,189 / 9,918",
            "16.92% · 13,014 rec",
            "—",
            "CSAT bajo + RC alto",
          ],
          [
            "User disagrees with cancellation charge/debt",
            "67.4%",
            "1,951 / 5,992",
            "12.96% · 6,599 rec",
            "91.4 (n=59)",
            "QA ok · cliente no",
          ],
          [
            "order status & delays",
            "64.7%",
            "1,800 / 5,096",
            "19.34% · 7,680 rec",
            "97.3 (n=45)",
            "QA ok · cliente no",
          ],
          [
            "user don't want the order anymore",
            "88.3%",
            "1,229 / 10,518",
            "2.20% · 6,216 rec",
            "—",
            "Alto volumen, CSAT ok",
          ],
          [
            "refund status and conditions",
            "67.0%",
            "1,181 / 3,582",
            "15.69% · 2,901 rec",
            "98.4 (n=45)",
            "QA ok · cliente no",
          ],
          [
            "Order appears completed, not received — full service",
            "—",
            "—",
            "—",
            "68.2 (n=49)",
            "Aquí sí falla QA",
          ],
        ]}
      />
      <Text size="small" tone="tertiary">
        QA y CSAT no comparten el mismo grano de CR en todos los nombres
        (casing / n distinto). Donde hay n QA decente, el patrón “QA alto +
        CSAT bajo + RC alto” se sostiene. Excepción: mismatch de status de
        orden (completed vs not received), QA 68.2 con n=49 —ahí el proceso
        de agente también se rompe.
      </Text>

      <H3>VOC confirma el mismo cuello</H3>
      <Table
        headers={["Tema en comentarios negativos", "Menciones", "% de tagged"]}
        columnAlign={["left", "right", "right"]}
        rows={[
          ["Refund / compensation not received", "754", "27.4%"],
          ["No solution provided", "664", "24.2%"],
          ["Driver behavior", "435", "15.8%"],
          ["Order / trip issues", "292", "10.6%"],
          ["Long wait time", "237", "8.6%"],
          ["Poor service", "196", "7.1%"],
        ]}
        striped
      />
      <Text size="small" tone="tertiary">
        Universo: 8,223 comentarios reales; 4,655 negativos. Temas sobre una
        muestra tagged de comentarios low-score. Driver behavior es
        marketplace, no skill de agente CX —el contacto hereda un problema
        que CX no controla del todo.
      </Text>

      <Callout tone="warning" title="Worklist, no más promedio">
        El combined analysis del dashboard (CRs que fallan 2+ KPIs) ya es la
        cola de trabajo: order status & delays, cancellation charge/debt,
        refund status, cash/card antifraud, courier overcharged. Ahí el
        impacto es volumen de recontacto × CSAT roto, no un agente suelto.
      </Callout>
    </Stack>
  );
}

function Equipo() {
  return (
    <Stack gap={20}>
      <H2>Los promedios esconden concentración —pero CSAT es sistémico</H2>
      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader trailing="222 agentes · ≥5 audits">QA by agent</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Stat value="33" label="bajo meta 85 (15% del roster)" tone="warning" />
              <Text>
                El miss de QA es minoría. El concentrador de fails no es el
                score más bajo: Agent 190 (Supervisor 8) tiene 12 fails y QA
                82.7. Coaching por volumen de fail, no por “el peor promedio”.
              </Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing="304 agentes · ≥20 encuestas">CSAT by agent</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Stat value="223" label="bajo meta 85 (73% del roster)" tone="danger" />
              <Text>
                El miss de CSAT es la norma, no la cola. Aun así el volumen
                se concentra: Agent 212 (Supervisor 11) — CSAT 27.1, 411
                insatisfechos de 564 encuestas. Eso sí es un caso puntual.
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Callout tone="info" title="Supervisor 11 es el contraste">
        QA 90.7 (n=44, 15 agentes) y CSAT 71.0 sobre 4,243 encuestas. El
        supervisor “pasa calidad” y pierde satisfacción. Agent 212 vive
        ahí. No se resuelve con más calibración de rubric; hay que abrir
        mix de CR y canal de ese roster.
      </Callout>

      <Table
        headers={["Supervisor", "QA", "Evals", "CSAT", "Encuestas", "Lectura"]}
        columnAlign={["left", "right", "right", "right", "right", "left"]}
        rowTone={["danger", "warning", "warning", "warning", "danger"]}
        striped
        rows={[
          ["Supervisor 24", "76.2", "13", "77.0", "139", "QA y CSAT bajos; n QA chico"],
          ["Supervisor 22", "81.8", "17", "81.1", "1,664", "Ambos bajo 85"],
          ["Supervisor 12", "82.1", "53", "79.3", "2,583", "QA bajo con n útil"],
          ["Supervisor 23", "82.9", "14", "80.3", "467", "QA bajo; n chico"],
          ["Supervisor 11", "90.7", "44", "71.0", "4,243", "QA ok · peor CSAT de volumen"],
        ]}
      />
      <Text size="small" tone="tertiary">
        Supervisores con peor QA (y Supervisor 11 por CSAT). 71 agentes CSAT
        quedan en “Not mapped to a QA supervisor”. Recontact no tiene grano
        de agente —no se puede clonar el roster.
      </Text>

      <Divider />

      <H2>Tenure: los de más de un año son el único cohort bajo 85</H2>
      <Text>
        New hire está en 92.05. El pico es 3–6 months (96.24). More than 1
        year cae a 83.97 (n=136) —único cohort ámbar. No se puede leer como
        “los veteranos se descuidan”: tenure solo existe en QA, n es el más
        chico, y puede ser mix de Phone / CRs difíciles. Sirve como alerta,
        no como causa.
      </Text>
      <BarChart
        categories={["New hire", "30–90 d", "3–6 mo", "6–12 mo", "> 1 year"]}
        series={[
          { name: "QA Score", data: [92.05, 95.68, 96.24, 91.89, 83.97], tone: "info" },
        ]}
        valueSuffix=""
        height={220}
        yMin={75}
        yMax={100}
        beginAtZero={false}
        referenceLines={[{ value: 85, label: "Meta 85", tone: "success" }]}
        showValues
      />
      <Text size="small" tone="tertiary">
        QA Score por Tenure_Cohort · n = 259 / 1,128 / 529 / 408 / 136.
        CSAT y Recontact no tienen este corte.
      </Text>

      <H2>Qué haría con esto (prioridad, no catálogo)</H2>
      <Table
        headers={["Prioridad", "Dónde", "Por qué", "Qué no hacer"]}
        columnAlign={["left", "left", "left", "left"]}
        rowTone={["danger", "danger", "warning", "warning", "info"]}
        rows={[
          [
            "1",
            "Contact reason Lv4: status / delay",
            "13k+ recontactos y 3,189 insatisfechos. QA alto.",
            "Más training de greeting",
          ],
          [
            "2",
            "Cancellation charge / debt + refund",
            "Mismo patrón: CSAT ~67, RC alto, QA verde.",
            "Tratarlo como skill de agente",
          ],
          [
            "3",
            "Live Chat (no el 94 global)",
            "72% de las encuestas, CSAT 77.6, RC 16%.",
            "Celebrar QA 96 de Chat como éxito CX",
          ],
          [
            "4",
            "Phone QA + Agent 212 / Supervisor 11",
            "Único canal QA bajo meta; un agente con CSAT 27.",
            "Coaching masivo del roster CSAT (223 personas)",
          ],
          [
            "5",
            "Self Help / FCR oficial",
            "Explicar a negocio que 5.83% no es el live rate.",
            "Usar FCR 94% como prueba de resolución",
          ],
        ]}
      />
    </Stack>
  );
}
