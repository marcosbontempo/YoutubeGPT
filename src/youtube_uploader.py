import os
import pickle
import httplib2
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from tqdm import tqdm

class YouTubeUploader:
    def __init__(self, client_secrets_file, api_service_name="youtube", api_version="v3", scopes=["https://www.googleapis.com/auth/youtube.upload"]):
        self.client_secrets_file = client_secrets_file
        self.api_service_name = api_service_name
        self.api_version = api_version
        self.scopes = scopes
        self.credentials = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                self.credentials = pickle.load(token)

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, self.scopes)
                self.credentials = flow.run_local_server(port=0)

            with open("token.pickle", "wb") as token:
                pickle.dump(self.credentials, token)

        self.service = build(self.api_service_name, self.api_version, credentials=self.credentials)

    def upload_video(self, video_file, title, description, category="22", privacy="public", thumbnail_file=None):
        media = MediaFileUpload(video_file, chunksize=256 * 1024, resumable=True, mimetype="video/*")
        request = self.service.videos().insert(
            part="snippet,status",
            body=dict(
                snippet=dict(
                    title=title,
                    description=description,
                    categoryId=category
                ),
                status=dict(
                    privacyStatus=privacy
                )
            ),
            media_body=media
        )
        
        response = None
        with tqdm(total=100, unit="%", desc="Uploading video", dynamic_ncols=True) as pbar:
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    pbar.n = progress
                    pbar.last_print_n = progress
                    pbar.update(0)

        video_id = response['id']
        print(f"\nUpload complete! Video ID: {video_id}")
        
        # Upload thumbnail if provided
        if thumbnail_file and os.path.exists(thumbnail_file):
            self.upload_thumbnail(video_id, thumbnail_file)
        
        return response

    def upload_thumbnail(self, video_id, thumbnail_file):
        """
        Uploads a custom thumbnail for the given video ID.
        """
        request = self.service.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_file, mimetype='image/jpeg')
        )
        response = request.execute()
        print(f"Thumbnail uploaded successfully for Video ID: {video_id}")
        return response

if __name__ == "__main__":
    client_secrets_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'youtube_credentials.json')
    
    uploader = YouTubeUploader(client_secrets_file)

    video_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'videos', 'output_video.mp4')
    thumbnail_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'images', 'thumbnail.jpg')
    
    paragraphs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp', 'paragraphs')

    # Get title and description from files in paragraphs_dir
    with open(os.path.join(paragraphs_dir, 'video_title.txt'), 'r') as file:
        title = file.read().strip()

    with open(os.path.join(paragraphs_dir, 'seo_description.txt'), 'r') as file:
        description = file.read().strip()
  
    uploader.upload_video(video_file, title, description, thumbnail_file=thumbnail_file)
