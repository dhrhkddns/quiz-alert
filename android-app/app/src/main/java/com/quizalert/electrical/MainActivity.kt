package com.quizalert.electrical

import android.Manifest
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
    private val notifPermission = registerForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { /* ignore */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        findViewById<Button>(R.id.startButton).setOnClickListener { startQuiz() }
        findViewById<Button>(R.id.stopButton).setOnClickListener {
            QuizService.stop(this)
            refresh()
        }
        findViewById<Button>(R.id.overlayButton).setOnClickListener { openOverlaySettings() }
        findViewById<Button>(R.id.batteryButton).setOnClickListener { openBatterySettings() }
    }

    override fun onResume() {
        super.onResume()
        refresh()
        if (Build.VERSION.SDK_INT >= 33) {
            notifPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    private fun startQuiz() {
        if (!Settings.canDrawOverlays(this)) {
            Toast.makeText(this, "먼저 ‘다른 앱 위에 표시’를 허용하세요.", Toast.LENGTH_LONG).show()
            openOverlaySettings()
            return
        }
        QuestionBank.load(this)
        if (QuestionBank.size == 0) {
            Toast.makeText(this, "문제 은행을 불러오지 못했습니다. 앱을 다시 빌드해 주세요.", Toast.LENGTH_LONG).show()
            return
        }
        QuizService.start(this)
        refresh()
        Toast.makeText(this, "바로 퀴즈가 뜹니다. 홈으로 나가도 창이 유지됩니다.", Toast.LENGTH_LONG).show()
    }

    private fun openOverlaySettings() {
        startActivity(
            Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:$packageName"),
            ),
        )
    }

    private fun openBatterySettings() {
        val pm = getSystemService(PowerManager::class.java)
        if (Build.VERSION.SDK_INT >= 23 && !pm.isIgnoringBatteryOptimizations(packageName)) {
            startActivity(
                Intent(
                    Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                    Uri.parse("package:$packageName"),
                ),
            )
        } else {
            Toast.makeText(this, "이미 배터리 최적화가 해제되어 있습니다.", Toast.LENGTH_SHORT).show()
        }
    }

    private fun refresh() {
        val running = QuizService.isRunning(this)
        val overlay = Settings.canDrawOverlays(this)
        findViewById<TextView>(R.id.statusText).text = buildString {
            append(if (running) "실행 중  ·  문제 ${QuestionBank.size}개  ·  3분 간격" else "대기 중  ·  문제 ${QuestionBank.size}개")
            append('\n')
            append(if (overlay) "다른 앱 위에 표시: 허용됨" else "다른 앱 위에 표시: 필요함")
        }
        findViewById<Button>(R.id.startButton).isEnabled = !running
        findViewById<TextView>(R.id.statusText).setTextColor(
            ContextCompat.getColor(this, if (running) R.color.ok else R.color.muted),
        )
    }
}
