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

# Define the LangChain prompt for channel context
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

# Define the Chain for generating channel context
channel_context_chain = LLMChain(llm=llm, prompt=context_prompt)

# Generate channel context using LangChain
channel_context = channel_context_chain.run({"video_details": video_details})
print("\nChannel Context:")
print(channel_context)

# Define the LangChain prompt for video idea generation
video_idea_prompt = PromptTemplate(
    input_variables=["channel_context", "video_details", "recent_titles"],
    template=(
        "Based on the following channel context:\n"
        "{channel_context}\n\n"
        "And the following list of video titles and their respective view counts:\n"
        "{video_details}\n\n"
        "Also consider these recent video titles to avoid repetition:\n"
        "{recent_titles}\n\n"
        "Suggest a new, creative video idea with a focus on maximizing views and interest. "
        "The idea should be unique and engaging. Provide only the title of the video."
    )
)

# Define the Chain for generating video ideas
video_idea_chain = LLMChain(llm=llm, prompt=video_idea_prompt)

# Ensure the data folder exists
data_folder = "data"
os.makedirs(data_folder, exist_ok=True)

# Path for recent_titles.txt
recent_titles_file = os.path.join(data_folder, "recent_titles.txt")

# Check if the file exists, and create it if not
if not os.path.exists(recent_titles_file):
    with open(recent_titles_file, "w") as file:
        pass

# Read recent video titles from the file
with open(recent_titles_file, "r") as file:
    recent_titles = [line.strip() for line in file if line.strip()]

recent_titles_str = "\n".join(recent_titles) if recent_titles else "None"

# Generate a new video idea
new_video_title = video_idea_chain.run({
    "channel_context": channel_context,
    "video_details": video_details,
    "recent_titles": recent_titles_str
})
print("\nNew Video Title:")
print(new_video_title)

# Update the recent titles file to maintain only the last 10 titles
recent_titles.append(new_video_title.strip())
recent_titles = recent_titles[-10:]  # Keep only the last 10 titles

with open(recent_titles_file, "w") as file:
    file.write("\n".join(recent_titles))
