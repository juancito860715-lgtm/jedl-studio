# JEDL Studio — Estado y plan

> Este archivo es la memoria oficial del proyecto. Cualquier agente (GPT, Claude u otro) lo lee COMPLETO al empezar cada sesión y lo actualiza al terminar cada paso. Lo que no esté aquí no existe para el proyecto.

Definición completa del producto: `docs/PRODUCTO.md` (texto íntegro de la especificación, sin resumir).
Formato del inventario: `docs/CATALOGO.md`.

## 0. Reglas de trabajo (no negociables)

1. No se implementa nada sin un criterio de cierre escrito en este archivo.
2. No se declara nada cerrado sin evidencia: número de PR, SHA, run de CI o prueba en el Redmi Note 10.
3. El CI en verde no cierra un área. Un área se cierra cuando la prueba del criterio de la sección 3 se cumple en el teléfono.
4. No se fusiona ninguna PR sin aprobación explícita del usuario.
5. No se crean ramas nuevas sin autorización. Las PRs #16 y #17 quedan congeladas.
6. Antes de añadir un requisito, comprobar que existe en `docs/PRODUCTO.md`. Si no existe, se pregunta al usuario, no se inventa.
7. Cada sesión registra en la sección 6 lo que hizo, con fecha y evidencia.

## 1. Decisiones cerradas

- **Propósito:** cualquier usuario crea escenas y vídeos cortos desde un JSON generado por un LLM integrado o IA externa, sin conocimientos técnicos.
- **Motor:** Godot 4.5.1 estable (CI blindado con validación de importación y rechazo de GLB incompatibles).
- **Escena inicial:** siempre vacía. El JSON construye la escena a partir del inventario.
- **Formatos:** personajes, objetos, vehículos, entornos, vegetación y sonidos existen en 3D y en 2.5D. El formato es un atributo del recurso, no un camino distinto en el JSON.
- **2.5D:** personajes ilustrados listos para usar. No requieren rigging ni configuración manual.
- **Fondos:** no son imágenes fijas. Cada entorno se monta con piezas modulares del inventario (suelo, aceras, edificios, mobiliario, mar, espacio, etc.) según la descripción del JSON.
- **Inventario:** cubre cualquier contexto (urbano, interior, naturaleza, mar, espacio, fantasía, etc.). Crece hasta cientos de miles de recursos mediante paquetes descargables y disponibles sin conexión. Nada de eso va dentro del APK.
- **IA Integrada (LLM):** Un Modelo de Lenguaje Pequeño (SLM) actuará como "guionista técnico". Recibirá texto en lenguaje natural del usuario, consultará las etiquetas de `CATALOGO.md` y generará el JSON exacto. No renderiza gráficos, solo escribe la estructura lógica.
- **Fuentes:** Kenney aporta piezas 2D y 3D, no 2.5D. Poly Haven aporta texturas, no escenarios. Ninguna fuente se usa sin verificación de formato y licencia.
- **Formato de pieza y vocabulario de etiquetas:** definidos en `docs/CATALOGO.md`.
- **Licencias aceptadas:** CC0-1.0 y CC-BY-4.0 (con atribución automática). Otras según sección 4 de `CATALOGO.md`.
- **Recursos faltantes:** la app avisa y ofrece alternativas compatibles. Nunca sustituye en silencio.
- **Base de trabajo:** cadena de PRs #15 → #14 → #13 → #11. Los hitos 1 y 2 (#16, #17) quedan como referencia, no como base.
- **Criterio de cierre por área:** una prueba concreta en el Redmi Note 10, descrita en la sección 3.

## 2. Preguntas abiertas (requieren decisión del usuario)

| # | Pregunta | Estado |
|---|---|---|
| Q1 | Fuente de recursos 2.5D para cada dominio | Abierta. Sin fuente 2.5D clara, ningún dominio se anuncia como cubierto. |
| Q2 | Fuente por dominio para los dominios "Pendiente" de `CATALOGO.md` | Abierta |
| Q3 | Política de CC-BY: confirmar que se acepta con atribución automática en la exportación | Abierta |
| Q4 | Esqueleto común para animar personajes 2.5D sin rigging manual | Abierta |
| Q5 | Dónde se alojan los paquetes grandes (GitHub Releases u otro almacenamiento) | Abierta |
| Q6 | Estilos visuales: qué significa "anime", "Pixar" o "acuarela" en la práctica | Abierta |
| Q7 | Arquitectura del LLM: ¿Correrá en el dispositivo o en un backend propio? ¿Qué modelo específico se usará? | Abierta |

