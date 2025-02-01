import requests
import time
import os
from dotenv import load_dotenv

class LeonardoImageGenerator:
    def __init__(self, save_path):
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
        load_dotenv(dotenv_path=env_path)

        self.api_key = os.getenv("LEONARDO_API_KEY")
        if not self.api_key:
            raise ValueError("API key is missing. Please set 'LEONARDO_API_KEY' in the .env file.")

        self.url = "https://cloud.leonardo.ai/api/rest/v1/generations"
        self.save_path = save_path
        self.delay = 15

    def make_initial_request(self, prompt, num_images=1, width=1280, height=720, steps=15, seed=42):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "prompt": prompt,
            "num_images": num_images,
            "width": width,
            "height": height,
            "presetStyle": "CREATIVE",
            "modelId": "b24e16ff-06e3-43eb-8d33-4416c2d75876",
            "promptMagic": True,
            "promptMagicStrength": 0,
            "highContrast": True,
            "highResolution": True,
            "seed": seed
        }

        response = requests.post(self.url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json().get('sdGenerationJob', {}).get('generationId')
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

    def check_request_status(self, generation_id):
        status_url = f"{self.url}/{generation_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.get(status_url, headers=headers)

        if response.status_code == 200:
            status_data = response.json()

            generations_by_pk = status_data.get("generations_by_pk", {})
            generated_images = generations_by_pk.get("generated_images", [])
            
            if generated_images:  
                return "completed", generated_images
            else:
                print("No images generated yet.")
                return "in_progress", generated_images
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return "failed", None

    def download_image(self, image_url):
        response = requests.get(image_url)

        if response.status_code == 200:
            # Save the image directly to the path provided
            with open(self.save_path, 'wb') as f:
                f.write(response.content)
            print(f"Image successfully downloaded and saved to {self.save_path}")
        else:
            print(f"Error downloading the image: {response.status_code} - {response.text}")

    def manage_request(self, prompt):
        generation_id = self.make_initial_request(prompt)
        if not generation_id:
            return

        print("Waiting for image generation...")
        time.sleep(self.delay)

        while True:
            status, generated_images = self.check_request_status(generation_id)
            
            if status == "completed":
                image_url = generated_images[0]["url"]
                if image_url:
                    print("Image generated successfully!")
                    print("Image URL:", image_url)
                    self.download_image(image_url)  
                    break
            elif status == "failed":
                print("Image generation failed.")
                break
            else:
                print(f"Waiting... (status: {status})")
                time.sleep(self.delay)

if __name__ == "__main__":
    prompt = "A dramatic and action-packed scene set in the vastness of space, where a brave penguin, dressed in futuristic armor, is engaged in a fierce battle against a menacing alien."

    image_generator = LeonardoImageGenerator("../tmp/images/paragraph1.jpg")
    image_generator.manage_request(prompt)
