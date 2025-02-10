import os
import warnings
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from leonardo_image_generator import LeonardoImageGenerator
from better_profanity import profanity  

class ImageGenerator:
    def __init__(self):
        warnings.filterwarnings("ignore")

        # Load environment variables from the .env file
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
        load_dotenv(dotenv_path=env_path)

        # Set up the OpenAI GPT-4 model with LangChain (using ChatOpenAI)
        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4", max_tokens=300)

        # Ensure the tmp/images directory exists
        self.images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'images')
        os.makedirs(self.images_dir, exist_ok=True)

    def get_image_prompt(self, paragraph_text):
        """
        Generate a prompt for image generation based on a paragraph.
        """
        prompt_template = """
        Create a hyper-realistic, YouTube-style image based on the following paragraph. 
        The image should reflect the tone, environment, and subject matter of the paragraph.
        Use vivid details and imagine the scene in high quality.

        Please ensure that the prompt avoids any offensive, vulgar, or inappropriate language, 
        including any form of the word "fuck" or similar words, and any other profanities or slurs. 
        Ensure that only appropriate and respectful language is used throughout the prompt.

        Paragraph: {paragraph_text}
        """

        prompt = PromptTemplate(input_variables=["paragraph_text"], template=prompt_template)
        chain = LLMChain(llm=self.llm, prompt=prompt)
        image_prompt = chain.run(paragraph_text)

        # Apply profanity filter to the image prompt
        clean_prompt = profanity.censor(image_prompt)
        return clean_prompt[:1500]

    def get_thumbnail_prompt(self, title, video_topic):
        """
        Generate a highly engaging prompt for creating a YouTube thumbnail.
        """
        prompt_template = """
        Generate a visually striking and engaging YouTube thumbnail image based on the following details.
        The thumbnail should be eye-catching, with vibrant colors, dramatic lighting, and bold composition.
        Ensure that the image captures attention and conveys the essence of the video topic.
        
        Video Title: {title}
        Video Topic: {video_topic}
        
        The image should focus on:
        - A bold, clear central subject.
        - High contrast and sharp details.
        - Expressive emotions, dramatic poses, or dynamic movement.
        - Avoid any offensive or inappropriate content.
        
        Generate a detailed prompt for this thumbnail.
        """
        
        prompt = PromptTemplate(input_variables=["title", "video_topic"], template=prompt_template)
        chain = LLMChain(llm=self.llm, prompt=prompt)
        thumbnail_prompt = chain.run(title=title, video_topic=video_topic)

        # Apply profanity filter to the generated prompt
        clean_prompt = profanity.censor(thumbnail_prompt)
        return clean_prompt[:1500]

    def generate_and_save_images(self, paragraph_files=["intro.txt", "call_to_adventure.txt", "refusal_of_call.txt", 
                                                       "mentor.txt", "crossing_the_threshold.txt", "trials_and_allies.txt", 
                                                       "climax_and_return.txt"]):
        """
        Reads the paragraph files from tmp/paragraphs and generates and saves images for each paragraph.
        """
        image_prompts = {}  

        for file_name in paragraph_files:
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'paragraphs', file_name)

            if not os.path.exists(file_path):
                print(f"File {file_name} not found!")
                continue

            with open(file_path, "r") as file:
                paragraphs = file.read().split("\n\n")  # Assuming paragraphs are separated by two newlines

            for i, paragraph in enumerate(paragraphs, start=1):
                print(f"Generating image prompt for Paragraph {i} in {file_name}")
                image_prompt = self.get_image_prompt(paragraph)
                image_prompts[f"{file_name}_paragraph_{i}"] = image_prompt

                # Initialize LeonardoImageGenerator
                save_path = os.path.join(self.images_dir, f"{file_name.replace('.txt', '')}_paragraph_{i}.jpg")
                image_generator = LeonardoImageGenerator(save_path)
                image_generator.manage_request(image_prompt)  # Generate and save the image
                print()

        # Generate thumbnail prompt and image
        paragraphs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'paragraphs')

        with open(os.path.join(paragraphs_dir, 'video_title.txt'), 'r') as file:
            title = file.read().strip()

        with open(os.path.join(paragraphs_dir, 'seo_description.txt'), 'r') as file:
            description = file.read().strip()

        print("Generating thumbnail image...")
        thumbnail_prompt = self.get_thumbnail_prompt(title, description)
        thumbnail_path = os.path.join(self.images_dir, "thumbnail.jpg")
        thumbnail_generator = LeonardoImageGenerator(thumbnail_path)
        thumbnail_generator.manage_request(thumbnail_prompt)

        self.save_prompts_to_file(image_prompts)

    def save_prompts_to_file(self, image_prompts):
        """
        Save the generated image prompts to a text file.
        """
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'images', 'image_prompts.txt')

        with open(output_file, "w") as file:
            for file_name, prompt in image_prompts.items():
                file.write(f"{file_name}:\n{prompt}\n\n")
        print(f"Image prompts saved to {output_file}")

# Example for testing the updated class
if __name__ == "__main__":
    # Create an instance of ImageGenerator
    image_generator = ImageGenerator()

    # Generate and save images for the paragraphs in specified files, and create a thumbnail
    image_generator.generate_and_save_images()
