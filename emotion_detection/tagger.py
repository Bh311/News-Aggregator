# tagger.py

from emotion_model import predict_emotion

def tag_news_with_emotion(news_list):
    """
    Takes a list of news articles (each as a string) and returns a list of dicts with text and emotion.
    """
    tagged = [[
    {"text": "Some news headline", "emotion": "joy"},
    {"text": "Another headline", "emotion": "anger"},
    ...
]
]
    for article in news_list:
        emotion = predict_emotion(article)
        tagged.append({"text": article, "emotion": emotion})
    return tagged
