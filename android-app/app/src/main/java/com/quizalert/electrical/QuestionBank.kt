package com.quizalert.electrical

import android.app.Application
import android.content.Context
import org.json.JSONObject

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

    val size: Int get() = all.size

    fun load(context: Context) {
        if (all.isNotEmpty()) return
        val text = context.assets.open("questions.json").bufferedReader(Charsets.UTF_8).use { it.readText() }
        val root = JSONObject(text)
        intervalMs = (root.optDouble("interval_minutes", 3.0) * 60_000).toLong().coerceAtLeast(10_000)
        val arr = root.getJSONArray("questions")
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            val choices = o.getJSONArray("choices")
            val list = buildList {
                for (c in 0 until choices.length()) add(choices.getString(c))
            }
            all += Question(
                source = o.optString("source"),
                q = o.getString("q"),
                choices = list,
                answer = o.getInt("answer"),
                explain = o.optString("explain"),
                visual = o.optString("visual"),
                caption = o.optString("caption"),
            )
        }
        refill()
    }

    fun next(): Question {
        if (remaining.isEmpty()) refill()
        return remaining.removeAt(remaining.lastIndex)
    }

    private fun refill() {
        remaining.clear()
        remaining.addAll(all.shuffled())
    }
}
