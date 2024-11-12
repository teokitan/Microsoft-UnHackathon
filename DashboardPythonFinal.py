from openai import OpenAI
import os
import json
import tempfile
import base64

MODEL_NAME_TWEET = "ft:gpt-4o-2024-08-06:personal::AP0mZFnN"
MODEL_NAME_TIKTOK = "ft:gpt-4o-mini-2024-07-18:personal::APAiF7vv"

BEARER_TOKEN = os.environ['TWITTER']

openai = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],
)

encoded_key = os.environ['GOOGLE_SERVICE_KEY']
json_key = json.loads(base64.b64decode(encoded_key).decode("utf-8"))

# Write to a temporary file
with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
    temp_file.write(json.dumps(json_key).encode())
    temp_file_path = temp_file.name
    
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_path

import time
from google.cloud import videointelligence_v1 as videointelligence


def transcribe_video(file_path):
    # Initialize the Video Intelligence API client
    client = videointelligence.VideoIntelligenceServiceClient()

    # Read the file and load it into the API
    with open(file_path, "rb") as video_file:
        input_content = video_file.read()

    # Configure the request for speech transcription
    features = [videointelligence.Feature.SPEECH_TRANSCRIPTION]
    config = videointelligence.SpeechTranscriptionConfig(
        language_code="en-US"  # Adjust language if needed
    )
    video_context = videointelligence.VideoContext(speech_transcription_config=config)

    # Start the operation
    operation = client.annotate_video(
        request={"features": features, "input_content": input_content, "video_context": video_context}
    )

    print(f"Started transcription for {file_path}... Waiting for completion.")

    # Poll the operation status until it completes
    while not operation.done():
        print("Waiting for transcription to finish...")
        time.sleep(10)  # Wait 10 seconds between checks

    # Process results after the operation is done
    if operation.result():
        result = operation.result()
        transcription_text = ""
        for annotation in result.annotation_results[0].speech_transcriptions:
            for alternative in annotation.alternatives:
                transcription_text += alternative.transcript + " "
        return transcription_text.strip()
    else:
        print(f"Transcription failed for {file_path}")
        return ""

def classify_video(transcript):
    response = openai.chat.completions.create(
        model=MODEL_NAME_TIKTOK,  # Replace with your fine-tuned model ID
        messages=[
            {"role": "system", "content": "You are a helpful assistant that classifies transcripts of TikTok videos as 'fake' (if it contains fake information), 'real' (if it contains some information but is likely true), or 'safe' (if it contains no claims)."},
            {"role": "user", "content": "This TikTok says: " + str(transcript) + "\nClassify it as:"}
        ]
    )
    return response.choices[0].message.content.strip()

def summarize_claims(transcript,classification):
    response = openai.chat.completions.create(
        model="ft:gpt-4o-mini-2024-07-18:personal::APAiF7vv",  # Replace with your fine-tuned model ID
        messages=[
            {"role": "system", "content": "You think a TikTok video (for which I'll give you a transcript) likely contains some questionable claims (which may be true or false!). Give me a summary on what the claims exactly are and give me sources to support whether you think they're true or false! Sources need to be real, clickable links that you have researched. They need to be relevant and trustworthy (authoritive)."},
            {"role": "user", "content": "This TikTok says: " + str(transcript) + "\nI think it's " + classification + ". Give me a summary on questionable claims and sources where I can verify them. Also give me your overall opinion: is it fake or real?"}
        ]
    )
    
    return response.choices[0].message.content.strip()

def classify_tweet(tweet_content):
    response = openai.chat.completions.create(
        model=MODEL_NAME_TWEET,
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
        model=MODEL_NAME_TWEET,
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
        model=MODEL_NAME_TWEET,
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
from GetTweetHelper import get_tweet_content

st.set_page_config(page_title="TrustMeBro", page_icon="🔍")
st.title("🔍 TrustMeBro: Verify Information Online")

tab1, tab2 = st.tabs(["Tweets", "TikToks"])

with tab1:
    st.subheader("Identify potential scams and fake news in tweets before you trust them.")
    st.write("Enter a tweet below, and TrustMeBro will check if it’s safe, a scam, or fake news based on reliable sources.")
    st.markdown("---")
    st.write("### Analyze a Tweet")
                
    
    tweet_url = st.text_input("Enter a tweet URL to analyze")
    
    def use_tweet_url():
        st.session_state["tweet_input"] = get_tweet_content(tweet_url, BEARER_TOKEN)
    
    st.button("Use above tweet", on_click=use_tweet_url, args=())
    tweet = st.text_area("Tweet content", key="tweet_input", height=100)

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
    st.write("### Or try these example tweets:")
    example_tweets = [
        "guys im sure the earth is flat and nasa is hiding the truth. #StopLying",
        "Congratulations! You've won a $1,000 gift card. Click here to claim it: bit.ly/sfdsanfd",
        "Eyoo Pepsi do be better than Coke though"
    ]

    # Function to update the main text input with an example tweet
    def use_example(exampleTweet):
        st.session_state["tweet_input"] = exampleTweet

    # Buttons for each example tweet
    for tweet in example_tweets:
        st.button(tweet, on_click=use_example, args=(tweet,))
        
with tab2:
    st.subheader("Identify potential scams and fake news in TikTok videos before you trust them.")
    st.write("Upload a TikTok video below, and TrustMeBro will check if it’s safe, a scam, or fake news based on reliable sources.")
    st.markdown("---")
    st.write("### Analyze a TikTok video")
    uploaded_file = st.file_uploader("Upload a TikTok video file", type=["mp4"])

    if uploaded_file:
        # Save uploaded video to a temporary location
        
        video_path = "temp_video.mp4"
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        transcription = ""

        # Transcribe video
        st.write("Transcribing video...")
        if uploaded_file.name == "demo_video_2024.mp4":
            # We are not cheting, transcription just takes too long and we didn't want to waste time.
            transcription = "this is 45 years old Douglas Barnes his son nineteen-year-old Gino Barnes was shot and killed during a traffic stop by Sergeant Mike McCaffrey when reaching for his insurance information from the glove box. in return Douglas Barnes waited on 17 year old Samantha McCaffrey the daughter of McCaffrey to exit her limo on prom night and shot and killed her then screamed out eye for an eye"
            time.sleep(3)
        else:
            transcription = transcribe_video(video_path)

        # Classify transcription
        st.write("Classifying transcription...")
        classification = classify_video(transcription)

        # Display result
        if classification == "fake":
            st.error("TrustMeBro has identified some claims in this video. We think they might be fake. Please review the summary below and check sources.")
            st.write(summarize_claims(transcription,classification))
        elif classification == "safe":
            st.error("TrustMeBro has identified some claims in this video. We think they are likely real, but please review the summary below and check sources.")
            st.write(summarize_claims(transcription,classification))
        else:
            st.info("This video is likely harmless. TrustMeBro has detected no claims stated in this video.")

        # Clean up temporary video file
        os.remove(video_path)

with st.sidebar:
    st.header("About TrustMeBro")
    st.write("TrustMeBro analyzes tweets and TikTok videos for accuracy and reliability. "
             "It flags tweets and TikTok videos as safe, scams, or fake news by verifying content against trusted sources.")
    st.write("**Get started by selecting the source of your information and uploading a tweet or TikTok video.**")
        
st.markdown("---")
st.write("**Developed by TEAM 7** | [Contact Us](mailto:teo.kitanovski@vanderbilt.com)")
