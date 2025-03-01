from models import Session, ChatHistory, ChannelConfig, BotSettings, UserAccess
from datetime import datetime

class DatabaseHandler:
    def __init__(self):
        self.session = Session()
    
    def add_chat_history(self, user_id, message, response):
        chat_entry = ChatHistory(
            user_id=user_id,
            message=message,
            response=response,
            timestamp=datetime.utcnow()
        )
        self.session.add(chat_entry)
        self.session.commit()
    
    def get_chat_history(self, user_id, limit=10):
        return self.session.query(ChatHistory)\
            .filter(ChatHistory.user_id == user_id)\
            .order_by(ChatHistory.timestamp.desc())\
            .limit(limit)\
            .all()
    
    def set_channel(self, guild_id, channel_id):
        config = self.session.query(ChannelConfig)\
            .filter(ChannelConfig.guild_id == guild_id)\
            .first()
        
        if config:
            config.channel_id = channel_id
        else:
            config = ChannelConfig(guild_id=guild_id, channel_id=channel_id)
            self.session.add(config)
        
        self.session.commit()
    
    def get_channel(self, guild_id):
        config = self.session.query(ChannelConfig)\
            .filter(ChannelConfig.guild_id == guild_id)\
            .first()
        return config.channel_id if config else None
    
    def update_temperature(self, temperature):
        settings = self.session.query(BotSettings).first()
        
        if not settings:
            settings = BotSettings()
            self.session.add(settings)
        
        settings.temperature = temperature
        self.session.commit()
    
    def get_settings(self):
        settings = self.session.query(BotSettings).first()
        if not settings:
            settings = BotSettings()
            self.session.add(settings)
            self.session.commit()
        return settings
    
    def set_user_access(self, user_id, is_blacklisted, modified_by):
        user_access = self.session.query(UserAccess).filter(
            UserAccess.user_id == user_id
        ).first()
        
        if user_access:
            user_access.is_blacklisted = is_blacklisted
            user_access.modified_at = datetime.utcnow()
            user_access.modified_by = modified_by
        else:
            user_access = UserAccess(
                user_id=user_id,
                is_blacklisted=is_blacklisted,
                modified_by=modified_by
            )
            self.session.add(user_access)
            
        self.session.commit()
    
    def is_user_blacklisted(self, user_id):
        user_access = self.session.query(UserAccess).filter(
            UserAccess.user_id == user_id
        ).first()
        return user_access.is_blacklisted if user_access else False
