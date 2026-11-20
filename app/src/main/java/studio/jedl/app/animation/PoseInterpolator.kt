package studio.jedl.app.animation

/** One complete pose sample at a timeline position. Angles are degrees. */
data class PoseKeyframe(val timeMs: Long, val anglesDegrees: Map<String, Double>)

object PoseInterpolator {
    fun interpolate(from: PoseKeyframe, to: PoseKeyframe, timeMs: Long): PoseKeyframe {
        require(to.timeMs > from.timeMs) { "Keyframes must have strictly increasing timestamps" }
        require(from.anglesDegrees.keys == to.anglesDegrees.keys) {
            "Keyframes must contain the same bone set"
        }
        val t = ((timeMs - from.timeMs).toDouble() / (to.timeMs - from.timeMs))
            .coerceIn(0.0, 1.0)
        val angles = from.anglesDegrees.mapValues { (bone, start) ->
            val end = to.anglesDegrees.getValue(bone)
            require(start.isFinite() && end.isFinite()) { "Angles must be finite" }
            val shortestDelta = shortestAngularDelta(start, end)
            normalizeDegrees(start + shortestDelta * t)
        }
        return PoseKeyframe(timeMs.coerceIn(from.timeMs, to.timeMs), angles)
    }

    /** Signed shortest path in [-180, 180); exact half-turn ties choose -180 degrees. */
    fun shortestAngularDelta(fromDegrees: Double, toDegrees: Double): Double {
        require(fromDegrees.isFinite() && toDegrees.isFinite()) { "Angles must be finite" }
        val raw = (toDegrees - fromDegrees) % 360.0
        return ((raw + 180.0) % 360.0 + 360.0) % 360.0 - 180.0
    }

    private fun normalizeDegrees(value: Double): Double {
        val normalized = ((value % 360.0) + 360.0) % 360.0
        return if (normalized > 180.0) normalized - 360.0 else normalized
    }
}
