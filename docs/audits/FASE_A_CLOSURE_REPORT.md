# Informe de cierre — Fase A

- **Fecha:** 2026-11-22
- **Repositorio:** `juancito860715-lgtm/jedl-studio`
- **PR:** [#13 — mantener abierta y sin fusionar](https://github.com/juancito860715-lgtm/jedl-studio/pull/13)
- **Run de validación técnica de referencia:** [#184 — 45105876978](https://github.com/juancito860715-lgtm/jedl-studio/actions/runs/45105876978)
- **Commit validado:** `64b575133604df0088af1a24af75c0cb6de01d7f`
- **Motor:** Godot 4.5.1 stable, build `f62fdbde1`.

## Alcance y criterio

Esta fase valida la confiabilidad de importación, integridad del catálogo congelado, rechazo de recursos incompatibles, pruebas automatizadas y exportación Android. No constituye una prueba física en dispositivo Android ni una certificación de rendimiento en hardware.

## Resultados A1–A5

| Criterio | Estado | Evidencia del Run #184 |
|---|---|---|
| A1 — Importación limpia | **CERRADO** | Job completo SUCCESS; `GODOT_IMPORT_EXIT_CODE=0`; importación mediante sesión portal; sin `ERROR:`, `SCRIPT ERROR:` ni error de importación en el log normal. |
| A2 — Sidecars y caché | **CERRADO** | `GODOT_IMPORT_ARTIFACTS_OK: expectedImportableResources=68 verifiedSidecarsAndCache=68 importSidecarCount=68 cacheFileCount=208`. |
| A3 — Integridad e instanciación | **CERRADO** | `CATALOG_ASSET_VALIDATION_OK: assets=24`; `CATALOG_REPORT_VALIDATION_OK: assets=24 imported=24 instantiated=24 renderable=24 dependenciesVerified=55 threeDimensionalNodeCountsVerified=12`. |
| A4 — Prueba negativa GLB real | **CERRADO** | `GODOT_NEGATIVE_IMPORT_OK`; GLB estructuralmente válido de 676 bytes; el importador real rechaza específicamente `EXT_meshopt_compression`; `ciGateWouldFail=true`. |
| A5 — Exclusión de Tevy | **CERRADO** | [Registro de exclusión](../asset_exclusions.json): fecha, referencia de auditoría, extensiones no soportadas y prohibición de catálogo activo. El log registra `GLB_EXCLUDED_BY_POLICY: character.tevy.casual_walker.v1`. |

### Evidencia adicional del Run #184

- [Registros y salidas de GitHub Actions](https://github.com/juancito860715-lgtm/jedl-studio/actions/runs/45105876978).
- [Artefactos del Run #184](https://github.com/juancito860715-lgtm/jedl-studio/actions/runs/45105876978): `jedl-studio-resource-validation`, `jedl-studio-validation-logs` y `jedl-studio-godot-android-debug-apk`.
- APK exportado: `build/JEDLStudio-debug.apk`, ZIP Android válido, 101,314,223 bytes.
- SHA-256 del APK: `10118c6ab74ac5b0222f9b3b9369f31b7028264ffe113a27773eced12565ddc3`.
- Las cinco pruebas de escena/parser/editor finalizaron correctamente: `SCENE_PARSER_TEST_OK`, `CATALOG_MANAGER_TEST_OK`, `CAMERA_FRAMING_TEST_OK`, `PRODUCTION_EDITOR_TEST_OK` y `SCENE_PARSER_SMOKE_OK`.
- El APK se generó y se subió como artefacto. El mensaje ADB `tcp:5037` no invalida la exportación; la instalación y validación física siguen pendientes.

## A6 — Empaquetado y cierre documental

**Estado previsto: CERRADO al completar correctamente el workflow de este commit.**

Este commit incorpora el registro `docs/asset_exclusions.json` y este informe en un único artefacto de auditoría, junto con los informes de validación, todos los logs disponibles y el APK con su SHA-256. El nombre del paquete es `jedl-studio-evidence-run-<run_number>`; para este commit corresponde el Run #185.

La comprobación final de A6 requiere que el Run #185 termine en `success` y que su ZIP consolidado contenga, como mínimo:

- `docs/asset_exclusions.json`
- `docs/audits/FASE_A_CLOSURE_REPORT.md`
- `assets/gallery/glb_compatibility_report.json`
- `assets/gallery/validation_report.json`
- `build/JEDLStudio-debug.apk`
- `build/JEDLStudio-debug.apk.sha256`
- Los logs de validación del runner.

## Decisión de fase

La Fase A queda formalmente cerrada únicamente cuando el Run #185 confirme el artefacto consolidado y el PR #13 permanezca abierto y sin fusionar. No se modifican los recursos ni el catálogo; se conserva el conjunto validado de 24 recursos.

> La Fase A (Confiabilidad de importación y CI) queda formalmente cerrada. Se autoriza el inicio de la Fase B (Integridad de escena y materiales), manteniendo el catálogo congelado y el PR #13 sin fusionar.

**Restricción de transición:** la declaración anterior entra en vigor solamente después de que el workflow de confirmación sea SUCCESS y se verifique el ZIP consolidado. No iniciar Fase B antes de esa verificación.
