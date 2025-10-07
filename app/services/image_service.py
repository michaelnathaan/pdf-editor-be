from PIL import Image
from typing import Tuple, Optional


class ImageService:
    """Service for image processing operations"""
    
    @staticmethod
    def get_image_dimensions(image_path: str) -> Tuple[int, int]:
        """Get image width and height"""
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            raise ValueError(f"Error reading image: {str(e)}")
    
    @staticmethod
    def validate_image(image_path: str) -> bool:
        """Validate if file is a valid image"""
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except:
            return False
    
    @staticmethod
    def optimize_image(
        image_path: str,
        output_path: str,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        quality: int = 85
    ) -> Tuple[int, int]:
        """
        Optimize image size and quality
        Returns: (width, height) of optimized image
        """
        try:
            with Image.open(image_path) as img:
                # Convert RGBA to RGB if saving as JPEG
                if img.mode == 'RGBA' and output_path.lower().endswith(('.jpg', '.jpeg')):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                
                # Resize if needed
                if max_width or max_height:
                    img.thumbnail((max_width or img.width, max_height or img.height), Image.Resampling.LANCZOS)
                
                # Save optimized
                img.save(output_path, quality=quality, optimize=True)
                return img.size
                
        except Exception as e:
            raise ValueError(f"Error optimizing image: {str(e)}")
    
    @staticmethod
    def get_mime_type(image_path: str) -> str:
        """Get MIME type of image"""
        try:
            with Image.open(image_path) as img:
                format_to_mime = {
                    'JPEG': 'image/jpeg',
                    'PNG': 'image/png',
                    'GIF': 'image/gif',
                    'WEBP': 'image/webp',
                    'BMP': 'image/bmp',
                }
                return format_to_mime.get(img.format, 'image/unknown')
        except:
            return 'image/unknown'