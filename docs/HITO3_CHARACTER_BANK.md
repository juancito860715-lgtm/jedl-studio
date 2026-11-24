# Hito 3-A — Contrato del banco de personajes 2D

## Objetivo de esta subfase

Preparar una puerta de calidad estricta para incorporar arte real al rig 2D de Hito 2, sin introducir todavía imágenes provisionales ni cambiar el editor. El contrato valida un paquete local, su correspondencia con el rig, sus pivotes, sus hashes y sus derechos de redistribución.

**Esta subfase no incorpora arte final.** No crea PNG ficticios ni marca como terminado el personaje. El siguiente paso, Hito 3-B, será seleccionar un paquete de arte concreto y mapearlo a los seis slots después de revisar visualmente cada pieza y su licencia.

## Rig admitido

El identificador del contrato es jedl_humanoid_v1, esquema 1. Los seis slots obligatorios deben corresponder exactamente a los nodos del rig actual:

| Slot | Bone ID |
|---|---|
| head | head |
| torso | torso |
| arm_left | arm_left |
| arm_right | arm_right |
| leg_left | leg_left |
| leg_right | leg_right |

Un banco puede contener varias variantes para un mismo slot. Debe declarar una pieza predeterminada para cada uno de los seis slots.

**Limitación del rig actual:** esta versión refleja los seis nodos de Hito 2. Cada brazo y cada pierna es una sola pieza; no hay antebrazo, espinilla ni articulaciones jerárquicas de codo/rodilla. Este contrato no certifica todavía un humano completamente articulado. Antes de incorporar arte final, el rig debe ampliarse y el contrato debe versionarse para sus nuevos slots.

## Ubicación del paquete

Cada banco se guarda en:

assets/characters/banks/<bankId>/

Debe incluir:
- manifest.json
- LICENSE.txt
- parts/*.png

Las rutas de los recursos se expresan como res://assets/characters/banks/<bankId>/... No se admiten rutas absolutas, segmentos .., enlaces simbólicos ni archivos fuera de la carpeta del banco.

## Esquema de manifest.json

Campos de raíz:
- schemaVersion: entero 1.
- bankId: identificador estable en minúsculas.
- version: entero positivo.
- title: nombre visible.
- rigId: jedl_humanoid_v1.
- rigSchemaVersion: 1.
- offline: true.
- licensePolicy: solo CC0-1.0, con redistribución y uso offline permitidos.
- license: identificador CC0, URL oficial de evidencia y ruta local a LICENSE.txt.
- provenance: URL HTTPS de origen, editor, autores y atribución.
- parts: lista de variantes.
- defaultParts: mapa exacto de los seis slots a sus IDs predeterminados.

Cada objeto de parts contiene:
- id: ID único.
- slot: uno de los seis slots.
- boneId: debe coincidir con slot.
- path: PNG local dentro de la carpeta del banco.
- sha256: SHA-256 hexadecimal del PNG.
- pivot: coordenadas normalizadas x e y, entre 0 y 1.
- zIndex: entero entre -128 y 128.

## Límites para Redmi Note 10

- PNG de 8 bits con canal alfa.
- Ancho y alto máximos: 1024 píxeles.
- Máximo de 1.048.576 píxeles por textura.
- Máximo de 4 MiB por PNG.
- Máximo de 24 MiB para los PNG únicos del banco.
- Máximo de 64 variantes por banco.
- No se descarga ni consulta ningún recurso durante la ejecución de la app.

Los límites son deliberadamente conservadores para evitar paquetes de texturas desproporcionados en un dispositivo de memoria modesta.

## Licencia y procedencia

La primera versión del contrato admite exclusivamente CC0-1.0. Exige:
- URL de evidencia oficial de Creative Commons.
- Copia local de la licencia dentro del banco.
- URL HTTPS de la fuente original.
- Editor, autores y atribución no vacíos.
- Confirmación explícita de redistribución y uso offline.

No basta con que una página diga "free". El banco real no se aceptará hasta verificar la licencia de la descarga concreta y guardar su aviso original.

## Pruebas

Ejecutar desde la raíz del repositorio:

python tools/character_bank/test_validate_bank.py

La suite utiliza solo la biblioteca estándar de Python y PNG sintéticos temporales; no descarga archivos ni depende de Pillow, CairoSVG o servicios externos.

Para validar un banco real:

python tools/character_bank/validate_bank.py assets/characters/banks/<bankId>/manifest.json

El resultado esperado es CHARACTER_BANK_OK. Cualquier ruta insegura, licencia ausente, hash incorrecto, slot incompleto o textura fuera de límites debe hacer fallar la validación.

## Criterio de cierre de Hito 3-A

- Todas las pruebas positivas y negativas pasan.
- El workflow Android ejecuta la suite antes de importar Godot.
- El APK de Hito 2 y sus escenas no cambian.
- No se añade ningún recurso de arte provisional.
- La PR permanece aislada y sin fusionar hasta que el banco real esté seleccionado y revisado.
