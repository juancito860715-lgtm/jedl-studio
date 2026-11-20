package studio.jedl.app

import android.content.Context
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
        temporary.writeText(StudioProjectJsonCodec.encode(valid).toString(), Charsets.UTF_8)
        if (!temporary.renameTo(target)) {
            target.writeText(temporary.readText(Charsets.UTF_8), Charsets.UTF_8)
            temporary.delete()
        }
    }

    fun list(): List<StudioProject> = directory.listFiles()
        ?.filter { it.isFile && it.name.endsWith(".json") }
        ?.mapNotNull { runCatching { StudioProjectJsonCodec.decode(org.json.JSONObject(it.readText(Charsets.UTF_8))) }.getOrNull() }
        ?.sortedBy { it.name.lowercase() } ?: emptyList()

    fun open(id: String): StudioProject {
        require(id.matches(Regex("[a-fA-F0-9-]{36}"))) { "Invalid project id" }
        val file = fileFor(id)
        require(file.isFile) { "Proyecto no encontrado" }
        return StudioProjectJsonCodec.decode(org.json.JSONObject(file.readText(Charsets.UTF_8)))
    }

    private fun fileFor(id: String) = File(directory, "$id.json")

}
