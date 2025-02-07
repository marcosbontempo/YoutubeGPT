import os
import warnings
from dotenv import load_dotenv
from youtube_retriever import YoutubeRetriever
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

class ScriptGenerator:
    def __init__(self):
        # Suppress warnings
        warnings.filterwarnings("ignore")

        # Load environment variables from the .env file
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
        load_dotenv(dotenv_path=env_path)

        # Retrieve API keys from environment variables
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

        if not self.OPENAI_API_KEY or not self.YOUTUBE_API_KEY:
            raise ValueError("Missing API keys. Please ensure OPENAI_API_KEY and YOUTUBE_API_KEY are set in the .env file.")

        # Initialize YoutubeRetriever
        self.retriever = YoutubeRetriever(api_key=self.YOUTUBE_API_KEY)
        
        # Initialize LangChain model
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1, openai_api_key=self.OPENAI_API_KEY)
        
        # Define memory to keep track of previous interactions
        self.memory = ConversationBufferMemory(return_messages=True, input_key="combined_input")

    def retrieve_video_details(self, handles_file="handles.txt"):
        """
        Retrieve channel IDs and video details from YouTube based on the handles file.
        """
        if not os.path.exists(handles_file):
            raise FileNotFoundError(f"Handles file not found: {handles_file}")

        with open(handles_file, "r") as file:
            handles = [line.strip() for line in file if line.strip()]

        if not handles:
            raise ValueError("No handles found in the file. Please add handles line by line in 'handles.txt'.")

        # Retrieve channel IDs
        channel_ids = self.retriever.get_channel_ids(handles)
        print("Channel IDs:", channel_ids)

        # Retrieve video details
        video_details_list = self.retriever.get_video_details(list(channel_ids.values()))

        video_details = "\n".join(
            f"Title: {video['title']}, Views: {video['views']}, Channel ID: {video['channel_id']}"
            for video in video_details_list
        )

        print("\nVideo Details:")
        print(video_details)

        return video_details

    def generate_channel_context(self, video_details):
        """
        Generate the channel context based on video details.
        """
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

        # Create chain for generating channel context
        channel_context_chain = LLMChain(llm=self.llm, prompt=context_prompt)

        # Generate channel context using LangChain
        channel_context = channel_context_chain.run({"video_details": video_details})
        print("\nChannel Context:")
        print(channel_context)

        return channel_context

    def generate_unique_video_title(self, recent_titles_file="data/recent_titles.txt"):
        """
        Generate a unique video title, ensuring it doesn't repeat recent titles.
        """
        # Ensure the directory exists for storing recent titles
        os.makedirs(os.path.dirname(recent_titles_file), exist_ok=True)

        # Load recent titles
        if os.path.exists(recent_titles_file):
            with open(recent_titles_file, "r") as file:
                recent_titles = [line.strip() for line in file if line.strip()]
        else:
            recent_titles = []

        # Define prompt to generate a unique video title
        unique_title_prompt = PromptTemplate(
            input_variables=["recent_titles"],
            template=(
                "Generate a unique and engaging YouTube video title that is between 60-70 characters long. "
                "Avoid excessive punctuation or symbols. The title should be clear, concise, and relevant to the content. "
                "Make sure it is different from the following recent titles:\n"
                "{recent_titles}\n\n"
                "Think about what would catch the audience's attention while remaining true to the content."
                "Ensure the title is no longer than 70 characters and no shorter than 60 characters. "
                "If the title goes over 70 characters, adjust it slightly without losing its meaning. "
                "If the title is under 60 characters, make it slightly longer but still relevant."                
            )
        )

        # Create chain for generating a unique video title
        title_chain = LLMChain(llm=self.llm, prompt=unique_title_prompt)

        # Generate a new video title
        recent_titles_str = "\n".join(recent_titles) if recent_titles else "None"
        video_title = title_chain.run({"recent_titles": recent_titles_str, "max_tokens": 10}).strip()

        # Ensure the new title is added to the recent titles list and keep only the last 10
        recent_titles.append(video_title)
        recent_titles = recent_titles[-10:]

        # Save updated recent titles back to the file
        with open(recent_titles_file, "w") as file:
            file.write("\n".join(recent_titles))

        with open("tmp/paragraphs/video_title.txt", "w") as file:
            file.write(video_title.strip('\"'))            

        print("\nGenerated Video Title:", video_title)

        return video_title
    
    def generate_seo_description(self):
        """Generate SEO description directly from memory."""
        video_context = self.memory.load_memory_variables({})  # Retrieve stored context

        seo_input = f"Generate an SEO-optimized YouTube video description based on the following context:\n{video_context}\n\n"

        seo_prompt = PromptTemplate(
            input_variables=["seo_input"],
            template=(
                "Write a YouTube video description that is SEO-optimized for YouTube. "
                "Use relevant keywords and make it engaging. Here's the context for the video:\n"
                "{seo_input}\n\n"
                "Make the description concise with relevant keywords and a call to action."
            )
        )

        # Create chain for generating SEO description
        seo_description_chain = LLMChain(llm=self.llm, prompt=seo_prompt)
        seo_description = seo_description_chain.run({"seo_input": seo_input})

        print("\nSEO Description:")
        print(seo_description)

        # Save SEO description to file
        seo_description_path = "tmp/paragraphs/seo_description.txt"
        os.makedirs(os.path.dirname(seo_description_path), exist_ok=True)
        
        with open(seo_description_path, "w") as file:
            file.write(seo_description)

        return seo_description    

    def generate_video_script(self, combined_input):
        """
        Generate the video script (beginning, middle, and end) using LangChain.
        """
        # Define prompts for generating video script
        beginning_prompt = PromptTemplate(
            input_variables=["combined_input"],
            template=(
                "{combined_input}\n\n"
                "Write the beginning of the video as if it were being spoken directly to the audience. "
                "Focus on engaging the listener with clear and natural language, without scene descriptions or annotations. "
                "Create 3 engaging paragraphs to grab the audience's attention, introduce the topic, and spark curiosity."
            )
        )

        middle_prompt = PromptTemplate(
            input_variables=["combined_input"],
            template=(
                "{combined_input}\n\n"
                "Write the middle section of the video as if it were being spoken directly to the audience. "
                "Focus on delivering insights and keeping the listener interested, using clear and conversational language. "
                "Develop the story in 3 paragraphs, providing deeper insights while maintaining viewer interest."
            )
        )

        end_prompt = PromptTemplate(
            input_variables=["combined_input"],
            template=(
                "{combined_input}\n\n"
                "Write the conclusion of the video as if it were being spoken directly to the audience. "
                "Focus on wrapping up the story naturally, leaving the audience with a thought-provoking question or idea. "
                "Create 3 paragraphs that summarize the content, inspire further thought, and encourage engagement."
            )
        )

        # Create chains for beginning, middle, and end using memory
        beginning_chain = LLMChain(llm=self.llm, prompt=beginning_prompt, memory=self.memory)
        middle_chain = LLMChain(llm=self.llm, prompt=middle_prompt, memory=self.memory)
        end_chain = LLMChain(llm=self.llm, prompt=end_prompt, memory=self.memory)

        # Generate video script
        beginning = beginning_chain.run({"combined_input": combined_input})
        middle = middle_chain.run({"combined_input": combined_input})
        end = end_chain.run({"combined_input": combined_input})

        # Ensure the directory exists for paragraphs
        paragraphs_dir = "tmp/paragraphs"
        os.makedirs(paragraphs_dir, exist_ok=True)

        # Save each section to separate files
        with open(os.path.join(paragraphs_dir, "beginning.txt"), "w") as file:
            file.write(beginning)

        with open(os.path.join(paragraphs_dir, "middle.txt"), "w") as file:
            file.write(middle)

        with open(os.path.join(paragraphs_dir, "end.txt"), "w") as file:
            file.write(end)

        # Combine all parts of the script
        full_script = f"{beginning}\n\n{middle}\n\n{end}"
        print("\nFull Video Script:")
        print(full_script)

        # Generate SEO description based on the memory content
        self.generate_seo_description()        

        return beginning, middle, end, full_script
