package com.quizalert.electrical

import android.content.Context
import android.graphics.PixelFormat
import android.os.Build
import android.view.Gravity
import android.view.KeyEvent
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.content.ContextCompat

class OverlayManager(private val context: Context) {
    var onQuizClosed: (() -> Unit)? = null
    var onQuit: (() -> Unit)? = null
    var onSolved: ((Boolean) -> Unit)? = null

    private val wm = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private val inflater = LayoutInflater.from(context)
    private var quizView: View? = null
    private var waitView: View? = null
    private var locked = false
    private var current: Question? = null

    fun showQuiz() {
        hideWait()
        if (quizView != null) return
        locked = false
        val q = QuestionBank.next()
        current = q
        val view = inflater.inflate(R.layout.overlay_quiz, null)
        quizView = view
        view.isFocusableInTouchMode = true
        view.setOnKeyListener { _, code, event ->
            if (event.action == KeyEvent.ACTION_UP &&
                (code == KeyEvent.KEYCODE_BACK || code == KeyEvent.KEYCODE_ESCAPE)
            ) {
                true
            } else {
                code == KeyEvent.KEYCODE_BACK
            }
        }

        view.findViewById<TextView>(R.id.sourceText).text = q.source
        view.findViewById<TextView>(R.id.questionText).text = q.q
        view.findViewById<TextView>(R.id.captionText).text = q.caption.ifBlank { "8비트 그림: 이 문제가 말하는 상황" }
        view.findViewById<PixelArtView>(R.id.pixelArt).show(q.visual, q.q)

        val box = view.findViewById<LinearLayout>(R.id.choicesBox)
        box.removeAllViews()
        val feedback = view.findViewById<TextView>(R.id.feedbackText)
        val explainBox = view.findViewById<View>(R.id.explainBox)
        val explainText = view.findViewById<TextView>(R.id.explainText)
        val close = view.findViewById<Button>(R.id.closeButton)
        explainBox.visibility = View.GONE
        close.visibility = View.GONE

        q.choices.forEachIndexed { idx, text ->
            val btn = Button(context).apply {
                this.text = "${idx + 1}.  $text"
                isAllCaps = false
                setBackgroundColor(ContextCompat.getColor(context, R.color.btn))
                setTextColor(ContextCompat.getColor(context, R.color.text))
                textAlignment = View.TEXT_ALIGNMENT_TEXT_START
                setPadding(28, 22, 28, 22)
                setOnClickListener { tryAnswer(idx, this, box, feedback, explainBox, explainText, close) }
            }
            val lp = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
            )
            lp.topMargin = 10
            box.addView(btn, lp)
        }

        close.setOnClickListener { closeQuiz() }

        val type = if (Build.VERSION.SDK_INT >= 26) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            type,
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON or
                WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON,
            PixelFormat.TRANSLUCENT,
        )
        params.gravity = Gravity.CENTER
        wm.addView(view, params)
        view.requestFocus()
    }

    private fun tryAnswer(
        idx: Int,
        clicked: Button,
        box: LinearLayout,
        feedback: TextView,
        explainBox: View,
        explainText: TextView,
        close: Button,
    ) {
        val q = current ?: return
        if (locked) return
        if (idx == q.answer) {
            locked = true
            onSolved?.invoke(true)
            for (i in 0 until box.childCount) box.getChildAt(i).isEnabled = false
            clicked.setBackgroundColor(ContextCompat.getColor(context, R.color.ok))
            clicked.setTextColor(ContextCompat.getColor(context, R.color.bg))
            feedback.setTextColor(ContextCompat.getColor(context, R.color.ok))
            feedback.text = "정답입니다. 해설을 읽고 닫으면 3분 뒤에 다시 나옵니다."
            explainText.text = q.explain
            explainBox.visibility = View.VISIBLE
            close.visibility = View.VISIBLE
        } else {
            onSolved?.invoke(false)
            clicked.setBackgroundColor(ContextCompat.getColor(context, R.color.wrong))
            feedback.setTextColor(ContextCompat.getColor(context, R.color.wrong))
            feedback.text = "오답입니다. 다시 골라 주세요."
            clicked.postDelayed({
                if (!locked) {
                    clicked.setBackgroundColor(ContextCompat.getColor(context, R.color.btn))
                }
            }, 280)
        }
    }

    private fun closeQuiz() {
        if (!locked) return
        hideQuiz()
        onQuizClosed?.invoke()
    }

    fun showWait() {
        if (waitView != null) return
        val view = inflater.inflate(R.layout.overlay_wait, null)
        waitView = view
        view.findViewById<Button>(R.id.waitQuit).setOnClickListener { onQuit?.invoke() }
        val type = if (Build.VERSION.SDK_INT >= 26) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }
        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            type,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT,
        )
        params.gravity = Gravity.TOP or Gravity.END
        params.x = 16
        params.y = 48
        wm.addView(view, params)
    }

    fun updateWait(nextAt: Long, solved: Int, missed: Int) {
        val v = waitView ?: return
        val left = ((nextAt - System.currentTimeMillis()) / 1000).coerceAtLeast(0)
        val m = left / 60
        val s = left % 60
        v.findViewById<TextView>(R.id.waitText).text =
            "다음 기출 %02d:%02d   ·   정답 %d  오답 %d".format(m, s, solved, missed)
    }

    fun hideWait() {
        waitView?.let {
            runCatching { wm.removeView(it) }
        }
        waitView = null
    }

    private fun hideQuiz() {
        quizView?.let { runCatching { wm.removeView(it) } }
        quizView = null
        current = null
        locked = false
    }

    fun destroy() {
        hideQuiz()
        hideWait()
    }
}
