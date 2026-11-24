# JEDL Studio — Especificación del producto

**Versión:** 1.0  
**Estado:** especificación funcional base  
**Motor:** Godot 4.5.1 estable  
**Plataforma objetivo:** Android, con Redmi Note 10 como dispositivo de validación

## 1. Propósito

JEDL Studio es un estudio de creación audiovisual móvil. El usuario describe en lenguaje natural la escena o el vídeo que quiere producir. Un modelo de lenguaje pequeño integrado (SLM/LLM, T14) convierte esa descripción en un JSON estructurado. Godot interpreta el JSON, consulta el inventario local y construye la escena con recursos 3D y 2.5D.

La aplicación está orientada a usuarios que no necesitan conocer nodos, programación ni técnicas de producción 3D. La interfaz debe presentar operaciones visuales y comprensibles.

## 2. Principios obligatorios

1. **Android y Godot 4.5.1:** Godot es el motor de escenas, composición, animación y renderizado.
2. **Offline-first:** el proyecto abierto, el editor, el catálogo ya instalado, la reproducción y la exportación deben funcionar sin conexión. Los paquetes se descargan cuando hay conexión y permanecen disponibles localmente después.
3. **Sin servicios de pago obligatorios:** el flujo principal no puede depender de APIs comerciales, suscripciones, créditos ni servicios cloud de pago.
4. **Escena inicial vacía:** iniciar un proyecto no debe cargar personajes, fondos ni escenas de demostración automáticamente.
5. **JSON como descripción reproducible:** el JSON define recursos, transformaciones, acciones, tiempos y relaciones. El motor ejecuta la descripción; el LLM no renderiza imágenes ni sustituye al motor.
6. **Inventario externo al APK:** los paquetes grandes de recursos se almacenan fuera del APK, se instalan bajo demanda y se pueden usar sin conexión.
7. **Sin sustituciones silenciosas:** si falta un recurso, la aplicación informa cuál falta y ofrece alternativas compatibles para que el usuario decida.
8. **Trazabilidad:** cada recurso debe conservar identificador, origen, licencia y atribución cuando corresponda.

## 3. Flujo principal

1. El usuario escribe una descripción de la escena o vídeo.
2. El SLM/LLM integrado consulta las etiquetas y metadatos del catálogo disponible.
3. El modelo produce JSON conforme al contrato de escena.
4. El validador comprueba estructura, tipos, referencias, recursos y acciones.
5. Godot construye la escena a partir del JSON y de los recursos instalados.
6. El usuario revisa y modifica la composición con controles visuales.
7. El usuario reproduce la secuencia y, cuando esté lista, exporta el resultado a MP4.

El usuario también debe poder crear y editar escenas manualmente sin utilizar el LLM. El JSON debe poder guardarse, abrirse y reproducirse de forma determinista.

## 4. Escenas, recursos y composición

### 4.1 Formatos

Los tipos de contenido incluyen personajes, objetos, vehículos, entornos, vegetación y elementos de escena. Un recurso puede estar disponible en formato 3D o 2.5D. El formato es un atributo del recurso, no una sintaxis alternativa del JSON.

- **3D:** modelos y escenas tridimensionales importados y validados por Godot.
- **2.5D (personajes):** personaje ilustrado espacial, compuesto por piezas Sprite3D colocadas en BoneAttachment3D dentro de un Skeleton3D con huesos reales. La escena debe declarar `format: "2.5d"` y el catálogo debe certificar `character_format: "2.5d"`.
- **3D (personajes):** modelo volumétrico con raíz Node3D, Skeleton3D con huesos y MeshInstance3D con Skin. La escena debe declarar `format: "3d"` y el catálogo debe certificar `character_format: "3d"`.
- **2D auxiliar:** imágenes planas, iconos y elementos decorativos. No son personajes, no se admiten en `characters` y nunca pueden reemplazar un personaje 2.5D o 3D.

La disponibilidad real de cada formato depende de los paquetes verificados. No se anunciará un dominio como cubierto si no tiene recursos utilizables.

### 4.2 Entornos modulares

Un entorno no se considera una imagen de fondo fija. Se construye combinando piezas del inventario según el JSON y la descripción: terreno, suelo, aceras, calles, edificios, fachadas, mobiliario, vegetación, cielo, mar, elementos espaciales y otros módulos pertinentes.

Los fondos fotográficos que existan en el inventario se clasifican como recursos planos auxiliares o referencias visuales. No se contabilizan como sustitutos de un entorno modular ni demuestran que el constructor modular esté implementado.

### 4.3 Transformaciones y capas

Los recursos deben poder colocarse, moverse, rotarse, escalarse, ordenarse y eliminarse mediante controles visuales. La escena debe conservar identificadores estables para que las acciones JSON resuelvan correctamente su objetivo. La composición debe respetar visibilidad, orden de capas, límites y transformaciones guardadas.

## 5. Animación y movimiento

La aplicación debe admitir:

