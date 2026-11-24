# JEDL Studio — Catálogo de recursos

**Versión del formato:** 1.0  
**Estado:** contrato documental inicial; inventario actual limitado a 24 recursos  
**Ubicación:** metadatos del catálogo y paquetes instalables fuera del APK

## 1. Propósito

Este documento define cómo se clasifican, identifican, validan e instalan los recursos que utiliza JEDL Studio. El catálogo es la fuente canónica de metadatos que consulta el editor y el SLM/LLM para producir JSON válido.

El catálogo debe poder crecer mediante paquetes descargables y funcionar sin conexión después de instalar cada paquete. Los recursos de los paquetes no se incluyen en el APK principal.

## 2. Estado actual del inventario

La evidencia de validación de la Fase A registra **24 recursos**:

| Grupo actual | Cantidad | Clasificación | Observación |
|---|---:|---|---|
| Fondos fotográficos | 12 | Imagen plana / recurso auxiliar | No son entornos modulares ni sustituyen su construcción |
| Modelos 3D | 12 | Modelo 3D | Recursos importados, instanciados y validados en CI |
| **Total** | **24** | | |

No se asignan nombres, identificadores ni dominios individuales a esos 24 recursos en este documento porque deben proceder de los manifiestos reales y no de suposiciones. El manifiesto de cada paquete es la autoridad para esos datos.

### 2.1 Lo que el inventario actual no demuestra

- No demuestra que exista una galería 2.5D suficiente.
- Los fondos fotográficos no cuentan como edificios, calles, suelos ni piezas modulares.
- No demuestra cobertura completa de todos los dominios (urbano, interior, naturaleza, mar, espacio o fantasía).
- No implica que todos los recursos puedan utilizarse en cualquier dispositivo o escena sin revisar memoria, dependencias y rendimiento.

## 3. Clasificación del catálogo

Cada entrada tendrá un tipo funcional y un formato:

### 3.1 Tipos funcionales

- `character`: personaje.
- `object`: objeto de escena.
- `vehicle`: vehículo.
- `environment_piece`: pieza modular de entorno (terreno, suelo, acera, calle, edificio, fachada, mobiliario, vegetación, cielo, mar u otra pieza ambiental).
- `environment_set`: conjunto coherente de piezas que permite construir un entorno.
- `vegetation`: planta, árbol u otro elemento vegetal.
- `audio`: voz, música, ambiente o efecto sonoro.
- `background_image`: imagen plana auxiliar; no equivale a un entorno modular.
- `reference`: recurso de referencia que no se instancia en la escena final.

### 3.2 Formatos

- `3d`: recurso tridimensional importable por Godot.
- `2.5d`: personaje o elemento ilustrado preparado para colocarse y animarse sin rigging manual por parte del usuario.
- `2d`: imagen o elemento plano auxiliar.
- `audio`: archivo de audio compatible con el reproductor del proyecto.

El formato describe el recurso; no crea una ruta distinta del lenguaje JSON.

## 4. Dominios

Los dominios de búsqueda previstos son:

- Urbano y transporte.
- Interiores y arquitectura.
- Naturaleza y vegetación.
- Mar y costa.
- Espacio y ciencia ficción.
- Fantasía y mundos imaginarios.
- Personajes y accesorios.
- Audio y efectos.

La presencia de un dominio en esta lista solo define una categoría prevista. El dominio se marca como disponible únicamente cuando existe al menos un paquete cuyos recursos hayan pasado validación de formato, integridad, licencia y uso.

## 5. Metadatos obligatorios por recurso

Cada entrada del manifiesto debe contener los siguientes campos. Los valores concretos deben extraerse del recurso y su fuente:

| Campo | Tipo | Significado |
|---|---|---|
| `id` | string | Identificador estable y único del recurso |
| `name` | string | Nombre legible |
| `type` | string | Tipo funcional de la sección 3.1 |
| `format` | string | Formato de la sección 3.2 |
| `domain` | string | Dominio principal |
| `tags` | array de strings | Etiquetas de búsqueda |
| `package_id` | string | Paquete al que pertenece |
| `path` | string | Ruta relativa dentro del paquete instalado |
| `source` | string | Fuente o proyecto de origen |
| `license` | string | Identificador exacto de licencia |
| `author` | string | Autor o titular, cuando corresponda |
| `attribution` | string | Texto de atribución requerido, si aplica |
| `sha256` | string | Hash SHA-256 del archivo |
| `size_bytes` | integer | Tamaño del archivo en bytes |
| `dependencies` | array | Dependencias necesarias para usar el recurso |
| `version` | string | Versión del recurso o revisión del paquete |

