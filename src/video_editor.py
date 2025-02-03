import os
import warnings
from moviepy.editor import *
from moviepy.video.fx.all import crop, fadein, fadeout
from PIL import Image

class VideoEditor:
    def __init__(self, images_dir=None):
        warnings.filterwarnings("ignore")
        
        self.images_dir = images_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'images')
        self.videos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'videos')
        self.audios_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'audios')
        
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)
        
        self.video_width = 1280
        self.video_height = 720
        self.fade_duration = 2
        
        self.image_audio_map = self.load_audio_durations()

    def load_audio_durations(self):
        durations_file = os.path.join(self.audios_dir, "audio_durations.txt")
        image_audio_map = {}
        
        if not os.path.exists(durations_file):
            raise FileNotFoundError(f"Audio durations file not found: {durations_file}")
        
        with open(durations_file, 'r') as file:
            for line in file:
                parts = line.strip().split(": ")
                if len(parts) == 2:
                    filename, duration = parts
                    duration_seconds = float(duration.replace(" seconds", ""))
                    image_name = filename.replace(".mp3", ".jpg")
                    audio_path = os.path.join(self.audios_dir, filename)
                    image_audio_map[image_name] = (duration_seconds, audio_path)
        
        return image_audio_map

    def create_video(self):
        clips = []
        
        for image_name, (duration, audio_path) in self.image_audio_map.items():
            img_path = os.path.join(self.images_dir, image_name)
            
            if not os.path.exists(img_path) or not os.path.exists(audio_path):
                print(f"Warning: Missing file {img_path} or {audio_path}, skipping.")
                continue
            
            clip = ImageClip(img_path, duration=duration).resize(height=self.video_height, width=self.video_width)
            zoom_clip = self.add_zoom_effect(clip, zoom_factor=1.2, duration=duration)
            pan_clip = crop(zoom_clip, x1=50, width=self.video_width - 100, y1=50, height=self.video_height - 100)
            animated_clip = fadein(pan_clip, self.fade_duration).fadeout(self.fade_duration)
            audio_clip = AudioFileClip(audio_path).set_duration(duration)
            final_clip = animated_clip.set_audio(audio_clip)
            clips.append(final_clip)
        
        final_video = concatenate_videoclips(clips, method="compose", padding=-self.fade_duration)
        video_output_path = os.path.join(self.videos_dir, "output_video.mp4")
        final_video.write_videofile(video_output_path, fps=30, codec="libx264", bitrate="5000k", audio=True)
        print(f"Video saved at: {video_output_path}")

    def add_zoom_effect(self, clip, zoom_factor=1.2, duration=30):
        return clip.resize(lambda t: 1 + (zoom_factor - 1) * (t / duration))

if __name__ == "__main__":
    video_editor = VideoEditor()
    video_editor.create_video()
