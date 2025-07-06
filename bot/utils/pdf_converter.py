import os
import logging
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

class PDFConverter:
    @staticmethod
    def convert_pdf_to_images(pdf_path, output_dir='data/temp'):
        """
        Convert a PDF file to images.

        Args:
            pdf_path (str): Path to the PDF file
            output_dir (str, optional): Directory to save images. Defaults to 'pdf_images'.

        Returns:
            list: Paths to the generated image files
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Convert PDF to images
            images = convert_from_path(pdf_path)

            # Store image paths
            image_paths = []

            # Save images
            for i, image in enumerate(images):
                # Generate unique filename
                filename = os.path.join(
                    output_dir,
                    f'page_{i+1}.png'
                )

                # Save image
                image.save(filename, 'PNG')
                image_paths.append(filename)

            return image_paths

        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            return []

    @staticmethod
    def cleanup_images(image_paths):
        """
        Remove generated image files.

        Args:
            image_paths (list): List of image file paths to delete
        """
        for path in image_paths:
            try:
                os.remove(path)
            except Exception as e:
                logger.error(f"Error deleting image {path}: {e}")
                
    @staticmethod
    def validate_pdf_before_conversion(pdf_path):
        """
        Validate PDF file before attempting conversion.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return False
            
        if os.path.getsize(pdf_path) < 100:  # Basic size check
            logger.error(f"PDF file too small (possibly corrupt): {pdf_path}")
            return False
            
        return True