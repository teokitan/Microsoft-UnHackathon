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

st.set_page_config(page_title="TruthGuard", page_icon="🔍")
st.title("🔍 TruthGuard: Verify Tweets for Trust")
st.subheader("Identify potential scams and fake news in tweets before you trust them.")
st.write("Enter a tweet below, and TruthGuard will check if it’s safe, a scam, or fake news based on reliable sources.")

st.markdown("---")
st.write("### Analyze a Tweet")
tweet = st.text_area("Enter a tweet to analyze", key="tweet_input", height=100)

if st.button("Classify"):
    if tweet.strip() == "":
        st.error("Please enter a tweet!")
    else:
        # Step 1: Initial classification and keyword extraction
        classification = classify_tweet(tweet)

        if classification == "fake-news":
            # Step 2: Search Wikipedia and fetch content
            wikipedia_result = search_and_fetch_wikipedia_content(tweet)

            if wikipedia_result["status"] == "found":
                # Step 3: Verify content with AI
                verification_result = verify_with_wikipedia_content(tweet, wikipedia_result["content"])

                if "refute" in verification_result.lower():
                    st.error("🚨 This tweet contains claims or elements that are likely to be fake news based on Wikipedia.")
                    st.write("For more information, check this Wikipedia article:")
                    st.write(wikipedia_result["link"])
                else:
                    st.success("✅ This tweet appears safe based on Wikipedia verification.")
                    st.write("You may find relevant information here:")
                    st.write(wikipedia_result["link"])
            else:
                st.warning("⚠️ This tweet contains some claims or elements that could not be verified; no relevant Wikipedia article was found.")
        elif classification == "scam":
            st.error("🚨 This tweet may be a scam.")
        else:
            st.success("✅ This tweet appears safe.")

st.markdown("---")
# Example Tweets
st.write("### Try these example tweets:")
example_tweets = [
    "The Earth is flat and NASA is hiding the truth.",
    "Congratulations! You've won a $1,000 gift card. Click here to claim it.",
    "I think Pepsi is better than Coke."
]

# Function to update the main text input with an example tweet
def use_example(exampleTweet):
    st.session_state["tweet_input"] = exampleTweet

# Buttons for each example tweet
for tweet in example_tweets:
    st.button(tweet, on_click=use_example, args=(tweet,))

with st.sidebar:
    st.header("About TruthGuard")
    st.write("TruthGuard analyzes tweets for accuracy and reliability. "
             "It flags tweets as safe, scams, or fake news by verifying content against trusted sources.")
    st.write("**Get started by entering a tweet on the main screen.**")
        
st.markdown("---")
st.write("**Developed by TEAM 7** | [Contact Us](mailto:support@example.com)")
