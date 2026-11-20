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

    @Test fun rejectsKeyframeOutsideDuration() {
        assertThrows(IllegalArgumentException::class.java) {
            StudioProject("p", "Demo", keyframes = listOf(StudioKeyframe(120, emptyMap()))).validated()
        }
    }
}
