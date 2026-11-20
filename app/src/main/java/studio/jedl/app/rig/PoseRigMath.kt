package studio.jedl.app.rig

import kotlin.math.cos
import kotlin.math.sin

/** Pure 2D affine math. Column vectors; positive angles are clockwise in screen coordinates (Y down). */
data class Vec2(val x: Double, val y: Double)

data class Affine2(
    val a: Double = 1.0, val c: Double = 0.0, val tx: Double = 0.0,
    val b: Double = 0.0, val d: Double = 1.0, val ty: Double = 0.0
) {
    operator fun times(rhs: Affine2) = Affine2(
        a = a * rhs.a + c * rhs.b,
        c = a * rhs.c + c * rhs.d,
        tx = a * rhs.tx + c * rhs.ty + tx,
        b = b * rhs.a + d * rhs.b,
        d = b * rhs.c + d * rhs.d,
        ty = b * rhs.tx + d * rhs.ty + ty
    )

    fun map(point: Vec2) = Vec2(a * point.x + c * point.y + tx, b * point.x + d * point.y + ty)

    companion object {
        fun translation(x: Double, y: Double) = Affine2(tx = x, ty = y)
        fun rotationDegrees(degrees: Double): Affine2 {
            val radians = Math.toRadians(degrees)
            val co = cos(radians)
            val si = sin(radians)
            // In screen coordinates (Y down), this is visually clockwise for positive angles.
            return Affine2(a = co, c = -si, b = si, d = co)
        }
    }
}

object PoseRigMath {
    val parents: Map<String, String?> = linkedMapOf(
        "torso" to null,
        "head" to "torso",
        "armUL" to "torso", "foreArmL" to "armUL",
        "armUR" to "torso", "foreArmR" to "armUR",
        "thighL" to "torso", "shinL" to "thighL",
        "thighR" to "torso", "shinR" to "thighR"
    )

    /**
     * restJoints are absolute rest-pose joint coordinates in rig units.
     * Each child is composed as parent * T(childRest - parentRest) * R(childAngle).
     * The torso angle rotates the complete hierarchy around the torso origin.
     */
    fun resolve(
        restJoints: Map<String, Vec2>,
        anglesDegrees: Map<String, Double>,
        root: Vec2 = Vec2(0.0, 0.0)
    ): Map<String, Affine2> {
        require(restJoints.keys.containsAll(parents.keys)) { "Missing rest joints: ${parents.keys - restJoints.keys}" }
        require(anglesDegrees.values.all { it.isFinite() }) { "Pose angles must be finite" }
        val result = linkedMapOf<String, Affine2>()
        parents.forEach { (bone, parent) ->
            val parentMatrix = parent?.let { result[it] ?: error("Parent $it must be resolved before $bone") }
            val localRotation = Affine2.rotationDegrees(anglesDegrees[bone] ?: 0.0)
            val matrix = if (parent == null) {
                Affine2.translation(root.x, root.y) * localRotation
            } else {
                val childRest = restJoints.getValue(bone)
                val parentRest = restJoints.getValue(parent)
                parentMatrix!! *
                    Affine2.translation(childRest.x - parentRest.x, childRest.y - parentRest.y) *
                    localRotation
            }
            result[bone] = matrix
        }
        return result
    }
}
