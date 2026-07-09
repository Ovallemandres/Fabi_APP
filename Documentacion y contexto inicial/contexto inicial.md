# Documento de Contexto Inicial: Sistema de Gestión, Presupuestos y Facturación de Flotas

## 1. Arquitectura y Tecnologías Base (Requisitos Estrictos)
Para todo el desarrollo de esta aplicación web, los agentes de IA deben contemplar la siguiente base tecnológica desde el día 1:
*   **Base de Datos:** PostgreSQL. (Obligatorio respetar tipado estricto y migraciones seguras).
*   **Despliegue (Deploy):** Render.com.
*   **Procesos en Segundo Plano:** Se debe establecer e integrar **Redis, Cronjobs y Background Workers** (ej. Celery, RQ o similar) desde el inicio. Toda lógica que pueda bloquear el hilo principal (ej. generación de PDFs, envío de correos, cálculos masivos) deberá diseñarse teniendo en cuenta el uso de estos workers.

---

## 2. Objetivo General del Sistema
La aplicación web es un sistema enfocado en la administración de camiones de servicios (camiones de basura, camiones cesta, etc.), cuyo núcleo principal es la creación de presupuestos y la facturación detallada de **servicios** y **suministros** aplicados a dichos vehículos. Debe ser intuitiva, rápida y de uso profesional.

---

## 3. Flujo Principal de la Aplicación

### Paso 1: Gestión del Camión
*   El usuario inicia el flujo seleccionando un perfil de camión existente en la base de datos o creando uno nuevo.
*   La creación implica llenar un formulario con toda la información y descripción detallada del vehículo (Placa, modelo, VIN, propietario responsable, etc.).

### Paso 2: Selección de Servicios y Suministros
Una vez seleccionado el camión, el usuario le "aplica" uno o más ítems. Estos ítems se dividen en dos categorías independientes que pueden presupuestarse/facturarse juntas o por separado. **Para ambos casos, el costo y el precio al cliente se ingresan de manera manual por el usuario en cada transacción.**

*   **2.1. Servicios:** 
    *   Incluye mantenimiento, reparación, revisiones, mano de obra, etc.
    *   No están predefinidos. El sistema debe permitir al usuario ir creando y alimentando la tabla de servicios dinámicamente, definiendo campos genéricos aplicables a todos.
    *   *Regla de negocio:* Un servicio puede incluir intrínsecamente un suministro/autoparte que no será cobrado individualmente en la sección de suministros.
*   **2.2. Suministros:** 
    *   Autopartes y consumibles.
    *   Pueden aplicarse como complemento a un servicio o cobrarse de forma totalmente individual y aislada (ej. el cliente provee su propia mano de obra).

### Paso 3: Presupuestos (Cotizaciones)
*   Las selecciones del Paso 2 se formalizan en un Presupuesto.
*   Se detalla cada ítem junto con su monto en **Dólares (USD)**.
*   El sistema solicitará al usuario que ingrese manualmente una **Tasa de Cambio**.
*   El presupuesto mostrará tanto el total en USD como su conversión a **Bolívares (VES)** calculada en base a la tasa ingresada. 
*   *Nota:* Los montos puros arrojados en esta pantalla (Subtotal USD y Subtotal VES) son exclusivos de la cotización y no se trasladan visualmente de la misma forma a la factura.

### Paso 4: Facturación
El usuario puede generar una factura a partir de un presupuesto guardado (con la libertad de modificar costos o precios de cualquier ítem antes de emitirla) o saltar directamente a la facturación sin guardar presupuesto.

**Composición de la Factura:**
1.  **Datos Fiscales (Obligatorios y Automáticos):** El sistema extraerá e insertará automáticamente la información fiscal del propietario del camión (RIF, Nombre completo exacto asociado al RIF, Dirección Fiscal, Teléfono).
2.  **Datos del Camión (Opcionales / Multiselección):** El usuario tendrá checkboxes para decidir si imprime o no en la factura datos como: Marca/Modelo, VIN, y Conductor o Responsable.

**Reglas Estrictas de Cálculos en la Facturación:**
*   **Moneda:** En la factura **NUNCA** se mostrará el monto en Dólares (USD). Solo se mostrará el monto convertido a Bolívares usando la tasa ingresada previamente.
*   **Impuestos:** Al monto convertido se le debe sumar automáticamente el IVA correspondiente (16%).
*   **Retenciones:** Existen porcentajes de retención específicos. 
    *   Hay un porcentaje de retención fijo/específico para **Servicios**.
    *   Hay un porcentaje de retención fijo/específico para **Suministros**.
    *   *Regla:* El porcentaje no varía entre los distintos servicios (todos tienen el mismo %) ni entre los distintos suministros.