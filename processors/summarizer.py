from transformers import pipeline

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def summarize_texts(items):
    items = items[:30]
    summarized_items = []
    for item in items:
        title = item.get('title', 'No Title')
        text = item.get('text', '')
        summary_text = item.get('summary', '')
        link = item.get('link', '#')
        source = item.get('source', 'Unknown')
        emotion = item.get('emotion', 'unknown')

        text_to_summarize = summary_text or text or title
        text_to_summarize = text_to_summarize[:500]

        try:
            summary = summarizer(text_to_summarize, max_length=50, min_length=25, do_sample=False)
            summary_output = summary[0]['summary_text']
        except Exception as e:
            summary_output = text_to_summarize[:60] + '...' if len(text_to_summarize) > 60 else text_to_summarize

        summarized_items.append({
            'title': title,
            'summary': summary_output,
            'link': link,
            'source': source,
            'emotion': emotion
        })

    return summarized_items
