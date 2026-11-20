package studio.jedl.app.avatar

/**
 * Manifest part IDs are stable content identifiers, not Kotlin symbols.
 * Existing generated assets intentionally use side suffixes "_L"/"_R" and
 * names such as "armU_skin_L", so ASCII uppercase is valid.
 */
object AvatarPartId {
    private val pattern = Regex("[A-Za-z0-9][A-Za-z0-9_-]{0,79}")

    fun isValid(value: String): Boolean = pattern.matches(value)
}
