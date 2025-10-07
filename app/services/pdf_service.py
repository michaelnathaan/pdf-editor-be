from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from io import BytesIO
from typing import List, Dict, Any
import os


class PDFService:
    """Service for PDF manipulation operations"""
    
    @staticmethod
    def get_page_count(pdf_path: str) -> int:
        """Get number of pages in PDF"""
        try:
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception as e:
            raise ValueError(f"Error reading PDF: {str(e)}")
    
    @staticmethod
    def get_page_size(pdf_path: str, page_number: int = 0) -> tuple[float, float]:
        """Get page size (width, height) in points"""
        try:
            reader = PdfReader(pdf_path)
            page = reader.pages[page_number]
            box = page.mediabox
            return (float(box.width), float(box.height))
        except Exception as e:
            raise ValueError(f"Error getting page size: {str(e)}")
    
    @staticmethod
    def apply_operations_to_pdf(
        input_pdf_path: str,
        output_pdf_path: str,
        operations: List[Dict[str, Any]]
    ) -> None:
        """
        Apply all operations to PDF and save result
        
        Operations format:
        {
            "operation_type": "add_image",
            "operation_data": {
                "page": 1,
                "image_path": "/path/to/image.png",
                "position": {"x": 100, "y": 200, "width": 300, "height": 200},
                "rotation": 0,
                "opacity": 1.0
            }
        }
        """
        try:

            reader = PdfReader(input_pdf_path)
            writer = PdfWriter()

            ops_by_page = {}
            for op in operations:
                if op["operation_type"] == "add_image":
                    page_num = op["operation_data"]["page"]
                    if page_num not in ops_by_page:
                        ops_by_page[page_num] = []
                    ops_by_page[page_num].append(op)

            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                
                if page_num in ops_by_page:
                    overlay_pdf = PDFService._create_page_overlay(
                        page,
                        ops_by_page[page_num]
                    )
                    
                    if overlay_pdf:
                        overlay_reader = PdfReader(BytesIO(overlay_pdf))
                        page.merge_page(overlay_reader.pages[0])
                
                writer.add_page(page)

            with open(output_pdf_path, 'wb') as output_file:
                writer.write(output_file)
                
        except Exception as e:
            raise ValueError(f"Error applying operations to PDF: {str(e)}")
    
    @staticmethod
    def _create_page_overlay(page, operations: List[Dict[str, Any]]) -> bytes:
        """Create a PDF overlay with images for a single page"""
        try:
            box = page.mediabox
            page_width = float(box.width)
            page_height = float(box.height)
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

            for op in operations:
                data = op["operation_data"]
                image_path = data["image_path"]
                pos = data["position"]
                
                x = pos["x"]
                y = page_height - pos["y"] - pos["height"] 
                width = pos["width"]
                height = pos["height"]

                rotation = data.get("rotation", 0)
                opacity = data.get("opacity", 1.0)
                
                if os.path.exists(image_path):
                    img = ImageReader(image_path)
                    
                    if rotation != 0:
                        c.saveState()
                        cx = x + width / 2
                        cy = y + height / 2
                        c.translate(cx, cy)
                        c.rotate(rotation)
                        c.translate(-cx, -cy)
                    
                    if opacity < 1.0:
                        c.setFillAlpha(opacity)
                    
                    c.drawImage(img, x, y, width=width, height=height, preserveAspectRatio=False)
                    
                    if rotation != 0:
                        c.restoreState()
            
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Error creating overlay: {str(e)}")
            return None
    
    @staticmethod
    def validate_pdf(file_path: str) -> bool:
        """Validate if file is a valid PDF"""
        try:
            reader = PdfReader(file_path)
            return len(reader.pages) > 0
        except:
            return False