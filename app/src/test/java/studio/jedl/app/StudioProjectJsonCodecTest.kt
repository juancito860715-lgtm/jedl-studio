package studio.jedl.app

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Test
import studio.jedl.app.avatar.AvatarColorPalette

class StudioProjectJsonCodecTest {
    @Test fun colorsAndResourceProvenanceRoundTrip() {
        val colors = AvatarColorPalette.DEFAULTS + ("skin" to 0xFF123456.toInt())
        val objectRef = SceneObjectInstance("bank:asset", 0.2f, 0.4f, 0.12f, 0.18f, 15f,
            "bank", "a".repeat(64), "1.0.0")
        val project = StudioProject("project-id", "Round trip",
            sceneObjects = listOf(objectRef), colors = colors)
        val decoded = StudioProjectJsonCodec.decode(StudioProjectJsonCodec.encode(project))
        assertEquals(project, decoded)
        assertEquals(3, StudioProjectJsonCodec.encode(project).getInt("schemaVersion"))
    }

    @Test fun schemaV1MigratesToDefaultColorsAndEmptySceneObjects() {
        val legacy = JSONObject().put("schemaVersion", 1).put("id", "legacy-id").put("name", "Legacy")
            .put("selectedParts", JSONObject()).put("hiddenSlots", JSONArray()).put("layerOrder", JSONArray())
            .put("pose", JSONObject()).put("durationFrames", 120).put("keyframes", JSONArray())
        val decoded = StudioProjectJsonCodec.decode(legacy)
        assertEquals(AvatarColorPalette.DEFAULTS, decoded.colors)
        assertEquals(emptyList<SceneObjectInstance>(), decoded.sceneObjects)
    }

    @Test fun schemaV2ResourceReferencesMigrateWithoutInventedHashes() {
        val legacyV2 = JSONObject().put("schemaVersion", 2).put("id", "legacy-v2-id").put("name", "Legacy v2")
            .put("selectedParts", JSONObject()).put("hiddenSlots", JSONArray()).put("layerOrder", JSONArray())
            .put("pose", JSONObject()).put("durationFrames", 120).put("keyframes", JSONArray())
            .put("sceneObjects", JSONArray().put(JSONObject().put("assetId", "old:asset")
                .put("x", 0.2).put("y", 0.3)))
        val decoded = StudioProjectJsonCodec.decode(legacyV2)
        assertEquals("", decoded.sceneObjects.single().assetSha256)
        assertEquals("", decoded.sceneObjects.single().bankId)
    }
}
