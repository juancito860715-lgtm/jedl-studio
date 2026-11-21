package studio.jedl.app

import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File
import java.nio.file.Files

class ProjectStorePersistenceTest {
    @Test fun sceneAssetFingerprintAndMotionKeyframesSurviveStoreRecreation() {
        val root = Files.createTempDirectory("jedl-project-persistence").toFile()
        try {
            val beforeClose = ProjectStore(File(root, "projects"))
            val project = StudioProject(
                id = "12345678-1234-1234-1234-123456789012",
                name = "Persistence test",
                pose = mapOf("torso" to 8f, "armUL" to 22f),
                keyframes = listOf(StudioKeyframe(0, mapOf("torso" to 0f)), StudioKeyframe(15, mapOf("torso" to 8f))),
                sceneObjects = listOf(SceneObjectInstance(
                    "bank:tree", 0.2f, 0.3f, bankId = "bank",
                    assetSha256 = "a".repeat(64), packageVersion = "1.0.0"
                ))
            )
            beforeClose.save(project)
            val afterReopen = ProjectStore(File(root, "projects"))
            assertEquals(project, afterReopen.open(project.id))
        } finally { root.deleteRecursively() }
    }
}
