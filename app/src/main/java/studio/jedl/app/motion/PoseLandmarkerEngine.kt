package studio.jedl.app.motion

import android.content.Context
import android.graphics.Bitmap
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarker
import java.io.Closeable
import studio.jedl.app.StudioKeyframe

data class PosePoint(
    val x: Float,
    val y: Float,
    val z: Float,
    val visibility: Float
)

/** Offline MediaPipe inference; call from a worker dispatcher, never the UI thread. */
class PoseLandmarkerEngine(context: Context) : Closeable {
    private val landmarker: PoseLandmarker

    init {
        val options = PoseLandmarker.PoseLandmarkerOptions.builder()
            .setBaseOptions(BaseOptions.builder().setModelAssetPath("models/pose_landmarker_lite.task").build())
            .setRunningMode(RunningMode.VIDEO)
            .setNumPoses(1)
            .build()
        landmarker = PoseLandmarker.createFromOptions(context.applicationContext, options)
    }

    fun detectVideoFrame(bitmap: Bitmap, timestampMs: Long): List<PosePoint> {
        require(timestampMs >= 0L) { "Timestamp must be non-negative" }
        val image = BitmapImageBuilder(bitmap).build()
        val result = landmarker.detectForVideo(image, timestampMs)
        return result.landmarks().firstOrNull().orEmpty().map { point ->
            PosePoint(point.x(), point.y(), point.z(), point.visibility().orElse(0f))
        }
    }

    fun detectVideoKeyframe(bitmap: Bitmap, timestampMs: Long, frame: Int): StudioKeyframe? =
        MotionPoseMapper.toKeyframe(detectVideoFrame(bitmap, timestampMs), frame)

    override fun close() = landmarker.close()
}
