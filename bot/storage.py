import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
load_dotenv()

class SupabaseStorage:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.notices_table_name = os.getenv('SUPABASE_NOTICES_TABLE', 'notices')
        self.users_table_name = os.getenv('SUPABASE_USERS_TABLE', 'users')

        if not all([self.supabase_url, self.supabase_key]):
            logger.error("Supabase URL or Key not set in environment variables.")
            raise ValueError("Supabase credentials missing.")

        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Caching properties
        self.user_cache = None
        self.user_cache_time = None
        self.notice_urls_cache = None
        self.notice_urls_cache_time = None
        self.cache_ttl = timedelta(hours=2)

    # User management
    def add_user(self, chat_id, username=None):
        if not self.user_exists(chat_id):
            try:
                joined_date = datetime.utcnow().isoformat()
                user_data = {
                    'chat_id': chat_id,
                    'joined_date': joined_date
                }
                if username:
                    user_data['username'] = username
                
                response = self.client.table(self.users_table_name).insert(user_data).execute()
                if response.data:
                    logger.info(f"User {chat_id} added to Supabase.")
                    # Invalidate user cache on new user addition
                    self.user_cache = None
                    return True
                else:
                    logger.error(f"Error adding user {chat_id} to Supabase: {response.status_code} - {response.data}")
                    return False
            except Exception as e:
                logger.error(f"Error adding user {chat_id} to Supabase: {e}")
                return False
        logger.info(f"User {chat_id} already exists. Not adding.")
        return False

    def user_exists(self, chat_id):
        # Use the main user cache if available
        if self.user_cache is not None and (datetime.now() - self.user_cache_time < self.cache_ttl):
            return chat_id in self.user_cache

        try:
            # If cache is not valid, query the database
            response = self.client.table(self.users_table_name).select("chat_id").eq("chat_id", chat_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking if user {chat_id} exists in Supabase: {e}")
            return False

    def get_all_users(self):
        # Check if cache is valid
        if self.user_cache is not None and (datetime.now() - self.user_cache_time < self.cache_ttl):
            logger.info("Returning cached user data.")
            return self.user_cache

        logger.info("Fetching users from Supabase and updating cache.")
        try:
            response = self.client.table(self.users_table_name).select("chat_id").execute()
            self.user_cache = [record['chat_id'] for record in response.data if 'chat_id' in record]
            self.user_cache_time = datetime.now()
            return self.user_cache
        except Exception as e:
            logger.error(f"Error fetching all users from Supabase: {e}")
            return []

    # Notice management
    def add_notice(self, notice_data):
        try:
            # Check if notice already exists by title or link
            response_title = self.client.table(self.notices_table_name).select("id").eq("title", notice_data['title']).execute()
            response_link = self.client.table(self.notices_table_name).select("id").eq("link", notice_data['link']).execute()

            if response_title.data or response_link.data:
                logger.info(f"Notice '{notice_data['title']}' already exists in Supabase. Skipping.")
                return None

            # Ensure date is in ISO format if present
            if 'date' in notice_data and isinstance(notice_data['date'], datetime):
                notice_data['date'] = notice_data['date'].isoformat()
            elif 'date' in notice_data and not isinstance(notice_data['date'], str):
                notice_data['date'] = None # Clear invalid date

            response = self.client.table(self.notices_table_name).insert({
                'title': notice_data.get('title'),
                'link': notice_data.get('link'),
                'date': notice_data.get('date'),
                'summary': notice_data.get('summary', ''),
                'status': 'New'
            }).execute()
            
            if response.data:
                logger.info(f"Notice '{notice_data.get('title')}' added to Supabase.")
                # Add to live cache if cache is active
                if self.notice_urls_cache is not None:
                    self.notice_urls_cache.add(notice_data.get('link'))
                return response.data[0] # Return the first inserted record
            else:
                logger.error(f"Error adding notice to Supabase: {response.status_code} - {response.data}")
                return None
        except Exception as e:
            logger.error(f"Error adding notice to Supabase: {e}")
            return None


    def notice_exists(self, title, link):
        # This check is against processed notices, so it should always be fresh
        try:
            # Check if a notice with the same title exists and has been processed (status 'Sent')
            response_title = self.client.table(self.notices_table_name).select("id").eq("title", title).eq("status", "Sent").execute()
            if len(response_title.data) > 0:
                return True

            # Check if a notice with the same link exists and has been processed (status 'Sent')
            response_link = self.client.table(self.notices_table_name).select("id").eq("link", link).eq("status", "Sent").execute()
            if len(response_link.data) > 0:
                return True

            return False
        except Exception as e:
            logger.error(f"Error checking if notice '{title}' exists and is processed: {e}")
            return False

    def get_all_notice_urls(self):
        """Retrieves all notice URLs from the database or cache."""
        # Check if cache is valid
        if self.notice_urls_cache is not None and (datetime.now() - self.notice_urls_cache_time < self.cache_ttl):
            logger.info("Returning cached notice URLs.")
            return self.notice_urls_cache

        logger.info("Fetching notice URLs from Supabase and updating cache.")
        try:
            response = self.client.table(self.notices_table_name).select("link").execute()
            self.notice_urls_cache = {record['link'] for record in response.data if 'link' in record}
            self.notice_urls_cache_time = datetime.now()
            return self.notice_urls_cache
        except Exception as e:
            logger.error(f"Error fetching all notice URLs from Supabase: {e}")
            return set()

    def update_notice_status(self, record_id, status):
        try:
            response = self.client.table(self.notices_table_name).update({'status': status}).eq("id", record_id).execute()
            if response.data:
                logger.info(f"Notice {record_id} status updated to {status}.")
                return True
            else:
                logger.error(f"Error updating notice {record_id} status: {response.status_code} - {response.data}")
                return False
        except Exception as e:
            logger.error(f"Error updating notice {record_id} status: {e}")
            return False