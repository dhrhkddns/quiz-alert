package com.quizalert.electrical

import android.app.Application
import android.content.Context
import org.json.JSONObject
import java.security.MessageDigest

class QuizApp : Application() {
    override fun onCreate() {
        super.onCreate()
        QuestionBank.load(this)
    }
}

object QuestionBank {
    var intervalMs: Long = 3 * 60 * 1000L
        private set
    private val all = mutableListOf<Question>()
    private val remaining = mutableListOf<Question>()
    private var appContext: Context? = null

    val size: Int get() = all.size

    fun load(context: Context) {
        if (all.isNotEmpty()) return
        appContext = context.applicationContext
        val text = try {
            context.assets.open("questions.json").bufferedReader(Charsets.UTF_8).use { it.readText() }
        } catch (_: Exception) {
            return
        }
        val root = JSONObject(text)
        intervalMs = (root.optDouble("interval_minutes", 3.0) * 60_000).toLong().coerceAtLeast(10_000)
        val arr = root.getJSONArray("questions")
        val seen = linkedSetOf<String>()
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            val qText = o.getString("q").trim()
            if (qText.isEmpty() || qText in seen) continue
            seen += qText
            val choices = o.getJSONArray("choices")
            val list = buildList {
                for (c in 0 until choices.length()) add(choices.getString(c))
            }
            all += Question(
                source = o.optString("source"),
                q = qText,
                choices = list,
                answer = o.getInt("answer"),
                explain = o.optString("explain"),
                visual = o.optString("visual"),
                caption = o.optString("caption"),
            )
        }
        restoreRemaining()
    }

    fun next(): Question {
        if (remaining.isEmpty()) refill()
        val q = remaining.removeAt((0 until remaining.size).random())
        persistRemaining()
        return q
    }

    fun shuffleRemaining() {
        if (remaining.isEmpty()) {
            refill()
            return
        }
        remaining.shuffle()
        persistRemaining()
    }

    private fun questionKey(q: Question) = q.q.trim()

    private fun bankSignature(): String {
        val blob = all.map { questionKey(it) }.sorted().joinToString("\n")
        val digest = MessageDigest.getInstance("SHA-256").digest(blob.toByteArray(Charsets.UTF_8))
        return digest.joinToString("") { "%02x".format(it) }.take(20)
    }

    private fun restoreRemaining() {
        val ctx = appContext ?: return
        val prefs = QuizService.prefs(ctx)
        val sig = prefs.getString(KEY_BANK_SIG, null)
        val saved = prefs.getStringSet(KEY_REMAINING, null)
        remaining.clear()
        if (sig == bankSignature() && !saved.isNullOrEmpty()) {
            val map = all.associateBy { questionKey(it) }
            remaining.addAll(saved.mapNotNull { map[it] }.shuffled())
            if (remaining.isNotEmpty()) return
        }
        refill()
    }

    private fun persistRemaining() {
        val ctx = appContext ?: return
        QuizService.prefs(ctx).edit()
            .putString(KEY_BANK_SIG, bankSignature())
            .putStringSet(KEY_REMAINING, remaining.map { questionKey(it) }.toSet())
            .apply()
    }

    private fun refill() {
        remaining.clear()
        remaining.addAll(all.shuffled())
        persistRemaining()
    }

    private const val KEY_BANK_SIG = "bank_sig"
    private const val KEY_REMAINING = "remaining_keys"
}
