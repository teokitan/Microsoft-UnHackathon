from openai import OpenAI
import os

MODEL_NAME_TIKTOK = "ft:gpt-4o-mini-2024-07-18:personal::APAiF7vv"

openai = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],
)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/teo/Downloads/psyched-freedom-182221-658209fdfd55.json"

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


import streamlit as st

st.title("Video Fact Checker")

# Video upload
uploaded_file = st.file_uploader("Upload a video file", type=["mp4"])

if uploaded_file:
    # Save uploaded video to a temporary location
    video_path = "temp_video.mp4"
    with open(video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Transcribe video
    st.write("Transcribing video...")
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
