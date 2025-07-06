import os
import logging
import requests
import datetime
from bs4 import BeautifulSoup
import time

from bot.utils.summarizer import GeminiPDFSummarizer
from bot.storage import SupabaseStorage

logger = logging.getLogger(__name__)

class NoticeProcessor:
    def __init__(self, summarizer: GeminiPDFSummarizer, storage: SupabaseStorage, neet_website_url: str):
        self.summarizer = summarizer
        self.storage = storage
        self.neet_website_url = neet_website_url
        os.makedirs('data/temp', exist_ok=True) # Ensure temp directory exists

    def scrape_notices(self, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = requests.get(self.neet_website_url, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')

                notices_container = soup.find('div', {'class': 'vc_tta-container'})
                if not notices_container:
                    logger.error("Could not find notices container.")
                    continue
                
                active_panel = notices_container.find('div', {'class': 'vc_tta-panel vc_active'})
                if not active_panel:
                    logger.error("Could not find active notices panel.")
                    continue
                
                notices_list_container = active_panel.find('div', {'class': 'gen-list'})
                if not notices_list_container:
                    logger.error("Could not find notices list container.")
                    continue

                notices_list = notices_list_container.find('ul')
                if not notices_list:
                    logger.error("Could not find notices list.")
                    continue

                new_notices = []
                # Fetch existing notice URLs once
                existing_notice_urls = self.storage.get_all_notice_urls()
                logger.info(f"Fetched {len(existing_notice_urls)} existing notice URLs.")

                for li in notices_list.find_all('li'):
                    anchor = li.find('a')
                    notice_title = anchor.text.strip()
                    notice_link = anchor['href']

                    date_element = li.find('span', {'class': lambda x: x and 'date' in x.lower()})
                    if date_element:
                        date_string = date_element.text.strip()
                        try:
                            notice_date = datetime.datetime.strptime(date_string, '%d-%m-%Y')
                        except ValueError:
                            try:
                                notice_date = datetime.datetime.strptime(date_string, '%Y-%m-%d')
                            except ValueError:
                                logger.error(f"Could not parse date: {date_string}")
                                notice_date = None
                    else:
                        notice_date = None

                    # Check against the local set instead of repeated DB calls
                    if notice_link not in existing_notice_urls:
                        new_notices.append({
                            'title': notice_title,
                            'link': notice_link,
                            'date': notice_date
                        })

                # Sort notices by date (most recent first)
                new_notices = sorted(new_notices, key=lambda x: x['date'] if x['date'] else datetime.datetime.min, reverse=True)
                return new_notices

            except Exception as e:
                logger.error(f"Error scraping notices (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                
        return []

    def download_pdf(self, pdf_url, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = requests.get(pdf_url, timeout=30)
                if not response.headers.get('content-type', '').startswith('application/pdf'):
                    logger.error("Downloaded file is not a PDF")
                    return None

                pdf_path = os.path.join('data/temp', 'current_notice.pdf')
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)

                if os.path.getsize(pdf_path) < 100:
                    logger.error("Downloaded PDF file is too small")
                    os.remove(pdf_path)
                    return None

                return pdf_path

            except Exception as e:
                logger.error(f"PDF download error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)

        return None

    def send_telegram_alerts(self, bot, notice, summary, user_ids):
        for user_id in user_ids:
            try:
                alert_message = f"""
🚨New NEET Notice!🚨
Title: {notice['title']}
PDF Link: {notice['link']}
                """
                bot.send_message(user_id, alert_message)

                summary_message = f"""
📋 Notice Summary:
{summary}
                """
                bot.send_message(user_id, summary_message)

            except Exception as e:
                logger.error(f"Telegram message send error to user {user_id}: {e}")

    def process_new_notices(self, bot):
        try:
            logger.info("Checking for new notices")
            new_notices = self.scrape_notices()
            logger.info(f"Found {len(new_notices)} new notices")

            # Fetch all users once before the loop
            all_users = self.storage.get_all_users()
            logger.info(f"Fetched {len(all_users)} users.")

            for notice in new_notices:
                try:
                    logger.info(f"Processing notice: {notice['title']}")
                    pdf_path = self.download_pdf(notice['link'])
                    if not pdf_path:
                        continue

                    logger.info("Generating summary using Gemini")
                    summary = self.summarizer.summarize_pdf(pdf_path)

                    # Add notice to Airtable with summary
                    added_record = self.storage.add_notice({
                        'title': notice['title'],
                        'link': notice['link'],
                        'date': notice['date'],
                        'summary': summary,
                        'status': 'Sent' # Mark as sent after processing
                    })

                    if added_record:
                        logger.info("Sending alerts to users")
                        # Pass the fetched user list to the alert method
                        self.send_telegram_alerts(bot, notice, summary, all_users)
                        logger.info("Notice processed successfully")
                    else:
                        logger.warning(f"Notice '{notice['title']}' was not added to Airtable, skipping alerts.")

                    try:
                        os.remove(pdf_path)
                    except Exception as e:
                        logger.error(f"Error removing temporary PDF: {e}")

                except Exception as e:
                    logger.error(f"Notice processing error: {e}")

        except Exception as e:
            logger.error(f"Error in process_new_notices: {e}")