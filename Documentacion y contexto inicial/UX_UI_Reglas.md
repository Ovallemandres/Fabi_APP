1. Estilo General y Estética (Neumorfismo)
El diseño se basa enteramente en la tendencia conocida como Neumorfismo (o Soft UI). La filosofía principal de este estilo es crear la ilusión de que los elementos de la interfaz están extruidos o tallados directamente sobre el fondo, como si fueran un material físico continuo (plástico suave o arcilla). Esto se logra eliminando los bordes duros tradicionales y sustituyéndolos por un juego sutil de luces y sombras.

2. Uso de Sombras y Elevación (La Luz)
El sistema define una fuente de luz virtual consistente, ubicada en la esquina superior izquierda.

Elementos Elevados (Raised): Presentan un brillo blanco/claro en el borde superior izquierdo y una sombra oscura/tostada en el borde inferior derecho, dándoles volumen hacia afuera (ej. botones base, tarjetas).

Elementos Hundidos (Inset): Invierten el patrón de sombras (sombra oscura arriba a la izquierda, brillo abajo a la derecha) para simular agujeros o cavidades en la superficie (ej. campos de texto, el fondo de los switches o la barra de progreso).

Capas (Elevations): Muestra 5 niveles claros de profundidad, desde superficies totalmente planas hasta modales que parecen flotar más arriba gracias a sombras más difusas y extensas.

3. Paleta de Colores
Es una paleta monocromática cálida con un único color de acento fuerte, lo que facilita la carga cognitiva:

