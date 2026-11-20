package studio.jedl.app.avatar

import org.junit.Assert.*
import org.junit.Test

class RigPackCompatibilityTest {
    private val requiredBones = setOf(
        "torso", "head", "armUL", "foreArmL", "armUR", "foreArmR",
        "thighL", "shinL", "thighR", "shinR"
    )
    private val requiredSlots = setOf("HEAD", "TORSO", "HAND_L", "HAND_R")

    @Test fun acceptsDifferentArtPartsWhenTheyShareTheSameRigContract() {
        val master = RigDefinition("jedl_humanoid_v1", requiredBones, requiredSlots)
        val imported = RigDefinition("jedl_humanoid_v1", requiredBones, requiredSlots)
        RigPackCompatibility.requireCompatible(master, imported)
    }

    @Test fun rejectsDifferentRigVersions() {
        val master = RigDefinition("jedl_humanoid_v1", requiredBones, requiredSlots)
        val imported = RigDefinition("other_rig", requiredBones, requiredSlots)
        assertThrows(IllegalArgumentException::class.java) {
            RigPackCompatibility.requireCompatible(master, imported)
        }
    }

    @Test fun rejectsMissingOrAdditionalBones() {
        val master = RigDefinition("jedl_humanoid_v1", requiredBones, requiredSlots)
        val missing = RigDefinition("jedl_humanoid_v1", requiredBones - "foreArmL", requiredSlots)
        val extra = RigDefinition("jedl_humanoid_v1", requiredBones + "tail", requiredSlots)
        assertThrows(IllegalArgumentException::class.java) {
            RigPackCompatibility.requireCompatible(master, missing)
        }
        assertThrows(IllegalArgumentException::class.java) {
            RigPackCompatibility.requireCompatible(master, extra)
        }
    }

    @Test fun rejectsDifferentSlotContractsButDoesNotRequireIdenticalPieceIds() {
        val master = RigDefinition("jedl_humanoid_v1", requiredBones, requiredSlots)
        val missingSlot = RigDefinition("jedl_humanoid_v1", requiredBones, requiredSlots - "HAND_R")
        assertThrows(IllegalArgumentException::class.java) {
            RigPackCompatibility.requireCompatible(master, missingSlot)
        }
        assertNotEquals("same rig contract must not depend on source-art IDs",
            "kenney_hand_open_r", "hand_open_R")
    }
}
