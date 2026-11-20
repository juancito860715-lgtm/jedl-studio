package studio.jedl.app.avatar

data class RigDefinition(
    val id: String,
    val bones: Set<String>,
    val slots: Set<String>
)

object RigPackCompatibility {
    private val slotBones = mapOf(
        "HEAD" to "head", "EYES" to "head", "EYEBROWS" to "head", "MOUTH" to "head",
        "FACIAL_HAIR" to "head", "HAIR_BACK" to "head", "HAIR_FRONT" to "head",
        "HAT_BACK" to "head", "HAT_FRONT" to "head",
        "TORSO" to "torso", "SHIRT" to "torso", "PANTS" to "torso",
        "UPPER_ARM_L" to "armUL", "SLEEVE_L" to "armUL",
        "UPPER_ARM_R" to "armUR", "SLEEVE_R" to "armUR",
        "FOREARM_L" to "foreArmL", "HAND_L" to "foreArmL",
        "FOREARM_R" to "foreArmR", "HAND_R" to "foreArmR",
        "THIGH_L" to "thighL", "THIGH_R" to "thighR",
        "SHIN_L" to "shinL", "SHIN_R" to "shinR",
        "SHOE_L" to "shinL", "SHOE_R" to "shinR"
    )

    fun isSlotBoneCompatible(slot: String, bone: String): Boolean = slotBones[slot] == bone

    fun requireCompatible(reference: RigDefinition, candidate: RigDefinition) {
        require(reference.id.isNotBlank() && candidate.id.isNotBlank()) {
            "El identificador del rig no puede estar vacío"
        }
        require(reference.id == candidate.id) {
            "El paquete usa un rig diferente: ${candidate.id}; se esperaba ${reference.id}"
        }
        require(reference.bones.isNotEmpty() && candidate.bones == reference.bones) {
            "El paquete no respeta el conjunto de huesos del rig ${reference.id}"
        }
        require(reference.slots.isNotEmpty() && candidate.slots == reference.slots) {
            "El paquete no respeta las ranuras del rig ${reference.id}"
        }
    }

    fun preserveCompatibleSelection(
        selection: Map<String, String>,
        availableParts: Map<String, String>
    ): Map<String, String> = selection.filter { (slot, partId) ->
        availableParts[partId] == slot
    }
}
