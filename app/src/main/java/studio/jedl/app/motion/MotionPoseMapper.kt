package studio.jedl.app.motion

import studio.jedl.app.StudioKeyframe
import studio.jedl.app.avatar.PoseHierarchy
import kotlin.math.atan2

/** Converts MediaPipe's 33 normalized landmarks into the local angles used by JEDL's 2D rig. */
object MotionPoseMapper {
    private const val MIN_VISIBILITY = 0.45f
    private const val NOSE = 0
    private const val LEFT_SHOULDER = 11
    private const val RIGHT_SHOULDER = 12
    private const val LEFT_ELBOW = 13
    private const val RIGHT_ELBOW = 14
    private const val LEFT_WRIST = 15
    private const val RIGHT_WRIST = 16
    private const val LEFT_HIP = 23
    private const val RIGHT_HIP = 24
    private const val LEFT_KNEE = 25
    private const val RIGHT_KNEE = 26
    private const val LEFT_ANKLE = 27
    private const val RIGHT_ANKLE = 28

    fun toPose(points: List<PosePoint>, minVisibility: Float = MIN_VISIBILITY): Map<String, Float>? {
        if (points.size < 33 || minVisibility !in 0f..1f) return null
        val required = intArrayOf(NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_ELBOW, RIGHT_ELBOW,
            LEFT_WRIST, RIGHT_WRIST, LEFT_HIP, RIGHT_HIP, LEFT_KNEE, RIGHT_KNEE, LEFT_ANKLE, RIGHT_ANKLE)
        if (required.any { points[it].visibility < minVisibility }) return null
        val nose = points[NOSE]
        val ls = points[LEFT_SHOULDER]
        val rs = points[RIGHT_SHOULDER]
        val le = points[LEFT_ELBOW]
        val re = points[RIGHT_ELBOW]
        val lw = points[LEFT_WRIST]
        val rw = points[RIGHT_WRIST]
        val lh = points[LEFT_HIP]
        val rh = points[RIGHT_HIP]
        val lk = points[LEFT_KNEE]
        val rk = points[RIGHT_KNEE]
        val la = points[LEFT_ANKLE]
        val ra = points[RIGHT_ANKLE]

        val shoulderMid = midpoint(ls, rs)
        val hipMid = midpoint(lh, rh)
        val torso = fromDown(shoulderMid, hipMid)
        val headGlobal = fromUp(shoulderMid, nose)
        val leftUpper = fromDown(ls, le)
        val rightUpper = fromDown(rs, re)
        val leftFore = fromDown(le, lw)
        val rightFore = fromDown(re, rw)
        val leftThigh = fromDown(lh, lk)
        val rightThigh = fromDown(rh, rk)
        val leftShin = fromDown(lk, la)
        val rightShin = fromDown(rk, ra)

        return linkedMapOf(
            "torso" to normalize(torso),
            "head" to normalize(headGlobal - torso),
            "armUL" to normalize(leftUpper - torso),
            "foreArmL" to normalize(leftFore - leftUpper),
            "armUR" to normalize(rightUpper - torso),
            "foreArmR" to normalize(rightFore - rightUpper),
            "thighL" to normalize(leftThigh - torso),
            "shinL" to normalize(leftShin - leftThigh),
            "thighR" to normalize(rightThigh - torso),
            "shinR" to normalize(rightShin - rightThigh)
        ).also { require(it.keys == PoseHierarchy.boneNames) }
    }

    fun toKeyframe(points: List<PosePoint>, frame: Int): StudioKeyframe? {
        require(frame >= 0) { "Frame must be non-negative" }
        val pose = toPose(points) ?: return null
        return StudioKeyframe(frame, pose)
    }

    private fun midpoint(a: PosePoint, b: PosePoint) =
        PosePoint((a.x + b.x) / 2f, (a.y + b.y) / 2f, (a.z + b.z) / 2f,
            minOf(a.visibility, b.visibility))

    private fun fromDown(a: PosePoint, b: PosePoint): Float =
        Math.toDegrees(atan2((b.x - a.x).toDouble(), (b.y - a.y).toDouble())).toFloat()

    private fun fromUp(a: PosePoint, b: PosePoint): Float =
        Math.toDegrees(atan2((b.x - a.x).toDouble(), (a.y - b.y).toDouble())).toFloat()

    private fun normalize(value: Float): Float {
        var angle = value % 360f
        if (angle > 180f) angle -= 360f
        if (angle < -180f) angle += 360f
        return angle.coerceIn(-180f, 180f)
    }
}
