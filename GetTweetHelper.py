import requests
import re
import os

# Twitter API Bearer token

def get_tweet_content(tweet_url, BEARER_TOKEN):
    if tweet_url == "":
        return ""

    # Extract tweet ID from the URL
    tweet_id = re.search(r'status/(\d+)', tweet_url).group(1)
    
    # Twitter API endpoint
    url = f"https://api.twitter.com/2/tweets/{tweet_id}"
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }
    params = {
        "tweet.fields": "text"  # Fields we want to retrieve
    }
    
    # Make the request
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        tweet_data = response.json()
        return tweet_data['data']['text']
    else:
        return f"Error: {response.status_code} - {response.text}"

