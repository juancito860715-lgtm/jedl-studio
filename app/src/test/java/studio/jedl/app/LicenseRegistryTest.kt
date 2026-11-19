package studio.jedl.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class LicenseRegistryTest {
    private val allowed = setOf("CC0", "OWN", "MIT", "APACHE-2.0", "OFL-1.1")

    @Test
    fun everyBundledAssetHasAnAllowedLicenseRegistryEntry() {
        val root = findRepositoryRoot()
        val assets = File(root, "app/src/main/assets")
        val registry = File(root, "licenses/REGISTRY.json")
        assertTrue("License registry is missing: ${registry.path}", registry.isFile)
        assertTrue("Assets directory is missing: ${assets.path}", assets.isDirectory)

        val json = registry.readText()
        val allowedBlock = Regex("\\\"allowedLicenses\\\"\\s*:\\s*\\[(.*?)]", RegexOption.DOT_MATCHES_ALL)
            .find(json)?.groupValues?.get(1).orEmpty()
        val declaredAllowed = Regex("\\\"([^\\"]+)\\\"")
            .findAll(allowedBlock).map { it.groupValues[1] }.toSet()
        assertEquals("Registry allowed licenses must match the policy", allowed, declaredAllowed)

        val entryPattern = Regex("""\{\s*"path"\s*:\s*"([^"]+)"\s*,\s*"license"\s*:\s*"([^"]+)"\s*}""")
        fun readEntries(key: String): Map<String, String> {
            val block = Regex("\\\"$key\\\"\\s*:\\s*\\[(.*?)]", RegexOption.DOT_MATCHES_ALL)
                .find(json)?.groupValues?.get(1).orEmpty()
            val matches = entryPattern.findAll(block).toList()
            val parsed = matches.associate { it.groupValues[1] to it.groupValues[2] }
            assertEquals("Duplicate paths in license registry section $key", matches.size, parsed.size)
            return parsed
        }

        val entries = readEntries("entries")
        val directoryEntries = readEntries("directoryEntries")
        assertTrue("Directory license paths must end with /", directoryEntries.keys.all { it.endsWith("/") })

        val assetFiles = assets.walkTopDown().filter { it.isFile }.map {
            it.relativeTo(assets).invariantSeparatorsPath
        }.toSet()

        val missing = assetFiles.filter { path ->
            path !in entries && directoryEntries.keys.none { path.startsWith(it) }
        }.toSet()
        val orphaned = entries.keys - assetFiles
        val orphanedDirectories = directoryEntries.keys.filter { prefix ->
            assetFiles.none { it.startsWith(prefix) }
        }.toSet()
        val forbidden = (entries + directoryEntries).filterValues { it !in allowed }.keys
        assertTrue("Unregistered assets: $missing", missing.isEmpty())
        assertTrue("Registry entries without asset files: $orphaned", orphaned.isEmpty())
        assertTrue("Directory registry entries without matching assets: $orphanedDirectories", orphanedDirectories.isEmpty())
        assertTrue("Assets with forbidden license labels: $forbidden", forbidden.isEmpty())
    }

    private fun findRepositoryRoot(): File {
        var current = File(System.getProperty("user.dir")).absoluteFile
        while (true) {
            if (File(current, "licenses/REGISTRY.json").isFile &&
                File(current, "app/src/main/assets").isDirectory) return current
            current = current.parentFile ?: error("Cannot locate repository root from ${System.getProperty("user.dir")}")
        }
    }
}
