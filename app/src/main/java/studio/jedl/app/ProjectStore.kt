package studio.jedl.app

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.UUID

class ProjectStore(context: Context) {
    private val directory = File(context.applicationContext.filesDir, "projects").apply { mkdirs() }

    fun create(name: String): StudioProject {
        val clean = name.trim()
        require(clean.isNotEmpty()) { "El proyecto necesita un nombre" }
        val project = StudioProject(UUID.randomUUID().toString(), clean)
        save(project)
        return project
    }

    fun save(project: StudioProject) {
        val valid = project.validated()
        val target = fileFor(valid.id)
        val temporary = File(directory, "${valid.id}.tmp")
        temporary.writeText(encode(valid).toString(), Charsets.UTF_8)
        if (!temporary.renameTo(target)) {
            target.writeText(temporary.readText(Charsets.UTF_8), Charsets.UTF_8)
            temporary.delete()
        }
    }

    fun list(): List<StudioProject> = directory.listFiles()
        ?.filter { it.isFile && it.name.endsWith(".json") }
        ?.mapNotNull { runCatching { decode(JSONObject(it.readText(Charsets.UTF_8))) }.getOrNull() }
        ?.sortedBy { it.name.lowercase() } ?: emptyList()

    fun open(id: String): StudioProject {
        require(id.matches(Regex("[a-fA-F0-9-]{36}"))) { "Invalid project id" }
        val file = fileFor(id)
        require(file.isFile) { "Proyecto no encontrado" }
        return decode(JSONObject(file.readText(Charsets.UTF_8)))
    }

    private fun fileFor(id: String) = File(directory, "$id.json")

    private fun encode(p: StudioProject) = JSONObject().apply {
        put("schemaVersion", 2)
        put("id", p.id); put("name", p.name)
        put("selectedParts", JSONObject(p.selectedParts))
        put("hiddenSlots", JSONArray(p.hiddenSlots.toList()))
        put("layerOrder", JSONArray(p.layerOrder))
        put("pose", JSONObject(p.pose))
        put("durationFrames", p.durationFrames)
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

    private fun decode(json: JSONObject): StudioProject {
        val schemaVersion = json.getInt("schemaVersion")
        require(schemaVersion in 1..2) { "Unsupported project version" }
        fun stringMap(obj: JSONObject): Map<String, String> =
            obj.keys().asSequence().associateWith { obj.getString(it) }
        fun floatMap(obj: JSONObject): Map<String, Float> =
            obj.keys().asSequence().associateWith { obj.getDouble(it).toFloat() }
        val frames = json.getJSONArray("keyframes")
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
            } ?: emptyList()
        ).validated()
    }
}
