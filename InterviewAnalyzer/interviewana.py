import os
import json
import re
from flask import Flask, request, render_template

app = Flask(__name__)

# ====== Load JSON Data ======
JSON_FILE_NAME = os.path.join(os.path.dirname(__file__), "mock_interview_questions.json")
interview_data = []

try:
    with open(JSON_FILE_NAME, 'r', encoding='utf-8') as f:
        full_data = json.load(f)
        if isinstance(full_data, dict) and "questions" in full_data:
            interview_data = full_data["questions"]
        elif isinstance(full_data, list):
            interview_data = full_data
        else:
            print("⚠️ JSON structure not recognized.")
except Exception as e:
    print(f"❌ Failed to load JSON: {e}")

# ====== Sentiment Map ======
sentiment_map = {
    "confident": {"confident", "solved", "achieved", "responsible", "initiated", "led"},
    "anxious": {"nervous", "unsure", "doubt", "scared", "tense"},
    "vague": {"some", "many", "sometimes", "usually", "often"},
    "passionate": {"love", "excited", "enthusiastic", "passionate"},
    "arrogant": {"best", "perfect", "flawless", "superior"},
    "humble": {"learn", "improve", "grow", "grateful"},
    "negative": {"fail", "problem", "weak", "stress", "mistake"},
    "neutral": {"work", "experience", "interview", "project"}
}

# ====== Analyzer Function ======
def analyze_answer(answer):
    words = re.findall(r'\b\w+\b', answer.lower())
    word_count = len(words)
    sentence_count = len(re.findall(r'[.!?]', answer))
    sentiment_counts = {label: 0 for label in sentiment_map}
    highlight_words = []

    for word in words:
        for label, word_set in sentiment_map.items():
            if word in word_set:
                sentiment_counts[label] += 1
                highlight_words.append((word, label))

    dominant = max(sentiment_counts, key=lambda k: sentiment_counts[k])
    score = sentiment_counts[dominant]
    tone_strength = min(10, score + (word_count // 20))

    suggestions = []
    if word_count < 40:
        suggestions.append("⚠️ Your answer is too short. Aim for more depth and detail.")
    if sentiment_counts["vague"] > 2:
        suggestions.append("✏️ Avoid vague language. Use specific examples.")
    if sentiment_counts["arrogant"] > 1:
        suggestions.append("🤏 Watch for overconfidence — stay professional.")
    if sentiment_counts["humble"] < 1:
        suggestions.append("🌱 Include mentions of learning or growth.")
    if sentiment_counts["negative"] > 2:
        suggestions.append("🚫 Reframe negativity. Show how you overcame issues.")
    if sentiment_counts["passionate"] < 1:
        suggestions.append("💡 Express your enthusiasm for the topic or role.")
    if sentence_count < 3:
        suggestions.append("📌 Try to structure your response into clear sentences.")

    professionalism_score = 100 - len(suggestions) * 10 + tone_strength * 2
    professionalism_score = max(0, min(professionalism_score, 100))

    return {
        "Dominant Sentiment": dominant,
        "Tone Strength": tone_strength,
        "Sentiment Counts": sentiment_counts,
        "Keyword Highlights": highlight_words,
        "Suggestions": suggestions,
        "Total Words": word_count,
        "Sentence Count": sentence_count,
        "Professionalism Score": professionalism_score,
        "Original Answer": answer.strip()
    }

# ====== Web App Routes ======
@app.route('/', methods=['GET', 'POST'])
def index():
    result = None

    # Filter and prepare sample answers from dataset (at least 4-line responses)
    sample_answers = []
    for item in interview_data:
        if "answer" in item and len(item["answer"].split()) >= 60:
            sample_answers.append(item["answer"])
        if len(sample_answers) >= 3:
            break

    if request.method == 'POST':
        answer = request.form['answer']
        result = analyze_answer(answer)

    return render_template('index.html', result=result, samples=sample_answers)

if __name__ == '__main__':
    app.run(debug=True)
