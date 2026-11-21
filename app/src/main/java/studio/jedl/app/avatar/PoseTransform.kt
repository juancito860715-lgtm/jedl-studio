package studio.jedl.app.avatar

data class Point2(val x: Double, val y: Double)

/** 2D affine matrix. Coordinates use Android's y-down screen convention. */
data class PoseTransform(
    val m00: Double,
    val m01: Double,
    val m02: Double,
    val m10: Double,
    val m11: Double,
    val m12: Double
) {
    operator fun times(other: PoseTransform) = PoseTransform(
        m00 * other.m00 + m01 * other.m10,
        m00 * other.m01 + m01 * other.m11,
        m00 * other.m02 + m01 * other.m12 + m02,
        m10 * other.m00 + m11 * other.m10,
        m10 * other.m01 + m11 * other.m11,
        m10 * other.m02 + m11 * other.m12 + m12
    )

    fun transform(point: Point2) = Point2(
        m00 * point.x + m01 * point.y + m02,
        m10 * point.x + m11 * point.y + m12
    )

    fun toAndroidValues(): FloatArray = floatArrayOf(
        m00.toFloat(), m01.toFloat(), m02.toFloat(),
        m10.toFloat(), m11.toFloat(), m12.toFloat(),
        0f, 0f, 1f
    )

    companion object {
        val IDENTITY = PoseTransform(1.0, 0.0, 0.0, 0.0, 1.0, 0.0)

        fun translation(dx: Double, dy: Double) =
            PoseTransform(1.0, 0.0, dx, 0.0, 1.0, dy)

        /** Positive degrees rotate clockwise on a y-down canvas. */
        fun rotationClockwiseDegrees(degrees: Double): PoseTransform {
            require(degrees.isFinite()) { "Rotation must be finite" }
            val radians = Math.toRadians(degrees)
            val cosine = kotlin.math.cos(radians)
            val sine = kotlin.math.sin(radians)
            return PoseTransform(cosine, -sine, 0.0, sine, cosine, 0.0)
        }
    }
}
