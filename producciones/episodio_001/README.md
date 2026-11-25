# Episodio 001 — El secreto del viejo taller

Primera producción HTML de JEDL Studio con Three.js.

## Abrir

Abrir este directorio mediante GitHub Pages o un servidor web estático. Se necesita internet para Three.js y los GLB externos.

## Montaje actual

- Duración de reproducción: 30 segundos.
- Dos personajes GLB externos de Gobkit, con animación idle disponible.
- Taller procedural y banco de trabajo GLB CC0 en LOD2.
- Ocho encuadres: plano general, dos planos medios, regreso al inventor, detalle de manos/mecanismo, dos primeros planos y plano conjunto.
- Cámara con transición suavizada y campo de visión ampliado para pantallas estrechas.
- Diálogos y subtítulos temporizados.
- Actuación procedural: movimiento sutil de cabeza/brazos y apertura de boca cuando los GLB exponen huesos o morph targets con nombres compatibles.
- Audio ambiental provisional generado con Web Audio API.
- Voz mediante Web Speech API, con detección de voces españolas.

## Limitaciones conocidas — no ocultar

1. **Selección de personajes pendiente:** GrandmaShopper es una mujer mayor y no corresponde al inventor masculino de la referencia; Schoolkid es un modelo genérico. Ambos son placeholders funcionales, no el casting artístico aprobado.
2. Los GLB son dependencias remotas y no están empaquetados localmente.
3. La síntesis de voz depende de Safari/iOS y de las voces instaladas. No hay locución grabada y no se garantiza la misma voz en todos los teléfonos.
4. La música actual es una textura sonora procedural, no una banda sonora musical ni una pista de estudio.
5. El lip-sync es aproximado y solo actúa si el modelo expone morph targets faciales compatibles.
6. La validación de CI comprueba JSON, estructura, funciones y sintaxis JavaScript; no demuestra la reproducción real de los modelos, las voces ni el audio en un teléfono.

## Criterio para aceptar nuevos personajes

No se reemplazarán por un modelo solo porque su nombre parezca apropiado. El recurso debe cumplir:
- apariencia coherente con el inventor mayor masculino y la niña aprendiz de la referencia;
- licencia libre verificable y compatible con el uso del proyecto;
- GLB íntegro, tamaño razonable para móvil, texturas embebidas o locales;
- esqueleto y clips de animación inspeccionados;
- morph targets faciales o un plan de actuación comprobable;
- pruebas de carga y reproducción en navegador móvil.

## Recursos y licencias

Consultar [LICENCIAS.md](./LICENCIAS.md) y [guion.json](./guion.json).

## Controles

Pulsa «Iniciar escena · 30 s». El audio se activa desde ese gesto del usuario, como exige el navegador. El botón de voz permite silenciar la síntesis de diálogos.
