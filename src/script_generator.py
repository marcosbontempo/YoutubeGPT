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
        Generate the video script (Hero's Journey) using LangChain.
        """
        # Define prompts for each part of the Hero's Journey
        intro_prompt = PromptTemplate(
            input_variables=["combined_input"],
            template=(
                "{combined_input}\n\n"
                "Write the Introduction, introducing the main character and their world. "
                "Set the scene, establishing the protagonist's normal life in 3 paragraphs."
            )
        )

        call_to_adventure_prompt = PromptTemplate(
            input_variables=["combined_input"],
            template=(
                "{combined_input}\n\n"
                "Write the Call to Adventure, explaining what challenges or events lead the protagonist to begin their journey. "
                "Describe in 3 paragraphs how the protagonist is drawn into the adventure."
            )
        )

        refusal_of_call_prompt = PromptTemplate(
            input_variables=["combined_input"],
            template=(
                "{combined_input}\n\n"
                "Write the Refusal of the Call, where the protagonist resists or hesitates to take on the challenge. "
                "Create 3 paragraphs showing the inner conflict or doubt of the protagonist."
            )
        )

        mentor_prompt = PromptTemplate(
            input_variables=["combined_input"],
            template=(
                "{combined_input}\n\n"
                "Write the Meeting with the Mentor, where the protagonist encounters a guide or helper who provides wisdom or power. "
                "Write 3 paragraphs about the mentor's impact."
            )
        )

        crossing_the_threshold_prompt = PromptTemplate(
            input_variables=["combined_input"],
            template=(
                "{combined_input}\n\n"
                "Write the Crossing of the Threshold, where the protagonist fully commits to the adventure and leaves the ordinary world behind. "
                "Write 3 paragraphs describing this turning point."
            )
        )

        trials_and_allies_prompt = PromptTemplate(
            input_variables=["combined_input"],
            template=(
                "{combined_input}\n\n"
                "Write the Trials, Allies, and Enemies, where the protagonist faces challenges, makes allies, and confronts enemies. "
                "Provide 3 paragraphs detailing the challenges faced during the journey."
            )
        )

        climax_and_return_prompt = PromptTemplate(
            input_variables=["combined_input"],
            template=(
                "{combined_input}\n\n"
                "Write the Climax and Return with the Elixir, where the protagonist confronts the main challenge and returns home transformed. "
                "Write 3 paragraphs about the final battle and the protagonist's return."
            )
        )

        # Create chains for each part of the Hero's Journey
        intro_chain = LLMChain(llm=self.llm, prompt=intro_prompt, memory=self.memory)
        call_to_adventure_chain = LLMChain(llm=self.llm, prompt=call_to_adventure_prompt, memory=self.memory)
        refusal_of_call_chain = LLMChain(llm=self.llm, prompt=refusal_of_call_prompt, memory=self.memory)
        mentor_chain = LLMChain(llm=self.llm, prompt=mentor_prompt, memory=self.memory)
        crossing_the_threshold_chain = LLMChain(llm=self.llm, prompt=crossing_the_threshold_prompt, memory=self.memory)
        trials_and_allies_chain = LLMChain(llm=self.llm, prompt=trials_and_allies_prompt, memory=self.memory)
        climax_and_return_chain = LLMChain(llm=self.llm, prompt=climax_and_return_prompt, memory=self.memory)

        # Generate video script parts
        intro = intro_chain.run({"combined_input": combined_input})
        print("\nIntro section generated.")
        call_to_adventure = call_to_adventure_chain.run({"combined_input": combined_input})
        print("Call to Adventure section generated.")
        refusal_of_call = refusal_of_call_chain.run({"combined_input": combined_input})
        print("Refusal of Call section generated.")
        mentor = mentor_chain.run({"combined_input": combined_input})
        print("Mentor section generated.")
        crossing_the_threshold = crossing_the_threshold_chain.run({"combined_input": combined_input})
        print("Crossing the Threshold section generated.")
        trials_and_allies = trials_and_allies_chain.run({"combined_input": combined_input})
        print("Trials and Allies section generated.")
        climax_and_return = climax_and_return_chain.run({"combined_input": combined_input})
        print("Climax and Return section generated.")        

        # Ensure the directory exists for paragraphs
        paragraphs_dir = "tmp/paragraphs"
        os.makedirs(paragraphs_dir, exist_ok=True)

        # Save each section to separate files
        with open(os.path.join(paragraphs_dir, "intro.txt"), "w") as file:
            file.write(intro)

        with open(os.path.join(paragraphs_dir, "call_to_adventure.txt"), "w") as file:
            file.write(call_to_adventure)

        with open(os.path.join(paragraphs_dir, "refusal_of_call.txt"), "w") as file:
            file.write(refusal_of_call)

        with open(os.path.join(paragraphs_dir, "mentor.txt"), "w") as file:
            file.write(mentor)

        with open(os.path.join(paragraphs_dir, "crossing_the_threshold.txt"), "w") as file:
            file.write(crossing_the_threshold)

        with open(os.path.join(paragraphs_dir, "trials_and_allies.txt"), "w") as file:
            file.write(trials_and_allies)

        with open(os.path.join(paragraphs_dir, "climax_and_return.txt"), "w") as file:
            file.write(climax_and_return)

        # Combine all parts of the script
        full_script = f"{intro}\n\n{call_to_adventure}\n\n{refusal_of_call}\n\n{mentor}\n\n{crossing_the_threshold}\n\n{trials_and_allies}\n\n{climax_and_return}"
        print("\nFull Video Script generated")
        #print(full_script)

        # Generate SEO description based on the memory content
        self.generate_seo_description()        

        return intro, call_to_adventure, refusal_of_call, mentor, crossing_the_threshold, trials_and_allies, climax_and_return, full_script
