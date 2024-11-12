## TrustMeBro - Scam & Misinformation Detector

TrustMeBro is a fake news and scam detection system that leverages GPT-4 to verify the credibility of tweets and TikTok videos. It was built for the Microsoft "Accelerate Your AI" Hackathon 2024 in Atlanta, where it was also awarded the third place.

### Features:
- Social Media Post Extraction: Pulls tweets using the X api and can transcribe Tiktoks using the Google Cloud API
- Fine-Tuned Models: Two GPT-4 models were fine-tuned in order to achieve high accuracy when detecting the type of potential threat
- Keyword Extraction: Automatically extracts key claims from a tweet or video in order to ascertain their validity
- Wikipedia/Online Source Retrieval: Fetches summaries from Wikipedia or other online sources for relevant topics
- Credibility Analysis: Uses GPT-4 to classify the tweet as "credible" or "fake news" based on Wikipedia information
- Supporting Links: Provides source links if the tweet is flagged as potentially fake news

### Usage:
- TrustMeBro is hosted as a Streamlit app, accessible at [trustmebro.streamlit.app](https://trustmebro.streamlit.app)
- You can also clone and install the repository on your computer. In order to do so, note that you will require the `openai`, `wikipedia-api` and `google-cloud-videointelligence` Python packages

### Examples:
![TweetFakeNewsExample](https://github.com/user-attachments/assets/36a3c652-d5d9-4b09-a38d-90ab121b6f9e)
![TweetScamExample](https://github.com/user-attachments/assets/fb52c997-44f3-401c-b42e-b35e77f3a99d)
