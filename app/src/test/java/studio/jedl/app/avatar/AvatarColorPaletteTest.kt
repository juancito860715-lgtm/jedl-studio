package studio.jedl.app.avatar

import org.junit.Assert.assertEquals
import org.junit.Test

class AvatarColorPaletteTest {
    @Test fun defaultsMatchApprovedCharacterPalette() {
        assertEquals(0xFFF1C6A3.toInt(), AvatarColorPalette.DEFAULTS.getValue("skin"))
        assertEquals(0xFF6B3E26.toInt(), AvatarColorPalette.DEFAULTS.getValue("hair"))
        assertEquals(0xFFFFFFFF.toInt(), AvatarColorPalette.DEFAULTS.getValue("shirt"))
        assertEquals(0xFF9DB9CC.toInt(), AvatarColorPalette.DEFAULTS.getValue("pants"))
        assertEquals(0xFFF28C28.toInt(), AvatarColorPalette.DEFAULTS.getValue("shoe"))
        assertEquals(0xFFFFFFFF.toInt(), AvatarColorPalette.DEFAULTS.getValue("sole"))
        assertEquals(0xFFF28C28.toInt(), AvatarColorPalette.DEFAULTS.getValue("hat_crown"))
        assertEquals(0xFFFFFFFF.toInt(), AvatarColorPalette.DEFAULTS.getValue("hat_panel"))
        assertEquals(0xFF2B2B2B.toInt(), AvatarColorPalette.DEFAULTS.getValue("hat_brim"))
    }

    @Test fun paletteDefinesExactlyNineSupportedChannels() {
        assertEquals(setOf("skin","hair","shirt","pants","shoe","sole","hat_crown","hat_panel","hat_brim"),
            AvatarColorPalette.DEFAULTS.keys)
    }
}
