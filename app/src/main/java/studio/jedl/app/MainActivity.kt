package studio.jedl.app

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val title = TextView(this).apply {
            text = "JEDL Studio v2"
            setTextColor(Color.WHITE)
            textSize = 24f
            gravity = Gravity.CENTER
            setBackgroundColor(Color.BLACK)
            contentDescription = "JEDL Studio v2"
        }

        window.decorView.setBackgroundColor(Color.BLACK)
        setContentView(title)
    }
}
