package studio.jedl.app.avatar

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class AvatarColorPaletteTest {
    @Test
    fun providesEveryGeneratedTintChannel() {
        val expected = setOf(
            "skin", "hair", "shirt", "pants", "shoe", "sole",
            "hat_crown", "hat_panel", "hat_brim"
        )
        assertEquals(expected, AvatarColorPalette.DEFAULTS.keys)
    }

    @Test
    fun allDefaultChannelsHaveVisibleOpaqueColors() {
        AvatarColorPalette.DEFAULTS.forEach { (channel, color) ->
            assertTrue("$channel must have an opaque non-white default", color ushr 24 == 0xFF && color != -1)
        }
    }
}