Los manifiestos reales pueden añadir metadatos técnicos específicos del formato, como escala, orientación, número de mallas, superficies, materiales, animaciones, duración, canales o compatibilidad. No se deben inventar valores ausentes.

## 6. Paquetes

Un paquete descargable debe incluir:

1. Identificador y versión del paquete.
2. Manifiesto de recursos.
3. Archivos de recursos y dependencias.
4. Hashes SHA-256 y tamaños.
5. Procedencia y licencia de cada recurso.
6. Atribuciones requeridas.
7. Versión mínima del formato de catálogo y requisitos de compatibilidad.

La instalación debe verificar integridad y dependencias antes de marcar el paquete como disponible. Una instalación incompleta o corrupta no debe aparecer como utilizable. La retirada de un paquete no debe destruir proyectos del usuario: debe dejar referencias faltantes visibles y ofrecer alternativas explícitas.

Los paquetes deben permanecer fuera del APK y almacenarse localmente después de su descarga. La ubicación y el hosting de distribución de paquetes siguen pendientes de decisión (Q5).

## 7. Licencias y procedencia

Solo se aceptan para integración las licencias:

- **CC0-1.0**
- **CC-BY-4.0**, con atribución automática y preservada.

Para cada recurso se debe verificar la licencia del archivo concreto; no basta con que la página general de una colección mencione una licencia. Deben conservarse autor, fuente, licencia y atribución exigida. Si no se puede verificar la procedencia o la licencia, el recurso no se integra.

Fuentes ya identificadas:

- **Kenney:** candidato para piezas 2D y 3D. No se considera fuente de personajes 2.5D.
- **Poly Haven:** fuente de texturas. No se considera fuente de escenarios modulares completos.

Estas referencias no autorizan a incorporar automáticamente todo su contenido. Cada recurso requiere selección y validación individual. Las fuentes para personajes 2.5D y para los dominios aún sin cobertura continúan pendientes.

## 8. Reglas de selección y búsqueda

- El buscador consulta nombre, tipo, formato, dominio y etiquetas.
- Los filtros deben permitir distinguir 3D, 2.5D y 2D.
- El resultado debe indicar si el recurso está instalado o pertenece a un paquete descargable.
- El LLM solo puede elegir IDs presentes en el catálogo consultado.
- Si un ID no existe o el paquete no está instalado, el validador debe informar el problema.
- Las alternativas se muestran al usuario y requieren su elección; nunca se sustituye un recurso silenciosamente.
- Los recursos fotográficos planos no deben aparecer como piezas modulares de entorno.

## 9. Validación técnica

Antes de activar un recurso se verifica, según corresponda:

1. Existencia del archivo y tamaño no nulo.
2. SHA-256 coincidente con el manifiesto.
3. Licencia y procedencia documentadas.
4. Importación real mediante la versión fijada de Godot.
5. Dependencias resueltas.
6. Carga e instanciación del recurso.
7. Estructura interna esperada (nodos, mallas, superficies, animaciones o canales).
8. Geometría o contenido renderizable cuando corresponda.
9. Compatibilidad con el renderer y las restricciones Android del proyecto.

Los recursos incompatibles se rechazan con un motivo explícito; no se corrigen ni reemplazan silenciosamente. La validación CI es necesaria, pero el uso satisfactorio en Redmi Note 10 sigue siendo el criterio de cierre de producto.

## 10. Pendientes del catálogo

- Fuente y paquete de personajes 2.5D para cada dominio (Q1).
- Fuentes verificadas para dominios sin cobertura (Q2).
- Confirmación operativa de CC-BY y atribución en la exportación (Q3).
- Esqueleto común para animación 2.5D sin rigging manual (Q4).
- Hosting y distribución de paquetes grandes (Q5).
- Taxonomía final de estilos visuales (Q6).
- Integración del catálogo con el SLM/LLM (Q7).

No se ampliará el inventario de 24 recursos actuales hasta completar la selección y verificación de fuentes y licencias. La cifra actual es una fotografía del estado validado, no un límite permanente del producto.
