package studio.jedl.app.avatar

data class RigDefinition(
    val id: String,
    val bones: Set<String>,
    val slots: Set<String>
)

object RigPackCompatibility {
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
}
