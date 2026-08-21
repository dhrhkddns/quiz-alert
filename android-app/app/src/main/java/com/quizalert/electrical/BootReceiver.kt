package com.quizalert.electrical

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Settings

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Intent.ACTION_BOOT_COMPLETED) return
        if (!QuizService.prefs(context).getBoolean(QuizService.KEY_RUNNING, false)) return
        if (!Settings.canDrawOverlays(context)) return
        QuizService.start(context)
    }
}
