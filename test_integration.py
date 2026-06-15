import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import datetime

# Add the project root to the path so we can import the modules
sys.path.insert(0, os.path.abspath('.'))

from bot.storage import JsonbinStorage
from bot.notice_processor import NoticeProcessor
from bot.handlers import BotHandlers
from bot.utils.summarizer import GeminiPDFSummarizer, SummarizationError

class TestIntegration(unittest.TestCase):
    
    @patch('bot.storage.requests.get')
    def test_storage_initialization(self, mock_requests_get):
        """Test that JsonbinStorage initializes correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'record': {'users': [], 'notices': []}}
        mock_requests_get.return_value = mock_response
        
        # Test with proper environment variables
        with patch.dict(os.environ, {'JSONBIN_API_KEY': 'test_key', 'JSONBIN_BIN_ID': 'test_bin'}):
            storage = JsonbinStorage()
            self.assertIsNotNone(storage)
            mock_requests_get.assert_called_once_with('https://api.jsonbin.io/v3/b/test_bin/latest', headers={'X-Master-Key': 'test_key', 'Content-Type': 'application/json'})
    
    @patch('bot.storage.requests.put')
    @patch('bot.storage.requests.get')
    def test_storage_add_user(self, mock_requests_get, mock_requests_put):
        """Test that users can be added to storage"""
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'record': {'users': [], 'notices': []}}
        mock_requests_get.return_value = mock_get_response

        mock_put_response = MagicMock()
        mock_put_response.status_code = 200
        mock_requests_put.return_value = mock_put_response
        
        with patch.dict(os.environ, {'JSONBIN_API_KEY': 'test_key', 'JSONBIN_BIN_ID': 'test_bin'}):
            storage = JsonbinStorage()
            
            result = storage.add_user(12345, 'test_user')
            self.assertTrue(result)
            self.assertTrue(mock_requests_put.called)
    
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_summarizer_initialization(self, mock_generative_model, mock_configure):
        """Test that GeminiPDFSummarizer initializes correctly"""
        mock_model = MagicMock()
        mock_generative_model.return_value = mock_model
        
        summarizer = GeminiPDFSummarizer('test_api_key')
        self.assertIsNotNone(summarizer)
        mock_configure.assert_called_once_with(api_key='test_api_key')
        mock_generative_model.assert_called_once_with('gemini-3.5-flash')
    
    @patch('requests.get')
    @patch('bot.storage.JsonbinStorage.get_all_notice_urls')
    def test_notice_processor_scraping(self, mock_get_urls, mock_requests_get):
        """Test notice scraping functionality"""
        # Mock the response from the NEET website
        mock_response = MagicMock()
        mock_response.text = '''
        <div class="vc_tta-container">
            <div class="vc_tta-panel vc_active">
                <div class="gen-list">
                    <ul>
                        <li>
                            <a href="http://example.com/notice1.pdf">Notice 1</a>
                            <span class="date">2025-08-01</span>
                        </li>
                        <li>
                            <a href="http://example.com/notice2.pdf">Notice 2</a>
                            <span class="date">2025-08-02</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
        '''
        mock_requests_get.return_value = mock_response
        mock_get_urls.return_value = set()  # No existing notices
        
        processor = NoticeProcessor(MagicMock(), MagicMock(), 'http://neet.nta.nic.in/')
        notices = processor.scrape_notices()
        
        self.assertEqual(len(notices), 2)
        self.assertEqual(notices[0]['title'], 'Notice 2')  # Should be sorted by date, newest first
        self.assertEqual(notices[1]['title'], 'Notice 1')
    
    def test_notice_processor_download_pdf(self):
        """Test PDF download functionality"""
        processor = NoticeProcessor(MagicMock(), MagicMock(), 'http://neet.nta.nic.in/')
        
        # Mock requests.get to raise an exception
        with patch('requests.get', side_effect=Exception('Network error')):
            result = processor.download_pdf('http://example.com/notice.pdf')
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()