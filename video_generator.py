import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.script_generator import ScriptGenerator
from src.audio_generator import AudioGenerator
from src.image_generator import ImageGenerator

STEPS = [1, 2, 3]

if __name__ == "__main__":
    # Step 1: Create the script
    if 1 in STEPS:
        print("***** Step 1: Creating the video script... *****")
        script_generator = ScriptGenerator()    
        video_details = script_generator.retrieve_video_details()  # Retrieve video details

        channel_context = script_generator.generate_channel_context(video_details)  # Generate channel context
        video_title = script_generator.generate_unique_video_title()  # Generate a unique video title
        
        combined_input = f"Channel Context: {channel_context}\nVideo Title: {video_title}"  # Combine input for memory    
        beginning, middle, end, full_script = script_generator.generate_video_script(combined_input)  # Generate full video script

    # Step 2: Generate the audio
    if 2 in STEPS:
        print("\n***** Step 2: Generating the audio... *****")
        audio_generator = AudioGenerator(language_code="en-US", voice_name="en-US-Neural2-I", gender="MALE")  # Initialize AudioGenerator
        audio_generator.generate_audio_for_paragraphs()  # Generate audio for the script paragraphs

    # Step 3: Generate the images
    if 3 in STEPS:
        print("\n***** Step 3: Generating the image prompts... *****")
        image_generator = ImageGenerator()  # Initialize ImageGenerator
        image_prompts = image_generator.generate_image_prompts()  # Generate image prompts based on the script    
        image_generator.save_prompts_to_file(image_prompts)  # Save the generated image prompts to a file

    print("\n***** Process completed successfully! *****")
