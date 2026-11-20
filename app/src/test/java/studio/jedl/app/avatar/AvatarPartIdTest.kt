package studio.jedl.app.avatar

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AvatarPartIdTest {
    @Test fun acceptsExistingGeneratedRightForearmId() {
        assertTrue(AvatarPartId.isValid("forearm_skin_open_R"))
    }

    @Test fun acceptsExistingGeneratedLeftAndMixedCaseIds() {
        assertTrue(AvatarPartId.isValid("forearm_skin_open_L"))
        assertTrue(AvatarPartId.isValid("armU_skin_L"))
        assertTrue(AvatarPartId.isValid("shoe_sneaker_upper_R"))
    }

    @Test fun rejectsEmptyUnsafeOrOverlongIds() {
        assertFalse(AvatarPartId.isValid(""))
        assertFalse(AvatarPartId.isValid("../forearm_R"))
        assertFalse(AvatarPartId.isValid("forearm skin R"))
        assertFalse(AvatarPartId.isValid("a".repeat(81)))
    }
}
