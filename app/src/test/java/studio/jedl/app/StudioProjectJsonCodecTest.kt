package studio.jedl.app

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Test
import studio.jedl.app.avatar.AvatarColorPalette

class StudioProjectJsonCodecTest {
    @Test fun colorsRoundTripAsArgbPerChannel() {
        val colors = AvatarColorPalette.DEFAULTS + ("skin" to 0xFF123456.toInt()) + ("shoe" to 0xFFABCDEF.toInt())
        val project = StudioProject(
            "project-id", "Color test",
            sceneObjects = listOf(SceneObjectInstance("object:tree", 0.2f, 0.4f, 0.12f, 0.18f, 15f)),
            colors = colors
        )
        val decoded = StudioProjectJsonCodec.decode(StudioProjectJsonCodec.encode(project))
        assertEquals(colors, decoded.colors)
        assertEquals(project, decoded)
    }

    @Test fun schemaV1MigratesToDefaultColorsAndEmptySceneObjects() {
        val legacy = JSONObject()
            .put("schemaVersion", 1)
            .put("id", "legacy-id")
            .put("name", "Legacy")
            .put("selectedParts", JSONObject())
            .put("hiddenSlots", JSONArray())
            .put("layerOrder", JSONArray())
            .put("pose", JSONObject())
            .put("durationFrames", 120)
            .put("keyframes", JSONArray())
        val decoded = StudioProjectJsonCodec.decode(legacy)
        assertEquals(AvatarColorPalette.DEFAULTS, decoded.colors)
        assertEquals(emptyList<SceneObjectInstance>(), decoded.sceneObjects)
    }

    @Test fun schemaV2WithoutColorsMigratesToDefaultPalette() {
        val legacyV2 = JSONObject()
            .put("schemaVersion", 2)
            .put("id", "legacy-v2-id")
            .put("name", "Legacy v2")
            .put("selectedParts", JSONObject())
            .put("hiddenSlots", JSONArray())
            .put("layerOrder", JSONArray())
            .put("pose", JSONObject())
            .put("durationFrames", 120)
            .put("keyframes", JSONArray())
            .put("sceneObjects", JSONArray())
        val decoded = StudioProjectJsonCodec.decode(legacyV2)
        assertEquals(AvatarColorPalette.DEFAULTS, decoded.colors)
    }
}
