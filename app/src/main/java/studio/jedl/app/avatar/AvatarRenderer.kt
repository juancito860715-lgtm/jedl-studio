package studio.jedl.app.avatar

import android.graphics.Canvas
import android.graphics.Matrix
import android.graphics.Paint
import android.graphics.PorterDuff
import android.graphics.PorterDuffColorFilter

/** Draws selected PNG layers in manifest Z order around their normalized rig pivots. */
class AvatarRenderer {
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)

    fun draw(
        canvas: Canvas,
        library: PieceLibrary,
        boneMatrices: Map<String, Matrix>,
        selection: Map<CharacterLayerSlot, String> = emptyMap(),
        colors: Map<String, Int> = emptyMap()
    ) {
        val layers = library.resolve(selection)
        require(layers.isNotEmpty()) { "Avatar manifest resolved to no visible layers" }
        layers.forEach { part ->
            val matrix = boneMatrices[part.boneId]
                ?: error("Missing rig matrix for bone ${part.boneId} required by ${part.id}")
            val bitmap = library.bitmap(part.id)
            val save = canvas.save()
            try {
                canvas.concat(matrix)
                canvas.translate(
                    part.offsetX - part.pivotX * part.widthUnits,
                    part.offsetY - part.pivotY * part.heightUnits
                )
                canvas.scale(part.widthUnits / bitmap.width, part.heightUnits / bitmap.height)
                paint.colorFilter = part.tintChannel?.let { key ->
                    colors[key]?.let { PorterDuffColorFilter(it, PorterDuff.Mode.SRC_IN) }
                }
                canvas.drawBitmap(bitmap, 0f, 0f, paint)
            } finally {
                paint.colorFilter = null
                canvas.restoreToCount(save)
            }
        }
    }
}
