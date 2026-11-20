package studio.jedl.app.avatar

/**
 * Default color channels applied to the neutral white fills in generated PNGs.
 * The PNG alpha remains transparent outside each independently-rendered piece.
 */
object AvatarColorPalette {
    val DEFAULTS: Map<String, Int> = mapOf(
        "skin" to 0xFF87583F.toInt(),
        "hair" to 0xFF25232B.toInt(),
        "shirt" to 0xFFF3F1EC.toInt(),
        "pants" to 0xFF30445D.toInt(),
        "shoe" to 0xFFE8E5DE.toInt(),
        "sole" to 0xFFF8F7F2.toInt(),
        "hat_crown" to 0xFFF3F1EC.toInt(),
        "hat_panel" to 0xFF344D78.toInt(),
        "hat_brim" to 0xFF26364F.toInt()
    )
}