- Reproducción de animaciones incluidas en recursos importados, siempre que Godot pueda importarlas y reproducirlas correctamente.
- Secuencias de acciones definidas en JSON, con objetivos identificados por ID, tiempos, duración, interpolación y propiedades animadas.
- Edición visual de keyframes y secuencias en una línea temporal.
- Captura y transferencia de movimiento mediante MediaPipe (T13), con mapeo del movimiento capturado al esqueleto compatible del personaje.

MediaPipe es una capacidad planificada, no se considera integrada por la mera existencia de documentación o código auxiliar. Los personajes 2.5D deben poder utilizarse sin que el usuario tenga que construir manualmente un rig. El esquema común de esqueleto y la fuente de personajes 2.5D requieren validación antes de declarar esa cobertura completa.

## 6. Audio, voces y subtítulos

La escena debe poder asociar audio, voces, música y efectos a momentos de la secuencia. Los subtítulos deben poder editarse y sincronizarse con la línea temporal. La reproducción y exportación deben conservar la sincronización audiovisual. La disponibilidad de bancos de audio queda sujeta a las fuentes y licencias registradas en el catálogo.

## 7. LLM/SLM integrado (T14)

El modelo actúa como guionista técnico: interpreta la petición, consulta etiquetas y metadatos del inventario y produce JSON válido. No genera ni renderiza los recursos visuales.

El objetivo de producto es que la creación no dependa de APIs comerciales ni de conexión permanente. La arquitectura concreta, modelo, cuantización, memoria y estrategia de ejecución local deben definirse y probarse en Android antes de seleccionar el modelo definitivo. El LLM no puede inventar identificadores de recursos ni afirmar que un recurso inexistente está disponible.

## 8. Exportación de vídeo (T12)

Godot debe renderizar la secuencia compuesta y permitir exportarla como archivo MP4 reproducible en Android. La exportación debe incluir imagen, audio y sincronización temporal cuando existan. Debe informar de errores, falta de espacio y resultados incompletos; no debe anunciar éxito si el archivo no se ha generado y validado.

La implementación del exportador, códec, resolución, duración y rendimiento objetivo se validarán en el dispositivo de referencia. La existencia de un APK de CI no equivale a exportación de vídeo funcional.

## 9. Inventario y paquetes descargables

El inventario crece mediante paquetes descargables, instalables y disponibles sin conexión. Los paquetes no se incorporan al APK principal. La aplicación debe poder consultar metadatos localmente, verificar integridad, detectar dependencias, instalar y retirar paquetes sin corromper proyectos existentes.

El catálogo debe poder crecer a gran escala (objetivo de largo plazo: cientos de miles de recursos) sin cargar todos los recursos en memoria a la vez. La búsqueda debe utilizar etiquetas y metadatos y mostrar formato, dominio, licencia y estado de instalación.

### 9.1 Licencias

Licencias aceptadas para integrar recursos:

- **CC0-1.0:** conservar los datos de procedencia y licencia disponibles.
- **CC-BY-4.0:** conservar autoría, fuente, licencia y texto/enlace de atribución, y generar la atribución correspondiente en la exportación o documentación del proyecto.

No se incorporará un recurso cuya licencia o procedencia no pueda verificarse. No se asumirá que una licencia permite redistribución de paquetes sin revisar sus términos.

## 10. Contrato de datos y validación JSON

El JSON debe describir, como mínimo, la versión del esquema, la escena, recursos referenciados por identificadores del catálogo, formato, transformaciones, jerarquía/capas y secuencias temporales. Cuando proceda, incluirá audio y subtítulos.

El parser debe validar tipos y campos requeridos, resolver cada identificador contra el catálogo instalado y comprobar que las acciones apuntan a objetos existentes. Ante errores debe informar el campo, identificador o recurso afectado. No debe sustituir recursos, ignorar acciones ni cambiar valores silenciosamente.

La estructura exacta y sus ejemplos ejecutables se concretarán en T3/T4 y se mantendrán versionados. Ningún ejemplo puede introducir un recurso que no exista en el catálogo.

## 11. Estado inicial conocido y límites

Estado documental a 2026-11-24:

- Inventario validado en CI: **24 recursos**, distribuidos en **12 fondos fotográficos** y **12 modelos 3D**.
- Los 12 fondos fotográficos no equivalen a piezas modulares de entorno.
- No se considera demostrada una galería 2.5D completa.
- El catálogo y las fuentes adicionales requieren decisiones y validación de licencia/formato antes de ampliarse.
- La Fase A de importación/CI figura cerrada en el historial por Run #186; esto no certifica el producto completo ni el funcionamiento en el teléfono.
- La reproducción JSON/animación tiene una incidencia conocida registrada en `docs/ESTADO_Y_PLAN.md` (Run #222).
- MediaPipe, generación LLM integrada y exportación MP4 siguen siendo objetivos de desarrollo, no capacidades certificadas.

## 12. Criterio general de aceptación

Una función no se declara terminada solo porque compile o porque un workflow termine en verde. Debe tener pruebas automatizadas pertinentes, evidencia CI asociada al commit y cumplir su criterio de uso en el Redmi Note 10. Los criterios concretos por área se mantienen en `docs/ESTADO_Y_PLAN.md`.
