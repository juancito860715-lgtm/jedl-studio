import { readFileSync, existsSync, mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';

const root = 'producciones/episodio_001';
const html = readFileSync(`${root}/index.html`, 'utf8');
const script = JSON.parse(readFileSync(`${root}/guion.json`, 'utf8'));
const licenses = readFileSync(`${root}/LICENCIAS.md`, 'utf8');

assert.equal(script.duration_seconds, 30, 'El episodio debe durar 30 segundos');
assert.equal(script.shots.length, 8, 'Deben existir ocho planos cinematográficos');
assert.equal(script.dialogue.length, 5, 'Deben existir cinco líneas de diálogo');
assert.equal(script.cast.length, 2, 'Deben existir dos personajes');
assert.ok(html.includes('new THREE.PerspectiveCamera'), 'Falta la cámara Three.js');
assert.ok(html.includes('function cameraAt(t)'), 'Falta el control de planos');
assert.ok(html.includes('function bindActorControls(root)'), 'Falta la detección de huesos y morph targets');
assert.ok(html.includes('function animateActorPerformance(t)'), 'Falta la actuación corporal procedural');
assert.ok(html.includes('activeSpeaker'), 'Falta el seguimiento de la voz activa');
assert.ok(html.includes('camera.fov=innerWidth<700?64:42'), 'Falta el encuadre ampliado para móvil');
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
const startTag = '<script type="module">';
const endTag = '</script>';
const start = html.indexOf(startTag);
const end = html.indexOf(endTag, start + startTag.length);
assert.ok(start >= 0 && end > start, 'No se encontró el módulo JavaScript de la escena');
const temp = mkdtempSync(join(tmpdir(), 'jedl-episode-'));
const tempFile = join(temp, 'episode.mjs');
try {
  writeFileSync(tempFile, html.slice(start + startTag.length, end));
  const syntax = spawnSync(process.execPath, ['--check', tempFile], { encoding: 'utf8' });
  assert.equal(syntax.status, 0, 'JavaScript inválido: ' + (syntax.stderr || syntax.stdout));
} finally {
  rmSync(temp, { recursive: true, force: true });
}
console.log('OK: guion JSON, 30 s, 8 planos, 5 diálogos, 2 personajes, objeto 3D, voces, subtítulos, gestos y sintaxis JS.');
console.log('NOTA: esta validación es estática; no sustituye una prueba real en navegador/teléfono ni verifica la descarga de GLB.');
