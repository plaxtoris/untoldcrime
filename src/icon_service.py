"""Dynamic icon generation service."""
from pathlib import Path
from PIL import Image
import io
from fastapi import Response
from typing import Optional

class IconService:
    def __init__(self, source_path: str = "src/static/logo.png"):
        self.source_path = Path(source_path)
        self._source_image: Optional[Image.Image] = None
    
    @property
    def source_image(self) -> Image.Image:
        """Lazy load and cache the source image."""
        if self._source_image is None:
            self._source_image = Image.open(self.source_path)
            # Convert to RGB if necessary
            if self._source_image.mode != 'RGB':
                self._source_image = self._source_image.convert('RGB')
        return self._source_image
    
    def generate_icon(self, size: int, format: str = "PNG") -> bytes:
        """Generate icon of specified size."""
        # Create a copy and resize
        img = self.source_image.copy()
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        
        # Create square canvas with transparent background for PNG
        if format.upper() == "PNG":
            canvas = Image.new('RGBA', (size, size), (255, 255, 255, 0))
            # Center the image
            offset = ((size - img.width) // 2, (size - img.height) // 2)
            # Convert to RGBA for pasting
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            canvas.paste(img, offset)
        else:
            canvas = img
        
        # Save to bytes
        buffer = io.BytesIO()
        canvas.save(buffer, format=format)
        buffer.seek(0)
        return buffer.read()
    
    def generate_favicon(self) -> bytes:
        """Generate multi-resolution ICO file."""
        # ICO can contain multiple sizes
        sizes = [16, 32, 48]
        images = []
        
        for size in sizes:
            img = self.source_image.copy()
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            # Ensure it's exactly square
            canvas = Image.new('RGB', (size, size), (255, 255, 255))
            offset = ((size - img.width) // 2, (size - img.height) // 2)
            canvas.paste(img, offset)
            images.append(canvas)
        
        # Save as ICO
        buffer = io.BytesIO()
        images[0].save(buffer, format='ICO', sizes=[(s, s) for s in sizes])
        buffer.seek(0)
        return buffer.read()

# Global instance
icon_service = IconService()