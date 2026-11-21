package studio.jedl.app.content

import org.json.JSONObject
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.security.MessageDigest
import java.util.zip.ZipEntry
import java.util.zip.ZipFile

data class InstalledAssetPackage(
    val id: String,
    val version: String,
    val directory: File,
    val fileCount: Int,
    val sha256: String
)

/** Installs a signed-by-content (manifest + per-file SHA-256) CC0 package atomically. */
object AssetPackageInstaller {
    private const val MAX_FILES = 50_000
    private const val MAX_EXPANDED_BYTES = 1_073_741_824L
    private const val MAX_PACKAGE_BYTES = 536_870_912L
    private const val COMMUNITY_ARCHIVE = "community-2d.zip"

    fun install(packageZip: File, filesDir: File): InstalledAssetPackage {
        require(packageZip.isFile && packageZip.length() in 1..MAX_PACKAGE_BYTES) {
            "El ZIP no existe o supera el límite permitido"
        }
        val packageDigest = sha256(packageZip)
        val stagingRoot = File(filesDir, "installed-libraries")
        check(stagingRoot.exists() || stagingRoot.mkdirs()) { "No se pudo crear el directorio de bibliotecas" }
        ZipFile(packageZip).use { zip ->
            val manifestEntry = zip.getEntry("JEDL-PACKAGE.json")
                ?: throw IllegalArgumentException("Falta JEDL-PACKAGE.json en la raíz")
            val manifest = zip.getInputStream(manifestEntry).bufferedReader(Charsets.UTF_8).use {
                JSONObject(it.readText())
            }
            require(manifest.optInt("schemaVersion") == 1) { "Versión de manifiesto no compatible" }
            val id = manifest.getString("id")
            val version = manifest.getString("packageVersion")
            require(id.matches(Regex("[a-z0-9][a-z0-9._-]{1,63}"))) { "Identificador de paquete inválido" }
            require(version.isNotBlank() && version.length <= 40) { "Versión de paquete inválida" }
            require(manifest.getString("license") == "CC0-1.0" &&
                manifest.optBoolean("commercialUse") &&
                manifest.optBoolean("modificationAllowed") &&
                manifest.optBoolean("redistributionAllowed")) {
                "El paquete no acredita permisos CC0 completos para redistribución"
            }
            val evidence = manifest.optJSONArray("licenseEvidence")
            require(evidence != null && evidence.length() > 0) { "Falta evidencia de licencia" }

            val records = manifest.getJSONArray("files")
            require(records.length() in 1..MAX_FILES) { "Cantidad de archivos no permitida" }
            val expected = LinkedHashMap<String, Pair<String, Long>>()
            var totalBytes = 0L
            for (i in 0 until records.length()) {
                val item = records.getJSONObject(i)
                val path = safePath(item.getString("path"))
                val digest = item.getString("sha256").lowercase()
                val size = item.getLong("bytes")
                require(digest.matches(Regex("[a-f0-9]{64}")) && size >= 0L) { "Registro de hash/tamaño inválido: $path" }
                require(expected.put(path, digest to size) == null) { "Ruta duplicada en manifiesto: $path" }
                totalBytes += size
                require(totalBytes <= MAX_EXPANDED_BYTES) { "El paquete supera el tamaño expandido permitido" }
            }

            val zipFiles = LinkedHashSet<String>()
            val entries = zip.entries()
            var entryCount = 0
            while (entries.hasMoreElements()) {
                val entry = entries.nextElement()
                entryCount++
                require(entryCount <= MAX_FILES + 2) { "Demasiadas entradas ZIP" }
                if (entry.isDirectory) {
                    safePath(entry.name.removeSuffix("/"))
                } else {
                    zipFiles += safePath(entry.name)
                }
            }
            require(zipFiles.size == expected.size + 1 &&
                zipFiles.contains("JEDL-PACKAGE.json") &&
                zipFiles - "JEDL-PACKAGE.json" == expected.keys) {
                "El contenido ZIP no coincide con el inventario del manifiesto"
            }

            val target = File(stagingRoot, id)
            val staging = File(stagingRoot, ".$id.installing")
            deleteRecursively(staging)
            check(staging.mkdirs()) { "No se pudo crear el área temporal de instalación" }
            try {
                for ((path, proof) in expected) {
                    val entry = zip.getEntry(path) ?: error("Falta el archivo $path")
                    require(entry.size == proof.second) { "Tamaño incorrecto: $path" }
                    val output = destination(staging, path)
                    output.parentFile?.let { check(it.exists() || it.mkdirs()) }
                    val digest = MessageDigest.getInstance("SHA-256")
                    var count = 0L
                    zip.getInputStream(entry).use { input ->
                        FileOutputStream(output).use { out ->
                            val buffer = ByteArray(32 * 1024)
                            while (true) {
                                val read = input.read(buffer)
                                if (read < 0) break
                                count += read
                                require(count <= proof.second) { "El archivo excede el tamaño declarado: $path" }
                                digest.update(buffer, 0, read)
                                out.write(buffer, 0, read)
                            }
                            out.fd.sync()
                        }
                    }
                    require(count == proof.second && hex(digest.digest()) == proof.first) {
                        "SHA-256 incorrecto: $path"
                    }
                }
                File(staging, "JEDL-PACKAGE.json").writeText(manifest.toString(), Charsets.UTF_8)
                val community = File(staging, COMMUNITY_ARCHIVE)
                if (community.isFile) extractCommunity(community, File(staging, "community-2d"))
                val backup = File(stagingRoot, ".$id.previous")
                deleteRecursively(backup)
                if (target.exists()) check(target.renameTo(backup)) { "No se pudo respaldar la biblioteca anterior" }
                if (!staging.renameTo(target)) {
                    if (backup.exists()) backup.renameTo(target)
                    error("No se pudo activar la biblioteca instalada")
                }
                deleteRecursively(backup)
                return InstalledAssetPackage(id, version, target, expected.size, packageDigest)
            } catch (failure: Throwable) {
                deleteRecursively(staging)
                val backup = File(stagingRoot, ".$id.previous")
                if (!target.exists() && backup.exists()) backup.renameTo(target)
                throw failure
            }
        }
    }

