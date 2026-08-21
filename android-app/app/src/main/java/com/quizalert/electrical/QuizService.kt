package com.quizalert.electrical

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import androidx.core.app.NotificationCompat

class QuizService : Service() {
    private val handler = Handler(Looper.getMainLooper())
    private lateinit var overlay: OverlayManager
    private var nextAt = 0L

    private val tick = object : Runnable {
        override fun run() {
            overlay.updateWait(nextAt, solved, missed)
            handler.postDelayed(this, 250)
        }
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        QuestionBank.load(this)
        overlay = OverlayManager(this)
        overlay.onSolved = { correct ->
            if (correct) solved++ else missed++
        }
        overlay.onQuizClosed = {
            scheduleNext()
        }
        overlay.onQuit = { stopSelf() }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIF_ID, buildNotification())
        prefs(this).edit().putBoolean(KEY_RUNNING, true).apply()
        handler.removeCallbacksAndMessages(null)
        overlay.showQuiz()
        return START_STICKY
    }

    fun scheduleNext() {
        handler.removeCallbacksAndMessages(null)
        nextAt = System.currentTimeMillis() + QuestionBank.intervalMs
        overlay.showWait()
        handler.post(tick)
        handler.postDelayed({
            overlay.hideWait()
            overlay.showQuiz()
        }, QuestionBank.intervalMs)
    }

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        overlay.destroy()
        prefs(this).edit().putBoolean(KEY_RUNNING, false).apply()
        instance = null
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun buildNotification(): Notification {
        val nm = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= 26) {
            nm.createNotificationChannel(
                NotificationChannel(CHANNEL, getString(R.string.channel_name), NotificationManager.IMPORTANCE_LOW),
            )
        }
        val open = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(R.drawable.ic_stat)
            .setContentTitle(getString(R.string.app_name))
            .setContentText(getString(R.string.notif_running))
            .setContentIntent(open)
            .setOngoing(true)
            .build()
    }

    companion object {
        const val CHANNEL = "quiz_alert"
        const val NOTIF_ID = 71
        const val KEY_RUNNING = "running"
        var solved = 0
        var missed = 0
        var instance: QuizService? = null
            private set

        fun prefs(ctx: Context) = ctx.getSharedPreferences("quiz_alert", MODE_PRIVATE)

        fun start(ctx: Context) {
            val i = Intent(ctx, QuizService::class.java)
            if (Build.VERSION.SDK_INT >= 26) ctx.startForegroundService(i) else ctx.startService(i)
        }

        fun stop(ctx: Context) {
            ctx.stopService(Intent(ctx, QuizService::class.java))
        }

        fun isRunning(ctx: Context) = prefs(ctx).getBoolean(KEY_RUNNING, false) && instance != null
    }
}
