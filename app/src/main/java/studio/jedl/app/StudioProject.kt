package studio.jedl.app

import studio.jedl.app.avatar.PoseHierarchy

data class StudioKeyframe(val frame: Int, val pose: Map<String, Float>)

data class SceneObjectInstance(
    val assetId: String,
    val x: Float,
    val y: Float,
    val width: Float = 0.12f,
    val height: Float = 0.12f,
    val rotation: Float = 0f
)

data class StudioProject(
    val id: String,
    val name: String,
    val selectedParts: Map<String, String> = emptyMap(),
    val hiddenSlots: Set<String> = emptySet(),
    val layerOrder: List<String> = emptyList(),
    val pose: Map<String, Float> = emptyMap(),
    val keyframes: List<StudioKeyframe> = emptyList(),
    val durationFrames: Int = 120,
    val sceneObjects: List<SceneObjectInstance> = emptyList()
) {
    fun validated(): StudioProject {
        require(id.isNotBlank()) { "Project id cannot be blank" }
        require(name.isNotBlank()) { "Project name cannot be blank" }
        require(durationFrames in 1..3600) { "Project duration must be between 1 and 3600 frames" }
        require(hiddenSlots.all { it in SLOT_NAMES }) { "Unknown hidden layer slot" }
        require(layerOrder.distinct().size == layerOrder.size && layerOrder.all { it in SLOT_NAMES }) {
            "Layer order contains an unknown or duplicate slot"
        }
        require(pose.keys.all { it in PoseHierarchy.boneNames }) { "Pose contains an unknown bone" }
        require(pose.values.all { it.isFinite() && it in -180f..180f }) { "Pose angle out of range" }
        require(keyframes.all { it.frame in 0 until durationFrames &&
            it.pose.keys.all { bone -> bone in PoseHierarchy.boneNames } &&
            it.pose.values.all { angle -> angle.isFinite() && angle in -180f..180f } }) {
            "Invalid keyframe"
        }
        require(keyframes.map { it.frame }.distinct().size == keyframes.size) {
            "Duplicate keyframe frame"
        }
        require(sceneObjects.size <= 500) { "Scene supports at most 500 placed assets" }
        require(sceneObjects.all { item ->
            item.assetId.isNotBlank() && item.assetId.length <= 180 &&
                item.x.isFinite() && item.x in -2f..2f &&
                item.y.isFinite() && item.y in -2f..2f &&
                item.width.isFinite() && item.width in 0.01f..1.5f &&
                item.height.isFinite() && item.height in 0.01f..1.5f &&
                item.rotation.isFinite() && item.rotation in -360f..360f
        }) { "Invalid scene object placement" }
        return this
    }

    companion object {
        val SLOT_NAMES = setOf(
            "HEAD","EYES","EYEBROWS","MOUTH","FACIAL_HAIR","HAIR_BACK","HAIR_FRONT",
            "HAT_BACK","HAT_FRONT","TORSO","SHIRT","PANTS","UPPER_ARM_L","UPPER_ARM_R",
            "SLEEVE_L","SLEEVE_R","FOREARM_L","FOREARM_R","HAND_L","HAND_R",
            "THIGH_L","THIGH_R","SHIN_L","SHIN_R","SHOE_L","SHOE_R"
        )
    }
}
