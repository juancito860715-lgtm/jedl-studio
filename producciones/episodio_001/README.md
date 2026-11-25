# Episodio 001 — El secreto del viejo taller

Reproductor cinematográfico HTML de 30 segundos para navegador móvil.

## Qué incluye
- Taller, engranajes, banco y herramientas construidos dentro de la escena Three.js.
- Inventor masculino mayor con barba y cabello blancos, gafas, suéter verde y overol rojo.
- Niña aprendiz con cabello oscuro y ropa rosa.
- Personajes y utilería generados proceduralmente: no se descargan modelos GLB externos.
- Ocho encuadres, cámara con transiciones suavizadas y composición ajustada a pantallas estrechas.
- Cinco diálogos con subtítulos temporizados, voz española del navegador cuando está disponible y gestos sincronizados.
- Ambiente sonoro procedural mediante Web Audio.

## Abrir
Abrir mediante GitHub Pages. Se requiere conexión para cargar Three.js desde jsDelivr. Los personajes, el banco y el taller no dependen de servidores externos.

## Límites conocidos
- Los personajes son geometría low-poly original, no modelos artísticos detallados ni una copia exacta de la referencia.
- La voz depende de Web Speech API y de las voces disponibles en el teléfono; no hay archivos de locución grabados.
- El audio es una textura musical procedural, no una banda sonora de estudio.
- El validador de CI verifica el guion, estructura y sintaxis JavaScript, pero no reemplaza la reproducción real en Safari/iPhone.

## Controles
Pulsa «Iniciar escena · 30 s». La voz puede silenciarse con el segundo botón.