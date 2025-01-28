import os
import warnings
from google.cloud import texttospeech
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI  # Correct import for GPT-4 (Chat model)
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from pydub import AudioSegment

class AudioGenerator:
    def __init__(self, language_code="en-US", voice_name="en-US-Neural2-I", gender="MALE"):
        # Suppress warnings
        warnings.filterwarnings("ignore")

        # Load environment variables from the .env file in the parent directory
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
        load_dotenv(dotenv_path=env_path)

        # Voice configuration
        self.language_code = language_code
        self.voice_name = voice_name
        self.gender = gender

        # Initialize the Google TTS client
        self.client = texttospeech.TextToSpeechClient()

        # Set up the OpenAI GPT-4 model with LangChain (using ChatOpenAI)
        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4")

    def get_ssml_text(self, paragraph_files=["beginning.txt", "middle.txt", "end.txt"]):
        """
        Reads the paragraph files from the ../tmp/paragraphs folder and generates SSML for each paragraph.
        
        :param paragraph_files: List of paragraph filenames.
        :return: Dictionary containing the SSML generated for each paragraph.
        """
        ssml_texts = []

        for file_name in paragraph_files:
            file_path = os.path.join("..", "tmp", "paragraphs", file_name)

            # Check if the file exists
            if not os.path.exists(file_path):
                print(f"File {file_name} not found!")
                continue

            with open(file_path, "r") as file:
                paragraph_text = file.read()

            # Print the paragraph text to check if it is read correctly
            print(f"Reading file: {file_name}")
            print(f"Paragraph text: {paragraph_text}")

            # Generate SSML for the paragraph using LangChain + GPT-4
            prompt_template = """
            Generate high-quality SSML for the following paragraph. Use SSML tags such as <break>, <prosody>, <emphasis>, etc., to add pauses and tone variation.
            Paragraph: {paragraph_text}
            """
            prompt = PromptTemplate(input_variables=["paragraph_text"], template=prompt_template)
            chain = LLMChain(llm=self.llm, prompt=prompt)
            ssml_text = chain.run(paragraph_text)

            # Log the generated SSML to check if it's empty
            print(f"Generated SSML for {file_name}: {ssml_text}")

            if ssml_text.strip():  # Check if SSML is non-empty
                ssml_texts.append(ssml_text)
            else:
                print(f"Warning: SSML for {file_name} is empty.")

        # Combine all SSML texts into one
        full_ssml = "<speak>" + "".join(ssml_texts) + "</speak>"
        return full_ssml

    def narrate_text_with_ssml(self, ssml_text, output_file="output.mp3"):
        """
        Method to generate audio from SSML text for each paragraph.

        :param ssml_text: SSML text to be synthesized.
        :param output_file: Path for the output file (default: 'output.mp3').
        """
        # Configure the text to be synthesized using SSML
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

        # Voice configuration
        voice = texttospeech.VoiceSelectionParams(
            language_code=self.language_code,  # Language code
            name=self.voice_name,  # Voice name
            ssml_gender=getattr(texttospeech.SsmlVoiceGender, self.gender)  # Gender of the voice
        )

        # Audio file configuration
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3  # Audio format (MP3)
        )

        # Request to Google TTS
        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Save the audio to the specified file
        with open("../tmp/" + output_file, "wb") as out:
            out.write(response.audio_content)
            print(f"Audio content written to file: {output_file}")

    def generate_audio_for_paragraphs(self):
        """
        This method generates SSML for each paragraph, saves them as individual MP3 files,
        and then combines those MP3s into a single MP3 file.
        """
        # Get SSML for each paragraph
        paragraph_files = ["beginning.txt", "middle.txt", "end.txt"]
        for i, file_name in enumerate(paragraph_files):
            ssml_text = self.get_ssml_text(paragraph_files=[file_name])
            mp3_file_name = f"{file_name.replace('.txt', '')}.mp3"  # Output file name
            self.narrate_text_with_ssml(ssml_text, output_file=mp3_file_name)

        # Combine the MP3 files into one
        self.combine_mp3_files(paragraph_files)

    def combine_mp3_files(self, paragraph_files):
        """
        Combine the individual MP3 files into a single MP3 file.

        :param paragraph_files: List of MP3 filenames to be combined.
        """
        # Load the individual MP3 files using pydub
        combined_audio = AudioSegment.empty()

        for file_name in paragraph_files:
            mp3_file = f"../tmp/{file_name.replace('.txt', '')}.mp3"
            audio = AudioSegment.from_mp3(mp3_file)
            combined_audio += audio  # Concatenate the audio

        # Export the combined audio to a single file
        combined_audio.export("../tmp/combined_paragraphs.mp3", format="mp3")
        print("Combined audio saved as combined_paragraphs.mp3")

# Example of using the class

if __name__ == "__main__":
    # Create an instance of AudioGenerator
    audio_generator = AudioGenerator(language_code="en-US", voice_name="en-US-Neural2-I", gender="MALE")

    # Generate SSML, create MP3s, and combine them into one MP3
    audio_generator.generate_audio_for_paragraphs()
