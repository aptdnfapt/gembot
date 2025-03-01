from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
import datetime

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class ChatHistory(Base):
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    message = Column(String)
    response = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class ChannelConfig(Base):
    __tablename__ = 'channel_config'
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(String)
    channel_id = Column(String)

class BotSettings(Base):
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True)
    temperature = Column(Float, default=0.7)

class UserAccess(Base):
    __tablename__ = 'user_access'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True)
    is_blacklisted = Column(Boolean, default=False)
    modified_at = Column(DateTime, default=datetime.datetime.utcnow)
    modified_by = Column(String)

# Create all tables
Base.metadata.create_all(engine)
