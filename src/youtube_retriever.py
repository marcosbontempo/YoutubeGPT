import requests

class YoutubeRetriever:
    def __init__(self, api_key):
        """
        Initializes the YoutubeRetriever with the provided YouTube API key.
        :param api_key: YouTube API key
        """
        self.api_key = api_key
        self.base_search_url = "https://www.googleapis.com/youtube/v3/search"
        self.base_video_url = "https://www.googleapis.com/youtube/v3/videos"

    def get_channel_ids(self, handles):
        """
        Retrieves the channel IDs for a list of YouTube handles.
        :param handles: A list of YouTube handles (e.g., ["@HFYVengeance", "@EpicSpaceChronicles"])
        :return: A dictionary where keys are handles and values are channel IDs
        """
        channel_ids = {}
        for handle in handles:
            params = {
                "part": "snippet",
                "type": "channel",
                "q": f"{handle}",  # Handle to query
                "key": self.api_key,
            }
            try:
                response = requests.get(self.base_search_url, params=params)
                response.raise_for_status()  # Raise exception for HTTP errors
                data = response.json()

                if "items" in data and data["items"]:
                    channel_id = data["items"][0]["id"]["channelId"]
                    channel_ids[handle] = channel_id
                else:
                    print(f"No channel found for handle: {handle}")
                    channel_ids[handle] = None
            except requests.exceptions.RequestException as e:
                print(f"Error fetching channel ID for handle: {handle} - {e}")
                channel_ids[handle] = None

        return channel_ids

    def get_video_details(self, channel_ids, max_results=10):
        """
        Retrieves video details (title and view count) for a list of channel IDs.
        :param channel_ids: A list of channel IDs
        :param max_results: Number of videos to fetch per channel
        :return: A list of dictionaries with video details (title and views)
        """
        video_details = []

        for channel_id in channel_ids:
            try:
                # Fetch the most recent videos for the channel
                search_params = {
                    "part": "snippet",
                    "channelId": channel_id,
                    "maxResults": max_results,
                    "order": "date",  # Most recent videos
                    "type": "video",
                    "key": self.api_key,
                }
                search_response = requests.get(self.base_search_url, params=search_params)
                search_response.raise_for_status()
                search_data = search_response.json()
                
                video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]

                if not video_ids:
                    print(f"No videos found for channel ID: {channel_id}")
                    continue

                # Fetch statistics for the videos
                video_params = {
                    "part": "snippet,statistics",
                    "id": ",".join(video_ids),
                    "key": self.api_key,
                }
                video_response = requests.get(self.base_video_url, params=video_params)
                video_response.raise_for_status()
                video_data = video_response.json()

                for video in video_data.get("items", []):
                    title = video["snippet"]["title"]
                    views = video["statistics"].get("viewCount", "0")
                    video_details.append({"title": title, "views": views, "channel_id": channel_id})

            except requests.exceptions.RequestException as e:
                print(f"Error fetching video details for channel ID: {channel_id} - {e}")

        return video_details
