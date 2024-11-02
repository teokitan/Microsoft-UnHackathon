from openai import OpenAI
import os

MODEL_NAME = "ft:gpt-4o-2024-08-06:personal::AP0mZFnN"



openai = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],
)

def classify_tweet(tweet_content):
    response = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that classifies tweets as either safe, scam, or fake-news."},
            {"role": "user", "content": "This tweet says: '" + tweet_content + "'\nClassify it as:"}
        ]
    )
    
    classification =  (response.choices[0].message.content)

    return classification

import wikipediaapi

def search_and_fetch_wikipedia_content(tweet_content):
    response = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a verifier that, given a tweet that may contain fake news, identifies what parts may be problematic and finds the Wikipedia article that is most likely related to the questionable claim. Go through the Wikipedia website, confirm it exists, and give me ONLY the real Wikipedia title of the article."},
            {"role": "user", "content": "Here is a tweet to verify: " + tweet + ". Give me a Wikipedia article title where I can confirm the questionable claim in the tweet: " + tweet_content}
        ],
        max_tokens=50,
        temperature=0
    )

    article_title = response.choices[0].message.content.strip()

    # Search and fetch content
    wiki_wiki = wikipediaapi.Wikipedia('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0')
    page = wiki_wiki.page(article_title)
    if page.exists():
        return {"status": "found", "content": page.text[:60000], "link": page.fullurl}  # Limit content to first 60.000 characters
    else:
        return {"status": "not_found", "content": None, "link": None}
        
def verify_with_wikipedia_content(tweet, wikipedia_content):
    if not wikipedia_content:
        return "not_verified"

    response = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a verifier that checks if the content of a tweet is accurate based on reliable information from Wikipedia. Respond simply with confirm (if the article confirms it), or refute (if the article refutes it or is not clear). Say confirm only if you are absolutely sure."},
            {"role": "user", "content": "Here is a tweet to verify: " + str(tweet) + ". Does the following Wikipedia content confirm or refute it? Respond with 'confirm' or 'refute': " + str(wikipedia_content)}
        ],
        max_tokens=10,
        temperature=0
    )
    verification = response.choices[0].message.content.strip()
    return verification


import streamlit as st

tweet = st.text_area("Enter a tweet:")
if st.button("Classify"):
    # Step 1: Initial classification and keyword extraction
    classification = classify_tweet(tweet)

    if classification == "fake-news":
        # Step 2: Search Wikipedia and fetch content
        wikipedia_result = search_and_fetch_wikipedia_content(tweet)

        if wikipedia_result["status"] == "found":
            # Step 3: Verify content with AI
            verification_result = verify_with_wikipedia_content(tweet, wikipedia_result["content"])

            if "refute" in verification_result.lower():
                st.error("⚠️ This tweet is confirmed as fake news based on Wikipedia.")
                st.write("For more information, check this Wikipedia article:")
                st.write(wikipedia_result["link"])
            else:
                st.success("✅ This tweet appears safe based on Wikipedia verification.")
                st.write("You may find relevant information here:")
                st.write(wikipedia_result["link"])
        else:
            st.warning("⚠️ This tweet could not be verified as fake news; no relevant Wikipedia article was found.")
    elif classification == "scam":
        st.error("⚠️ This tweet may be a scam.")
    else:
        st.success("✅ This tweet appears safe.")

