import os
import requests
from dotenv import load_dotenv

load_dotenv('tokens.env')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_OAUTH_TOKEN = os.getenv('TWITCH_OAUTH_TOKEN')
HEADERS = {
    'Client-ID': TWITCH_CLIENT_ID,
    'Authorization': f'Bearer {TWITCH_OAUTH_TOKEN}'
}

def get_user_color(username: str):
    user_url = 'https://api.twitch.tv/helix/users'
    color_url = 'https://api.twitch.tv/helix/chat/color'
    try:
        user_resp = requests.get(user_url, headers=HEADERS, params={'login': username})
        user_resp.raise_for_status()
        user_data = user_resp.json()
        if not user_data.get('data'):
            return None
        user_id = user_data['data'][0]['id']
        color_resp = requests.get(color_url, headers=HEADERS, params={'user_id': user_id})
        color_resp.raise_for_status()
        color_data = color_resp.json()
        if color_data.get('data'):
            return color_data['data'][0].get('color', 'Default Color')
    except requests.RequestException:
        return None

def create_clip(channel_name: str):
    user_url = 'https://api.twitch.tv/helix/users'
    clip_url = 'https://api.twitch.tv/helix/clips'
    try:
        user_resp = requests.get(user_url, headers=HEADERS, params={'login': channel_name})
        user_resp.raise_for_status()
        user_data = user_resp.json()
        if not user_data.get('data'):
            return None
        user_id = user_data['data'][0]['id']
        clip_resp = requests.post(clip_url, headers=HEADERS, params={'broadcaster_id': user_id})
        clip_resp.raise_for_status()
        clip_data = clip_resp.json()
        clip_edit_url = clip_data['data'][0]['edit_url']
        clip_url = os.path.dirname(clip_edit_url) # removes /edit from the end of the URL
        return clip_url
    except requests.RequestException:
        return None