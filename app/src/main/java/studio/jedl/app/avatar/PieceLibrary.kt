package studio.jedl.app.avatar

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Log
import org.json.JSONObject

enum class CharacterLayerSlot {
    HEAD, EYES, EYEBROWS, MOUTH, FACIAL_HAIR, HAIR_BACK, HAIR_FRONT,
    HAT_BACK, HAT_FRONT, TORSO, SHIRT, PANTS,
    UPPER_ARM_L, UPPER_ARM_R, SLEEVE_L, SLEEVE_R,
    FOREARM_L, FOREARM_R, HAND_L, HAND_R,
    THIGH_L, THIGH_R, SHIN_L, SHIN_R, SHOE_L, SHOE_R
}

data class AvatarPiece(
    val id: String, val slot: CharacterLayerSlot, val boneId: String, val file: String,
    val pivotX: Float, val pivotY: Float, val widthUnits: Float, val heightUnits: Float,
    val zIndex: Int, val offsetX: Float, val offsetY: Float, val tintChannel: String?
)

class PieceLibrary private constructor(
    val selectedStyle: String,
    val manifestId: String,
    val parts: List<AvatarPiece>,
    val defaults: Map<CharacterLayerSlot, String>,
    private val bitmaps: Map<String, Bitmap>
) : AutoCloseable {
    fun bitmap(partId: String): Bitmap = bitmaps[partId] ?: error("Falta la imagen PNG: $partId")

    fun resolve(selection: Map<CharacterLayerSlot, String> = emptyMap()): List<AvatarPiece> {
        val chosen = defaults.toMutableMap()
        selection.forEach { (slot, id) ->
            require(parts.any { it.id == id && it.slot == slot }) { "La pieza $id no pertenece a $slot" }
            chosen[slot] = id
        }
        val byId = parts.associateBy { it.id }
        return chosen.values.map { id -> byId[id] ?: error("El manifiesto referencia una pieza inexistente: $id") }
            .sortedBy { it.zIndex }
    }

    fun requireCompatibleWith(reference: PieceLibrary) {
        require(parts.map { it.id }.toSet() == reference.parts.map { it.id }.toSet()) {
            "El estilo no contiene las mismas piezas que el estilo de referencia"
        }
        val referenceById = reference.parts.associateBy { it.id }
        parts.forEach { part ->
            val expected = referenceById.getValue(part.id)
            require(part.slot == expected.slot && part.boneId == expected.boneId &&
                part.pivotX == expected.pivotX && part.pivotY == expected.pivotY &&
                part.widthUnits == expected.widthUnits && part.heightUnits == expected.heightUnits &&
                part.zIndex == expected.zIndex && part.offsetX == expected.offsetX &&
                part.offsetY == expected.offsetY) {
                "El estilo cambia el contrato del rig en ${part.id}"
            }
        }
        require(defaults == reference.defaults) { "El estilo cambia las piezas predeterminadas" }
    }

    override fun close() {
        bitmaps.values.forEach { if (!it.isRecycled) it.recycle() }
    }

    companion object {
        private const val TAG = "StylePacks"
        private val SUPPORTED_BONES = setOf(
            "torso", "head", "armUL", "foreArmL", "armUR", "foreArmR",
            "thighL", "shinL", "thighR", "shinR"
        )

        fun availableStyles(context: Context): List<String> {
            val assets = context.applicationContext.assets
            return StylePackContract.discover(assets.list("styles").orEmpty()) { style ->
                runCatching {
                    assets.open(StylePackContract.manifestPath(style)).use { }
                }.isSuccess
            }
        }

        fun load(context: Context, selectedStyle: String = StylePackContract.DEFAULT_STYLE): PieceLibrary {
            val style = StylePackContract.requireStyleId(selectedStyle)
            val app = context.applicationContext
            val manifestPath = StylePackContract.manifestPath(style)
            val text = try {
                app.assets.open(manifestPath).bufferedReader(Charsets.UTF_8).use { it.readText() }
            } catch (failure: Exception) {
                throw IllegalStateException("No se pudo abrir el paquete de estilo $style: ${failure.message}", failure)
            }
            val root = JSONObject(text)
            val id = root.getString("id").also { require(it.isNotBlank()) }
            require(root.getInt("version") == 1) { "Versión de manifiesto no compatible" }
            val array = root.getJSONArray("parts")
            require(array.length() == 42) { "El paquete $style debe contener 42 piezas; contiene ${array.length()}" }
            val parts = (0 until array.length()).map { index ->
                val item = array.getJSONObject(index)
                val part = AvatarPiece(
                    id = item.getString("id"),
                    slot = CharacterLayerSlot.valueOf(item.getString("slot")),
                    boneId = item.getString("boneId"),
                    file = item.getString("file"),
                    pivotX = item.getDouble("pivotX").toFloat(),
                    pivotY = item.getDouble("pivotY").toFloat(),
                    widthUnits = item.getDouble("widthUnits").toFloat(),
                    heightUnits = item.getDouble("heightUnits").toFloat(),
                    zIndex = item.getInt("zIndex"),
                    offsetX = item.optDouble("offsetX", 0.0).toFloat(),
                    offsetY = item.optDouble("offsetY", 0.0).toFloat(),
                    tintChannel = item.optString("tintChannel").takeIf { it.isNotBlank() && it != "null" }
                )
                require(part.id.isNotBlank() && part.boneId in SUPPORTED_BONES) {
                    "Identificador o hueso no válido para ${part.id}"
                }
                require(part.pivotX.isFinite() && part.pivotX in 0f..1f &&
                    part.pivotY.isFinite() && part.pivotY in 0f..1f) {
                    "Pivote no normalizado para ${part.id}"
                }
                require(part.widthUnits.isFinite() && part.widthUnits > 0f &&
                    part.heightUnits.isFinite() && part.heightUnits > 0f) {
                    "Dimensiones no válidas para ${part.id}"
                }
                require(StylePackContract.isSafeCharacterPath(part.file)) {
                    "Ruta de imagen no segura para ${part.id}"
                }
                part
            }
            require(parts.map { it.id }.toSet().size == parts.size) { "Hay identificadores de pieza duplicados" }
            val defaultsJson = root.getJSONObject("defaults")
            val defaults = mutableMapOf<CharacterLayerSlot, String>()
            val keys = defaultsJson.keys()
            while (keys.hasNext()) {
                val key = keys.next()
                defaults[CharacterLayerSlot.valueOf(key)] = defaultsJson.getString(key)
            }
            val byId = parts.associateBy { it.id }
            defaults.forEach { (slot, partId) ->
                require(byId[partId]?.slot == slot) { "La pieza predeterminada $partId no coincide con $slot" }
            }
            require(defaults.isNotEmpty()) { "El manifiesto no contiene piezas predeterminadas" }

            val decoded = linkedMapOf<String, Bitmap>()
            try {
                parts.forEach { part ->
                    val assetPath = StylePackContract.characterAssetPath(style, part.file)
                    val bitmap = app.assets.open(assetPath).use { BitmapFactory.decodeStream(it) }
                        ?: error("No se pudo decodificar $assetPath")
                    require(bitmap.width > 0 && bitmap.height > 0 && bitmap.hasAlpha()) {
                        "La imagen debe tener dimensiones y transparencia: $assetPath"
                    }
                    decoded[part.id] = bitmap
                }
            } catch (failure: Exception) {
                decoded.values.forEach { if (!it.isRecycled) it.recycle() }
                Log.e(TAG, "No se pudo cargar el paquete completo $style", failure)
                throw IllegalStateException("No se pudo cargar el paquete completo $style: ${failure.message}", failure)
            }
            return PieceLibrary(style, id, parts, defaults, decoded)
        }
    }
}
