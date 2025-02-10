import os
import warnings
from google.cloud import texttospeech
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from pydub import AudioSegment

class AudioGenerator:
    def __init__(self, language_code="en-US", voice_name="en-US-Neural2-I", gender="MALE"):
        warnings.filterwarnings("ignore")

        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
        load_dotenv(dotenv_path=env_path)

        self.language_code = language_code
        self.voice_name = voice_name
        self.gender = gender
        self.client = texttospeech.TextToSpeechClient()

        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4")
        
        self.audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'audios')
        os.makedirs(self.audio_dir, exist_ok=True)

    def get_ssml_text(self, paragraph_text):
        """
        Generate SSML for the given paragraph.
        """
        prompt_template = """
        Generate high-quality SSML for the following paragraph. Use SSML tags such as <break>, <prosody>, <emphasis>, etc., to add pauses and tone variation.
        Paragraph: {paragraph_text}
        """
        prompt = PromptTemplate(input_variables=["paragraph_text"], template=prompt_template)
        chain = LLMChain(llm=self.llm, prompt=prompt)
        ssml_text = chain.run(paragraph_text)

        if ssml_text.strip():
            return ssml_text
        else:
            print(f"Warning: SSML for paragraph is empty.")
            return None

    def narrate_text_with_ssml(self, ssml_text, output_file="output.mp3"):
        """
        Generate audio from SSML text for each paragraph.
        """
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=self.language_code,
            name=self.voice_name,
            ssml_gender=getattr(texttospeech.SsmlVoiceGender, self.gender)
        )

        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        output_path = os.path.join(self.audio_dir, output_file)
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
            print(f"Audio content written to file: {output_file}")
        
        # Calculate the duration of the generated audio
        audio = AudioSegment.from_mp3(output_path)
        return len(audio) / 1000  # Duration in seconds

    def generate_audio_for_paragraphs(self, paragraph_files=["intro.txt", "call_to_adventure.txt", "refusal_of_call.txt", 
                                                           "mentor.txt", "crossing_the_threshold.txt", "trials_and_allies.txt", 
                                                           "climax_and_return.txt"]):
        """
        Generate audio for each paragraph, save them as individual MP3 files, and calculate the duration.
        """
        audio_durations = {}

        for section in paragraph_files:
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'paragraphs', section)

            if not os.path.exists(file_path):
                print(f"File {section} not found!")
                continue

            with open(file_path, "r") as file:
                paragraphs = file.read().split("\n\n")  # Assuming paragraphs are separated by two newlines

            for i, paragraph in enumerate(paragraphs, start=1):
                print(f"Generating audio for Paragraph {i} in {section}")
                ssml_text = self.get_ssml_text(paragraph)
                mp3_file_name = f"{section.replace('.txt', '')}_paragraph_{i}.mp3"

                duration = self.narrate_text_with_ssml(ssml_text, output_file=mp3_file_name)
                audio_durations[mp3_file_name] = duration

        # Write the durations to a file
        audio_durations_file = os.path.join(self.audio_dir, 'audio_durations.txt')
        with open(audio_durations_file, "w") as out_file:
            for audio_file, duration in audio_durations.items():
                out_file.write(f"{audio_file}: {duration:.2f} seconds\n")
            print(f"Audio durations written to file: {audio_durations_file}")

        return audio_durations

# Example usage
if __name__ == "__main__":
    audio_generator = AudioGenerator()
    durations = audio_generator.generate_audio_for_paragraphs()
    print(f"Durations of each paragraph's audio: {durations}")