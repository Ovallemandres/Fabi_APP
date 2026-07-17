# Documento de Contexto Inicial: Sistema de Gestión, Presupuestos y Facturación de Flotas

**Versión:** 1.1  
**Fecha:** 2026-07-17  
**Estado:** Fuente de verdad del producto (MVP)  
**Empresa emisora de referencia (Excel actual):** MJ SINO IMPORT, C.A. — RIF G-20013109-8

---

## 1. Arquitectura y Tecnologías Base (Requisitos Estrictos)

Stack inicial del proyecto. Toda tecnología nueva que se incorpore debe documentarse aquí.

| Capa | Tecnología | Notas |
|------|------------|--------|
| Backend | **Django** | Apps por dominio, settings split (dev/prod/test) |
| Frontend | **Django Templates + HTMX + Tailwind CSS** | Sin SPA; interacción parcial vía HTMX |
| Base de datos | **PostgreSQL** | Tipado estricto, migraciones seguras, constraints, `unaccent` |
| Cola / cache | **Redis** | Broker de tareas y cache |
| Workers | **Celery** (o RQ equivalente) | PDFs, correos futuros, jobs pesados |
| Cron | **Render Cron Jobs** + tareas Celery beat si aplica | Mantenimiento / jobs periódicos |
| Deploy | **Render.com** | Web service + worker + PostgreSQL + Redis |
| PDF | Obligatorio desde el MVP | Generación en background worker |
| Correo | **Fuera del MVP** | Se definirá después |
| Node/npm | **Prohibido** en el flujo del agente | Tailwind vía flujo que no dependa de npm del agente |

**Regla de diseño async:** toda lógica que pueda bloquear el hilo web (PDF, correos, cálculos masivos, exportaciones) debe encolarse en workers desde el día 1.

---

## 2. Objetivo General del Sistema

Aplicación web profesional para administrar flotas de camiones de servicio (basura, cesta, etc.), con núcleo en:

1. Gestión de **propietarios fiscales**, **camiones** y **conductores/responsables**.
2. Catálogo dinámico de **servicios** y **suministros**.
3. **Presupuestos** en USD con tasa de cambio manual.
4. **Facturas** en VES (Bolívares), con IVA y retenciones configurables.
5. **PDF** de presupuesto y factura desde el MVP.

---

## 3. Modelo de Negocio y Entidades

### 3.1. Propietario (cliente fiscal)

El **propietario = cliente fiscal**. No es lo mismo que el conductor.

Campos mínimos:

- RIF
- Nombre / razón social exacta asociada al RIF
- Dirección fiscal
- Teléfono

**Regla:** un propietario puede tener **varios camiones**.

### 3.2. Conductor / Responsable

Persona distinta del propietario fiscal. Se asocia al camión (o a la transacción) y puede imprimirse opcionalmente en la factura.

### 3.3. Camión

Campos:

- Placa
- Marca
- Modelo
- VIN
- Año
- Tipo (`basura` | `cesta` | `otro`)
- Propietario (FK al cliente fiscal)
- Conductor / responsable

### 3.4. Catálogo dinámico

**Servicio (plantilla):**

- Nombre
- Descripción
- Activo (sí/no)

**Suministro (plantilla):**

- Nombre
- Descripción
- Unidad
- Activo (sí/no)

Los precios **no** viven en el catálogo: se capturan manualmente en cada transacción.

### 3.5. Línea de presupuesto / factura

- Tipo: `service` | `supply` | `embedded_supply`
- Descripción (snapshot al momento de la transacción)
- Costo USD (interno)
- Precio cliente USD
- Cantidad
- Flag embebido (suministro incluido en un servicio)

---

## 4. Flujo Principal de la Aplicación

### Paso 1: Gestión del camión

- Seleccionar un camión existente o crear uno nuevo.
- Al crear: datos del vehículo + propietario fiscal + conductor/responsable.

### Paso 2: Selección de servicios y suministros

Sobre el camión seleccionado se aplican uno o más ítems. Pueden presupuestarse/facturarse juntos o por separado.

**Para ambos tipos, costo y precio al cliente se ingresan manualmente en cada transacción.**

#### 2.1. Servicios

- Mantenimiento, reparación, revisiones, mano de obra, etc.
- Catálogo alimentado dinámicamente por el usuario.
- Un servicio puede incluir un **suministro embebido** (autoparte incluida).

