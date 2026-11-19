package studio.jedl.app

import android.app.Activity
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Matrix
import android.os.Bundle
import android.util.Log
import android.view.Gravity
import android.view.View
import android.widget.TextView
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import studio.jedl.app.avatar.AvatarRenderer
import studio.jedl.app.avatar.PieceLibrary
import kotlin.math.min

class MainActivity : Activity() {
    private val startupScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.decorView.setBackgroundColor(Color.rgb(245, 245, 245))
        showMessage("Cargando recursos del personaje…")

        startupScope.launch {
            try {
                // All manifest parsing and decoding of the 42 PNGs happens off the UI thread.
                val library = withContext(Dispatchers.IO) {
                    PieceLibrary.load(applicationContext)
                }
                // Renderer construction and View installation return to the main thread.
                val renderer = AvatarRenderer()
                setContentView(AvatarPreviewView(this@MainActivity, library, renderer))
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (failure: Exception) {
                Log.e("Assets", "Error loading avatar assets", failure)
                val detail = failure.message ?: failure.javaClass.simpleName
                showMessage("Error cargando assets: $detail")
            }
        }
    }

    private fun showMessage(message: String) {
        setContentView(TextView(this).apply {
            text = message
            textSize = 16f
            setTextColor(Color.DKGRAY)
            gravity = Gravity.CENTER
            setPadding(32, 32, 32, 32)
        })
    }

    override fun onDestroy() {
        startupScope.cancel()
        super.onDestroy()
    }
}

private class AvatarPreviewView(
    context: android.content.Context,
    private val library: PieceLibrary,
    private val renderer: AvatarRenderer
) : View(context) {
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
        if (width == 0 || height == 0) return
        val scale = min(width / 0.42f, height / 1.52f) * 0.88f
        val save = canvas.save()
        try {
            canvas.translate(width / 2f, height * 0.52f)
            canvas.scale(scale, scale)
            renderer.draw(canvas, library, rig)
        } finally {
            canvas.restoreToCount(save)
        }
    }
}
