package studio.jedl.app.content

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import org.json.JSONObject
import java.io.File
import java.io.FileInputStream
import java.security.MessageDigest

enum class ContentKind { CHARACTER_PART, OBJECT }

data class ContentAsset(
    val id: String, val title: String, val category: String, val kind: ContentKind,
    val bankId: String, val assetPath: String, val width: Int, val height: Int,
    val sha256: String = "", val packageVersion: String = "", val installed: Boolean = false
)
data class ContentBank(
    val id: String, val title: String, val license: String, val source: String,
    val kind: ContentKind, val assets: List<ContentAsset>,
    val packageVersion: String = "", val installed: Boolean = false
)
data class CharacterPreset(val id: String, val title: String, val description: String, val selectedParts: Map<String, String>)

class ContentLibrary private constructor(
    val banks: List<ContentBank>, val presets: List<CharacterPreset>, private val context: Context
) {
    val characters: List<ContentAsset> get() = banks.filter { it.kind == ContentKind.CHARACTER_PART }.flatMap { it.assets }
    val objects: List<ContentAsset> get() = banks.filter { it.kind == ContentKind.OBJECT }.flatMap { it.assets }
    private val cache = LinkedHashMap<String, Bitmap>(24, 0.75f, true)
    private val verificationCache = HashMap<String, Boolean>()
    private val assetIndex: Map<String, ContentAsset> = banks.flatMap { it.assets }.associateBy { it.id }

    fun bitmap(asset: ContentAsset): Bitmap = loadBitmap(asset, 512)
    fun thumbnail(asset: ContentAsset): Bitmap = loadBitmap(asset, 72)
    private fun openAsset(asset: ContentAsset) =
        if (asset.installed) FileInputStream(File(asset.assetPath)) else context.assets.open(asset.assetPath)

    private fun loadBitmap(asset: ContentAsset, maxDimension: Int): Bitmap = synchronized(cache) {
        val cacheKey = asset.id + "@" + maxDimension
        cache[cacheKey]?.let { return@synchronized it }
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        openAsset(asset).use { BitmapFactory.decodeStream(it, null, bounds) }
        require(bounds.outWidth > 0 && bounds.outHeight > 0) { "Imagen inválida: " + asset.assetPath }
        var sample = 1
        while (maxOf(bounds.outWidth, bounds.outHeight) / sample > maxDimension) sample *= 2
        val options = BitmapFactory.Options().apply { inSampleSize = sample }
        val decoded = openAsset(asset).use { BitmapFactory.decodeStream(it, null, options) }
            ?: error("No se pudo decodificar " + asset.assetPath)
        if (cache.size >= 64) {
            val iterator = cache.entries.iterator()
            if (iterator.hasNext()) iterator.next().also { it.value.recycle(); iterator.remove() }
        }
        cache[cacheKey] = decoded
        decoded
    }

    fun find(assetId: String): ContentAsset? = assetIndex[assetId]

    /** Resolves the exact saved resource revision and verifies installed bytes once per app session. */
    fun resolve(reference: studio.jedl.app.SceneObjectInstance): ContentAsset? {
        val asset = assetIndex[reference.assetId] ?: return null
        if (!AssetReferenceValidator.matches(reference, asset)) return null
        if (asset.installed) {
            val valid = verificationCache.getOrPut(asset.id) {
                val file = File(asset.assetPath)
                file.isFile && asset.sha256.matches(Regex("[a-fA-F0-9]{64}")) &&
                    sha256(file).equals(asset.sha256, true)
            }
            if (!valid) return null
        }
        return asset
    }

    fun close() = synchronized(cache) {
        cache.values.forEach { if (!it.isRecycled) it.recycle() }
        cache.clear()
        verificationCache.clear()
    }

    companion object {
        fun load(context: Context): ContentLibrary {
            val app = context.applicationContext
            val roots = mutableListOf<String>()
            fun visit(path: String, depth: Int) {
                require(depth <= 4) { "Estructura de bibliotecas demasiado profunda" }
                val children = app.assets.list(path).orEmpty()
                if ("manifest.json" in children) roots += path
                else children.filter { child -> app.assets.list(path + "/" + child).orEmpty().isNotEmpty() }
                    .forEach { child -> visit(path + "/" + child, depth + 1) }
            }
            if (app.assets.list("content").orEmpty().isNotEmpty()) visit("content", 0)
            val banks = roots.distinct().map { root ->
                val json = app.assets.open(root + "/manifest.json").bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
                val id = json.getString("id")
                val kind = if (root.contains("/characters/")) ContentKind.CHARACTER_PART else ContentKind.OBJECT
                require(json.getString("license") == "CC0-1.0") { "Licencia no admitida para " + id }
                require(json.optBoolean("commercialUse") &&
                    (json.optBoolean("apkRedistributionAllowed") || json.optBoolean("redistributionAllowed"))) {
                    "Permisos de redistribución insuficientes para " + id
                }
                val array = json.getJSONArray("assets")
                val assets = (0 until array.length()).mapNotNull { index ->
                    val item = array.getJSONObject(index)
                    val sourceFile = item.optString("sourceFile", item.getString("file"))
                    val lowerName = sourceFile.substringAfterLast('/').lowercase()
                    if (lowerName.contains("preview") || lowerName.contains("sample") || lowerName.contains("instruction")) return@mapNotNull null
                    if (kind == ContentKind.CHARACTER_PART && !sourceFile.startsWith("PNG/")) return@mapNotNull null
                    val category = if (kind == ContentKind.CHARACTER_PART) {
                        val folder = sourceFile.split('/').getOrNull(1) ?: "General"
                        if (folder.lowercase() !in SAFE_CHARACTER_FOLDERS) return@mapNotNull null
                        folder
                    } else {
                        val parts = sourceFile.split('/')
                        if (parts.firstOrNull() == "PNG") parts.getOrNull(1) ?: "General"
                        else parts.firstOrNull() ?: "General"
                    }
                    val file = item.getString("file")
                    require(file.startsWith("png/") && !file.contains("..") && !file.startsWith("/")) {
                        "Ruta insegura en " + id + ": " + file
                    }
                    val path = root + "/" + file
                    app.assets.open(path).use { input ->
                        val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                        BitmapFactory.decodeStream(input, null, options)
                        require(options.outWidth > 0 && options.outHeight > 0) { "PNG inexistente: " + path }
                    }
                    ContentAsset(id + ":" + item.getString("id"),
                        sourceFile.substringAfterLast('/').substringBeforeLast('.').replace('_', ' '),
                        category, kind, id, path, item.getInt("width"), item.getInt("height"),
                        item.optString("sha256", ""))
                }
                require(assets.isNotEmpty()) { "Banco vacío: " + id }
                require(assets.map { it.id }.distinct().size == assets.size) { "IDs duplicados en " + id }
                ContentBank(id, json.getString("title"), json.getString("license"), json.getString("source"), kind, assets)
            }.toMutableList()

            val embeddedBankIds = banks.map { it.id }.toSet()
            banks += loadInstalledBanks(app).filterNot { it.id in embeddedBankIds }
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
                CharacterPreset(item.getString("id"), item.getString("title"), item.optString("description"), selectedParts)
            }
            require(presets.isNotEmpty() && presets.map { it.id }.distinct().size == presets.size) {
                "Banco de presets vacío o con identificadores duplicados"
            }
            return ContentLibrary(banks, presets, app)
        }

        private val SAFE_CHARACTER_FOLDERS = setOf(
            "face", "skin", "body", "clothing", "clothes", "outfit", "outfits",
            "hair", "hat", "hats", "shirt", "shirts", "pants", "shoes",
            "eyebrows", "eyes", "mouth", "nose", "sleeves", "arms", "legs", "hands"
        )

        private fun loadInstalledBanks(context: Context): List<ContentBank> {
            val installedRoot = File(context.filesDir, "installed-libraries")
            return installedRoot.listFiles()?.filter { it.isDirectory }?.flatMap { packageDir ->
                val rootManifest = File(packageDir, "JEDL-PACKAGE.json")
                if (!rootManifest.isFile) return@flatMap emptyList()
                val packageJson = JSONObject(rootManifest.readText(Charsets.UTF_8))
                val packageVersion = packageJson.getString("packageVersion")
                val communityManifest = File(packageDir, "community-2d/JEDL-PACKAGE.json")
                val communityBanks = if (communityManifest.isFile) {
                    val community = JSONObject(communityManifest.readText(Charsets.UTF_8))
                    require(community.getString("license") == "CC0-1.0") { "Licencia comunitaria no admitida" }
                    val records = community.getJSONArray("files")
                    val packs = community.getJSONArray("packs")
                    for (packIndex in 0 until packs.length()) {
                        val pack = packs.getJSONObject(packIndex)
                        val evidencePath = pack.optString("sourceEvidenceFile", "")
                        require(pack.optString("sourceLicenseStatement", "").contains("CC0", true) &&
                            pack.optString("sourceUrl", "").startsWith("https://") &&
                            evidencePath.isNotBlank() && !evidencePath.startsWith("/") &&
                            !evidencePath.contains("..") && evidencePath.indexOf(92.toChar()) < 0 &&
                            File(packageDir, "community-2d/" + evidencePath).isFile) {
                            "Evidencia CC0 incompleta para un banco comunitario"
                        }
                    }
                    (0 until packs.length()).mapNotNull { packIndex ->
                        val pack = packs.getJSONObject(packIndex)
                        val packId = pack.getString("pack")
                        val category = pack.optString("category", "General")
                        val bankId = packageJson.getString("id") + ":" + packId
                        val assets = (0 until records.length()).mapNotNull { fileIndex ->
                            val record = records.getJSONObject(fileIndex)
                            if (record.optString("pack") != packId) return@mapNotNull null
                            val relative = record.getString("path")
                            if (!relative.lowercase().endsWith(".png") || relative.startsWith("/") ||
                                relative.contains("..") || relative.indexOf(92.toChar()) >= 0) return@mapNotNull null
                            val file = File(packageDir, "community-2d/" + relative)
                            val digest = record.getString("sha256")
                            if (!file.isFile || !digest.matches(Regex("[a-fA-F0-9]{64}"))) return@mapNotNull null
                            val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                            FileInputStream(file).use { BitmapFactory.decodeStream(it, null, options) }
                            if (options.outWidth <= 0 || options.outHeight <= 0) return@mapNotNull null
                            val id = bankId + ":" + digest.take(16)
                            ContentAsset(id, file.nameWithoutExtension.replace('_', ' '), category,
                                ContentKind.OBJECT, bankId, file.absolutePath, options.outWidth, options.outHeight,
                                digest, packageVersion, installed = true)
                        }
                        if (assets.isEmpty()) null else ContentBank(bankId,
                            packId.replace('-', ' ').replaceFirstChar { it.uppercase() },
                            "CC0-1.0", pack.optString("sourceUrl"),
                            ContentKind.OBJECT, assets, packageVersion, installed = true)
                    }
                } else emptyList()
                communityBanks + loadInstalledManifestBanks(packageDir, packageVersion)
            }.orEmpty()
        }

        private fun loadInstalledManifestBanks(packageDir: File, packageVersion: String): List<ContentBank> {
            val banksRoot = File(packageDir, "banks")
            if (!banksRoot.isDirectory) return emptyList()
            return banksRoot.walkTopDown().maxDepth(5).filter { it.isFile && it.name == "manifest.json" }
                .mapNotNull { manifestFile ->
                    val manifest = runCatching { JSONObject(manifestFile.readText(Charsets.UTF_8)) }.getOrNull()
                        ?: return@mapNotNull null
                    val records = manifest.optJSONArray("assets") ?: return@mapNotNull null
                    if (manifest.optString("license") != "CC0-1.0" ||
                        !manifest.optBoolean("commercialUse") ||
                        !(manifest.optBoolean("apkRedistributionAllowed") || manifest.optBoolean("redistributionAllowed"))) {
                        return@mapNotNull null
                    }
                    val bankId = manifest.optString("id")
                    if (bankId.isBlank()) return@mapNotNull null
                    val bankRoot = manifestFile.parentFile ?: return@mapNotNull null
                    if (!manifest.optString("source").startsWith("https://") ||
                        !manifest.optString("licenseTerms").startsWith("https://creativecommons.org/publicdomain/zero/1.0/") ||
                        !File(bankRoot, "LICENSE.txt").isFile || !File(bankRoot, "SOURCE.json").isFile) {
                        return@mapNotNull null
                    }
                    val assets = (0 until records.length()).mapNotNull { index ->
                        val item = records.getJSONObject(index)
                        val relative = item.optString("file", "")
                        if (!relative.startsWith("png/") || !relative.lowercase().endsWith(".png") ||
                            relative.contains("..") || relative.startsWith("/") || relative.indexOf(92.toChar()) >= 0) {
                            return@mapNotNull null
                        }
                        val file = File(bankRoot, relative)
                        val digest = item.optString("sha256", "")
                        if (!file.isFile || !digest.matches(Regex("[a-fA-F0-9]{64}"))) return@mapNotNull null
                        val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                        FileInputStream(file).use { BitmapFactory.decodeStream(it, null, options) }
                        if (options.outWidth <= 0 || options.outHeight <= 0) return@mapNotNull null
                        val sourceFile = item.optString("sourceFile", relative.removePrefix("png/"))
                        val category = item.optString("category", sourceFile.split('/').getOrNull(1) ?: sourceFile.substringBefore('/'))
                        ContentAsset(bankId + ":" + item.getString("id"),
                            item.optString("title", file.nameWithoutExtension.replace('_', ' ')),
                            category, ContentKind.OBJECT, bankId, file.absolutePath,
                            options.outWidth, options.outHeight, digest, packageVersion, installed = true)
                    }
                    if (assets.isEmpty()) null else ContentBank(bankId,
                        manifest.optString("title", bankId), "CC0-1.0", manifest.optString("source"),
                        ContentKind.OBJECT, assets, packageVersion, installed = true)
                }.toList()
        }

        private fun sha256(file: File): String {
            val digest = MessageDigest.getInstance("SHA-256")
            FileInputStream(file).use { input ->
                val buffer = ByteArray(16 * 1024)
                while (true) {
                    val n = input.read(buffer)
                    if (n < 0) break
                    digest.update(buffer, 0, n)
                }
            }
            return digest.digest().joinToString("") { "%02x".format(it) }
        }
    }
}