#### 2.2. Suministros

- Autopartes y consumibles.
- Pueden ir como complemento de un servicio o cobrarse solos (ej. el cliente aporta su mano de obra).

#### 2.3. Regla de suministros embebidos

| Documento | Visibilidad | Monto al cliente | Costo interno |
|-----------|-------------|------------------|---------------|
| **Presupuesto** | Sí, aparece como línea/subtítulo **sin monto** de precio al cliente | No se cobra aparte | Sí: el costo del suministro embebido forma parte del costo del servicio que lo incluye |
| **Factura** | **No aparece** | No se factura aparte | Se conserva en datos internos / auditoría, no en PDF de factura |

### Paso 3: Presupuestos (cotizaciones)

Referencia visual: Excel de presupuesto de servicios (líneas en USD + IVA + conversión BCV).

- Las líneas se detallan en **USD** (cantidad × precio unitario = neto línea).
- El usuario ingresa **manualmente** la tasa de cambio del presupuesto (`tasa_presupuesto`).
- El presupuesto muestra:
  - Subtotal USD (suma de líneas facturables; **sin** precio de embebidos)
  - IVA 16% sobre subtotal USD (porcentaje configurable)
  - Total USD = Subtotal + IVA
  - Equivalente en Bs. = Total USD × `tasa_presupuesto` (y/o desglose Subtotal/IVA convertidos)
- Los montos del presupuesto **no se copian tal cual** a la factura: al facturar se pide **una tasa nueva** y se recalcula.

**PDF de presupuesto:** obligatorio en MVP (worker).

### Paso 4: Facturación

- Se genera **desde un presupuesto** (relación **1 presupuesto = 1 factura**).
- Antes de emitir se pueden modificar costos/precios de ítems.
- Al convertir a factura el usuario **debe introducir una nueva tasa de cambio** (`tasa_factura`), vigente para ese documento.
- Con esa tasa se **recalculan todos los montos en VES**.
- En la factura **nunca** se muestra USD: solo Bolívares.
- Factura directa sin presupuesto: **fuera de alcance del MVP** salvo que se reabra explícitamente (el Excel actual parte de presupuesto facturado).

**Composición de la factura (PDF / pantalla):**

1. **Datos del emisor** (configurables en settings / tabla de empresa): RIF, razón social, dirección.
2. **Datos fiscales del cliente** (automáticos desde el propietario del camión): RIF, nombre, dirección fiscal, teléfono.
3. **Datos del camión** (opcionales por checkbox al imprimir): marca/modelo, VIN, conductor/responsable.
4. Líneas de servicio/suministro **facturables** (sin embebidos), en Bs.
5. Totales: base imponible, IVA, total factura.
6. **Detalle de pago / retenciones** (ver §5), configurable.

**PDF de factura:** obligatorio en MVP (worker).

**Nota observada en Excel actual:** el formato de factura impreso agrupa a veces **varias unidades** en un mismo documento. El MVP queda definido como **un camión por presupuesto/factura**. Multi-unidad en un solo PDF queda como extensión futura documentada, no como regla del MVP.

---

## 5. Motor Fiscal (IVA, Retenciones y Totales)

### 5.1. Principio de diseño: 100% configurable

Todos los porcentajes e importes fiscales viven en **configuración** (modelo `FiscalSettings` / settings de empresa), **no hardcodeados** en vistas ni templates.

Valores iniciales tomados del Excel operativo actual; el usuario podrá cambiarlos sin redeploy de lógica.

Si cambia la fórmula en el futuro, se ajusta la capa de cálculo (`billing/services/calculations.py` o equivalente) + la config. Las facturas **ya emitidas** conservan un **snapshot** de porcentajes y montos usados al emitir.

### 5.2. Conceptos base (en VES, sobre la factura)

Después de convertir cada línea facturable:

```text
precio_linea_ves = cantidad × precio_cliente_usd × tasa_factura

BASE_IMPONIBLE (VES) = suma de precio_linea_ves de líneas facturables
IVA (VES)            = BASE_IMPONIBLE × iva_pct          # default 0.16
TOTAL_FACTURA (VES)  = BASE_IMPONIBLE + IVA
```

