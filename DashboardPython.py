from openai import OpenAI
import os

openai = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],
)

import streamlit as st
import pandas as pd

# Function to classify tweet using OpenAI API
def classify_tweet(tweet_content):
    response = openai.chat.completions.create(
        model="ft:gpt-4o-2024-08-06:personal::AOzWrfwn",  # REPLACE LATER
        messages=[
            {"role": "system", "content": "You are a helpful assistant that classifies tweets as either safe or scam."},
            {"role": "user", "content": "This tweet says: '" + tweet_content + "'\nClassify it as:"}
        ]
    )
    
    return (response.choices[0].message.content)

# Streamlit Dashboard Interface
st.title("Tweet Classification Dashboard")

# Input fields for classifying a new tweet
st.subheader("Classify a New Tweet")
tweet_content = st.text_area("Tweet Content")

if st.button("Classify Tweet"):
    if tweet_content:
        classification = classify_tweet(tweet_content)
        st.write("**Classification:**", classification)
    else:
        st.error("Please enter tweet content to classify.")
