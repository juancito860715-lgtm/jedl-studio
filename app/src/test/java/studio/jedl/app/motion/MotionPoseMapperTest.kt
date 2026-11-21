package studio.jedl.app.motion

import org.junit.Assert.*
import org.junit.Test
import studio.jedl.app.avatar.PoseHierarchy

class MotionPoseMapperTest {
    private fun upright(): List<PosePoint> = MutableList(33) { PosePoint(0.5f, 0.5f, 0f, 1f) }.apply {
        this[0] = PosePoint(0.5f, 0.08f, 0f, 1f)
        this[11] = PosePoint(0.4f, 0.2f, 0f, 1f); this[12] = PosePoint(0.6f, 0.2f, 0f, 1f)
        this[13] = PosePoint(0.4f, 0.34f, 0f, 1f); this[14] = PosePoint(0.6f, 0.34f, 0f, 1f)
        this[15] = PosePoint(0.4f, 0.48f, 0f, 1f); this[16] = PosePoint(0.6f, 0.48f, 0f, 1f)
        this[23] = PosePoint(0.44f, 0.52f, 0f, 1f); this[24] = PosePoint(0.56f, 0.52f, 0f, 1f)
        this[25] = PosePoint(0.44f, 0.72f, 0f, 1f); this[26] = PosePoint(0.56f, 0.72f, 0f, 1f)
        this[27] = PosePoint(0.44f, 0.92f, 0f, 1f); this[28] = PosePoint(0.56f, 0.92f, 0f, 1f)
    }

    @Test fun uprightSkeletonMapsToAllRigBonesAndKeyframe() {
        val points = upright()
        val pose = MotionPoseMapper.toPose(points)!!
        assertEquals(PoseHierarchy.boneNames, pose.keys)
        assertTrue(pose.values.all { it.isFinite() && it in -180f..180f })
        assertEquals(0f, pose.getValue("torso"), 0.001f)
        assertEquals(0f, pose.getValue("armUL"), 0.001f)
        assertEquals(0f, pose.getValue("foreArmR"), 0.001f)
        assertEquals(12, MotionPoseMapper.toKeyframe(points, 12)!!.frame)
    }

    @Test fun lowConfidenceLandmarksRejectFrameInsteadOfInventingPose() {
        val points = upright().toMutableList()
        points[15] = points[15].copy(visibility = 0.1f)
        assertNull(MotionPoseMapper.toPose(points))
        assertNull(MotionPoseMapper.toKeyframe(points, 4))
    }

    @Test fun missingLandmarksRejectFrame() {
        assertNull(MotionPoseMapper.toPose(upright().take(20)))
    }
}
