"""QR code generation utilities for mobile interface access."""

import qrcode
import io
import base64
from PIL import Image


def generate_qr_code(url: str, size: int = 200) -> str:
    """
    Generate a QR code for the given URL and return it as a base64 data URI.
    
    Args:
        url: The URL to encode in the QR code
        size: Size of the QR code image in pixels
        
    Returns:
        Base64 data URI string for use in img src attribute
    """
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR code
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add data
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create image
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Resize if needed
    if qr_image.size[0] != size:
        qr_image = qr_image.resize((size, size), Image.Resampling.NEAREST)
    
    # Convert to base64 data URI
    img_buffer = io.BytesIO()
    qr_image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    img_base64 = base64.b64encode(img_buffer.read()).decode()
    data_uri = f"data:image/png;base64,{img_base64}"
    
    return data_uri


def get_mobile_url(request_url: str = None) -> str:
    """
    Generate the mobile interface URL based on the current request.
    
    Args:
        request_url: Current request URL to derive base URL
        
    Returns:
        Complete URL to the mobile interface
    """
    if request_url:
        # Extract base URL from request
        if "/big-screen" in request_url:
            base_url = request_url.replace("/big-screen", "")
        else:
            base_url = request_url.rstrip("/")
    else:
        # Default fallback
        base_url = "http://localhost:3000"
    
    return base_url