**Importante — Retención de IVA:**  
La retención de IVA se calcula sobre el **monto del IVA**, **no** sobre el subtotal ni el total factura.

```text
RETENCION_IVA = IVA × retencion_iva_pct    # default 0.75 (75% del IVA)
```

### 5.3. Retenciones según tipo de documento / líneas

El Excel distingue **detalle de pago de servicios** vs **detalle de pago de suministros**.

#### Servicios (defaults iniciales)

| Concepto | % default | Base de cálculo |
|----------|-----------|-----------------|
| Retención IVA | 75% | **IVA** |
| ISLR | 2% | **Base imponible** |
| Retención 10×1000 | 0,1% (`0.001`) | **Base imponible** |
| Responsabilidad social | 0% | **Base imponible** (configurable) |
| Retención fiel cumplimiento | 10% | **Base imponible** |
| Retención laboral | 5% | **Base imponible** |

#### Suministros (defaults iniciales)

| Concepto | % default | Base de cálculo |
|----------|-----------|-----------------|
| Retención IVA | 75% | **IVA** |
| ISLR | **No aplica** (0% / desactivado) | — |
| Retención 10×1000 | 0,1% (`0.001`) | **Base imponible** |
| Responsabilidad social | 0% | **Base imponible** |
| Retención fiel cumplimiento | 10% | **Base imponible** |
| Retención laboral | 5% | **Base imponible** |

Si un documento mezcla servicios y suministros, el motor debe:

- Calcular base/IVA por grupo (servicios vs suministros) **o** aplicar el perfil de retenciones correspondiente a cada grupo y sumar.
- Persistir el desglose en el snapshot de la factura.

*(Decisión de implementación recomendada: subtotales por `line_type`, retenciones por grupo, luego suma = total retenciones.)*

### 5.4. Fórmula de total a pagar (Detalle de pago)

Referencia: capturas Excel “DETALLE PAGO” (servicios y suministros).

```text
TOTAL_RETENCION = suma de todas las retenciones aplicables (según config y tipo)

TOTAL_AL_PAGAR  = TOTAL_FACTURA − TOTAL_RETENCION
```

Ejemplo verificado (servicios, misma operación del Excel):

- Base imponible: `10.821.900,10`
- IVA 16%: `1.731.504,02`
- Total factura: `12.553.404,12`
- Retención IVA 75%: `1.298.628,01` ← 75% del IVA
- ISLR 2%: `216.438,00` ← 2% de la base
- 10×1000: `10.821,90` ← 0,1% de la base
- Fiel cumplimiento 10%: `1.082.190,01`
- Laboral 5%: `541.095,01`
- Total retención: `3.149.172,93`
- **Total al pagar: `9.404.231,19`**

### 5.5. Presupuesto vs factura (tasas distintas)

| Campo | Presupuesto | Factura |
|-------|-------------|---------|
| Moneda de líneas | USD | VES (convertido) |
| Tasa | `tasa_presupuesto` (manual) | `tasa_factura` (manual, **nueva**, obligatoria al facturar) |
| IVA visible | Sí (en USD y/o equiv. Bs.) | Sí (solo Bs.) |
| Retenciones / detalle de pago | No obligatorio en presupuesto | Sí (detalle de pago) |
| Embebidos | Visibles sin monto | Ocultos |

Al pasar presupuesto → factura: **recalcular** base, IVA, retenciones y total al pagar con `tasa_factura`.

### 5.6. Extensibilidad de la fórmula

Para que un cambio futuro no “reviente” la app:

1. Cada retención es un registro configurable: `codigo`, `nombre`, `porcentaje`, `base` (`iva` | `base_imponible`), `aplica_a` (`service` | `supply` | `both`), `activo`.
2. El motor itera retenciones activas; no asume una lista fija en el template.
3. Facturas emitidas guardan JSON/snapshot inmutable del cálculo.
4. Tests unitarios fijan los ejemplos numéricos del Excel como regresión.

---

## 6. Estados de Documentos

### Presupuesto

| Estado | Significado |
|--------|-------------|
| `borrador` | En edición |
| `enviado` | Enviado al cliente |
| `aceptado` | Cliente aceptó |
| `facturado` | Ya tiene factura asociada emitida/vigente |
| `anulado` | Anulado |
| `confirmar_presupuesto_factura_anulada` | La factura vinculada fue anulada; el presupuesto queda pendiente de confirmación/reproceso |

