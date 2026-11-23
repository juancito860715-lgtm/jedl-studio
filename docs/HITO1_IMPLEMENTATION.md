# Hito 1 — Base de producción 2D, JSON, timeline y persistencia

## Base y reutilización

Esta rama parte de `main` en `63d2b0a8bb82feddadb48069b5268b38822b6ab2`. No modifica `main` ni incorpora commits de PRs anteriores sin fusionar.

Se reutilizan:
- `project.godot` y `export_presets.cfg`: Godot 4.4.1, GL Compatibility y exportación Android ARM64.
- `Main.tscn`: escenario 3D, cámara, luz y entorno.
- `CatalogManager.gd`: esquema de catálogo v2, manifiesto raíz, comprobación SHA-256 del catálogo y validación de identidades/licencias.
- `SceneParser.gd`: validación JSON, resolución por assetId, instanciación de PackedScene y sprites transparentes, eventos temporizados de subtítulos y sonidos.
- `build_godot.yml`: instalación del motor/export templates, importación del proyecto, pruebas headless y exportación APK debug.

Se reemplaza el contenido de ejemplo que dependía de Fox/Mossy Forest y las descargas de recursos en tiempo de CI por un paquete local pequeño. El workflow ya no descarga modelos o galerías desde proveedores durante la validación del hito.

## Componentes nuevos

- `assets/gallery/catalog.json` y `manifest.json`: cuatro recursos propios CC0-1.0, con SHA-256, rutas locales y metadatos de licencia.
- Galería 2D independiente: tres PNG RGBA de 256×256 con transparencia, instanciados como Sprite2D bajo un CanvasLayer/Node2D propio, separado del escenario 3D.
- Galería 3D independiente: escena TSCN propia con geometría primitiva y raíz Node3D.
- El lienzo 2D mantiene coordenadas de escena en unidades lógicas y las transforma a píxeles de pantalla; posición, rotación y escala 2D se exponen al motor compartido como Vector3 lógico.
- `TimelineEngine.gd`: único motor de pistas/keyframes para acciones JSON y edición manual. Soporta creación, edición, movimiento, eliminación, seek, play, pause, resume, stop, secuencias consecutivas y propiedades concurrentes. Rechaza solapamientos de acciones sobre la misma propiedad.
- `ProjectStore.gd`: persistencia JSON versionada en `user://projects`, backup al sobrescribir, restauración y duplicación.
- UI: proyecto nuevo vacío, galerías separadas, lista visible de pistas y marcadores seleccionables, controles manuales de keyframes, sincronización del cabezal durante reproducción y alternativa/cancelación explícita cuando falta un recurso.

## Pruebas añadidas o actualizadas

- `test_local_catalog.py`: transparencia real de PNG, SHA-256, tamaños, manifiesto y contenido local.
- `catalog_manager_test.gd`: carga de catálogo y escena de ejemplo sin descargas.
- `scene_parser_test.gd`: acciones JSON, eventos, reproducción y error explícito de assetId ausente.
- `timeline_engine_test.gd`: equivalencia JSON/manual para posición, rotación y escala en varios instantes, continuidad sin keyframes duplicados en límites, concurrencia, secuencias, edición, movimiento, borrado, serialización y reproducción tras restauración.
- `camera_framing_test.gd`: separación real Sprite2D/Node3D, inserción desde la galería al lienzo 2D, transformaciones 2D y round-trip integrado de proyecto y timeline.
- `project_store_test.gd`: ida/vuelta exacta, backup/restore y duplicación.
- `camera_framing_test.gd`: proyecto vacío, galerías independientes, alternativa de recurso y cancelación restaurando la escena previa.

## Compatibilidad API

Las operaciones de serialización y archivos usan APIs documentadas para Godot 4.4:
- JSON: https://docs.godotengine.org/en/4.4/classes/class_json.html
- FileAccess: https://docs.godotengine.org/en/4.4/classes/class_fileaccess.html
- DirAccess: https://docs.godotengine.org/en/4.4/classes/class_diraccess.html
- ImageTexture y carga de recursos: https://docs.godotengine.org/en/4.4/classes/class_imagetexture.html

El timeline usa interpolación propia sobre transformaciones Node3D y no depende de métodos de plugins externos.

## Memoria y límites

El paquete de inicio ocupa aproximadamente 9.0 KB en disco según el manifiesto. Las tres texturas RGBA de 128×128 representan aproximadamente 0.19 MiB de píxeles descomprimidos si se cargan simultáneamente; la escena 3D utiliza primitivas de Godot y no añade una malla externa pesada. La galería limita la presentación a 24 tarjetas por vista y no instancia todo el catálogo.

Los PNG de la galería 2D se representan como Sprite2D en un CanvasLayer independiente, por encima del escenario 3D y debajo de la interfaz. Esto evita convertirlos en Sprite3D billboard; no ofrece todavía oclusión física entre sprites 2D y geometría 3D. La edición básica de posición, rotación y escala se realiza mediante el inspector y keyframes del timeline. La manipulación táctil directa y el rig por capas pertenecen al Hito 2.

## Estado de aceptación

Todos los criterios quedan **PENDIENTES DE CERTIFICACIÓN CI** hasta que `build_godot.yml` pase en el SHA exacto de esta rama. No se declara el hito cerrado ni se autoriza comenzar el Hito 2 antes de ese resultado.
