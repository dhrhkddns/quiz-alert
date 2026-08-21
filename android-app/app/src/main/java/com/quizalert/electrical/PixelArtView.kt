package com.quizalert.electrical

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View

class PixelArtView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs) {

    private var visual = "ac_power_types"
    private var title = "8BIT DIAGRAM"
    private val bg = Paint().apply { color = Color.parseColor("#140C32"); isAntiAlias = false }
    private val scan = Paint().apply { color = Color.parseColor("#1E1450"); isAntiAlias = false }
    private val yellow = paint("#F8D030")
    private val cyan = paint("#3CBCFC")
    private val green = paint("#70D030")
    private val red = paint("#F83818")
    private val orange = paint("#FC8830")
    private val gray = paint("#8888A0")
    private val white = paint("#F4F4F4")
    private val dark = paint("#2A2460")
    private val wire = paint("#E8E070")
    private val text = Paint(white).apply {
        textSize = 28f
        isFakeBoldText = true
        isAntiAlias = false
    }
    private val small = Paint(white).apply {
        textSize = 22f
        isAntiAlias = false
    }

    fun show(visualKey: String, question: String) {
        visual = visualKey.ifBlank { "ac_power_types" }
        title = visual.replace('_', ' ').uppercase()
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val w = width.toFloat()
        val h = height.toFloat()
        canvas.drawRect(0f, 0f, w, h, bg)
        var y = 0f
        while (y < h) {
            canvas.drawRect(0f, y, w, y + 3f, scan)
            y += 8f
        }
        canvas.drawText(title.take(22), 16f, 28f, text)
        when (visual) {
            "power_triangle" -> triangle(canvas, w, h)
            "parallel_wires" -> wires(canvas, w, h)
            "capacitor", "capacitor_phasor", "capacitor_discharge" -> cap(canvas, w, h)
            "y_three_phase", "y_load_line_voltage", "y_power", "balanced_3ph" -> wye(canvas, w, h)
            "delta_load" -> delta(canvas, w, h)
            "coupled_coils", "rl_coil", "coil_tau", "rlc_reactance" -> coils(canvas, w, h)
            "dc_motor", "three_phase_motor", "induction_slip", "stepper", "single_phase_im" -> motor(canvas, w, h)
            "transformer_noload", "transformer_yd", "transformer_sat", "transformer_oil", "percent_x", "voltage_reg" -> xfmr(canvas, w, h)
            "sync_gen", "sync_machine", "dc_generator" -> gen(canvas, w, h)
            "rectifier", "scr" -> diode(canvas, w, h)
            "corona", "ferranti", "transposition", "grounding" -> tower(canvas, w, h)
            "hex_number", "osi" -> bits(canvas, w, h)
            "rc_tau", "series_resonance" -> wave(canvas, w, h)
            else -> generic(canvas, w, h)
        }
    }

    private fun paint(hex: String) = Paint().apply { color = Color.parseColor(hex); isAntiAlias = false; style = Paint.Style.FILL }

    private fun triangle(c: Canvas, w: Float, h: Float) {
        c.drawRect(40f, h - 36f, w * 0.62f, h - 28f, green)
        c.drawRect(w * 0.62f, 48f, w * 0.62f + 8f, h - 28f, red)
        val pathYellow = yellow
        var x = 40f
        var yy = h - 32f
        while (x < w * 0.62f) {
            c.drawRect(x, yy, x + 6f, yy + 4f, cyan)
            x += 10f
            yy -= 6f
        }
        c.drawText("P", 80f, h - 10f, small)
        c.drawText("Q", w * 0.62f + 16f, 70f, small)
        c.drawText("S", w * 0.38f, 70f, small)
    }

    private fun wires(c: Canvas, w: Float, h: Float) {
        c.drawRect(w * 0.28f, 44f, w * 0.28f + 10f, h - 24f, cyan)
        c.drawRect(w * 0.62f, 44f, w * 0.62f + 10f, h - 24f, cyan)
        c.drawText("I", w * 0.26f, h - 8f, small)
        c.drawText("PULL", w * 0.40f, h * 0.55f, small)
        c.drawRect(w * 0.34f, h * 0.5f, w * 0.58f, h * 0.5f + 6f, red)
    }

    private fun cap(c: Canvas, w: Float, h: Float) {
        c.drawRect(w * 0.32f, 40f, w * 0.35f, h - 28f, cyan)
        c.drawRect(w * 0.55f, 40f, w * 0.58f, h - 28f, green)
        c.drawText("+", w * 0.24f, 70f, small)
        c.drawText("-", w * 0.62f, 70f, small)
        c.drawText("Q=CV", 20f, h - 10f, small)
    }

