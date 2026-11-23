# Hito 2 — implementación y validación

## Alcance
Editor táctil 2D, selección geométrica, transformación con uno/dos dedos, personaje procedural por partes, apariencias, poses conectadas al TimelineEngine existente y estilo global de escena. Sin audio, MP4, MediaPipe, 3D nuevo, descargas ni dependencias de red.

## Reutilización
- SceneParser conserva el documento de escena v2; `characters_2d`, `appearances` y `style` son campos opcionales.
- TimelineEngine mantiene schemaVersion 1 y las propiedades `rotation_degrees`; cada parte del rig se registra como target, también al reabrir.
- ProjectStore.gd y tests/project_store_recovery_test.gd permanecen intactos. Apariencias y estilos se guardan dentro del diccionario de escena.
- CatalogManager y assets/gallery permanecen sin cambios; el personaje se genera con Polygon2D/Marker2D en tiempo de ejecución.

## Componentes externos
- Godotion — MIT; el README declara soporte probado solo para Godot 4.7-stable. Godot 4.4.1/Android/GL Compatibility no verificados. No se usa: TimelineEngine ya cubre las pistas requeridas.
- Custom Sprite 2D — GPL-3.0; README declara Godot 4 genérico, sin verificación específica de Godot 4.4.1/Android/GL Compatibility. No se usa: las partes y apariencias se implementan con nodos nativos.
- VesperaFX — MPL-2.0; declara Godot 4.4.1. Android/GL Compatibility no verificados. No se usa: es postprocesado y no resuelve ninguno de los criterios C1-C4; C5 se cubre con CanvasItem.modulate.

## Criterios y pruebas
- C1: `tests/touch_selection_test.gd` — `TOUCH_SELECTION_TEST_OK`.
- C2: `tests/transform_gesture_test.gd` — `TRANSFORM_GESTURE_TEST_OK`.
- C3: `tests/appearance_test.gd` — `APPEARANCE_TEST_OK`.
- C4: `tests/rig_pose_test.gd` — `RIG_POSE_TEST_OK`.
- C5: `tests/style_test.gd` — `STYLE_TEST_OK`.
- C6: `tests/hito2_compatibility_test.gd` — `HITO2_COMPATIBILITY_TEST_OK`; regresiones Hito 1 ejecutadas sin modificar expectativas.

## Limitaciones conocidas
- El estilo global de Hito 2 actúa sobre los CanvasItem 2D de la escena; no altera nodos 3D.
- La selección usa límites geométricos (textura o polígonos) y no detección alfa por píxel ni física.
- La prueba física en Redmi Note 10 queda expresamente pendiente hasta el final del proyecto.


Validación incremental: las pruebas de pose también verifican serialización y restauración de pistas sobre targets re-registrados; los gestos convierten coordenadas de pantalla al espacio local del lienzo.

## APIs oficiales verificadas (Godot 4.4)
- [InputEventScreenTouch](https://docs.godotengine.org/en/4.4/classes/class_inputeventscreentouch.html): `index`, `position`, `pressed`.
- [InputEventScreenDrag](https://docs.godotengine.org/en/4.4/classes/class_inputeventscreendrag.html): `index`, `position`, `relative`, `screen_relative`.
- [Node2D](https://docs.godotengine.org/en/4.4/classes/class_node2d.html): transformaciones, `rotation_degrees`, `to_local`, `to_global`.
- [CanvasItem](https://docs.godotengine.org/en/4.4/classes/class_canvasitem.html): `modulate`, `make_canvas_position_local`, `get_global_transform_with_canvas`.
- [Sprite2D](https://docs.godotengine.org/en/4.4/classes/class_sprite2d.html): `texture`, `get_rect()`.
- [Polygon2D](https://docs.godotengine.org/en/4.4/classes/class_polygon2d.html), [Marker2D](https://docs.godotengine.org/en/4.4/classes/class_marker2d.html), [Dictionary](https://docs.godotengine.org/en/4.4/classes/class_dictionary.html), [JSON](https://docs.godotengine.org/en/4.4/classes/class_json.html) y [Transform2D](https://docs.godotengine.org/en/4.4/classes/class_transform2d.html): geometría, pivotes, datos, serialización y conversión de coordenadas.
