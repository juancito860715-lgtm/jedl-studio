package studio.jedl.app.avatar

/**
 * Solves the humanoid rig in parent-first order.
 *
 * M_child = M_parent * T(childRestJoint - parentRestJoint) * R(childAngle)
 * Torso is the root. All joint coordinates are expressed in torso rest space.
 */
object PoseHierarchy {
    val boneNames: Set<String> = linkedSetOf(
        "torso", "head", "armUL", "foreArmL", "armUR",
        "foreArmR", "thighL", "shinL", "thighR", "shinR"
    )

    val parents: Map<String, String?> = linkedMapOf(
        "torso" to null,
        "head" to "torso",
        "armUL" to "torso",
        "foreArmL" to "armUL",
        "armUR" to "torso",
        "foreArmR" to "armUR",
        "thighL" to "torso",
        "shinL" to "thighL",
        "thighR" to "torso",
        "shinR" to "thighR"
    )

    /** Anchor position of each bone in the unposed torso coordinate system. */
    val restJoints: Map<String, Point2> = linkedMapOf(
        "torso" to Point2(0.0, 0.0),
        "head" to Point2(0.0, -0.28),
        "armUL" to Point2(-0.10, -0.26),
        "foreArmL" to Point2(-0.10, -0.115),
        "armUR" to Point2(0.10, -0.26),
        "foreArmR" to Point2(0.10, -0.115),
        "thighL" to Point2(-0.07, -0.02),
        "shinL" to Point2(-0.07, 0.17),
        "thighR" to Point2(0.07, -0.02),
        "shinR" to Point2(0.07, 0.17)
    )

    fun solve(angles: Map<String, Float>): Map<String, PoseTransform> {
        require(angles.keys.all { it in boneNames }) { "Pose contains an unknown bone" }
        require(angles.values.all { it.isFinite() && it in -180f..180f }) {
            "Pose angle must be finite and between -180 and 180 degrees"
        }
        val result = linkedMapOf<String, PoseTransform>()
        boneNames.forEach { bone ->
            val parent = parents.getValue(bone)
            val angle = (angles[bone] ?: 0f).toDouble()
            if (parent == null) {
                result[bone] = PoseTransform.rotationClockwiseDegrees(angle)
            } else {
                val parentMatrix = result[parent]
                    ?: error("Rig parent must be solved before child: " + bone)
                val parentJoint = restJoints.getValue(parent)
                val childJoint = restJoints.getValue(bone)
                val local = PoseTransform.translation(
                    childJoint.x - parentJoint.x,
                    childJoint.y - parentJoint.y
                ) * PoseTransform.rotationClockwiseDegrees(angle)
                result[bone] = parentMatrix * local
            }
        }
        return result
    }
}
