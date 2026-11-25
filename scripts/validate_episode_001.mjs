import { readFileSync, existsSync } from 'node:fs';
import assert from 'node:assert/strict';

const root = 'producciones/episodio_001';
const html = readFileSync(`${root}/index.html`, 'utf8');
const script = JSON.parse(readFileSync(`${root}/guion.json`, 'utf8'));
const licenses = readFileSync(`${root}/LICENCIAS.md`, 'utf8');

assert.equal(script.duration_seconds, 30, 'El episodio debe durar 30 segundos');
assert.equal(script.shots.length, 6, 'Deben existir seis planos de cámara');
assert.equal(script.dialogue.length, 5, 'Deben existir cinco líneas de diálogo');
assert.equal(script.cast.length, 2, 'Deben existir dos personajes');
assert.ok(html.includes('new THREE.PerspectiveCamera'), 'Falta la cámara Three.js');
assert.ok(html.includes('function cameraAt(t)'), 'Falta el control de planos');
assert.ok(html.includes('SpeechSynthesisUtterance'), 'Falta la síntesis de voz');
assert.ok(html.includes('voiceschanged'), 'Falta detectar voces cargadas de forma asíncrona');
assert.ok(html.includes('subtitle.textContent'), 'Falta el sistema de subtítulos');
assert.ok(html.includes('requestAnimationFrame(tick)'), 'Falta el reloj de reproducción');
assert.ok(html.includes('loadModel(\'inventor\''), 'Falta cargar la inventora');
assert.ok(html.includes('loadModel(\'nina\''), 'Falta cargar la aprendiz');
assert.ok(html.includes('loadModel(\'banco\''), 'Falta cargar el objeto 3D');
assert.ok(licenses.includes('CC0 1.0'), 'Falta documentar la licencia de los recursos');
for (const item of script.cast) assert.match(item.asset, /^https:\/\//, `URL inválida para ${item.id}`);
for (const item of script.props) assert.match(item.asset, /^https:\/\//, `URL inválida para ${item.id}`);
assert.ok(existsSync(`${root}/README.md`), 'Falta el README del episodio');
console.log('OK: guion JSON, 30 s, 6 cámaras, 5 diálogos, 2 personajes, objeto 3D, voces y subtítulos.');
console.log('NOTA: esta validación es estática; no sustituye una prueba real en navegador/teléfono ni verifica la descarga de GLB.');