    private fun extractCommunity(archive: File, outputRoot: File) {
        ZipFile(archive).use { zip ->
            val manifestEntry = zip.getEntry("JEDL-PACKAGE.json")
                ?: throw IllegalArgumentException("El subpaquete comunitario no contiene manifiesto")
            val manifest = zip.getInputStream(manifestEntry).bufferedReader(Charsets.UTF_8).use { JSONObject(it.readText()) }
            require(manifest.optInt("schemaVersion") == 1 && manifest.getString("license") == "CC0-1.0") {
                "Licencia o versión no válida en el subpaquete comunitario"
            }
            val files = manifest.getJSONArray("files")
            require(files.length() <= MAX_FILES) { "Demasiados recursos comunitarios" }
            val declaredPaths = LinkedHashSet<String>()
            for (i in 0 until files.length()) declaredPaths += safePath(files.getJSONObject(i).getString("path"))
            val archivePaths = LinkedHashSet<String>()
            val allEntries = zip.entries()
            while (allEntries.hasMoreElements()) {
                val entry = allEntries.nextElement()
                if (!entry.isDirectory) archivePaths += safePath(entry.name)
            }
            require(archivePaths == declaredPaths + "JEDL-PACKAGE.json") {
                "El inventario comunitario no coincide con las entradas ZIP"
            }
            val packs = manifest.getJSONArray("packs")
            for (i in 0 until packs.length()) {
                val pack = packs.getJSONObject(i)
                val licenseStatement = pack.optString("sourceLicenseStatement", "")
                val sourceUrl = pack.optString("sourceUrl", "")
                val evidenceFile = safePath(pack.optString("sourceEvidenceFile", ""))
                require(licenseStatement.contains("CC0", ignoreCase = true) &&
                    sourceUrl.startsWith("https://") && evidenceFile in declaredPaths) {
                    "Evidencia CC0 incompleta para el banco comunitario " + pack.optString("pack")
                }
            }
            var expanded = 0L
            for (i in 0 until files.length()) {
                val item = files.getJSONObject(i)
                val path = safePath(item.getString("path"))
                val expectedHash = item.getString("sha256").lowercase()
                require(expectedHash.matches(Regex("[a-f0-9]{64}"))) { "Hash inválido: $path" }
                val entry = zip.getEntry(path) ?: error("Falta recurso comunitario: $path")
                require(!entry.isDirectory && entry.size == item.getLong("bytes")) { "Tamaño incorrecto: $path" }
                expanded += entry.size
                require(expanded <= MAX_EXPANDED_BYTES) { "Subpaquete comunitario demasiado grande" }
                val output = destination(outputRoot, path)
                output.parentFile?.let { check(it.exists() || it.mkdirs()) }
                val digest = MessageDigest.getInstance("SHA-256")
                var copied = 0L
                zip.getInputStream(entry).use { input ->
                    FileOutputStream(output).use { out ->
                        val buffer = ByteArray(32 * 1024)
                        while (true) {
                            val n = input.read(buffer)
                            if (n < 0) break
                            copied += n
                            require(copied <= entry.size) { "El recurso excede su tamaño declarado: " + path }
                            digest.update(buffer, 0, n)
                            out.write(buffer, 0, n)
                        }
                        out.fd.sync()
                    }
                }
                require(copied == entry.size && hex(digest.digest()) == expectedHash) { "SHA-256 comunitario incorrecto: $path" }
            }
            File(outputRoot, "JEDL-PACKAGE.json").writeText(manifest.toString(), Charsets.UTF_8)
        }
    }

    private fun safePath(raw: String): String {
        require(raw.isNotBlank() && !raw.startsWith("/") && !raw.contains('\\') && !raw.contains(':')) {
            "Ruta ZIP no permitida: $raw"
        }
        val parts = raw.split('/')
        require(parts.all { it.isNotEmpty() && it != "." && it != ".." }) { "Ruta ZIP no permitida: $raw" }
        return parts.joinToString("/")
    }

    private fun destination(root: File, relative: String): File {
        val safe = safePath(relative)
        val target = File(root, safe)
        val rootPath = root.canonicalPath + File.separator
        require(target.canonicalPath.startsWith(rootPath)) { "Ruta fuera del directorio de instalación" }
        return target
    }

    private fun sha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        FileInputStream(file).use { input ->
            val buffer = ByteArray(32 * 1024)
            while (true) {
                val n = input.read(buffer)
                if (n < 0) break
                digest.update(buffer, 0, n)
            }
        }
        return hex(digest.digest())
    }

    private fun hex(bytes: ByteArray) = bytes.joinToString("") { "%02x".format(it) }

    private fun deleteRecursively(file: File) {
        if (file.isDirectory) file.listFiles()?.forEach(::deleteRecursively)
        file.delete()
    }
}
