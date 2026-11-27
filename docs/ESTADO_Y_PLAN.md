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
  - 2026-11-24 — T2 cerrada: PR #22 fusionada en main (merge commit be164319b43b3c0c5291c85353211279f954256b). Quedan incorporados docs/PRODUCTO.md, docs/CATALOGO.md y el refuerzo de enforce_rules.yml. La aprobación humana y el merge fueron confirmados por el usuario y el estado merged de GitHub.
  - 2026-11-24 — T3, caso principal JSON de cruce urbano. Creado scenes/escena_cruce_coche.json en la rama feat/t3-crossing-car-scene-json. El documento describe el hombre, el coche azul, el entorno urbano modular, el desplazamiento del peatón, el plan de movimiento del coche y las señales temporizadas de pasos, puerta y motor. La versión original usaba `characters_2d` y quedó obsoleta tras el contrato 2.5D/3D. La escena se migró: `characters` queda vacío hasta instalar un personaje real 2.5D/3D; peatón, coche y entorno modular se registran como requisitos pendientes, sin inventar `assetId` ni sustituirlos por geometría. El coche y los módulos se dejan como requisitos pendientes de resolución desde catálogo; las rutas de audio están vacías y el bucle del motor queda señalado como pendiente porque el parser actual solo reproduce sonidos con path válido y no implementa looping. JSON validado sintácticamente. PR #23 abierta para revisión: https://github.com/juancito860715-lgtm/jedl-studio/pull/23. No fusionada.

  - 2026-11-24 — Corrección de formatos de personaje (PR #24): eliminado el generador procedural `CharacterRig2D.gd` y su prueba heredada; `SceneParser` rechaza `characters_2d`, exige `format` explícito (`2.5d` o `3d`), `assetId` del catálogo y un `PackedScene` con rig comprobable. 2.5D requiere `Skeleton3D` con `BoneAttachment3D` que contengan `Sprite3D`; 3D requiere `Skeleton3D` y `MeshInstance3D` con `Skin`. La figura geométrica de prueba se oculta de las galerías de personajes por carecer de `character_format`. La escena de demostración ya no instancia ningún personaje automáticamente; los PNG 2D se mantienen solo como elementos auxiliares. PR #18 (banco de seis slots 2D) no cumple esta definición y no debe fusionarse sin rediseño. Pendiente CI Godot 4.5.1 y recursos reales de personajes 2.5D/3D; no se declara galería de personajes terminada.
  - 2026-11-24 — Hallazgo post-merge PR #24, Run #303: Godot 4.4.1 detectó que `scripts/Editor2DPanel.gd` aún precargaba el generador eliminado y mantenía botones de creación/pose de personajes 2D. Corregido en PR #25: el panel ahora edita únicamente elementos gráficos auxiliares (posición, rotación, escala, orden Z y estilo); se eliminaron sus señales y conexión de alta/selección de personajes. El contrato de rig también exige textura no vacía en Sprite3D 2.5D y Skin con ruta Skeleton3D en MeshInstance3D 3D. El Run #303 falló en importación por esa referencia residual; la exportación APK no se ejecutó. Pendiente validar con Godot 4.5.1 y CI completo.

  - 2026-11-24 — Migración del caso T3 `escena_cruce_coche.json`: retirado `characters_2d`, `actions` queda vacío mientras no existan instancias reales y `motion_plan` conserva los movimientos como pendientes de enlazar. Se añaden requisitos de catálogo para peatón 2.5D/3D, coche 3D y piezas urbanas modulares. Test `scene_parser_test.gd` carga la escena y verifica que no aparecen sustitutos ni placeholders.
  - 2026-11-24 — Run #309 (Godot 4.5.1) confirmó importación limpia y pasó `character_format_contract_test.gd`; falló `scene_parser_test.gd` porque, al retirar el personaje de demostración, el test seguía esperando pausa de una línea temporal sin acciones. Corregido el ejemplo: la animación de 2 keyframes ahora mueve únicamente el elemento gráfico auxiliar `leaf_demo`, nunca un personaje. Se actualizaron las expectativas de smoke y catálogo y se añadió prueba de carga de `escena_cruce_coche.json` sin placeholders. Run #309 queda registrado como fallo de test, no como APK producido; pendiente nueva ejecución completa.

## Actualización — Episodio HTML 001 (2026-11-25)

- Se amplió la secuencia de cámara a ocho planos con encuadres específicos para móvil y transiciones suavizadas.
- Se añadieron controles de actuación procedural sobre huesos y morph targets faciales cuando el GLB los exponga.
- Se mejoró la gestión de voz del navegador y se documentó que no existe aún locución grabada ni música final.
- El banco de trabajo usa el GLB CC0 Tool Chest and Bench LOD2 (4.952 triángulos, 195 KB), URL versionada.
- La CI HTML valida JSON, ocho planos, estructura de diálogos, hooks de actuación y sintaxis JavaScript.
- Pendiente: sustituir GrandmaShopper y Schoolkid por personajes que sí correspondan a la referencia, con licencia verificable y rig inspeccionado; integrar voz y música como archivos locales; probar carga, sonido y sincronía en Safari/iPhone.
- Esta actualización afecta exclusivamente a la producción HTML. No se solicita APK; el workflow Android existente puede activarse automáticamente por la configuración general de PR.


  - 2026-11-25 — Episodio HTML 001, corrección de recursos y casting (PR #36): se sustituyeron las referencias remotas a GrandmaShopper, Schoolkid y Tool Chest por geometría procedural original integrada en `producciones/episodio_001/index.html`. El reparto ahora representa un inventor masculino mayor con barba/cabello blancos, gafas, suéter verde y overol rojo, junto a una niña aprendiz con ropa rosa. Banco, taller y engranajes se construyen dentro de la escena; se eliminó la carga GLB que causaba el aviso de recurso no disponible. Se ajustó la cámara para móvil, se conservaron ocho planos, cinco diálogos, subtítulos, voz Web Speech y ambiente Web Audio. Se actualizaron guion, licencias, README y validador. El workflow Pages ahora se dispara también cuando cambia el `index.html` raíz. Límite: Three.js sigue dependiendo del CDN; voz y música siguen siendo provisionales; falta verificación visual/auditiva real en Safari/iPhone. Run HTML #45542216828: validación estática completada con éxito; publicación omitida por ser evento pull_request. El candado enforce-rules exige esta actualización documental y la etiqueta de aprobación.

- 2026-11-24 — Episodio HTML 001 (PR #37): se sustituye la escena 3D procedural anterior por una ilustración SVG original autocontenida, con taller y dos protagonistas dibujados en el propio HTML, ocho encuadres interpolados, gestos, subtítulos y síntesis de voz del navegador. Se eliminan dependencias CDN/modelos externos. Validador actualizado; run de episodio #45543026319 validó estructura y sintaxis correctamente. La política de gobernanza requiere registrar este cambio en este archivo; la verificación visual real en Safari/iPhone queda pendiente y no se declara cerrada. Música grabada y locuciones profesionales no incluidas.

- 2026-11-24 — El usuario autorizó expresamente proceder con la reconstrucción HTML del episodio 001; PR #37 etiquetada `aprobado-por-usuario` para satisfacer la protección de integración.

- 2026-11-24 — PR #38: autorización del usuario para unificar publicación de Pages; el despliegue nativo de GitHub Pages es el único publicador y el workflow del episodio queda como validador.

- 2026-11-24 — PR #38: se unifica la publicación con el flujo nativo de GitHub Pages y se elimina el paso de etiqueta de aprobación duplicada del workflow de PR; se conserva la validación obligatoria de actualización de esta memoria del proyecto.


## 7. Auditoría matemática del manifiesto Three.js (2026-11-26)

- Alcance separado: completar las especificaciones matemáticas del manifiesto Three.js; esta tarea no cambia el motor de la aplicación ni autoriza alterar los registros preservados de Crimson Loong.
- PR #43 permanece abierta y en borrador. El manifiesto contiene 541 técnicas: 46 preservadas, 495 no preservadas pendientes y 0 certificadas como `IMPLEMENTATION_READY`.
- Se ampliaron las notas de derivación y localización de fuentes para XPBD, Kuwahara anisotrópico, Boids y el modelo microfacet de cabello. Ninguna de estas fichas se declara lista.
- XPBD: fuente primaria localizada en Macklin, Müller y Chentanez (2016), §4, Ecs. (16)-(18) y Algoritmo 1. Se documentaron la aproximación cuasi-Newton, el acumulador de multiplicadores y los casos singulares. La variante amortiguada (Ec. 26) queda separada.
- Kuwahara anisotrópico: fuente primaria localizada en Kyprianidis, Kang y Döllner (2009), §3.1-§3.2, Ecs. (1)-(4) y regla de pesos posterior. Se añadió un kernel de referencia Python/JavaScript con la fórmula publicada `alpha_i = 1/(1 + ||s_i||^q)`, q=8 en los ejemplos. La función anterior `weighted_sector_mean` se conserva como convención genérica y no debe presentarse como la ecuación publicada del filtro.
- Boids: se aclaró que la suma ponderada del manifiesto es una parametrización de implementación, no una ecuación textual única de Reynolds (1987). Falta fijar dimensionalmente si cada término es desplazamiento, velocidad deseada o aceleración.
- Cabello microfacet: se fijaron los localizadores §3.1 Ecs. (2), (4)-(12), Ecs. (13)-(25) y Appendix A Ecs. (41)-(44). Las fórmulas están como ecuaciones-imagen en la fuente web; se requiere transcripción y verificación de los términos antes de implementar.
- La primera ejecución de gobernanza falló porque el candado del repositorio exige actualizar este archivo cuando cambian pruebas/código. La ejecución matemática debe revisarse por separado; no se declara CI global verde por ese fallo.
- Próximo bloque: terminar pruebas independientes y contrato dimensional de XPBD/Kuwahara; extraer las ecuaciones completas de cabello; derivar Boids con magnitudes dimensionalmente homogéneas; después continuar las otras 19 R31 y procesar las 472 fichas históricas por dominio.


## 8. Segundo bloque de especificaciones R31 (2026-11-26)

- Se completó la revisión de localizadores primarios para cuatro fichas, sin promover ninguna a `IMPLEMENTATION_READY`.
- XPBD: ecuaciones (5)-(9), (12), (15)-(18) y Algoritmo 1 de Macklin et al. (2016) contrastados. Para restricción de distancia: compliance `s²/kg`, compliance escalada `kg^-1`, multiplicador `kg·m`. Añadidos fixtures cerrados para dos pasos temporales. Pendiente solver multiconstraint y restricciones no métricas.
- Kuwahara: corregido el localizador: PG 2009 contiene Ecs. (1)-(4); pesos y salida aparecen después de Ec. (4), §3.2, p. 1960. RGB entero 0..255; q=8 depende de esa escala. La fuente citada valida una escala por aplicación, no mezcla simultánea multiescala/saliencia.
- Boids: Reynolds (1987), §3, pp. 28-29, confirma comportamientos por prioridad, solicitudes de aceleración acotadas, strength [0,1] y reparto prioritario con recorte al máximo. Añadido kernel Python/JS. La suma ponderada del manifiesto no es ecuación textual de Reynolds y sigue sin validez dimensional demostrada.
- Cabello microfacet: transcritos BCSDF R de Ec. (12), NDF GGX de Appendix A Ec. (41) y producto escalar de Ec. (42). Añadido NDF de fibra con fixtures Python/JS. TT/TRT (13)-(24) localizados pero pendientes de implementación numérica independiente; el NDF aislado no certifica el modelo.
- Pruebas añadidas: XPBD sensibilidad a dt, asignación prioritaria de Reynolds y NDF GGX de fibra. Pendiente consultar CI del head actualizado.
- Estado: cuatro fichas mejor documentadas; ninguna certificada. Próximo bloque: verificar CI, corregir fallos y continuar las 19 R31 restantes; la paridad entre lenguajes no sustituye referencias matemáticas independientes.