## 3. Áreas: estado, evidencia y criterio de cierre

Estado a fecha de la última actualización de este archivo. Leyenda: ✅ cerrado · 🟡 parcial · 🔴 no existe · ⚪ no verificado.

| Área | Estado | Evidencia | Próximo paso | Criterio de cierre (prueba en Redmi) |
|---|---|---|---|---|
| Escena vacía | 🟡 En corrección | Hito 1 (#16) y composición en blanco (#15) | Auditar #15 | Abro la app y aparece una escena en blanco. |
| JSON → escena | 🟡 Parser básico | `SceneParser.gd`, `scene.example.json` | Definir formato completo del JSON | Importo el JSON de ejemplo y aparecen los objetos descritos. |
| Inventario y catálogo | 🟡 12 recursos 3D | PR #3, #13 (Fase A cerrada) | Auditar PRs #3 y #13 | Búsqueda por etiqueta devuelve recursos de tres dominios. |
| Galería 3D | 🟡 12 recursos | PR #3 | Separar de la 2.5D y ampliar | Abro la galería 3D, añado un elemento y lo veo. |
| Galería 2.5D | 🔴 Insuficiente | — | Definir fuente (Q1) | Abro la galería 2.5D, veo elementos ilustrados. |
| Personajes | 🔴 No completado | Hito 2 (#17), no fusionado | Auditar qué se conserva | Elijo personaje, lo cambio, lo guardo y lo uso. |
| Editor | 🟡 Base existente | Editor 2D y 3D (#17, #15) | Rediseñar a controles visuales | Muevo, giro, escalo y elimino sin ver nodos. |
| Animación | 🟡 Reproduce animaciones; secuencias JSON pendientes de corrección | `TimelineEngine.gd`; Run #222 falló en `SceneParser.gd`: AnimationPlayer no expone la biblioteca global esperada y no se resolvió la acción JSON por ID | Refactorizar la integración de AnimationPlayer al abordar PR #15; añadir pruebas de carga y resolución de acciones | El JSON describe acciones y la escena se reproduce. |
| MediaPipe | 🔴 No integrado | PR #9 (standalone) | Después de Animación | Grabo un vídeo y aplico el movimiento a un personaje. |
| Estilos globales | 🔴 No implementado | Hito 2 (#17) | Depende de Q6 | Cambio la escena entera a un estilo visual. |
| Audio y voces | 🟡 Base parcial | `sounds` en el JSON | Definir banco (Q2) | El JSON reproduce pasos y motor en el momento. |
| Subtítulos | 🟡 Base parcial | `subtitles` en el JSON | Edición y sincronización | Edito un texto y se sincroniza. |
| Proyectos | 🟡 Almacenamiento | `ProjectStore.gd`, #16 | Integrar en la interfaz | Cierro la app, la abro y el proyecto está igual. |
| Exportación | 🟡 Solo APK | Workflow de CI | Diseñar exportación de vídeo | Exporto 10 s a vídeo con audio y lo reproduzco. |
| Generación con LLM | 🔴 No integrado | Decisión Q7 | Implementar SLM | Escribo un texto, el LLM genera JSON y Godot monta la escena. |

## 4. Orden de trabajo

- **T1. Auditoría de PRs.** Leer #3, #13, #14, #15 y #11. Registrar qué se conserva, qué se descarta y qué falta.
- **T2. Documentos base.** Guardar `docs/PRODUCTO.md` y `docs/CATALOGO.md`.
- **T3. Escena vacía y JSON de ejemplo.** Escribir `scenes/escena_cruce_coche.json`.
- **T4. Escena vacía y lectura del JSON.** Cargar el JSON de T3 y avisar si falta un recurso.
- **T5. Galerías 2.5D y 3D separadas.**
- **T6. Editor sencillo.**
- **T7. Personajes editables y guardables.**
- **T8. Animación y secuencias desde el JSON.**
- **T9. Estilos globales.**
- **T10. Audio, voces y subtítulos.**
- **T11. Proyectos completos.**
- **T12. Exportación de vídeo.**
- **T13. MediaPipe.**
- **T14. Integración del LLM.** Conectar un SLM entrenado con `CATALOGO.md` para traducir texto humano al JSON exacto.

## 5. Historial de decisiones relevantes

- 2026-11-22: PR #12 fusionada, retira la fuente 2D rechazada.
- 2026-11-23: Hitos 1 y 2 no respetan el producto completo. Congelados.
- 2026-11-23: CI #272 y #284 en verde. No certifican el producto.
- Fecha de hoy: Criterio de cierre definido como prueba en Redmi Note 10.
- 2026-11-24: Fase A cerrada oficialmente (Run #186, Godot 4.5.1). Se añade T14 y Q7.

## 6. Registro de sesiones

- 2026-11-24 — T1, auditoría preliminar de PRs #3, #13, #14, #15 y #11. Gobernanza verificada tras merge de PR #19 (merge commit cc5607adc2e734b8ba3d935b9944babfd6c7c0f0): existen los archivos de instrucciones y el workflow enforce_rules.yml en main. El workflow está activo para pull_request hacia main, pero su protección es incompleta: la comprobación de etiqueta depende de mergeable_state y el detector de cambios solo cubre scripts/, scenes/ y tests/. Estado documental: Godot 4.5.1 confirmado; Fase A figura cerrada por Run #186; PR #13 sigue abierta y sin fusionar. No se pudo verificar una especificación de catálogo congelado en docs/CATALOGO.md porque el archivo no existe en main. Bloqueo de T1: docs/PRODUCTO.md tampoco existe en main (404), por lo que la clasificación definitiva de conservar/descartar contra requisitos del producto queda pendiente de recibir/restaurar ese documento.
  - PR #3: mergeada; aporta bancos Kenney CC0, presets y navegador Kotlin legado. No se recomienda tomar la interfaz Kotlin como base del runtime Godot sin validar compatibilidad con la arquitectura vigente.
  - PR #13: abierta; aporta catálogo offline, manifiestos/hashes, validación/importación GLB, editor 3D y recursos; run #191 del head actual completado con éxito. Tevy permanece excluido por extensiones no soportadas según los criterios registrados.
  - PR #14: abierta; añade aislamiento de materiales PBR por superficie y pruebas; run #196 del head actual completado con éxito. Conservar como candidato sujeto a validación contra PRODUCTO.md y pruebas funcionales.
  - PR #15: abierta; añade composición vacía, fondo opcional y acciones JSON/timeline. Run #222 falló en tests de SceneParser: AnimationPlayer no expone la biblioteca global esperada; falló la carga de acciones JSON y se omitió la exportación APK. No aceptar como funcional hasta corregir y repetir CI.
  - PR #11: abierta y en borrador; corrige validación de tipos, resolución de assetId y documentación de MediaPipe. Run #97 completado con éxito; el propio PR documenta que MediaPipe nativo/captura no está implementado y que el registro de licencias requiere completar atribuciones.
  - No se modificó código de aplicación ni se fusionó ninguna PR durante esta sesión. T1 permanece parcialmente bloqueada por la ausencia de docs/PRODUCTO.md y docs/CATALOGO.md.
  - 2026-11-24 — T2, documentos base y refuerzo del candado. Creados `docs/PRODUCTO.md` y `docs/CATALOGO.md` a partir de la visión confirmada por el usuario. El catálogo registra 24 recursos conocidos (12 fondos fotográficos y 12 modelos 3D) y aclara que los fondos no equivalen a entornos modulares; no se inventaron IDs ni nombres de recursos. Actualizado `.github/workflows/enforce_rules.yml`: la etiqueta `aprobado-por-usuario` se comprueba en cada ejecución sin condición basada en `mergeable_state`; la detección exige actualizar este documento ante cambios en `assets/`, `scripts/`, `scenes/`, `tests/` o cualquier archivo `.gd` fuera de `docs/`. La fila de Animación registra el fallo del Run #222 y deja su corrección para la refactorización de PR #15. Cambios preparados en la rama `docs/t2-product-catalog-and-ci-lock`; pendientes CI y revisión/merge de PR. No se modificó código de aplicación.
