package studio.jedl.app.avatar

import org.junit.Assert.*
import org.junit.Test

class StylePackContractTest {
    @Test fun acceptsOnlySafeStyleIdentifiers() {
        assertTrue(StylePackContract.isValidStyleId("default"))
        assertTrue(StylePackContract.isValidStyleId("boceto"))
        assertTrue(StylePackContract.isValidStyleId("hybrid"))
        assertEquals("hybrid", StylePackContract.DEFAULT_STYLE)
        assertTrue(StylePackContract.isValidStyleId("anime_v2"))
        assertFalse(StylePackContract.isValidStyleId("../default"))
        assertFalse(StylePackContract.isValidStyleId("Anime"))
        assertFalse(StylePackContract.isValidStyleId("style/name"))
    }
    @Test fun buildsExpectedAssetPathsAndRejectsTraversal() {
        assertEquals("styles/anime/manifest.json", StylePackContract.manifestPath("anime"))
        assertEquals("styles/boceto/characters/head_skin.png",
            StylePackContract.characterAssetPath("boceto", "characters/head_skin.png"))
        assertFalse(StylePackContract.isSafeCharacterPath("../secret.png"))
        assertFalse(StylePackContract.isSafeCharacterPath("png/head_skin.png"))
        assertFalse(StylePackContract.isSafeCharacterPath("characters/../../secret.png"))
    }
    @Test fun discoversOnlyDirectoriesWithManifests() {
        assertEquals(listOf("boceto", "default"),
            StylePackContract.discover(listOf("default", "boceto", "../invalid", "anime")) { it != "anime" })
    }
}
