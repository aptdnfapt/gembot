from models import Session, ChatHistory, ChannelConfig, BotSettings, UserAccess
from datetime import datetime
import traceback
from config import DEBUG_MODE, MAX_HISTORY_LENGTH

class DatabaseHandler:
    def __init__(self):
        """Initialize database handler with session and logging"""
        self.session = Session()
        self.startup_time = datetime.utcnow()
        print(f"Database Handler initialized at {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    def log_error(self, operation, error):
        """Log database operation errors"""
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        error_message = f"[{current_time}] Database Error in {operation}: {str(error)}"
        if DEBUG_MODE:
            error_message += f"\n{traceback.format_exc()}"
        print(error_message)

    def log_operation(self, operation, details=""):
        """Log database operations in debug mode"""
        if DEBUG_MODE:
            current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{current_time}] Database Operation - {operation}: {details}")

    def add_chat_history(self, user_id, message, response):
        """Add a new chat history entry"""
        try:
            # Create new chat history entry
            chat_entry = ChatHistory(
                user_id=user_id,
                message=message,
                response=response,
                timestamp=datetime.utcnow()
            )
            self.session.add(chat_entry)
            self.session.commit()
            
            self.log_operation("add_chat_history", f"User: {user_id}")
            
            # Cleanup old entries if needed
            self._cleanup_old_history(user_id)
            
        except Exception as e:
            self.log_error("add_chat_history", e)
            self.session.rollback()
            raise

    def _cleanup_old_history(self, user_id):
        """Clean up old chat history entries beyond MAX_HISTORY_LENGTH"""
        try:
            # Get all entries for user, ordered by timestamp
            entries = self.session.query(ChatHistory)\
                .filter(ChatHistory.user_id == user_id)\
                .order_by(ChatHistory.timestamp.desc())\
                .all()
            
            # If we have more entries than MAX_HISTORY_LENGTH, remove the oldest ones
            if len(entries) > MAX_HISTORY_LENGTH:
                for entry in entries[MAX_HISTORY_LENGTH:]:
                    self.session.delete(entry)
                self.session.commit()
                self.log_operation("cleanup_history", f"Removed {len(entries) - MAX_HISTORY_LENGTH} old entries for user {user_id}")
                
        except Exception as e:
            self.log_error("cleanup_history", e)
            self.session.rollback()

    def get_chat_history(self, user_id, limit=MAX_HISTORY_LENGTH):
        """Get chat history for a user"""
        try:
            history = self.session.query(ChatHistory)\
                .filter(ChatHistory.user_id == user_id)\
                .order_by(ChatHistory.timestamp.desc())\
                .limit(limit)\
                .all()
            
            self.log_operation("get_chat_history", f"User: {user_id}, Entries: {len(history)}")
            return history
            
        except Exception as e:
            self.log_error("get_chat_history", e)
            return []

    def set_channel(self, guild_id, channel_id):
        """Set or update the primary channel for a guild"""
        try:
            config = self.session.query(ChannelConfig)\
                .filter(ChannelConfig.guild_id == guild_id)\
                .first()
            
            if config:
                config.channel_id = channel_id
                config.updated_at = datetime.utcnow()
            else:
                config = ChannelConfig(
                    guild_id=guild_id,
                    channel_id=channel_id
                )
                self.session.add(config)
            
            self.session.commit()
            self.log_operation("set_channel", f"Guild: {guild_id}, Channel: {channel_id}")
            
        except Exception as e:
            self.log_error("set_channel", e)
            self.session.rollback()
            raise

    def get_channel(self, guild_id):
        """Get the primary channel for a guild"""
        try:
            config = self.session.query(ChannelConfig)\
                .filter(ChannelConfig.guild_id == guild_id)\
                .first()
            
            channel_id = config.channel_id if config else None
            self.log_operation("get_channel", f"Guild: {guild_id}, Channel: {channel_id}")
            return channel_id
            
        except Exception as e:
            self.log_error("get_channel", e)
            return None

    def update_temperature(self, temperature):
        """Update the global temperature setting"""
        try:
            settings = self.session.query(BotSettings).first()
            
            if not settings:
                settings = BotSettings()
                self.session.add(settings)
            
            settings.temperature = temperature
            settings.updated_at = datetime.utcnow()
            
            self.session.commit()
            self.log_operation("update_temperature", f"New temperature: {temperature}")
            
        except Exception as e:
            self.log_error("update_temperature", e)
            self.session.rollback()
            raise

    def get_settings(self):
        """Get global bot settings"""
        try:
            settings = self.session.query(BotSettings).first()
            
            if not settings:
                settings = BotSettings()
                self.session.add(settings)
                self.session.commit()
            
            self.log_operation("get_settings", f"Temperature: {settings.temperature}")
            return settings
            
        except Exception as e:
            self.log_error("get_settings", e)
            return BotSettings()

    def set_user_access(self, user_id, is_blacklisted, modified_by, reason=None):
        """Set user access (blacklist/whitelist)"""
        try:
            user_access = self.session.query(UserAccess)\
                .filter(UserAccess.user_id == user_id)\
                .first()
            
            if user_access:
                user_access.is_blacklisted = is_blacklisted
                user_access.modified_at = datetime.utcnow()
                user_access.modified_by = modified_by
                user_access.reason = reason
            else:
                user_access = UserAccess(
                    user_id=user_id,
                    is_blacklisted=is_blacklisted,
                    modified_by=modified_by,
                    reason=reason
                )
                self.session.add(user_access)
            
            self.session.commit()
            status = "blacklisted" if is_blacklisted else "whitelisted"
            self.log_operation("set_user_access", f"User: {user_id} {status}")
            
        except Exception as e:
            self.log_error("set_user_access", e)
            self.session.rollback()
            raise

    def is_user_blacklisted(self, user_id):
        """Check if a user is blacklisted"""
        try:
            user_access = self.session.query(UserAccess)\
                .filter(UserAccess.user_id == user_id)\
                .first()
            
            is_blacklisted = user_access.is_blacklisted if user_access else False
            self.log_operation("check_blacklist", f"User: {user_id}, Blacklisted: {is_blacklisted}")
            return is_blacklisted
            
        except Exception as e:
            self.log_error("check_blacklist", e)
            return False

    def get_database_stats(self):
        """Get database statistics"""
        try:
            stats = {
                "total_messages": self.session.query(ChatHistory).count(),
                "total_users": self.session.query(ChatHistory.user_id.distinct()).count(),
                "blacklisted_users": self.session.query(UserAccess)\
                    .filter(UserAccess.is_blacklisted == True).count(),
                "configured_channels": self.session.query(ChannelConfig).count(),
                "uptime": str(datetime.utcnow() - self.startup_time)
            }
            return stats
            
        except Exception as e:
            self.log_error("get_stats", e)
            return {}

    def cleanup(self):
        """Clean up database connection"""
        try:
            self.session.close()
            self.log_operation("cleanup", "Database connection closed")
        except Exception as e:
            self.log_error("cleanup", e)

if __name__ == "__main__":
    # Test database operations
    db = DatabaseHandler()
    print("\nDatabase Stats:")
    stats = db.get_database_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    db.cleanup()
