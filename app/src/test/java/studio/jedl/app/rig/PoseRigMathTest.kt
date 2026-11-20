package studio.jedl.app.rig

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test
import kotlin.math.hypot

class PoseRigMathTest {
    private val rest = mapOf(
        "torso" to Vec2(0.0, 0.0),
        "head" to Vec2(0.0, -0.28),
        "armUL" to Vec2(-0.10, -0.26), "foreArmL" to Vec2(-0.10, -0.115),
        "armUR" to Vec2(0.10, -0.26), "foreArmR" to Vec2(0.10, -0.115),
        "thighL" to Vec2(-0.07, -0.02), "shinL" to Vec2(-0.07, 0.17),
        "thighR" to Vec2(0.07, -0.02), "shinR" to Vec2(0.07, 0.17)
    )

    @Test fun restPosePreservesEveryJointCoordinate() {
        val matrices = PoseRigMath.resolve(rest, emptyMap())
        rest.forEach { (bone, point) ->
            val actual = matrices.getValue(bone).map(Vec2(0.0, 0.0))
            assertEquals("$bone x", point.x, actual.x, 1e-9)
            assertEquals("$bone y", point.y, actual.y, 1e-9)
        }
    }

    @Test fun rotatingUpperArmCarriesForearmJointWithIt() {
        val neutral = PoseRigMath.resolve(rest, emptyMap())
        val turned = PoseRigMath.resolve(rest, mapOf("armUL" to 90.0))
        val neutralForearm = neutral.getValue("foreArmL").map(Vec2(0.0, 0.0))
        val turnedForearm = turned.getValue("foreArmL").map(Vec2(0.0, 0.0))
        assertNotEquals(neutralForearm, turnedForearm)
        val shoulder = turned.getValue("armUL").map(Vec2(0.0, 0.0))
        assertEquals(0.145, hypot(turnedForearm.x - shoulder.x, turnedForearm.y - shoulder.y), 1e-9)
    }

    @Test fun torsoRotationCarriesHeadAndBothArms() {
        val neutral = PoseRigMath.resolve(rest, emptyMap())
        val turned = PoseRigMath.resolve(rest, mapOf("torso" to 30.0))
        listOf("head", "armUL", "armUR").forEach { bone ->
            assertNotEquals(neutral.getValue(bone).map(Vec2(0.0, 0.0)), turned.getValue(bone).map(Vec2(0.0, 0.0)))
        }
    }

    @Test fun parentChildJointDistanceDoesNotChangeWhenParentRotates() {
        val matrices = PoseRigMath.resolve(rest, mapOf("armUL" to 63.0, "torso" to -27.0))
        val shoulder = matrices.getValue("armUL").map(Vec2(0.0, 0.0))
        val elbow = matrices.getValue("foreArmL").map(Vec2(0.0, 0.0))
        assertEquals(0.145, hypot(elbow.x - shoulder.x, elbow.y - shoulder.y), 1e-9)
    }
}
