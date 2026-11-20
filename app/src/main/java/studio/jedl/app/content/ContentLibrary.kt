package studio.jedl.app.content

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import org.json.JSONObject

enum class ContentKind { CHARACTER_PART, OBJECT }

data class ContentAsset(
    val id: String,
    val title: String,
    val category: String,
    val kind: ContentKind,
    val bankId: String,
    val assetPath: String,
    val width: Int,
    val height: Int
)

data class ContentBank(
    val id: String,
    val title: String,
    val license: String,
    val source: String,
    val kind: ContentKind,
    val assets: List<ContentAsset>
)

data class CharacterPreset(
    val id: String,
    val title: String,
    val description: String,
    val selectedParts: Map<String, String>
)

class ContentLibrary private constructor(
    val banks: List<ContentBank>,
    val presets: List<CharacterPreset>,
    private val context: Context
) {
    val characters: List<ContentAsset> get() = banks.filter { it.kind == ContentKind.CHARACTER_PART }.flatMap { it.assets }
    val objects: List<ContentAsset> get() = banks.filter { it.kind == ContentKind.OBJECT }.flatMap { it.assets }
    private val cache = LinkedHashMap<String, Bitmap>(24, 0.75f, true)
    private val assetIndex: Map<String, ContentAsset> = banks.flatMap { it.assets }.associateBy { it.id }

    fun bitmap(asset: ContentAsset): Bitmap = loadBitmap(asset, 512)
    fun thumbnail(asset: ContentAsset): Bitmap = loadBitmap(asset, 72)

    private fun loadBitmap(asset: ContentAsset, maxDimension: Int): Bitmap = synchronized(cache) {
        val cacheKey = asset.id + "@" + maxDimension
        cache[cacheKey]?.let { return@synchronized it }
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        context.assets.open(asset.assetPath).use { BitmapFactory.decodeStream(it, null, bounds) }
        require(bounds.outWidth > 0 && bounds.outHeight > 0) { "Imagen inválida: " + asset.assetPath }
        var sample = 1
        while (maxOf(bounds.outWidth, bounds.outHeight) / sample > maxDimension) sample *= 2
        val options = BitmapFactory.Options().apply { inSampleSize = sample }
        val decoded = context.assets.open(asset.assetPath).use { BitmapFactory.decodeStream(it, null, options) }
            ?: error("No se pudo decodificar " + asset.assetPath)
        if (cache.size >= 64) {
            val iterator = cache.entries.iterator()
            if (iterator.hasNext()) iterator.next().also { iterator.remove() }
        }
        cache[cacheKey] = decoded
        decoded
    }

    fun find(assetId: String): ContentAsset? = assetIndex[assetId]

    fun close() = synchronized(cache) {
        cache.values.forEach { if (!it.isRecycled) it.recycle() }
        cache.clear()
    }

    companion object {
        fun load(context: Context): ContentLibrary {
            val app = context.applicationContext
            val roots = mutableListOf<String>()
            fun visit(path: String, depth: Int) {
                require(depth <= 4) { "Estructura de bibliotecas demasiado profunda" }
                val children = app.assets.list(path).orEmpty()
                if ("manifest.json" in children) roots += path
                else children.filter { child ->
                    app.assets.list("$path/$child").orEmpty().isNotEmpty()
                }.forEach { child -> visit("$path/$child", depth + 1) }
            }
            if (app.assets.list("content").orEmpty().isNotEmpty()) visit("content", 0)
            val banks = roots.distinct().map { root ->
                val json = app.assets.open("$root/manifest.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
                val id = json.getString("id")
                val kind = if (root.contains("/characters/")) ContentKind.CHARACTER_PART else ContentKind.OBJECT
                require(json.getString("license") == "CC0-1.0") { "Licencia no admitida para " + id }
                require(json.optBoolean("commercialUse") && json.optBoolean("apkRedistributionAllowed")) {
                    "Permisos de redistribución insuficientes para " + id
                }
                val array = json.getJSONArray("assets")
                val assets = (0 until array.length()).mapNotNull { index ->
                    val item = array.getJSONObject(index)
                    val sourceFile = item.optString("sourceFile", item.getString("file"))
                    val lowerName = sourceFile.substringAfterLast('/').lowercase()
                    if (lowerName.contains("preview") || lowerName.contains("sample") || lowerName.contains("instruction")) {
                        return@mapNotNull null
                    }
                    if (kind == ContentKind.CHARACTER_PART &&
                        !(sourceFile.startsWith("PNG/") || sourceFile.startsWith("Spritesheet/"))) {
                        return@mapNotNull null
                    }
                    val category = if (kind == ContentKind.CHARACTER_PART) {
                        sourceFile.split('/').getOrNull(1) ?: "General"
                    } else {
                        sourceFile.substringBefore('/').takeIf { it != sourceFile } ?: "General"
                    }
                    val file = item.getString("file")
                    require(file.startsWith("png/") && !file.contains("..") && !file.startsWith("/")) {
                        "Ruta insegura en " + id + ": " + file
                    }
                    val path = "$root/$file"
                    app.assets.open(path).use { input ->
                        val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                        BitmapFactory.decodeStream(input, null, options)
                        require(options.outWidth > 0 && options.outHeight > 0) { "PNG inexistente: " + path }
                    }
                    ContentAsset(
                        id = id + ":" + item.getString("id"),
                        title = sourceFile.substringAfterLast('/').substringBeforeLast('.').replace('_', ' '),
                        category = category,
                        kind = kind,
                        bankId = id,
                        assetPath = path,
                        width = item.getInt("width"),
                        height = item.getInt("height")
                    )
                }
                require(assets.isNotEmpty()) { "Banco vacío: " + id }
                require(assets.map { it.id }.distinct().size == assets.size) { "IDs duplicados en " + id }
                ContentBank(id, json.getString("title"), json.getString("license"), json.getString("source"), kind, assets)
            }
            require(banks.any { it.kind == ContentKind.CHARACTER_PART }) { "No se encontró el banco de piezas de personajes" }
            require(banks.any { it.kind == ContentKind.OBJECT }) { "No se encontró el banco de objetos" }
            val presetFile = app.assets.open("content/character_presets.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
            require(presetFile.getString("rigId") == "jedl_humanoid_v1") { "Rig incompatible en presets de personaje" }
            val presetArray = presetFile.getJSONArray("presets")
            val presets = (0 until presetArray.length()).map { index ->
                val item = presetArray.getJSONObject(index)
                val selected = item.getJSONObject("selectedParts")
                val selectedParts = selected.keys().asSequence().associateWith { selected.getString(it) }
                require(selectedParts.isNotEmpty()) { "Preset de personaje sin piezas: " + item.getString("id") }
                CharacterPreset(item.getString("id"), item.getString("title"),
                    item.optString("description"), selectedParts)
            }
            require(presets.isNotEmpty() && presets.map { it.id }.distinct().size == presets.size) {
                "Banco de presets vacío o con identificadores duplicados"
            }
            return ContentLibrary(banks, presets, app)
        }
    }
}
