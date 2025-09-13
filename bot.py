import asyncio
import os
from dotenv import load_dotenv
from twitchAPI.twitch import Twitch
from twitchAPI.chat import Chat, ChatMessage, ChatEvent, ChatCommand
from twitchAPI.type import AuthScope
from twitch_api_handler import get_user_color, create_clip
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, UTC

# Load environment variables
load_dotenv('tokens.env')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
TWITCH_OAUTH_TOKEN = os.getenv('TWITCH_OAUTH_TOKEN')
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.CLIPS_EDIT]
CHANNELS = os.getenv('CHANNELS', '').split(',')

# Database setup
Base = declarative_base()
engine = create_engine('sqlite:///chat_logs.db', echo=False)
SessionLocal = sessionmaker(bind=engine)

class ChatLog(Base):
    __tablename__ = 'chat_logs'
    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String, index=True)
    username = Column(String, index=True)
    message = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))

Base.metadata.create_all(bind=engine)

async def on_ready(event):
    for channel in CHANNELS:
        await event.chat.join_room(channel)
    print('Bot is ready and joined channels.')
    

# Message triggers for non-prefixed commands
MESSAGE_TRIGGERS = {
    'clip': ['clip?', 'كليب؟'],
    'color': ['color?', 'لون؟'],
}

async def message_handler(msg: ChatMessage):
    text = msg.text.strip().lower()
    # Check for clip triggers
    if any(trigger in text for trigger in MESSAGE_TRIGGERS['clip']):
        clip_url = create_clip(msg.room.name)
        await msg.reply(clip_url or "Can't create clip.")
    # Check for color triggers
    elif any(trigger in text for trigger in MESSAGE_TRIGGERS['color']):
        # Extract username if present after the trigger
        for trigger in MESSAGE_TRIGGERS['color']:
            if text.startswith(trigger):
                parts = msg.text.strip().split()
                if len(parts) > 1:
                    username = parts[1].lstrip('@')
                else:
                    username = msg.user.name
                color = get_user_color(username)
                await msg.reply(f"{username}'s color: {color}")
                break

async def on_message(msg: ChatMessage):
    print(f'[{msg.room.name}] {msg.user.name}: {msg.text}')
    # Log to DB
    session = SessionLocal()
    chat_log = ChatLog(
        channel=msg.room.name,
        username=msg.user.name,
        message=msg.text,
        timestamp=datetime.now(UTC)
    )
    session.add(chat_log)
    session.commit()
    session.close()

async def color_command(cmd: ChatCommand):
    username = cmd.parameter.strip() or cmd.user.name
    color = get_user_color(username)
    await cmd.reply(f"{username}'s color: {color}")

async def clip_command(cmd: ChatCommand):
    clip_url = create_clip(cmd.room.name)
    # clip_url = create_clip('ourchickenlife')  # Temporary hardcoded for testing
    await cmd.reply(clip_url or "Can't create clip.")

async def run():
    twitch = await Twitch(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
    await twitch.set_user_authentication(TWITCH_OAUTH_TOKEN, USER_SCOPE, True)
    chat = await Chat(twitch)
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.MESSAGE, on_message)

    # Register commands and their aliases: !color, !clip.
    chat.register_command('color', color_command)
    chat.register_command('لون', color_command)
    chat.register_command('clip', clip_command)
    chat.register_command('c', clip_command)
    chat.register_command('كليب', clip_command)
    # Register message handler for non-prefixed commands
    chat.register_event(ChatEvent.MESSAGE, message_handler)

    chat.start()
    try:
        input('Press ENTER to stop\n')
    finally:
        chat.stop()
        await twitch.close()

if __name__ == '__main__':
    asyncio.run(run())