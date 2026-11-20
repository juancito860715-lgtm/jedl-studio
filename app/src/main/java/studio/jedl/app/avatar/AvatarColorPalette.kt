package studio.jedl.app.avatar

/** Default ARGB palette for the JEDL character master. */
object AvatarColorPalette {
    val DEFAULTS: Map<String, Int> = mapOf(
        "skin" to 0xFFF1C6A3.toInt(),
        "hair" to 0xFF6B3E26.toInt(),
        "shirt" to 0xFFFFFFFF.toInt(),
        "pants" to 0xFF9DB9CC.toInt(),
        "shoe" to 0xFFF28C28.toInt(),
        "sole" to 0xFFFFFFFF.toInt(),
        "hat_crown" to 0xFFF28C28.toInt(),
        "hat_panel" to 0xFFFFFFFF.toInt(),
        "hat_brim" to 0xFF2B2B2B.toInt()
    )
}
