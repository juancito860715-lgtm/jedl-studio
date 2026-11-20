package studio.jedl.app.avatar

import android.graphics.Matrix

fun PoseTransform.toAndroidMatrix(): Matrix = Matrix().apply {
    setValues(toAndroidValues())
}