    private fun wye(c: Canvas, w: Float, h: Float) {
        val cx = w * 0.5f
        val cy = h * 0.58f
        c.drawLine(cx, cy, cx, 48f, wire.apply { strokeWidth = 6f; style = Paint.Style.STROKE })
        c.drawLine(cx, cy, cx - 70f, h - 28f, wire)
        c.drawLine(cx, cy, cx + 70f, h - 28f, wire)
        wire.style = Paint.Style.FILL
        c.drawCircle(cx, cy, 8f, yellow)
        c.drawText("Y", 16f, h - 10f, small)
    }

    private fun delta(c: Canvas, w: Float, h: Float) {
        val p = android.graphics.Path()
        p.moveTo(w * 0.5f, 44f)
        p.lineTo(w * 0.28f, h - 28f)
        p.lineTo(w * 0.72f, h - 28f)
        p.close()
        wire.style = Paint.Style.STROKE
        wire.strokeWidth = 6f
        c.drawPath(p, wire)
        wire.style = Paint.Style.FILL
        c.drawText("DELTA", 16f, h - 10f, small)
    }

    private fun coils(c: Canvas, w: Float, h: Float) {
        var x = 40f
        repeat(8) {
            c.drawOval(RectF(x, 50f, x + 28f, h - 36f), cyan)
            x += 26f
        }
        c.drawText("L / R / C", 16f, h - 10f, small)
    }

    private fun motor(c: Canvas, w: Float, h: Float) {
        c.drawRect(36f, 44f, 150f, h - 28f, dark)
        c.drawRect(50f, 56f, 136f, h - 40f, cyan)
        c.drawCircle(93f, h * 0.55f, 22f, yellow)
        c.drawText("M", 82f, h * 0.58f, small)
        c.drawText("MOTOR", 170f, h * 0.55f, small)
    }

    private fun xfmr(c: Canvas, w: Float, h: Float) {
        c.drawRect(40f, 48f, 90f, h - 32f, cyan)
        c.drawRect(100f, 40f, 112f, h - 24f, gray)
        c.drawRect(122f, 48f, 172f, h - 32f, green)
        c.drawText("XFMR", 190f, h * 0.55f, small)
    }

    private fun gen(c: Canvas, w: Float, h: Float) {
        c.drawRect(30f, 48f, 160f, h - 28f, dark)
        c.drawText("GEN", 60f, h * 0.58f, yellow)
        c.drawText("Xs / E", 180f, h * 0.55f, small)
    }

    private fun diode(c: Canvas, w: Float, h: Float) {
        val p = android.graphics.Path()
        p.moveTo(50f, 50f)
        p.lineTo(50f, h - 30f)
        p.lineTo(140f, h * 0.55f)
        p.close()
        c.drawPath(p, orange)
        c.drawRect(140f, 50f, 150f, h - 30f, red)
        c.drawText("SCR / DIODE", 170f, h * 0.55f, small)
    }

    private fun tower(c: Canvas, w: Float, h: Float) {
        c.drawRect(70f, 40f, 82f, h - 16f, gray)
        c.drawRect(w - 90f, 40f, w - 78f, h - 16f, gray)
        c.drawRect(70f, 56f, w - 78f, 64f, wire)
        c.drawText("LINE", 16f, h - 10f, small)
    }

    private fun bits(c: Canvas, w: Float, h: Float) {
        c.drawRect(24f, 44f, w * 0.42f, h - 28f, dark)
        c.drawText("DEC", 40f, h * 0.58f, small)
        c.drawRect(w * 0.52f, 44f, w - 24f, h - 28f, dark)
        c.drawText("HEX / BIT", w * 0.56f, h * 0.58f, green)
    }

    private fun wave(c: Canvas, w: Float, h: Float) {
        var x = 16f
        var up = true
        while (x < w - 16f) {
            val y1 = if (up) 50f else h - 36f
            val y2 = if (up) h - 36f else 50f
            c.drawRect(x, y1.coerceAtMost(y2), x + 5f, y1.coerceAtLeast(y2), cyan)
            x += 10f
            up = !up
        }
    }

    private fun generic(c: Canvas, w: Float, h: Float) {
        c.drawRect(28f, 48f, w * 0.3f, h - 28f, orange)
        c.drawRect(w * 0.36f, 48f, w * 0.62f, h - 28f, cyan)
        c.drawRect(w * 0.68f, 48f, w - 24f, h - 28f, green)
        c.drawText("P", 48f, h * 0.58f, small)
        c.drawText("Q", w * 0.46f, h * 0.58f, small)
        c.drawText("S", w * 0.78f, h * 0.58f, small)
    }
}
