import os
import warnings
from dotenv import load_dotenv
from src.youtube_retriever import YoutubeRetriever
from langchain.chains import LLMChain
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

# Load environment variables from .env file
warnings.filterwarnings("ignore")
load_dotenv()

# Retrieve API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not OPENAI_API_KEY or not YOUTUBE_API_KEY:
    raise ValueError("Missing API keys. Please ensure OPENAI_API_KEY and YOUTUBE_API_KEY are set in the .env file.")

# Load YouTube handles from a file
handles_file = "handles.txt"
if not os.path.exists(handles_file):
    raise FileNotFoundError(f"Handles file not found: {handles_file}")

with open(handles_file, "r") as file:
    handles = [line.strip() for line in file if line.strip()]

if not handles:
    raise ValueError("No handles found in the file. Please add handles line by line in 'handles.txt'.")

# Initialize YoutubeRetriever
retriever = YoutubeRetriever(api_key=YOUTUBE_API_KEY)

# Retrieve channel IDs
channel_ids = retriever.get_channel_ids(handles)
print("Channel IDs:", channel_ids)

# Retrieve video details
video_details_list = retriever.get_video_details(list(channel_ids.values()))

# Format video details for the LangChain prompt
video_details = "\n".join(
    f"Title: {video['title']}, Views: {video['views']}, Channel ID: {video['channel_id']}"
    for video in video_details_list
)

print("\nVideo Details:")
print(video_details)

# Initialize LangChain with OpenAI's GPT model
llm = ChatOpenAI(model="gpt-4", temperature=0.7, openai_api_key=OPENAI_API_KEY)

# Define the LangChain prompt
context_prompt = PromptTemplate(
    input_variables=["video_details"],
    template=(
        "Analyze the following list of video titles and their respective view counts:\n"
        "{video_details}\n\n"
        "Based on this information, explain what this YouTube channel is about. "
        "Describe the themes, the type of audience it targets, and the writing style used in the titles. "
        "Be as detailed as possible."
    )
)

# Define the LangChain
channel_context_chain = LLMChain(llm=llm, prompt=context_prompt)

# Generate channel context using LangChain
channel_context = channel_context_chain.run({"video_details": video_details})
print("\nChannel Context:")
print(channel_context)
