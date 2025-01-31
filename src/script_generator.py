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
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.7, openai_api_key=self.OPENAI_API_KEY)
        
        # Define memory to keep track of previous interactions
        self.memory = ConversationBufferMemory(return_messages=True, input_key="combined_input")

    def retrieve_video_details(self, handles_file="../handles.txt"):
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

    def generate_unique_video_title(self, recent_titles_file="../data/recent_titles.txt"):
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
                "Generate a unique and engaging video title based on the channel's context. "
                "Make sure it is different from the following recent titles:\n"
                "{recent_titles}\n\n"
                "Be creative and think about what would catch the audience's attention."
            )
        )

        # Create chain for generating a unique video title
        title_chain = LLMChain(llm=self.llm, prompt=unique_title_prompt)

        # Generate a new video title
        recent_titles_str = "\n".join(recent_titles) if recent_titles else "None"
        video_title = title_chain.run({"recent_titles": recent_titles_str}).strip()

        # Ensure the new title is added to the recent titles list and keep only the last 10
        recent_titles.append(video_title)
        recent_titles = recent_titles[-10:]

        # Save updated recent titles back to the file
        with open(recent_titles_file, "w") as file:
            file.write("\n".join(recent_titles))

        print("\nGenerated Video Title:", video_title)

        return video_title

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
                "Develop the story in 4 paragraphs, providing deeper insights while maintaining viewer interest."
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
        paragraphs_dir = "../tmp/paragraphs"
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

        return beginning, middle, end, full_script


# Example of using the class

if __name__ == "__main__":
    # Create an instance of ScriptGenerator
    script_generator = ScriptGenerator()

    # Retrieve video details and generate channel context
    video_details = script_generator.retrieve_video_details()
    channel_context = script_generator.generate_channel_context(video_details)

    # Generate unique video title
    video_title = script_generator.generate_unique_video_title()

    # Combine channel context and video title into a single input for memory
    combined_input = f"Channel Context: {channel_context}\nVideo Title: {video_title}"

    # Generate the full video script
    beginning, middle, end, full_script = script_generator.generate_video_script(combined_input)
