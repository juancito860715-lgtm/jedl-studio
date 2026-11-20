package studio.jedl.app.avatar

object StylePackContract {
    const val DEFAULT_STYLE = "default"
    private val STYLE_ID = Regex("[a-z0-9][a-z0-9_-]{0,39}")

    fun isValidStyleId(value: String): Boolean = STYLE_ID.matches(value)
    fun requireStyleId(value: String): String {
        require(isValidStyleId(value)) { "Identificador de estilo no válido" }
        return value
    }
    fun manifestPath(style: String): String = "styles/${requireStyleId(style)}/manifest.json"
    fun isSafeCharacterPath(path: String): Boolean =
        path.startsWith("characters/") && path.endsWith(".png") &&
            !path.contains("..") && !path.startsWith("/") && !path.contains('\\')
    fun characterAssetPath(style: String, relativePath: String): String {
        require(isSafeCharacterPath(relativePath)) { "Ruta de pieza no permitida" }
        return "styles/${requireStyleId(style)}/$relativePath"
    }
    fun discover(assetDirectories: Iterable<String>, hasManifest: (String) -> Boolean): List<String> =
        assetDirectories.filter(::isValidStyleId).filter(hasManifest).distinct().sorted()
}
