import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.script_generator import ScriptGenerator
from src.audio_generator import AudioGenerator
from src.image_generator import ImageGenerator
from src.video_editor import VideoEditor

STEPS = [1, 2, 3, 4]

if __name__ == "__main__":
    if 1 in STEPS:
        print("***** Step 1: Creating the video script... *****")
        script_generator = ScriptGenerator()    
        video_details = script_generator.retrieve_video_details()  

        channel_context = script_generator.generate_channel_context(video_details)  
        video_title = script_generator.generate_unique_video_title(video_details)  
        
        combined_input = f"Channel Context: {channel_context}\nVideo Title: {video_title}"  
        script_generator.generate_video_script(combined_input)  

    if 2 in STEPS:
        print("\n***** Step 2: Generating the audio... *****")
        audio_generator = AudioGenerator(language_code="en-US", voice_name="en-US-Neural2-I", gender="MALE")  
        audio_generator.generate_audio_for_paragraphs()  

    if 3 in STEPS:
        print("\n***** Step 3: Generating and saving the images... *****")
        image_generator = ImageGenerator()  
        image_generator.generate_and_save_images()  

    if 4 in STEPS:
        print("\n***** Step 4: Creating the video... *****")
        video_editor = VideoEditor()
        video_editor.create_video()  

    print("\n***** Process completed successfully! *****")
