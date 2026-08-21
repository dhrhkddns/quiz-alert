package com.quizalert.electrical

data class Question(
    val source: String,
    val q: String,
    val choices: List<String>,
    val answer: Int,
    val explain: String,
    val visual: String,
    val caption: String,
)
