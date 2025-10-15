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
                "page": 0,  # 0-based page index
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
                    
                    # Ensure page number is valid
                    if page_num < 0 or page_num >= len(reader.pages):
                        print(f"Warning: Invalid page number {page_num}, skipping operation")
                        continue
                    
                    if page_num not in ops_by_page:
                        ops_by_page[page_num] = []
                    ops_by_page[page_num].append(op)

            for page_index in range(len(reader.pages)):
                page = reader.pages[page_index]
                
                # Check if this page has operations
                if page_index in ops_by_page:
                    # Create overlay with images
                    overlay_pdf = PDFService._create_page_overlay(
                        page,
                        ops_by_page[page_index]
                    )
                    
                    # Only merge if overlay was created successfully and has content
                    if overlay_pdf:
                        try:
                            overlay_reader = PdfReader(BytesIO(overlay_pdf))
                            # Check if overlay has pages before merging
                            if len(overlay_reader.pages) > 0:
                                page.merge_page(overlay_reader.pages[0])
                            else:
                                print(f"Warning: Overlay PDF has no pages for page {page_index}")
                        except Exception as e:
                            print(f"Warning: Could not merge overlay for page {page_index}: {str(e)}")
                
                writer.add_page(page)
            
            # Write output
            with open(output_pdf_path, 'wb') as output_file:
                writer.write(output_file)
                
        except Exception as e:
            import traceback
            print(f"Error in apply_operations_to_pdf: {str(e)}")
            print(traceback.format_exc())
            raise ValueError(f"Error applying operations to PDF: {str(e)}")
    
    @staticmethod
    def _create_page_overlay(page, operations: List[Dict[str, Any]]) -> bytes:
        """Create a PDF overlay with images for a single page"""
        try:
            # Get page dimensions
            box = page.mediabox
            page_width = float(box.width)
            page_height = float(box.height)
            
            print(f"Creating overlay for page with dimensions: {page_width}x{page_height}")
            print(f"Number of operations: {len(operations)}")
            
            # Track if we have any valid images
            valid_images_count = 0
            
            # Create in-memory PDF
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
            
            # Add each image
            for idx, op in enumerate(operations):
                try:
                    data = op["operation_data"]
                    image_path = data.get("image_path")
                    pos = data.get("position", {})
                    
                    if not image_path:
                        print(f"Warning: Operation {idx} has no image_path")
                        continue
                    
                    if not os.path.exists(image_path):
                        print(f"Warning: Image file not found: {image_path}")
                        continue
                    
                    x = pos.get("x", 0)
                    y = pos.get("y", 0)
                    width = pos.get("width", 100)
                    height = pos.get("height", 100)
                    
                    # PDF coordinates start from bottom, so we need to flip Y
                    y_flipped = page_height - y - height
                    
                    print(f"Drawing image {idx}: {image_path}")
                    print(f"  Position: x={x}, y={y} (flipped to {y_flipped})")
                    print(f"  Size: {width}x{height}")
                    
                    # Handle rotation if specified
                    rotation = data.get("rotation", 0)
                    opacity = data.get("opacity", 1.0)
                    
                    # Load and draw image
                    img = ImageReader(image_path)
                    
                    if rotation != 0:
                        c.saveState()
                        # Rotate around center of image
                        cx = x + width / 2
                        cy = y_flipped + height / 2
                        c.translate(cx, cy)
                        c.rotate(rotation)
                        c.translate(-cx, -cy)
                    
                    if opacity < 1.0:
                        c.setFillAlpha(opacity)
                    
                    c.drawImage(img, x, y_flipped, width=width, height=height, preserveAspectRatio=False)
                    
                    if rotation != 0:
                        c.restoreState()
                    
                    valid_images_count += 1
                    print(f"  Successfully drawn")
                    
                except Exception as e:
                    print(f"Error processing operation {idx}: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    continue
            
            # Only return overlay if we successfully drew at least one image
            if valid_images_count == 0:
                print("No valid images to draw, skipping overlay creation")
                return None
            
            c.save()
            buffer.seek(0)
            print(f"Overlay created successfully with {valid_images_count} images")
            return buffer.getvalue()
            
        except Exception as e:
            print(f"Error creating overlay: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def validate_pdf(file_path: str) -> bool:
        """Validate if file is a valid PDF"""
        try:
            reader = PdfReader(file_path)
            return len(reader.pages) > 0
        except:
            return False