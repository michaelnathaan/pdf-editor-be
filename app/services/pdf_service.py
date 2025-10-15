from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from io import BytesIO
from typing import List, Dict, Any
import os, traceback


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
        """
        import json
        from io import BytesIO
        from PyPDF2 import PdfReader, PdfWriter
        import traceback

        try:
            print("\n=== [PDF OPERATION DEBUG] ===")
            print(f"Input PDF: {input_pdf_path}")
            print(f"Output PDF: {output_pdf_path}")
            print(f"Total operations: {len(operations)}")

            for i, op in enumerate(operations):
                print(f"Operation #{i+1}: {op['operation_type']}")
                print(json.dumps(op, indent=2))

            reader = PdfReader(input_pdf_path)
            writer = PdfWriter()

            ops_by_page = {}
            for op in operations:
                op_type = op.get("operation_type")
                data = op.get("operation_data", {})

                if op_type not in ["add_image", "move_image"]:
                    print(f"Skipping unsupported op type: {op_type}")
                    continue

                page_num = data.get("page", 0)
                if page_num < 0 or page_num >= len(reader.pages):
                    print(f"⚠️ Invalid page number {page_num}, skipping operation")
                    continue

                if page_num not in ops_by_page:
                    ops_by_page[page_num] = []
                ops_by_page[page_num].append(op)

            for page_index, page in enumerate(reader.pages):
                if page_index not in ops_by_page:
                    writer.add_page(page)
                    continue

                print(f"\nProcessing page {page_index} ({len(ops_by_page[page_index])} ops)")

                overlay_pdf = PDFService._create_page_overlay(
                    page,
                    ops_by_page[page_index]
                )

                if not overlay_pdf:
                    print(f"⚠️ No overlay generated for page {page_index}")
                    writer.add_page(page)
                    continue

                try:
                    overlay_reader = PdfReader(BytesIO(overlay_pdf))
                    if len(overlay_reader.pages) == 0:
                        print(f"⚠️ Overlay has no pages for page {page_index}")
                        writer.add_page(page)
                        continue

                    page.merge_page(overlay_reader.pages[0])
                    writer.add_page(page)
                    print(f"✅ Merged overlay for page {page_index}")

                except Exception as e:
                    print(f"⚠️ Error merging overlay for page {page_index}: {e}")
                    print(traceback.format_exc())
                    writer.add_page(page)

            with open(output_pdf_path, "wb") as output_file:
                writer.write(output_file)
            print("=== [PDF OPERATION COMPLETE] ===\n")

        except Exception as e:
            print("❌ Error in apply_operations_to_pdf:", str(e))
            print(traceback.format_exc())
            raise ValueError(f"Error applying operations to PDF: {str(e)}")
    
    @staticmethod
    def _create_page_overlay(page, operations: List[Dict[str, Any]]) -> bytes:
        """
        Build a PDF overlay for a single page based on operations.
        Supports 'add_image' and 'move_image'.
        """
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        from io import BytesIO
        import traceback

        try:
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            print(f"Creating overlay for page with dimensions: {page_width}x{page_height}")
            print(f"Number of operations: {len(operations)}")

            # Merge move_image into latest add_image state
            image_ops = {}
            for op in operations:
                data = op.get("operation_data", {})
                img_id = data.get("image_id")
                if not img_id:
                    continue

                if op["operation_type"] == "add_image":
                    image_ops[img_id] = data

                elif op["operation_type"] == "move_image":
                    if img_id in image_ops:
                        image_ops[img_id]["position"] = data.get("new_position", image_ops[img_id].get("position"))
                        if "rotation" in data:
                            image_ops[img_id]["rotation"] = data["rotation"]
                    else:
                        print(f"⚠️ move_image found for {img_id} before add_image, skipping")

            if not image_ops:
                print("⚠️ No images to draw on overlay")
                return None

            packet = BytesIO()
            c = canvas.Canvas(packet, pagesize=(page_width, page_height))

            for idx, img_data in enumerate(image_ops.values()):
                img_path = img_data.get("image_path")
                pos = img_data.get("position", {})
                if not img_path:
                    print(f"⚠️ Image {idx} missing image_path, skipping")
                    continue

                x = float(pos.get("x", 0))
                y = float(pos.get("y", 0))
                w = float(pos.get("width", 100))
                h = float(pos.get("height", 100))
                rotation = float(img_data.get("rotation", 0))
                opacity = float(img_data.get("opacity", 1.0))

                # Flip Y coordinate for reportlab
                y_flipped = page_height - y - h

                print(f"Drawing image {idx}: {img_path}")
                print(f"  Position: x={x}, y={y} (flipped {y_flipped})")
                print(f"  Size: {w}x{h}, rotation={rotation}, opacity={opacity}")

                try:
                    pdf_y = page_height - y - h
                    center_x = x + w / 2
                    center_y = pdf_y + h / 2
                    c.saveState()
                    c.translate(center_x, center_y)
                    if rotation:
                        c.rotate(-rotation)
                    c.drawImage(
                        ImageReader(img_path), 
                        -w/2, 
                        -h/2, 
                        width=w, 
                        height=h, 
                        mask='auto'
                    )
                    c.restoreState()
                    print("  ✅ Successfully drawn")
                except Exception as e:
                    print(f"  ⚠️ Failed to draw image {idx}: {e}")
                    print(traceback.format_exc())


            c.save()
            packet.seek(0)
            print(f"Overlay created successfully with {len(image_ops)} images")
            return packet.read()

        except Exception as e:
            print(f"❌ Error in _create_page_overlay: {e}")
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