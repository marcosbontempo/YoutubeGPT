import os
import warnings
from moviepy.editor import *
from moviepy.video.fx.all import crop, fadein, fadeout
from PIL import Image

class VideoEditor:
    def __init__(self, images_dir=None):
        warnings.filterwarnings("ignore")
        self.images_dir = images_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'images')
        self.delay = 15
        self.video_width = 1920
        self.video_height = 1080
        self.clip_duration = 5
        self.fade_duration = 2

    def create_video(self):
        """
        Create a video from the images.
        """
        images = []
        
        # Loop over sections and create the image list
        for section in ['beginning', 'middle', 'end']:
            for i in range(1, 4):
                img_path = os.path.join(self.images_dir, f"{section}_paragraph_{i}.jpg")
                images.append(img_path)

        clips = []

        # Create clips for each image
        for img_path in images:
            print(f"Adding image {img_path} to video.")  # Debugging the order

            clip = ImageClip(img_path, duration=self.clip_duration).resize(height=self.video_height, width=self.video_width)

            # Apply zoom effect
            zoom_clip = self.add_zoom_effect(clip, zoom_factor=1.2, duration=self.clip_duration)

            # Apply pan effect
            pan_clip = crop(zoom_clip, x1=50, width=self.video_width - 100, y1=50, height=self.video_height - 100)

            # Add fade-in and fade-out
            animated_clip = fadein(pan_clip, self.fade_duration).fadeout(self.fade_duration)

            # Append the animated clip
            clips.append(animated_clip)

        # Concatenate clips and generate final video
        final_video = concatenate_videoclips(clips, method="compose", padding=-self.fade_duration)

        # Export the final video
        final_video.write_videofile(
            "output_video.mp4",
            fps=30,                 
            codec="libx264",        
            bitrate="5000k",        
            audio=False             
        )

    def add_zoom_effect(self, clip, zoom_factor=1.2, duration=30):
        """
        Add a zoom effect to a clip.
        """
        return clip.resize(lambda t: 1 + (zoom_factor - 1) * (t / duration))


# Example for testing
if __name__ == "__main__":
    video_editor = VideoEditor()
    video_editor.create_video()