Fondo y Superficies: Un tono crema, beige o arena muy cálido (#F2EBE0). Al ser el color predominante, da una sensación acogedora y reduce la fatiga visual en comparación con un blanco puro.

Color Primario (Acento): Un naranja sólido intenso (#DC2F23). Se utiliza estratégicamente solo para llamar la atención sobre elementos interactivos clave: botones principales, checkboxes seleccionados, toggles encendidos, notificaciones importantes y el estado activo de la paginación.

Texto y Estados: Tonos grises oscuros para el texto principal y grises medios para el secundario o estados deshabilitados. Se utiliza un rojo apagado exclusivamente para mensajes de error, manteniendo la sobriedad del sistema.

4. Geometría y Formas
El diseño evita por completo las esquinas afiladas, reforzando la sensación "suave" del Neumorfismo.

Radios de Borde (Border Radius): Se utiliza una escala progresiva (4px a 24px). Las tarjetas y modales tienen radios generosos, mientras que los botones, badges y barras de progreso adoptan formas de "píldora" (bordes completamente redondeados).

Proporciones: Los elementos interactivos tienen áreas de clic amplias, acompañadas de márgenes (spacing) generosos de 16px a 24px, lo que le da a la interfaz un aspecto limpio y descongestionado (airy).

5. Controles e Interacción
El diseño comunica claramente el estado de los componentes a través de cambios de volumen:

Botones y Toggles: En su estado normal sobresalen. Al ser presionados (Pressed State), la sombra cambia de Raised a Inset, dando retroalimentación visual táctil, como presionar un botón físico.

Campos de Texto: Están hundidos, invitando al usuario a "llenar" el espacio vacío. Cuando están activos, se les añade un borde sutil con el color primario para destacar el foco.

6. Tipografía e Iconografía
Tipografía: Utiliza una fuente sans-serif moderna y geométrica. La jerarquía se establece mediante el peso de la fuente (Regular vs. Bold) y el color (Gris oscuro vs. Gris claro), en lugar de usar muchos tamaños diferentes.

Iconos: Son de estilo lineal (outline), con un grosor de trazo consistente de 2px. Son simples, con bordes redondeados en sus terminaciones que hacen eco de la geometría general del diseño.


El principio fundamental del Neumorfismo es que la interfaz se comporta como un material físico (plástico suave o arcilla). Por lo tanto, las animaciones deben sentirse táctiles, fluidas y realistas, evitando rebotes elásticos (efecto "jelly") o movimientos bruscos y rápidos que romperían la ilusión de peso físico.

Dado que en tu stack usaremos Tailwind CSS y Alpine.js, estas animaciones son fáciles de lograr utilizando clases de transición simples sin sobrecargar el navegador.

Aquí tienes los tipos de animaciones y microanimaciones que encajan a la perfección con este estilo:

1. Microanimaciones de Interacción (Botones y Controles)
Transición de Sombra (Morphing Táctil): Es el alma de este diseño. Al hacer clic en un botón, la sombra exterior (Raised) debe transicionar suavemente hacia una sombra interior (Inset). Debe sentirse como si estuvieras hundiendo el dedo en un plástico maleable. En Tailwind, esto se logra con una transición de unos 150ms a 300ms (transition-shadow duration-200 ease-in-out).

Hover Flotante: Al pasar el ratón por encima de una tarjeta de un camión o un botón primario, la sombra debe expandirse y difuminarse ligeramente, dando la ilusión de que el elemento se levanta o se acerca al dedo del usuario.

Deslizamiento con Fricción (Switches): Al encender un switch (por ejemplo, para agregar un repuesto a la factura), el círculo interno debe deslizarse con una curva de aceleración natural (ease-in-out), simulando resistencia mecánica, acompañado de un cambio sutil de color de fondo a tu naranja sólido principal.

2. Animaciones de Navegación y Modales
Aparición por "Emergencia" (Fade & Scale): Los elementos en Neumorfismo rara vez entran deslizando desde fuera de la pantalla. Como son parte de la misma superficie plana, cuando abres un modal de confirmación o cargas la lista de servicios filtrados mediante HTMX, estos deben aparecer con un difuminado suave (Fade In) y un ligerísimo aumento de escala (de 0.95 a 1). Alpine.js maneja esto perfectamente con sus directivas x-transition.

Apertura de Acordeones o Menús: Deben expandirse suavemente revelando su contenido, como si el material se estuviera estirando, sin saltos repentinos.

3. Feedback y Estados de Carga
Pulsación de Skeletons: Al hacer una búsqueda pesada de facturas en la base de datos, en lugar de un spinner que gire frenéticamente, el Neumorfismo utiliza "Skeletons" (figuras hundidas con forma de píldora) que laten. La animación debe ser una transición lenta de opacidad (de más oscuro a más claro) o un barrido de luz diagonal muy tenue.

Toasts/Alertas Suaves: Los mensajes de éxito (ej. "Presupuesto guardado") deben aparecer levitando suavemente desde abajo o arriba con un fundido, manteniéndose en la pantalla unos segundos y disolviéndose sin movimientos agresivos.

{
  "design_system": {
    "name": "Neumorphic UI Kit",
    "theme": "Neumorphism / Soft UI",
    "colors": {
      "background": "#F2EBE0",
      "primary": "#DC2F23",
      "text_primary": "#202020",
      "text_secondary": "#606060",
      "disabled_background": "#C8C2B8",
      "disabled_text": "#F2EBE0",
      "error": "#B02A2A",
      "shadow_light": "#FFFFFF",
      "shadow_dark": "#D4CBB8"
    },
    "typography": {
      "font_family": "sans-serif",
      "weights": {
        "regular": 400,
        "medium": 500,
        "bold": 700
      }
    },
    "foundations": {
      "layers": {
        "base_layer": "Flat background",
        "raised_layer": "Outer shadow (light top-left, dark bottom-right)",
        "inset_layer": "Inner shadow (dark top-left, light bottom-right)",
        "pressed_layer": "Deep inner shadow"
      },
      "elevation_levels": [
        { "level": "Level 1", "state": "Flat" },
        { "level": "Level 2", "state": "Hover" },
        { "level": "Level 3", "state": "Raised" },
        { "level": "Level 4", "state": "Modal" },
        { "level": "Level 5", "state": "Popover" }
      ],
      "border_thickness": {
        "thin": "1px",
        "regular": "2px",
        "thick": "4px"
      },
      "radius_scale": ["4px", "8px", "12px", "16px", "24px"],
      "iconography": {
        "sizes": ["16px", "18px", "20px", "24px"],
        "stroke_weight": "2px"
      }
    },
    "components": {
      "controls": {
        "spacing": "16px",
        "buttons": {
          "primary": { "background": "primary", "text_color": "#FFFFFF", "radius": "24px" },
          "pressed": { "background": "primary", "effect": "inset_shadow", "text_color": "#FFFFFF" },
          "disabled": { "background": "disabled_background", "text_color": "disabled_text" }
        },
        "text_fields": {
          "default": { "background": "inset_layer", "border": "none" },
          "active": { "background": "inset_layer", "border": "2px solid primary" },
          "error": { "background": "inset_layer", "border": "2px solid error" }
        },
        "selection_controls": {
          "checkbox": "Square with rounded corners, inset when unselected, primary background when selected",
          "radio": "Circular, inset when unselected, primary dot when selected",
          "switch": "Pill-shaped, inset track, raised toggle button",
          "slider": "Inset track with raised draggable thumb"
        }
      },
      "navigation": {
        "spacing": "24px",
        "tabs": {
          "spacing": "15px",
          "style": "Raised pill shape for active tab, flat text for inactive"
        },
        "breadcrumbs": "Flat text separated by slashes within a raised pill container",
        "stepper": "Connected circular nodes with primary color for active/completed steps",
        "pagination": "Row of numbers, active page has primary background and rounded square shape"
      },
      "data_display": {
        "spacing": "24px",
        "cards": "Raised layer with 16px/24px radius",
        "list_items": "Flat text/avatars on base layer, hover state uses raised or inset layer",
        "badges": "Pill-shaped, primary background, white text",
        "avatars": "Circular, often with a thin border or raised effect",
        "tooltip": "Dark background, rounded rectangle with a pointer arrow",
        "table_header": "Compact, raised or base layer with sort icons"
      },
      "feedback": {
        "spacing": "8px",
        "modal_confirmation": "Raised card (Level 4 elevation) with centered warning icon and action buttons",
        "toast_stack": "Raised cards with status icons (Success, Info)",
        "alert_banner": "Primary color background, white text, rectangular with subtle radius",
        "linear_progress": "Inset track with primary color fill",
        "spinner": "Circular arrangement of dots with fading opacity",
        "skeleton_rows": "Inset pill shapes replacing text lines",
        "empty_state": "Large line-art icon with neutral text and a primary action button"
      }
    }
  }
}