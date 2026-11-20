package studio.jedl.app.animation

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import studio.jedl.app.StudioKeyframe
import kotlin.math.abs

class PoseInterpolatorTest {
    private fun near(expected: Float, actual: Float, epsilon: Float = 1e-4f) {
        assertTrue("Expected $expected but was $actual", abs(expected - actual) <= epsilon)
    }

    @Test fun interpolatesLinearlyBetweenKeyframes() {
        val keys = listOf(
            StudioKeyframe(0, mapOf("armUL" to 0f)),
            StudioKeyframe(10, mapOf("armUL" to 80f))
        )
        near(40f, PoseInterpolator.interpolate(keys, 5f, 20, loop = false).getValue("armUL"))
    }

    @Test fun usesShortestArcAcrossPositiveAndNegative180Degrees() {
        val keys = listOf(
            StudioKeyframe(0, mapOf("head" to 170f)),
            StudioKeyframe(10, mapOf("head" to -170f))
        )
        val midpoint = PoseInterpolator.interpolate(keys, 5f, 20, loop = false).getValue("head")
        near(180f, abs(midpoint))
    }

    @Test fun clampsOutsideKeyframeRangeWhenNotLooping() {
        val keys = listOf(
            StudioKeyframe(4, mapOf("head" to -30f)),
            StudioKeyframe(8, mapOf("head" to 70f))
        )
        near(-30f, PoseInterpolator.interpolate(keys, 0f, 12, loop = false).getValue("head"))
        near(70f, PoseInterpolator.interpolate(keys, 11f, 12, loop = false).getValue("head"))
    }

    @Test fun loopsSmoothlyFromLastKeyframeBackToFirst() {
        val keys = listOf(
            StudioKeyframe(2, mapOf("torso" to 0f)),
            StudioKeyframe(6, mapOf("torso" to 90f))
        )
        near(60f, PoseInterpolator.interpolate(keys, 8f, 10, loop = true).getValue("torso"))
    }

    @Test fun missingBoneValuesDefaultToZero() {
        val keys = listOf(
            StudioKeyframe(0, mapOf("head" to 0f)),
            StudioKeyframe(10, mapOf("armUL" to 60f))
        )
        val pose = PoseInterpolator.interpolate(keys, 5f, 20, loop = false)
        near(0f, pose.getValue("head"))
        near(30f, pose.getValue("armUL"))
    }

    @Test fun oneKeyframeProducesConstantPose() {
        val pose = PoseInterpolator.interpolate(listOf(StudioKeyframe(4, mapOf("head" to 22f))), 7f, 12)
        assertEquals(mapOf("head" to 22f), pose)
    }
}
