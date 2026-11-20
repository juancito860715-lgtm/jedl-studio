package studio.jedl.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class StudioProjectTest {
    @Test fun acceptsValidProjectAndKeyframes() {
        val project = StudioProject(
            id = "project-1", name = "Demo",
            hiddenSlots = setOf("HAT_FRONT"),
            layerOrder = listOf("HEAD", "TORSO"),
            pose = mapOf("head" to 12f),
            keyframes = listOf(StudioKeyframe(0, mapOf("head" to 0f)), StudioKeyframe(12, mapOf("head" to 12f)))
        )
        assertEquals(project, project.validated())
    }

    @Test fun rejectsDuplicateKeyframeFrames() {
        assertThrows(IllegalArgumentException::class.java) {
            StudioProject("p", "Demo", keyframes = listOf(
                StudioKeyframe(1, emptyMap()), StudioKeyframe(1, emptyMap())
            )).validated()
        }
    }

    @Test fun rejectsUnknownLayerAndOutOfRangeAngles() {
        assertThrows(IllegalArgumentException::class.java) {
            StudioProject("p", "Demo", hiddenSlots = setOf("NOT_A_LAYER")).validated()
        }
        assertThrows(IllegalArgumentException::class.java) {
            StudioProject("p", "Demo", pose = mapOf("head" to 181f)).validated()
        }
    }

    @Test fun acceptsAndValidatesPlacedLibraryAssets() {
        val item = SceneObjectInstance("kenney_tiny_town_objects:tree", x = 0.2f, y = 0.4f, width = 0.12f, height = 0.18f)
        val project = StudioProject("p", "Scene", sceneObjects = listOf(item))
        assertEquals(listOf(item), project.validated().sceneObjects)
    }

    @Test fun rejectsInvalidPlacedAssetGeometry() {
        assertThrows(IllegalArgumentException::class.java) {
            StudioProject("p", "Scene", sceneObjects = listOf(
                SceneObjectInstance("asset", x = Float.NaN, y = 0f)
            )).validated()
        }
        assertThrows(IllegalArgumentException::class.java) {
            StudioProject("p", "Scene", sceneObjects = listOf(
                SceneObjectInstance("asset", x = 0f, y = 0f, width = 0f)
            )).validated()
        }
    }

    @Test fun rejectsKeyframeOutsideDuration() {
        assertThrows(IllegalArgumentException::class.java) {
            StudioProject("p", "Demo", keyframes = listOf(StudioKeyframe(120, emptyMap()))).validated()
        }
    }
}
