package studio.jedl.app

import org.json.JSONArray
import org.json.JSONObject
import studio.jedl.app.avatar.AvatarColorPalette

/** Project JSON v2 codec with v1/v2 default-color migration. */
object StudioProjectJsonCodec {
    fun encode(project: StudioProject): JSONObject {
        val p = project.validated()
        return JSONObject().apply {
            put("schemaVersion", 2)
            put("id", p.id)
            put("name", p.name)
            put("selectedParts", JSONObject(p.selectedParts))
            put("hiddenSlots", JSONArray(p.hiddenSlots.toList()))
            put("layerOrder", JSONArray(p.layerOrder))
            put("pose", JSONObject(p.pose))
            put("durationFrames", p.durationFrames)
            put("colors", JSONObject(p.colors))
            put("keyframes", JSONArray().apply {
                p.keyframes.sortedBy { it.frame }.forEach { frame ->
                    put(JSONObject().put("frame", frame.frame).put("pose", JSONObject(frame.pose)))
                }
            })
            put("sceneObjects", JSONArray().apply {
                p.sceneObjects.forEach { item ->
                    put(JSONObject().put("assetId", item.assetId).put("x", item.x).put("y", item.y)
                        .put("width", item.width).put("height", item.height).put("rotation", item.rotation))
                }
            })
        }
    }

    fun decode(json: JSONObject): StudioProject {
        val schemaVersion = json.getInt("schemaVersion")
        require(schemaVersion in 1..2) { "Unsupported project version" }
        fun stringMap(obj: JSONObject): Map<String, String> =
            obj.keys().asSequence().associateWith { obj.getString(it) }
        fun floatMap(obj: JSONObject): Map<String, Float> =
            obj.keys().asSequence().associateWith { obj.getDouble(it).toFloat() }
        fun intMap(obj: JSONObject): Map<String, Int> =
            obj.keys().asSequence().associateWith { obj.getInt(it) }
        val frames = json.optJSONArray("keyframes") ?: JSONArray()
        val storedColors = json.optJSONObject("colors")?.let(::intMap).orEmpty()
        return StudioProject(
            id = json.getString("id"),
            name = json.getString("name"),
            selectedParts = stringMap(json.optJSONObject("selectedParts") ?: JSONObject()),
            hiddenSlots = json.optJSONArray("hiddenSlots")?.let { a -> (0 until a.length()).map { a.getString(it) }.toSet() } ?: emptySet(),
            layerOrder = json.optJSONArray("layerOrder")?.let { a -> (0 until a.length()).map { a.getString(it) } } ?: emptyList(),
            pose = floatMap(json.optJSONObject("pose") ?: JSONObject()),
            keyframes = (0 until frames.length()).map { i ->
                val item = frames.getJSONObject(i)
                StudioKeyframe(item.getInt("frame"), floatMap(item.getJSONObject("pose")))
            },
            durationFrames = json.optInt("durationFrames", 120),
            sceneObjects = json.optJSONArray("sceneObjects")?.let { array ->
                (0 until array.length()).map { index ->
                    val item = array.getJSONObject(index)
                    SceneObjectInstance(
                        assetId = item.getString("assetId"),
                        x = item.getDouble("x").toFloat(),
                        y = item.getDouble("y").toFloat(),
                        width = item.optDouble("width", 0.12).toFloat(),
                        height = item.optDouble("height", 0.12).toFloat(),
                        rotation = item.optDouble("rotation", 0.0).toFloat()
                    )
                }
            } ?: emptyList(),
            colors = AvatarColorPalette.DEFAULTS + storedColors
        ).validated()
    }
}
