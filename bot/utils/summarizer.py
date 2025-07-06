import os
import google.generativeai as genai
from bot.utils.pdf_converter import PDFConverter  # Import the PDF converter

class GeminiPDFSummarizer:
    def __init__(self, api_key):
        """
        Initialize Gemini PDF Summarizer

        Args:
            api_key (str): Google Gemini API key
        """
        # Configure Gemini API
        genai.configure(api_key=api_key)

        # Initialize Gemini model (Gemini 2.0 Flash)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def summarize_pdf(self, pdf_path, cleanup=True):
        """
        Summarize a PDF using Gemini API

        Args:
            pdf_path (str): Path to the PDF file
            cleanup (bool, optional): Whether to delete temporary images. Defaults to True.

        Returns:
            str: Summary of the PDF
        """
        try:
            # Convert PDF to images
            image_paths = PDFConverter.convert_pdf_to_images(pdf_path)

            if not image_paths:
                return "Could not convert PDF to images."

            # Prepare summarization prompt
            prompt = """
            Extract a concise bullet-point summary from the provided images in simple text format, strictly avoid markdown format as this introduces * in between the message.
            The summary should only include key information that is directly relevant and important for candidates.
            DO NOT include helpline, contact information, website link etc. Focus on critical updates, dates, requirements, instructions, and other actionable points.
            Ensure each point is brief and clear, targeting the needs of exam candidates. Provide enough empty space between lines.
            """

            try:
                # Upload and process images
                images = [genai.upload_file(path) for path in image_paths]

                # Generate summary
                response = self.model.generate_content([prompt] + images)
                summary = response.text

            except Exception as e:
                summary = f"Error in Gemini summarization: {e}"

            # Optional cleanup of temporary images
            if cleanup:
                PDFConverter.cleanup_images(image_paths)

            return summary

        except Exception as e:
            return f"Error processing PDF: {e}"
