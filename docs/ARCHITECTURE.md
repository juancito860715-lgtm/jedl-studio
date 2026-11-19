# JEDL Studio v2 — Architecture M0

La app se organiza en seis módulos con límites explícitos. M0 solo entrega el shell Android y las puertas de calidad; los módulos funcionales se incorporan en las fases posteriores.

1. **Project Core** — identidad, metadatos, escenas, guardado, apertura y migraciones de proyectos.
2. **Asset & License Registry** — importación de recursos, almacenamiento local, manifiesto y validación obligatoria de licencias.
3. **Scene & Layer Engine** — composición de escenas, orden Z, transformaciones y visibilidad de capas.
4. **Character & Motion Engine** — personajes articulados, rigs, poses, keyframes y biblioteca de movimientos.
5. **Timeline & Audio** — pistas temporales, sincronización de audio, voz, vídeo y subtítulos.
6. **Preview & Export** — reproducción, diagnóstico, renderizado y exportación local.

**Reglas transversales:** procesamiento local/offline como objetivo; dependencias explícitas entre módulos; contratos y pruebas antes de lógica productiva; ningún recurso empaquetado sin entrada de licencia permitida; CI es la única autoridad de compilación en este proyecto.