**Regla:** al anular una factura, el presupuesto asociado pasa a `confirmar_presupuesto_factura_anulada` (no vuelve silenciosamente a `aceptado`).

### Factura

| Estado | Significado |
|--------|-------------|
| `borrador` | En edición / pre-emisión |
| `emitida` | Numerada, bloqueada para edición de montos, PDF generado |
| `anulada` | Anulada; dispara el estado especial del presupuesto |

### Cardinalidad

- **1 presupuesto = 1 factura** (no facturación parcial de líneas en el MVP).

---

## 7. Numeración

- Presupuesto: `PRE-YYYY-NNNNN`
- Factura: `FAC-YYYY-NNNNN`

Generación concurrente-safe con `transaction.atomic()` + `select_for_update()` sobre secuencia en PostgreSQL.

---

## 8. Usuarios y Permisos

**MVP:** sección sin implementación de roles aún (auth básica / superusuario suficiente para desarrollo).

**Diseño futuro (obligatorio anticipar en arquitectura):**

- Habrá **múltiples usuarios** con **permisos distintos**.
- Algunos usuarios solo verán **una parte del flujo** (ej. solo flota, solo presupuestos, solo facturación, solo consulta).
- Por tanto: no acoplar permisos dentro de las vistas de negocio; usar grupos/permisos Django (o capa `permissions.py`) desde que existan las apps, aunque el MVP no restrinja pantallas todavía.

---

## 9. PDFs y Notificaciones

| Entregable | MVP |
|------------|-----|
| PDF presupuesto | **Sí** (worker) |
| PDF factura (+ detalle de pago / retenciones) | **Sí** (worker) |
| Envío por correo | **No** (se define después) |

Formato de referencia de factura: Excel actual (ítem, descripción, cantidad, precio unitario, IVA %, neto; totales base / IVA / total; cabecera con RIF y dirección del emisor).

---

## 10. Datos del Emisor (configurables)

Valores iniciales tomados del formato actual (editables en config):

- Razón social: `MJ SINO IMPORT, C.A.` (o la que defina el cliente)
- RIF: `G-20013109-8`
- Dirección fiscal del emisor

---

## 11. Glosario

| Término | Definición |
|---------|------------|
| Propietario | Cliente fiscal (RIF); dueño del camión a efectos de factura |
| Conductor / responsable | Persona operativa distinta del propietario |
| Servicio | Mano de obra / mantenimiento / reparación |
| Suministro | Autoparte o consumible cobrado aparte |
| Suministro embebido | Autoparte incluida en un servicio; sin precio al cliente; con costo interno |
| Base imponible | Suma en Bs. de líneas facturables (después de aplicar tasa de factura) |
| Tasa presupuesto | USD→VES informativa de la cotización |
| Tasa factura | USD→VES vigente al emitir; recalcula la factura |
| Detalle de pago | Bloque de retenciones y total al pagar |

---

## 12. Fuera de Alcance del MVP (explícito)

- Envío de correos
- Roles/permisos granulares (solo preparar arquitectura)
- Multi-camión en un mismo presupuesto/factura (visto en Excel histórico; no MVP)
- Factura directa sin presupuesto (reabrir si el negocio lo exige)
- Inventario físico / stock de suministros

---

## 13. Checklist de Aceptación del Dominio (para desarrollo)

- [ ] Propietario 1:N camiones; conductor ≠ propietario
- [ ] Catálogo dinámico sin precios fijos
- [ ] Líneas con costo/precio/cantidad y embebidos
- [ ] Embebido visible sin monto en presupuesto; oculto en factura; costo interno sí
- [ ] Presupuesto en USD + tasa manual + PDF
- [ ] Factura solo VES + tasa nueva + recálculo + PDF
- [ ] IVA configurable; retención IVA = % del **IVA**
- [ ] Retenciones de servicios vs suministros según tabla §5.3, todas configurables
- [ ] Total al pagar = total factura − total retenciones
- [ ] 1 presupuesto = 1 factura; anulación → estado `confirmar_presupuesto_factura_anulada`
- [ ] Numeración `PRE-` / `FAC-` con bloqueo Postgres
- [ ] Celery/Redis para PDF desde el inicio
)
