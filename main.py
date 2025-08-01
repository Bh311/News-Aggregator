from flask import (
    Flask, render_template, request, redirect, url_for, session
)
from flask_session import Session
from datetime import datetime
from collections import defaultdict
from dateutil import parser                # still used for article dates
import os, uuid

# ---------- helpers ----------------------------------------------------------
from collectors.rss_collector     import collect_rss_feeds, extract_article_data
from collectors.twitter_collector import collect_tweets
from processors.summarizer        import summarize_texts
from emotion_detection.emotion_model import predict_emotion
from config import RSS_FEEDS, TWITTER_LIST_ID
from gtts import gTTS
# -----------------------------------------------------------------------------


app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# ---------------- emoji util -------------------------------------------------
def tag_emotion(text: str) -> str:
    try:
        return predict_emotion(text).lower()
    except Exception:
        return "unknown"


# ---------------- article date helper (only for display) ---------------------
def _parse_article_date(article: dict):
    for key in ("published", "published_at", "pubDate",
                "created_at", "updated", "date"):
        val = article.get(key)
        if not val:
            continue
        if isinstance(val, datetime):
            return val
        try:
            return parser.parse(val)
        except Exception:
            continue
    return None


def stamp_parsed_date(articles):
    for a in articles:
        a["published_dt"] = _parse_article_date(a)
# -----------------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


# ---------------- detect-emotion --------------------------------------------
@app.route("/detect-emotion", methods=["POST"])
def detect_emotion():
    user_input = request.form.get("text", "").strip()
    if not user_input:
        return redirect(url_for("index"))

    detected_emotion = tag_emotion(user_input)

    # history
    history = session.get("emotion_history", [])
    history.append(detected_emotion)
    session["emotion_history"] = history

    # collect news
    rss_articles     = collect_rss_feeds(RSS_FEEDS, max_articles_per_region=15)
    twitter_articles = collect_tweets(TWITTER_LIST_ID, max_tweets=10)
    all_articles     = rss_articles + twitter_articles

    # tag emotion per article
    for art in all_articles:
        art["emotion"] = tag_emotion(
            f"{art.get('title','')} {art.get('summary','')}"
        )

    # summarise
    summaries = summarize_texts(all_articles)

    # re-attach images
    link_to_img = {a["link"]: a.get("image") for a in all_articles}
    for s in summaries:
        s.setdefault("image", link_to_img.get(s.get("link")))

    stamp_parsed_date(summaries)
    session["last_summaries"] = summaries
    session["last_emotion"]   = detected_emotion

    # counts for analytics
    counts = defaultdict(int)
    for s in summaries:
        counts[s["emotion"]] += 1
    session["emotion_counts"] = dict(counts)

    # split
    matched   = [a for a in summaries if a["emotion"] == detected_emotion]
    unmatched = [a for a in summaries if a["emotion"] != detected_emotion]

    return render_template(
        "digest.html",
        matched   = matched,
        unmatched = unmatched,
        emotion   = detected_emotion,
        date      = datetime.now().strftime("%Y-%m-%d")
    )


# ---------------- digest (no filter) ----------------------------------------
@app.route("/digest")
def digest():
    summaries = session.get("last_summaries", [])
    emotion   = session.get("last_emotion", "neutral")

    matched   = [a for a in summaries if a.get("emotion") == emotion]
    unmatched = [a for a in summaries if a.get("emotion") != emotion]

    return render_template(
        "digest.html",
        matched   = matched,
        unmatched = unmatched,
        emotion   = emotion,
        date      = datetime.now().strftime("%Y-%m-%d")
    )


@app.route("/analytics")
def analytics():
    return render_template(
        "analytics.html",
        emotion_history = session.get("emotion_history", []),
        emotion_counts  = session.get("emotion_counts", {})
    )


# ---------------- article view / audio  -------------------------------------
@app.route("/article")
def article_view():
    url = request.args.get("url")
    if not url:
        return "Missing url parameter", 400
    try:
        data = extract_article_data(url)
    except Exception as err:
        return f"Failed to fetch article: {err}", 500
    return render_template("article.html", article=data)


@app.route("/download-audio")
def download_audio():
    summaries = [
        a["summary"] for a in session.get("last_summaries", [])
        if a["emotion"] == session.get("last_emotion", "neutral")
    ]
    if not summaries:
        return "No summaries available.", 400

    fname = f"audio_digest_{uuid.uuid4().hex}.mp3"
    path  = os.path.join("static", "audio", fname)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        gTTS(text=". ".join(summaries), lang="en").save(path)
    except Exception as e:
        return f"Audio generation failed: {e}", 500
    return redirect(url_for("static", filename=f"audio/{fname}"))


@app.route("/article/<path:url>")
def show_article(url):
    data = extract_article_data(url)
    return render_template(
        "article.html",
        title     = data.get("title", "Untitled"),
        summary   = data.get("summary", ""),
        text      = data.get("text", ""),
        image_url = data.get("top_image") or "/static/images/default.jpg",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
