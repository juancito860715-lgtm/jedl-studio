package studio.jedl.app.motion

import org.junit.Assert.assertTrue
import org.junit.Test

class PosePointTest {
    @Test fun coordinatesAreNormalizedDataAndVisibilityIsBounded() {
        val point = PosePoint(0.25f, 0.75f, -0.1f, 0.9f)
        assertTrue(point.x in 0f..1f)
        assertTrue(point.y in 0f..1f)
        assertTrue(point.visibility in 0f..1f)
    }
}
