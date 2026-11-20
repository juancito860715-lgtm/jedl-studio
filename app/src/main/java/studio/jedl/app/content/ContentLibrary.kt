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

class ContentLibrary private constructor(
    val banks: List<ContentBank>,
    private val context: Context
) {
    val characters: List<ContentAsset> get() = banks.filter { it.kind == ContentKind.CHARACTER_PART }.flatMap { it.assets }
    val objects: List<ContentAsset> get() = banks.filter { it.kind == ContentKind.OBJECT }.flatMap { it.assets }

    fun bitmap(asset: ContentAsset): Bitmap {
        val decoded = context.assets.open(asset.assetPath).use { BitmapFactory.decodeStream(it) }
            ?: error("No se pudo decodificar " + asset.assetPath)
        require(decoded.width > 0 && decoded.height > 0 && decoded.hasAlpha()) {
            "Imagen inválida o sin transparencia: " + asset.assetPath
        }
        return decoded
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
                val assets = (0 until array.length()).map { index ->
                    val item = array.getJSONObject(index)
                    val sourceFile = item.optString("sourceFile", item.getString("file"))
                    val category = sourceFile.substringBefore('/').takeIf { it != sourceFile } ?: "General"
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
            return ContentLibrary(banks, app)
        }
    }
}
