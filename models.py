from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
import datetime

# Create base class for declarative models
Base = declarative_base()

# Create database engine
engine = create_engine(DATABASE_URL)

# Create session factory
Session = sessionmaker(bind=engine)

class ChatHistory(Base):
    """Store chat history for each user"""
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    message = Column(String, nullable=False)
    response = Column(String, nullable=False)
    timestamp = Column(
        DateTime, 
        default=datetime.datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<ChatHistory(user_id='{self.user_id}', timestamp='{self.timestamp}')>"

class ChannelConfig(Base):
    """Store channel configuration for each guild"""
    __tablename__ = 'channel_config'
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(String, nullable=False)
    channel_id = Column(String, nullable=False)
    created_at = Column(
        DateTime, 
        default=datetime.datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<ChannelConfig(guild_id='{self.guild_id}', channel_id='{self.channel_id}')>"

class BotSettings(Base):
    """Store global bot settings"""
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True)
    temperature = Column(Float, default=0.7, nullable=False)
    created_at = Column(
        DateTime, 
        default=datetime.datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<BotSettings(temperature={self.temperature})>"

class UserAccess(Base):
    """Store user access controls (blacklist/whitelist)"""
    __tablename__ = 'user_access'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    is_blacklisted = Column(Boolean, default=False, nullable=False)
    modified_at = Column(
        DateTime, 
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False
    )
    modified_by = Column(String, nullable=False)
    reason = Column(String, nullable=True)  # Optional reason for blacklist/whitelist

    def __repr__(self):
        status = "blacklisted" if self.is_blacklisted else "whitelisted"
        return f"<UserAccess(user_id='{self.user_id}', status='{status}')>"

def init_db():
    """Initialize the database by creating all tables"""
    try:
        Base.metadata.create_all(engine)
        print("Database initialized successfully!")
        
        # Create initial bot settings if they don't exist
        session = Session()
        if not session.query(BotSettings).first():
            initial_settings = BotSettings()
            session.add(initial_settings)
            session.commit()
            print("Initial bot settings created!")
        session.close()
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

# Create tables when the module is imported
if __name__ == "__main__":
    print(f"Initializing database at {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    init_db()
    print("Database setup complete!")
