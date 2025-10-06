"""Dynamic image optimization and caching."""

from pathlib import Path
from PIL import Image
import hashlib
import logging

logger = logging.getLogger(__name__)

# Cache directory for optimized images
CACHE_DIR = Path(__file__).parent.parent / "data" / ".image_cache"


def get_optimized_image(
    original_path: Path,
    width: int,
    quality: int = 85,
    format: str = "WEBP"
) -> Path:
    """Get optimized version of an image, creating it if needed.

    Args:
        original_path: Path to original image
        width: Target width in pixels
        quality: JPEG/WEBP quality (1-100)
        format: Output format (WEBP, JPEG, PNG)

    Returns:
        Path to optimized image
    """
    if not original_path.exists():
        raise FileNotFoundError(f"Original image not found: {original_path}")

    # Create cache directory
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate cache filename based on parameters
    cache_key = f"{original_path.stem}_{width}_{quality}_{format.lower()}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()[:16]

    extension = "webp" if format == "WEBP" else format.lower()
    cached_file = CACHE_DIR / f"{cache_hash}.{extension}"

    # Return cached version if exists
    if cached_file.exists():
        logger.debug(f"Serving cached image: {cached_file.name}")
        return cached_file

    # Create optimized version
    try:
        logger.info(f"Creating optimized image: {width}px, {format}, quality={quality}")

        with Image.open(original_path) as img:
            # Convert RGBA to RGB for JPEG
            if format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = rgb_img

            # Calculate new height maintaining aspect ratio
            aspect_ratio = img.height / img.width
            height = int(width * aspect_ratio)

            # Resize with high-quality resampling
            resized = img.resize((width, height), Image.Resampling.LANCZOS)

            # Save optimized version
            save_kwargs = {"quality": quality, "optimize": True}

            if format == "WEBP":
                save_kwargs["method"] = 6  # Best compression
            elif format == "PNG":
                save_kwargs = {"optimize": True, "compress_level": 9}

            resized.save(cached_file, format=format, **save_kwargs)

            logger.info(f"Optimized image saved: {cached_file.name} "
                       f"({original_path.stat().st_size // 1024}KB → "
                       f"{cached_file.stat().st_size // 1024}KB)")

            return cached_file

    except Exception as e:
        logger.error(f"Failed to optimize image: {e}")
        # Return original on error
        return original_path


def clear_cache() -> int:
    """Clear all cached optimized images.

    Returns:
        Number of files deleted
    """
    if not CACHE_DIR.exists():
        return 0

    count = 0
    for cached_file in CACHE_DIR.glob("*"):
        try:
            cached_file.unlink()
            count += 1
        except Exception as e:
            logger.error(f"Failed to delete cached file {cached_file}: {e}")

    logger.info(f"Cleared {count} cached images")
    return count
