package studio.jedl.app.avatar

/**
 * Produces actionable diagnostics for style-pack manifest failures.
 * Keep all four identifiers in the message so the exact source record can be fixed.
 */
object AvatarResourceDiagnostic {
    fun describe(
        manifestPath: String,
        pieceId: String,
        slotId: String,
        boneId: String,
        reason: String
    ): String = "Recurso de personaje no válido: manifiesto=$manifestPath; " +
        "pieza=$pieceId; ranura=$slotId; hueso=$boneId; causa=$reason"
}
