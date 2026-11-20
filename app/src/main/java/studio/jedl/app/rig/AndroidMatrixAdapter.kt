package studio.jedl.app.rig

import android.graphics.Matrix

/** Android adapter kept outside the pure-JVM rig math module. */
fun Affine2.toAndroidMatrix(): Matrix = Matrix().apply {
    setValues(floatArrayOf(
        a.toFloat(), c.toFloat(), tx.toFloat(),
        b.toFloat(), d.toFloat(), ty.toFloat(),
        0f, 0f, 1f
    ))
}
