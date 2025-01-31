import os
import warnings
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

class ImageGenerator:
    def __init__(self):
        # Suppress warnings
        warnings.filterwarnings("ignore")

        # Load environment variables from the .env file
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
        load_dotenv(dotenv_path=env_path)

        # Set up the OpenAI GPT-4 model with LangChain (using ChatOpenAI)
        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4")  # Use the correct GPT-4 model

        # Ensure the tmp/images directory exists
        self.images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'images')
        os.makedirs(self.images_dir, exist_ok=True)

    def get_image_prompt(self, paragraph_text):
        """
        Generate a prompt for image generation based on a paragraph.
        
        :param paragraph_text: Text content of the paragraph.
        :return: Generated prompt for image generation.
        """
        prompt_template = """
        Create a hyper-realistic, YouTube-style image based on the following paragraph. 
        The image should reflect the tone, environment, and subject matter of the paragraph.
        Use vivid details and imagine the scene in high quality.
        
        Paragraph: {paragraph_text}
        """
        prompt = PromptTemplate(input_variables=["paragraph_text"], template=prompt_template)
        chain = LLMChain(llm=self.llm, prompt=prompt)
        image_prompt = chain.run(paragraph_text)
        return image_prompt

    def generate_image_prompts(self, paragraph_files=["beginning.txt", "middle.txt", "end.txt"]):
        """
        Reads the paragraph files from tmp/paragraphs and generates image prompts for each paragraph.
        
        :param paragraph_files: List of paragraph filenames.
        :return: Dictionary containing the image prompt for each paragraph.
        """
        image_prompts = {}

        for file_name in paragraph_files:
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'paragraphs', file_name)

            # Check if the file exists
            if not os.path.exists(file_path):
                print(f"File {file_name} not found!")
                continue

            with open(file_path, "r") as file:
                paragraphs = file.read().split("\n\n")  # Assuming paragraphs are separated by two newlines

            # Generate image prompt for each paragraph
            for i, paragraph in enumerate(paragraphs, start=1):
                print(f"Generating image prompt for Paragraph {i} in {file_name}")
                image_prompt = self.get_image_prompt(paragraph)
                
                # Print the generated prompt for each paragraph
                print(f"Image Prompt {i} for {file_name}:\n{image_prompt}\n")
                
                # Save the image prompt for each paragraph
                image_prompts[f"{file_name}_paragraph_{i}"] = image_prompt

        return image_prompts

    def save_prompts_to_file(self, image_prompts, output_file="tmp/images/image_prompts.txt"):
        """
        Save the generated image prompts to a text file.
        
        :param image_prompts: Dictionary containing the image prompts.
        :param output_file: Path where the prompts will be saved.
        """
        with open(output_file, "w") as file:
            for file_name, prompt in image_prompts.items():
                file.write(f"{file_name}:\n{prompt}\n\n")
        print(f"Image prompts saved to {output_file}")
