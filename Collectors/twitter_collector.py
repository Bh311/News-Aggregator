import tweepy
import time
from config import (
    TWITTER_API_KEY, 
    TWITTER_API_SECRET, 
    TWITTER_ACCESS_TOKEN, 
    TWITTER_ACCESS_TOKEN_SECRET
)

def collect_tweets(list_id, max_tweets=10):
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    tweets = []
    try:
        timeline = api.list_timeline(list_id=list_id, count=max_tweets)
        for tweet in timeline:
            tweets.append({
                'title': f"Tweet from {tweet.author.name}",
                'text': tweet.text,
                'link': f"https://twitter.com/{tweet.author.screen_name}/status/{tweet.id}",
                'source': 'Twitter',
                'date': tweet.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
            time.sleep(1)  # Optional: to reduce rate limit risk
    except tweepy.TweepyException as e:
        print(f"Error collecting tweets: {e}")
    
    return tweets
