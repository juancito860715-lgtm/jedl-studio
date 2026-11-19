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
    val manifestId: String, val parts: List<AvatarPiece>,
    val defaults: Map<CharacterLayerSlot, String>, private val bitmaps: Map<String, Bitmap>
) {
    fun bitmap(partId: String): Bitmap =
        bitmaps[partId] ?: error("Required avatar PNG not loaded: $partId")

    fun resolve(selection: Map<CharacterLayerSlot, String> = emptyMap()): List<AvatarPiece> {
        val chosen = defaults.toMutableMap()
        selection.forEach { (slot, id) ->
            require(parts.any { it.id == id && it.slot == slot }) {
                "Part $id does not belong to slot $slot"
            }
            chosen[slot] = id
        }
        val byId = parts.associateBy { it.id }
        return chosen.values.map { id ->
            byId[id] ?: error("Manifest default references missing part: $id")
        }.sortedBy { it.zIndex }
    }

    companion object {
        private const val ASSET_ROOT = "characters/jedl_master_v1"
        private const val TAG = "Assets"
        private val SUPPORTED_BONES = setOf(
            "torso", "head", "armUL", "foreArmL", "armUR", "foreArmR",
            "thighL", "shinL", "thighR", "shinR"
        )

        fun load(context: Context): PieceLibrary {
            val app = context.applicationContext
            val manifestPath = "$ASSET_ROOT/manifest.json"
            val directoryEntries = app.assets.list(ASSET_ROOT)?.joinToString()
            Log.d(TAG, "Opening $manifestPath; directory entries=[$directoryEntries]")
            val text = try {
                app.assets.open(manifestPath).bufferedReader(Charsets.UTF_8).use { it.readText() }
            } catch (failure: Exception) {
                Log.e(TAG, "Failed opening $manifestPath", failure)
                throw IllegalStateException("No se pudo abrir $manifestPath: ${failure.message}", failure)
            }
            val root = JSONObject(text)
            val id = root.getString("id").also { require(it.isNotBlank()) }
            require(root.getInt("version") == 1) { "Unsupported avatar manifest version" }
            val array = root.getJSONArray("parts")
            require(array.length() == 42) {
                "Expected exactly 42 avatar parts, found ${array.length()}"
            }
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
                    "Invalid id or rig bone for ${part.id}"
                }
                require(part.pivotX.isFinite() && part.pivotX in 0f..1f &&
                    part.pivotY.isFinite() && part.pivotY in 0f..1f) {
                    "Non-normalized pivot for ${part.id}"
                }
                require(part.widthUnits.isFinite() && part.widthUnits > 0f &&
                    part.heightUnits.isFinite() && part.heightUnits > 0f) {
                    "Invalid dimensions for ${part.id}"
                }
                require(part.file.startsWith("png/") && part.file.endsWith(".png") &&
                    !part.file.contains("..")) { "Unsafe PNG path for ${part.id}" }
                part
            }
            require(parts.map { it.id }.toSet().size == parts.size) { "Duplicate avatar part id" }
            val defaultsJson = root.getJSONObject("defaults")
            val defaults = mutableMapOf<CharacterLayerSlot, String>()
            val keys = defaultsJson.keys()
            while (keys.hasNext()) {
                val key = keys.next()
                defaults[CharacterLayerSlot.valueOf(key)] = defaultsJson.getString(key)
            }
            val byId = parts.associateBy { it.id }
            defaults.forEach { (slot, partId) ->
                require(byId[partId]?.slot == slot) { "Default $partId does not match slot $slot" }
            }
            require(defaults.isNotEmpty()) { "Avatar manifest has no defaults" }

            val decoded = linkedMapOf<String, Bitmap>()
            try {
                parts.forEach { part ->
                    val pngPath = "$ASSET_ROOT/${part.file}"
                    Log.d(TAG, "Opening $pngPath")
                    val bitmap = app.assets.open(pngPath).use { BitmapFactory.decodeStream(it) }
                        ?: error("Cannot decode required PNG: $pngPath")
                    require(bitmap.width > 0 && bitmap.height > 0 && bitmap.hasAlpha()) {
                        "PNG must be non-empty and have alpha: $pngPath"
                    }
                    decoded[part.id] = bitmap
                }
            } catch (failure: Exception) {
                decoded.values.forEach { if (!it.isRecycled) it.recycle() }
                Log.e(TAG, "Failed loading avatar PNG bank", failure)
                throw IllegalStateException("Unable to load the complete 42-piece avatar bank: ${failure.message}", failure)
            }
            Log.d(TAG, "Loaded ${decoded.size} PNG assets for manifest $id")
            return PieceLibrary(id, parts, defaults, decoded)
        }
    }
}
