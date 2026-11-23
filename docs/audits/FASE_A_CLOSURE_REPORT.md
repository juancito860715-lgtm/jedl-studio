# Informe de cierre — Fase A

- **Fecha de actualización:** 2026-11-23
- **Repositorio:** `juancito860715-lgtm/jedl-studio`
- **PR:** [#13 — mantener abierta y sin fusionar](https://github.com/juancito860715-lgtm/jedl-studio/pull/13)
- **Run de validación y evidencia consolidada:** [#185 — 45109200353](https://github.com/juancito860715-lgtm/jedl-studio/actions/runs/45109200353)
- **Commit validado por el Run #185:** `75ce594c9baf539fa348ae05c96c236e6e3b11a0`
- **Motor:** Godot 4.5.1 stable, build `f62fdbde1`.

## Alcance y criterio

Esta fase valida la confiabilidad de importación, integridad del catálogo congelado, rechazo controlado de recursos incompatibles, pruebas automatizadas, exportación Android y empaquetado de evidencias. No constituye una prueba física en dispositivo Android ni una certificación de rendimiento en hardware.

## Resultados A1–A5 — Run #185

| Criterio | Estado | Evidencia del Run #185 |
|---|---|---|
| A1 — Importación limpia | **CERRADO** | Importación normal completada con código 0; el log normal no contiene `ERROR:` ni `SCRIPT ERROR:`. El error de extensión del GLB incompatible aparece únicamente en la prueba negativa controlada A4. |
| A2 — Sidecars y caché | **CERRADO** | `GODOT_IMPORT_ARTIFACTS_OK: expectedImportableResources=68 verifiedSidecarsAndCache=68 importSidecarCount=68 cacheFileCount=208`. |
| A3 — Integridad e instanciación | **CERRADO** | `CATALOG_REPORT_VALIDATION_OK: assets=24 imported=24 instantiated=24 renderable=24 dependenciesVerified=55 threeDimensionalNodeCountsVerified=12`. El informe registra Godot 4.5.1 y los 24 recursos sin errores de validación. |
| A4 — Prueba negativa GLB real | **CERRADO** | `GODOT_NEGATIVE_IMPORT_OK`; GLB estructuralmente válido de 676 bytes; el importador real lo rechaza específicamente por `EXT_meshopt_compression`; `importerRejectedForUnsupportedExtension=true` y `ciGateWouldFail=true`. |
| A5 — Exclusión de Tevy | **CERRADO** | [Registro de exclusión](../../asset_exclusions.json): fecha 2026-11-22, referencia de auditoría, extensiones no soportadas, estado excluido y `activeCatalogAllowed=false`. |

### Pruebas de escenas y editor

Todas las pruebas de escena/parser/editor del Run #185 finalizaron correctamente:

- `SCENE_PARSER_TEST_OK`
- `CATALOG_MANAGER_TEST_OK`
- `CAMERA_FRAMING_TEST_OK`
- `PRODUCTION_EDITOR_TEST_OK`
- `GODOT_SMOKE_OK characters=1 subtitle_events=4`

### Integridad del paquete Android

- APK: `build/JEDLStudio-debug.apk`.
- Tamaño exacto: **109.055.728 bytes**.
- SHA-256: `621ddd9a0a3d651b0e4912dc06e213aa550aef3220cfad744d7bd25a5e394599`.
- El archivo `build/JEDLStudio-debug.apk.sha256` incluido en el ZIP del Run #185 contiene el mismo digest y nombre de APK.
- El log de exportación registra la generación, firma y verificación del APK como correctas.
- El aviso posterior de ADB `tcp:5037` indica que no había daemon disponible; no invalida la exportación ni la verificación del APK. La instalación y validación física en dispositivo Android siguen pendientes.

## A6 — Empaquetado y cierre documental

**Estado: CERRADO Y VERIFICADO EN CI — Run #185.**

- Workflow: [Run #185 — 45109200353](https://github.com/juancito860715-lgtm/jedl-studio/actions/runs/45109200353), resultado SUCCESS.
- Commit probado: `75ce594c9baf539fa348ae05c96c236e6e3b11a0`.
- Artefacto consolidado: `jedl-studio-evidence-run-185`.
- Artifact ID: `14788678968`.
- El ZIP descargado e inspeccionado contiene **27 archivos**: los seis entregables requeridos y 21 logs del runner.

Entregables confirmados dentro del ZIP:

- `docs/asset_exclusions.json`
- `docs/audits/FASE_A_CLOSURE_REPORT.md`
- `assets/gallery/glb_compatibility_report.json`
- `assets/gallery/validation_report.json`
- `build/JEDLStudio-debug.apk`
- `build/JEDLStudio-debug.apk.sha256`
- 21 logs del runner, incluidos los logs de importación, prueba negativa, validación, pruebas de escena y exportación.

El SHA-256 del APK fue contrastado contra el archivo de checksum incluido en el mismo artefacto. Ambos coinciden exactamente.

## Decisión de fase

La evidencia del Run #185 verifica A1–A6 en CI. El catálogo permanece congelado en **24 recursos**; no se modificaron recursos ni contenido del catálogo durante esta corrección documental. El PR #13 debe permanecer abierto y sin fusionar.

**Todos los artefactos, hashes y validaciones han sido confirmados en el Run #185. Se autoriza el paso a la Fase B**, sujeto a la condición de transición indicada a continuación.

### Condición de transición

Este informe se está actualizando en un commit documental posterior al Run #185. Por tanto, la Fase B de código **no debe comenzar hasta que el commit que contiene esta versión corregida del informe haya completado su propio workflow en estado SUCCESS**. Ese siguiente run será la confirmación final del cierre documental y el punto de inicio autorizado de la Fase B.

La validación física en un dispositivo Android continúa pendiente y no se declara realizada.
