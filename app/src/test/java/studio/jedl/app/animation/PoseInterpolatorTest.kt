package studio.jedl.app.animation

import org.junit.Assert.assertEquals
import org.junit.Test

class PoseInterpolatorTest {
    @Test fun interpolatesLinearlyBetweenKeyframes() {
        val a = PoseKeyframe(0, mapOf("armUL" to 10.0))
        val b = PoseKeyframe(1000, mapOf("armUL" to 50.0))
        assertEquals(30.0, PoseInterpolator.interpolate(a, b, 500).anglesDegrees.getValue("armUL"), 1e-9)
    }

    @Test fun crossesZeroUsingShortestArc() {
        val a = PoseKeyframe(0, mapOf("head" to 350.0))
        val b = PoseKeyframe(1000, mapOf("head" to 10.0))
        assertEquals(0.0, PoseInterpolator.interpolate(a, b, 500).anglesDegrees.getValue("head"), 1e-9)
    }

    @Test fun interpolatesNegativeShortestArcAcrossBoundary() {
        val a = PoseKeyframe(0, mapOf("head" to 10.0))
        val b = PoseKeyframe(1000, mapOf("head" to 350.0))
        assertEquals(0.0, PoseInterpolator.interpolate(a, b, 500).anglesDegrees.getValue("head"), 1e-9)
    }

    @Test fun clampsOutsideKeyframeInterval() {
        val a = PoseKeyframe(100, mapOf("torso" to 0.0))
        val b = PoseKeyframe(200, mapOf("torso" to 90.0))
        assertEquals(0.0, PoseInterpolator.interpolate(a, b, 0).anglesDegrees.getValue("torso"), 1e-9)
        assertEquals(90.0, PoseInterpolator.interpolate(a, b, 300).anglesDegrees.getValue("torso"), 1e-9)
    }

    @Test(expected = IllegalArgumentException::class)
    fun rejectsDifferentBoneSets() {
        PoseInterpolator.interpolate(
            PoseKeyframe(0, mapOf("armUL" to 0.0)),
            PoseKeyframe(10, mapOf("head" to 10.0)), 5
        )
    }
}
