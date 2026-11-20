package studio.jedl.app.animation

import studio.jedl.app.StudioKeyframe

/** Linear pose interpolation using the shortest angular path and optional timeline wrap. */
object PoseInterpolator {
    fun interpolate(
        keyframes: List<StudioKeyframe>,
        frame: Float,
        durationFrames: Int,
        loop: Boolean = true
    ): Map<String, Float> {
        require(durationFrames > 0) { "Timeline duration must be positive" }
        require(frame.isFinite()) { "Playback frame must be finite" }
        if (keyframes.isEmpty()) return emptyMap()
        val sorted = keyframes.sortedBy { it.frame }
        require(sorted.all { it.frame in 0 until durationFrames }) { "Keyframe outside timeline" }
        require(sorted.map { it.frame }.distinct().size == sorted.size) { "Duplicate keyframe frame" }
        if (sorted.size == 1) return sorted.first().pose

        val current = if (loop) {
            ((frame % durationFrames) + durationFrames) % durationFrames
        } else {
            frame.coerceIn(0f, (durationFrames - 1).toFloat())
        }
        val first = sorted.first()
        val last = sorted.last()

        if (loop && (current < first.frame || current >= last.frame)) {
            val adjusted = if (current < first.frame) current + durationFrames else current
            val start = last.frame.toFloat()
            val end = first.frame.toFloat() + durationFrames
            return interpolatePair(last, first, ((adjusted - start) / (end - start)).coerceIn(0f, 1f))
        }

        if (current <= first.frame) return first.pose
        if (current >= last.frame) return last.pose
        val nextIndex = sorted.indexOfFirst { it.frame.toFloat() >= current }
        val before = sorted[nextIndex - 1]
        val after = sorted[nextIndex]
        val fraction = (current - before.frame) / (after.frame - before.frame).toFloat()
        return interpolatePair(before, after, fraction)
    }

    private fun interpolatePair(from: StudioKeyframe, to: StudioKeyframe, fraction: Float): Map<String, Float> {
        val bones = from.pose.keys + to.pose.keys
        return bones.associateWith { bone ->
            val start = from.pose[bone] ?: 0f
            val end = to.pose[bone] ?: 0f
            val delta = ((end - start + 540f) % 360f) - 180f
            normalize(start + delta * fraction)
        }
    }

    private fun normalize(angle: Float): Float =
        ((angle + 180f) % 360f + 360f) % 360f - 180f
}
