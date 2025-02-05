import os
import warnings
import random
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
        audio_clips = []
        total_duration = 0
        
        for image_name, (duration, audio_path) in self.image_audio_map.items():
            img_path = os.path.join(self.images_dir, image_name)
            
            if not os.path.exists(img_path) or not os.path.exists(audio_path):
                print(f"Warning: Missing file {img_path} or {audio_path}, skipping.")
                continue
            
            clip = ImageClip(img_path, duration=duration * 1.1).resize((self.video_width * 1.2, self.video_height * 1.2))
            zoom_direction = random.choice([
                "in", "out", 
                "top_left_to_center", "top_right_to_center", 
                "bottom_left_to_center", "bottom_right_to_center"
            ])
            zoom_clip = self.add_zoom_effect(clip, zoom_direction, duration)
            pan_clip = crop(zoom_clip, width=self.video_width, height=self.video_height, x_center=self.video_width//2, y_center=self.video_height//2)
            animated_clip = fadein(pan_clip, self.fade_duration).fadeout(self.fade_duration)
            
            audio_clip = AudioFileClip(audio_path).set_start(total_duration).set_duration(duration)
            total_duration += duration
            final_clip = animated_clip.set_audio(audio_clip)
            clips.append(final_clip)
            audio_clips.append(audio_clip)
        
        final_audio = CompositeAudioClip(audio_clips)
        final_video = concatenate_videoclips(clips, method="compose", padding=-self.fade_duration).set_audio(final_audio)
        
        video_output_path = os.path.join(self.videos_dir, "output_video.mp4")
        final_video.write_videofile(video_output_path, fps=30, codec="libx264", bitrate="5000k", audio=True)
        print(f"Video saved at: {video_output_path}")

    def add_zoom_effect(self, clip, direction, duration):
        if direction == "in":
            return clip.resize(lambda t: 1 + 0.1 * (t / duration))
        elif direction == "out":
            return clip.resize(lambda t: 1.2 - 0.1 * (t / duration))
        elif direction == "top_left_to_center":
            return self.zoom_from_top_left_to_center(clip, duration)
        elif direction == "top_right_to_center":
            return self.zoom_from_top_right_to_center(clip, duration)
        elif direction == "bottom_left_to_center":
            return self.zoom_from_bottom_left_to_center(clip, duration)
        elif direction == "bottom_right_to_center":
            return self.zoom_from_bottom_right_to_center(clip, duration)

    def zoom_from_top_left_to_center(self, clip, duration):
        return clip.resize(lambda t: 1 + 0.1 * (t / duration)).set_position(lambda t: (0 + (self.video_width // 2) * (t / duration), 0))

    def zoom_from_top_right_to_center(self, clip, duration):
        return clip.resize(lambda t: 1 + 0.1 * (t / duration)).set_position(lambda t: (self.video_width - (self.video_width // 2) * (t / duration), 0))

    def zoom_from_bottom_left_to_center(self, clip, duration):
        return clip.resize(lambda t: 1 + 0.1 * (t / duration)).set_position(lambda t: (0 + (self.video_width // 2) * (t / duration), self.video_height - (self.video_height // 2) * (t / duration)))

    def zoom_from_bottom_right_to_center(self, clip, duration):
        return clip.resize(lambda t: 1 + 0.1 * (t / duration)).set_position(lambda t: (self.video_width - (self.video_width // 2) * (t / duration), self.video_height - (self.video_height // 2) * (t / duration)))

if __name__ == "__main__":
    video_editor = VideoEditor()
    video_editor.create_video()
