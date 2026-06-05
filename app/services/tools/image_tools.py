import pytesseract
from PIL import Image, ImageChops
from io import BytesIO
from langchain.tools import tool
from app.core.database import get_gridfs
from bson import ObjectId
import statistics
import logging

logger = logging.getLogger(__name__)

def error_level_analysis(image_bytes: bytes, quality: int = 95) -> float:
    """
    Performs Error Level Analysis (ELA) to detect visual tampering.
    Returns a score representing the standard deviation of the difference.
    """
    original = Image.open(BytesIO(image_bytes)).convert("RGB")
    
    # Save at specified quality and reopen
    buffer = BytesIO()
    original.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    resaved = Image.open(buffer)
    
    # Calculate absolute difference
    diff = ImageChops.difference(original, resaved)
    
    # Analyze the difference image
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    
    scale = 255.0 / max_diff
    diff = ImageChops.multiply(diff, Image.new("RGB", diff.size, (int(scale), int(scale), int(scale))))
    
    # Calculate standard deviation as a tampering score
    stat = ImageChops.difference(original, resaved).convert("L")
    pixel_values = list(stat.getdata())
    
    if not pixel_values:
        return 0.0
        
    return statistics.stdev(pixel_values)

@tool
async def ocr_extract_text(gridfs_doc_id: str, bucket_name: str = "certificates") -> str:
    """
    Extracts text from an image (certificate) using OCR.
    Args:
        gridfs_doc_id: The ObjectId string of the file in GridFS.
        bucket_name: The GridFS bucket name ("resumes" or "certificates").
    """
    try:
        bucket = get_gridfs(bucket_name)
        grid_out = await bucket.open_download_stream(ObjectId(gridfs_doc_id))
        image_bytes = await grid_out.read()
        
        img = Image.open(BytesIO(image_bytes))
        text = pytesseract.image_to_string(img)
        return text.strip() if text else "No text found via OCR."
    except Exception as e:
        logger.error(f"OCR error on {bucket_name}: {str(e)}")
        return f"Error during OCR: {str(e)}"

@tool
async def analyze_certificate_image(gridfs_doc_id: str) -> dict:
    """
    Comprehensive certificate analysis: OCR + ELA.
    Args:
        gridfs_doc_id: The ObjectId string of the file in GridFS (certificates bucket).
    """
    try:
        bucket = get_gridfs("certificates")
        grid_out = await bucket.open_download_stream(ObjectId(gridfs_doc_id))
        image_bytes = await grid_out.read()
        
        # ELA
        ela_score = error_level_analysis(image_bytes)
        
        # OCR
        img = Image.open(BytesIO(image_bytes))
        ocr_text = pytesseract.image_to_string(img).strip()
        
        return {
            "ela_score": float(ela_score),
            "ocr_text": ocr_text,
            "suspicious_editing": ela_score > 15.0
        }
    except Exception as e:
        logger.error(f"Certificate analysis error: {str(e)}")
        return {"error": str(e)}
