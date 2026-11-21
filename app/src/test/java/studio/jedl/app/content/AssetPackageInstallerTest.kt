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
            .put("files", JSONArray().put(JSONObject().put("path", path).put("bytes", payload.size)
                .put("sha256", sha(payload))))
        val file = File(root, "test.zip")
        ZipOutputStream(file.outputStream()).use { zip ->
            zip.putNextEntry(ZipEntry("JEDL-PACKAGE.json")); zip.write(manifest.toString().toByteArray()); zip.closeEntry()
            zip.putNextEntry(ZipEntry(path)); zip.write(payload); zip.closeEntry()
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
            val installed = AssetPackageInstaller.install(packageZip(temp), temp)
            val assetFile = File(installed.directory, "asset.png")
            val reference = studio.jedl.app.SceneObjectInstance(
                "test-library:asset", 0.1f, 0.2f, bankId = installed.id,
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
                ContentAsset("test-library:asset", "Asset", "General", ContentKind.OBJECT,
                    installed.id, assetFile.absolutePath, 1, 1, sha(assetFile.readBytes()), installed.version, true)))
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
