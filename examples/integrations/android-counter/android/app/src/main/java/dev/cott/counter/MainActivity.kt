package dev.cott.counter

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import example.counter.decrement
import example.counter.increment
import kotlin.math.roundToInt

class MainActivity : Activity() {
    private var count = MIN_COUNT
    private lateinit var countView: TextView
    private lateinit var decrementButton: Button
    private lateinit var incrementButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        count = savedInstanceState
            ?.getInt(STATE_COUNT, MIN_COUNT)
            ?.coerceIn(MIN_COUNT, MAX_COUNT)
            ?: MIN_COUNT

        val padding = (24 * resources.displayMetrics.density).roundToInt()
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            fitsSystemWindows = true
            setPadding(padding, padding, padding, padding)
        }

        countView = TextView(this).apply {
            gravity = Gravity.CENTER
            textSize = 48f
        }
        root.addView(
            countView,
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
            ),
        )

        val controls = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
        }

        decrementButton = Button(this).apply {
            text = "−"
            contentDescription = "Decrement"
            setOnClickListener {
                if (count > MIN_COUNT) {
                    count = decrement(count)
                    renderCount()
                }
            }
        }
        controls.addView(
            decrementButton,
            LinearLayout.LayoutParams(
                0,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                1f,
            ),
        )

        incrementButton = Button(this).apply {
            text = "+"
            contentDescription = "Increment"
            setOnClickListener {
                if (count < MAX_COUNT) {
                    count = increment(count)
                    renderCount()
                }
            }
        }
        controls.addView(
            incrementButton,
            LinearLayout.LayoutParams(
                0,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                1f,
            ),
        )

        root.addView(
            controls,
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
            ),
        )

        setContentView(root)
        renderCount()
    }

    override fun onSaveInstanceState(outState: Bundle) {
        outState.putInt(STATE_COUNT, count)
        super.onSaveInstanceState(outState)
    }

    private fun renderCount() {
        countView.text = count.toString()
        decrementButton.isEnabled = count > MIN_COUNT
        incrementButton.isEnabled = count < MAX_COUNT
    }

    private companion object {
        const val MIN_COUNT = 0
        const val MAX_COUNT = 100
        const val STATE_COUNT = "count"
    }
}
