package studio.jedl.app

import android.app.Activity
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Matrix
import android.os.Bundle
import android.view.View
import studio.jedl.app.avatar.AvatarRenderer
import studio.jedl.app.avatar.PieceLibrary
import kotlin.math.min

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val library = PieceLibrary.load(this)
        window.decorView.setBackgroundColor(Color.rgb(245, 245, 245))
        setContentView(AvatarPreviewView(this, library))
    }
}

private class AvatarPreviewView(
    context: android.content.Context,
    private val library: PieceLibrary
) : View(context) {
    private val renderer = AvatarRenderer()
    private val rig = mapOf(
        "torso" to (0f to 0f),
        "head" to (0f to -0.28f),
        "armUL" to (-0.10f to -0.26f),
        "foreArmL" to (-0.10f to -0.115f),
        "armUR" to (0.10f to -0.26f),
        "foreArmR" to (0.10f to -0.115f),
        "thighL" to (-0.07f to -0.02f),
        "shinL" to (-0.07f to 0.17f),
        "thighR" to (0.07f to -0.02f),
        "shinR" to (0.07f to 0.17f)
    ).mapValues { (_, point) ->
        Matrix().apply { setTranslate(point.first, point.second) }
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        canvas.drawColor(Color.rgb(245, 245, 245))
        val scale = min(width / 0.42f, height / 1.52f) * 0.88f
        val save = canvas.save()
        canvas.translate(width / 2f, height * 0.52f)
        canvas.scale(scale, scale)
        renderer.draw(canvas, library, rig)
        canvas.restoreToCount(save)
    }

}