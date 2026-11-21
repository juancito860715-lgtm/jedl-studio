package studio.jedl.app.content

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.io.File
import java.security.MessageDigest
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class AssetPackageInstallerTest {
    private fun sha(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes)
        .joinToString("") { "%02x".format(it) }

    private fun packageZip(root: File, path: String = "asset.png", license: String = "CC0-1.0") : File {
        val payload = byteArrayOf(1, 2, 3, 4)
        val manifest = JSONObject().put("schemaVersion", 1).put("id", "test-library")
            .put("packageVersion", "1.0.0").put("license", license)
            .put("commercialUse", true).put("modificationAllowed", true).put("redistributionAllowed", true)
            .put("licenseEvidence", JSONArray().put("https://creativecommons.org/publicdomain/zero/1.0/"))
            .put("bankCount", 0).put("banks", JSONArray())
            .put("files", JSONArray().put(JSONObject().put("path", path).put("bytes", payload.size)
                .put("sha256", sha(payload))))
        val file = File(root, "test.zip")
        ZipOutputStream(file.outputStream()).use { zip ->
            zip.putNextEntry(ZipEntry("JEDL-PACKAGE.json")); zip.write(manifest.toString().toByteArray()); zip.closeEntry()
            zip.putNextEntry(ZipEntry(path)); zip.write(payload); zip.closeEntry()
        }
        return file
    }

    private fun packageWithBank(root: File, redistribution: Boolean = true, corruptBankHash: Boolean = false): File {
        val bankRoot = File(root, "banks/test-instruments")
        val png = byteArrayOf(9, 8, 7, 6)
        val assetFile = File(bankRoot, "png/Instruments/timbales.png")
        assetFile.parentFile!!.mkdirs()
        assetFile.writeBytes(png)
        val source = "https://github.com/juancito860715-lgtm/jedl-studio"
        File(bankRoot, "LICENSE.txt").writeText("CC0-1.0")
        File(bankRoot, "SOURCE.json").writeText(JSONObject().put("source", source).put("license", "CC0-1.0").toString())
        val bankManifest = JSONObject().put("schemaVersion", 1).put("id", "test-instruments")
            .put("title", "Test instruments").put("source", source).put("license", "CC0-1.0")
            .put("licenseTerms", "https://creativecommons.org/publicdomain/zero/1.0/")
            .put("commercialUse", true).put("modificationAllowed", true)
            .put("apkRedistributionAllowed", redistribution).put("assetCount", 1)
            .put("assets", JSONArray().put(JSONObject().put("id", "timbales")
                .put("file", "png/Instruments/timbales.png").put("sourceFile", "PNG/Instruments/timbales.png")
                .put("category", "Instruments").put("width", 128).put("height", 128)
                .put("sha256", if (corruptBankHash) "b".repeat(64) else sha(png))))
        File(bankRoot, "manifest.json").writeText(bankManifest.toString())
        val payloadFiles = listOf(
            File(bankRoot, "manifest.json"), File(bankRoot, "LICENSE.txt"),
            File(bankRoot, "SOURCE.json"), assetFile
        )
        val records = JSONArray()
        payloadFiles.forEach { file ->
            records.put(JSONObject().put("path", file.relativeTo(root).invariantSeparatorsPath)
                .put("bytes", file.length()).put("sha256", sha(file.readBytes())))
        }
        val manifest = JSONObject().put("schemaVersion", 1).put("id", "test-library")
            .put("packageVersion", "1.0.0").put("license", "CC0-1.0")
            .put("commercialUse", true).put("modificationAllowed", true).put("redistributionAllowed", true)
            .put("licenseEvidence", JSONArray().put("https://creativecommons.org/publicdomain/zero/1.0/"))
            .put("bankCount", 1).put("banks", JSONArray().put(JSONObject().put("id", "test-instruments").put("assetCount", 1)))
            .put("files", records)
        val file = File(root, "with-bank.zip")
        ZipOutputStream(file.outputStream()).use { zip ->
            zip.putNextEntry(ZipEntry("JEDL-PACKAGE.json")); zip.write(manifest.toString().toByteArray()); zip.closeEntry()
            payloadFiles.forEach { payload ->
                val name = payload.relativeTo(root).invariantSeparatorsPath
                zip.putNextEntry(ZipEntry(name)); zip.write(payload.readBytes()); zip.closeEntry()
            }
        }
        return file
    }

    @Test fun installsPackageOnlyAfterEveryHashPasses() {
        val temp = createTempDir()
        try {
            val archive = packageZip(temp)
            val installed = AssetPackageInstaller.install(archive, temp)
            assertTrue(File(installed.directory, "asset.png").isFile)
            assertEquals(1, installed.fileCount)
        } finally { temp.deleteRecursively() }
    }

    @Test fun rejectsPathTraversalBeforeWritingOutsidePrivateDirectory() {
        val temp = createTempDir()
        try {
            val archive = packageZip(temp, "../escape.png")
            assertThrows(IllegalArgumentException::class.java) { AssetPackageInstaller.install(archive, temp) }
            assertFalse(File(temp.parentFile, "escape.png").exists())
        } finally { temp.deleteRecursively() }
    }

    @Test fun installedAssetAndSceneReferenceSurviveSaveCloseAndReopen() {
        val temp = createTempDir()
        try {
            val installed = AssetPackageInstaller.install(packageWithBank(temp), temp)
            val assetFile = File(installed.directory, "banks/test-instruments/png/Instruments/timbales.png")
            val reference = studio.jedl.app.SceneObjectInstance(
                "test-instruments:timbales", 0.1f, 0.2f, bankId = "test-instruments",
                assetSha256 = sha(assetFile.readBytes()), packageVersion = installed.version
            )
            val project = studio.jedl.app.StudioProject(
                "12345678-1234-1234-1234-123456789012", "Imported asset",
                sceneObjects = listOf(reference)
            )
            studio.jedl.app.ProjectStore(File(temp, "projects")).save(project)
            val restored = studio.jedl.app.ProjectStore(File(temp, "projects")).open(project.id)
            assertEquals(project, restored)
            assertTrue(assetFile.isFile)
            assertTrue(AssetReferenceValidator.matches(restored.sceneObjects.single(),
                ContentAsset("test-instruments:timbales", "Timbales", "Instruments", ContentKind.OBJECT,
                    "test-instruments", assetFile.absolutePath, 128, 128,
                    sha(assetFile.readBytes()), installed.version, true)))
        } finally { temp.deleteRecursively() }
    }

    @Test fun installsBankOnlyAfterItsLicenseAndAssetFingerprintPass() {
        val temp = createTempDir()
        try {
            val installed = AssetPackageInstaller.install(packageWithBank(temp), temp)
            assertTrue(File(installed.directory, "banks/test-instruments/png/Instruments/timbales.png").isFile)
        } finally { temp.deleteRecursively() }
    }

    @Test fun rejectsBankWithoutRedistributionPermission() {
        val temp = createTempDir()
        try {
            assertThrows(IllegalArgumentException::class.java) {
                AssetPackageInstaller.install(packageWithBank(temp, redistribution = false), temp)
            }
        } finally { temp.deleteRecursively() }
    }

    @Test fun rejectsBankManifestWhenAssetHashDoesNotMatchFile() {
        val temp = createTempDir()
        try {
            assertThrows(IllegalArgumentException::class.java) {
                AssetPackageInstaller.install(packageWithBank(temp, corruptBankHash = true), temp)
            }
        } finally { temp.deleteRecursively() }
    }

    @Test fun rejectsNonCc0AndRedistributionIneligiblePackage() {
        val temp = createTempDir()
        try {
            assertThrows(IllegalArgumentException::class.java) {
                AssetPackageInstaller.install(packageZip(temp, license = "CC-BY-NC"), temp)
            }
        } finally { temp.deleteRecursively() }
    }
}
