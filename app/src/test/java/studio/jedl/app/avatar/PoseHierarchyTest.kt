package studio.jedl.app.avatar

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test
import kotlin.math.hypot

class PoseHierarchyTest {
    private fun near(expected: Double, actual: Double, epsilon: Double = 1e-6) {
        assertEquals(expected, actual, epsilon)
    }

    @Test
    fun restPosePlacesEveryBoneAtItsDeclaredJoint() {
        val matrices = PoseHierarchy.solve(emptyMap())
        PoseHierarchy.restJoints.forEach { (bone, joint) ->
            val actual = matrices.getValue(bone).transform(Point2(0.0, 0.0))
            near(joint.x, actual.x)
            near(joint.y, actual.y)
        }
    }

    @Test
    fun rotatingUpperArmMovesForearmJoint() {
        val rest = PoseHierarchy.solve(emptyMap())
        val rotated = PoseHierarchy.solve(mapOf("armUL" to 90f))
        val restElbow = rest.getValue("foreArmL").transform(Point2(0.0, 0.0))
        val rotatedElbow = rotated.getValue("foreArmL").transform(Point2(0.0, 0.0))
        assertNotEquals(restElbow.x, rotatedElbow.x, 1e-6)
        assertNotEquals(restElbow.y, rotatedElbow.y, 1e-6)
        near(-0.245, rotatedElbow.x)
        near(-0.26, rotatedElbow.y)
    }

    @Test
    fun rotatingTorsoCarriesHeadAndBothShoulders() {
        val rest = PoseHierarchy.solve(emptyMap())
        val rotated = PoseHierarchy.solve(mapOf("torso" to 90f))
        val restHead = rest.getValue("head").transform(Point2(0.0, 0.0))
        val rotatedHead = rotated.getValue("head").transform(Point2(0.0, 0.0))
        val restShoulder = rest.getValue("armUL").transform(Point2(0.0, 0.0))
        val rotatedShoulder = rotated.getValue("armUL").transform(Point2(0.0, 0.0))
        near(0.0, restHead.x)
        near(-0.28, restHead.y)
        near(0.28, rotatedHead.x)
        near(0.0, rotatedHead.y)
        near(0.26, rotatedShoulder.x)
        near(-0.10, rotatedShoulder.y)
    }

    @Test
    fun parentChildJointDistanceIsInvariantUnderRotation() {
        val angles = mapOf(
            "torso" to 33f, "armUL" to 71f, "foreArmL" to -42f,
            "thighR" to -58f, "shinR" to 27f
        )
        val matrices = PoseHierarchy.solve(angles)
        val pairs = listOf(
            "torso" to "head",
            "torso" to "armUL",
            "armUL" to "foreArmL",
            "torso" to "thighR",
            "thighR" to "shinR"
        )
        pairs.forEach { (parent, child) ->
            val parentAnchor = matrices.getValue(parent).transform(Point2(0.0, 0.0))
            val childAnchor = matrices.getValue(child).transform(Point2(0.0, 0.0))
            val distance = hypot(childAnchor.x - parentAnchor.x, childAnchor.y - parentAnchor.y)
            val parentJoint = PoseHierarchy.restJoints.getValue(parent)
            val childJoint = PoseHierarchy.restJoints.getValue(child)
            val restDistance = hypot(childJoint.x - parentJoint.x, childJoint.y - parentJoint.y)
            near(restDistance, distance)
        }
    }

    @Test
    fun positiveAngleIsClockwiseInScreenCoordinates() {
        val point = PoseTransform.rotationClockwiseDegrees(90.0).transform(Point2(0.0, -1.0))
        near(1.0, point.x)
        near(0.0, point.y)
    }
}
