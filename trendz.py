from openai import OpenAI
import subprocess
import base64
import os
from dotenv import load_dotenv
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os
import time
import requests
from pydub import AudioSegment
import simpleaudio as sa

# Function to open a file and return its contents as a string
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()
    
def save_file(filepath, content):
    with open(filepath, 'a', encoding='utf-8') as outfile:
        outfile.write(content)

# ANSI escape code for colors
PINK = '\033[95m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET_COLOR = '\033[0m'

# Set the OpenAI API key
api_key = open_file('openaiapikey2.txt')

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)

def get_mistral_response(user_content):
    """
    Interact with the Mistral API using a streaming approach. Print and return the response.
    """
    # Initialize the Mistral client with your API key
    api_key = open_file("mistapikey.txt")
    model = "mistral-medium"
    client = MistralClient(api_key=api_key)

    # Prepare a list of ChatMessage objects with the user's content
    messages = [ChatMessage(role="user", content=user_content)]

    # Initialize an empty string to accumulate responses
    accumulated_response = ""

    # Streaming approach
    try:
        for chunk in client.chat_stream(model=model, messages=messages):
            if chunk.choices:
                for choice in chunk.choices:
                    if choice.delta and choice.delta.content:
                        print(f"{CYAN}{choice.delta.content}{RESET_COLOR}", end='')
                        accumulated_response += choice.delta.content
    except Exception as e:
        print(f"An error occurred during streaming: {e}")

    return accumulated_response

def image_b64(image):
    with open(image, "rb") as f:
        return base64.b64encode(f.read()).decode()

def url2screenshot(url):
    print(f"{CYAN}Crawling {url}{RESET_COLOR}")

    if os.path.exists("screenshot.jpg"):
        os.remove("screenshot.jpg")

    result = subprocess.run(
        ["node", "screenshot.js", url],
        capture_output=True,
        text=True
    )

    if not os.path.exists("screenshot.jpg"):
        print("ERROR")
        return "Failed to scrape the website"
    
    # New Code: Open the screenshot.jpg file
    try:
        os_command = f'start screenshot.jpg'
        os.system(os_command)
    except Exception as e:
        print(f"An error occurred while opening the image: {e}")

    b64_image = image_b64("screenshot.jpg")
    return b64_image

def visionExtract(b64_image, prompt):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system",
                "content": "You a web scraper, your job is to extract the following information about Sports Game the image: 1. Score 2. Basic Statistics 3. The Best Performing Player (If applicable).  Use a structured format:",
            }
        ] + [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{b64_image}",
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ],
        max_tokens=1024,
    )

    message = response.choices[0].message
    message_text = message.content

    if "ANSWER_NOT_FOUND" in message_text:
        print("ERROR: Answer not found")
        return "I was unable to find the answer on that website. Please pick another one"
    else:
        print(f"{YELLOW}GPT: {message_text}{RESET_COLOR}")
        return message_text

def visionCrawl(url, prompt):
    b64_image = url2screenshot(url)

    print(f"{PINK}Image captured{RESET_COLOR}")
    
    if b64_image == "Failed to scrape the website":
        return "I was unable to crawl that site. Please pick a different one."
    else:
        return visionExtract(b64_image, prompt)

# Function for processing multiple URLs
def process_urls(urls, prompt):
    all_responses = []  # List to store all responses
    # Iterate through each URL
    for url in urls:
        print(f"{CYAN}Processing {url}...{RESET_COLOR}")
        response = visionCrawl(url, prompt)
        all_responses.append(response)
    return all_responses

def text_to_speech_and_download(text, download_path):
    CHUNK_SIZE = 1024
    url = "https://api.elevenlabs.io/v1/text-to-speech/(voice_id)"

    headers = {
      "Accept": "audio/mpeg",
      "Content-Type": "application/json",
      "xi-api-key": "YOUR ELEVEN LABS API KEY"
    }

    data = {
      "text": text,
      "model_id": "eleven_monolingual_v1",
      "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.5
      }
    }

    response = requests.post(url, json=data, headers=headers)

    # Ensure the response is valid
    if response.status_code != 200:
        print("Error: Unable to generate speech.")
        return

    file_path = os.path.join(download_path, 'output.mp3')
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)

    print(f"Downloaded MP3 file to {file_path}")
    
   

# List of URLs to process
urls_to_process = [
    "https://www.flashscore.com/match/zBKRXRu1/#/match-summary/player-statistics/0",
    "https://www.flashscore.com/match/vmsp802I/#/match-summary/match-statistics/0"
    # Add more URLs here...
]

# Prompt for the visionCrawl function
prompt = "Extract the following information about the Sports Game image: 1. Score 2. Basic Statistics 3. The Best Performing Player (If applicable).  Use a structured format:"

# Process the URLs
responses = process_urls(urls_to_process, prompt)

# Convert responses to a single string
responses_str = '\n'.join([resp for resp in responses if resp])

# Read the file and replace placeholder with the responses string
news_content = open_file("news.txt").replace("<<NEWS>>", responses_str)

# Get the response from Mistral
code = get_mistral_response(news_content)

download_folder = 'downloads'  # Ensure this folder exists or create it
text_to_speech_and_download(code, download_folder)


