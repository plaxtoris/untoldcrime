"""
Audio streaming service for the FastAPI application.
"""

import os
import re
from pathlib import Path
from typing import Generator, Optional
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from config import DATA_DIR


class AudioService:
    """Service for handling audio file operations and streaming."""
    
    def __init__(self):
        self.data_dir = Path(DATA_DIR)
        self.chunk_size = 1024 * 1024  # 1MB chunks
    
    def _create_file_iterator(
        self, 
        file_path: Path, 
        byte_start: int = 0, 
        byte_end: Optional[int] = None
    ) -> Generator[bytes, None, None]:
        """
        Create a file iterator for streaming audio files with range support.
        
        Args:
            file_path: Path to the audio file
            byte_start: Starting byte position
            byte_end: Ending byte position (optional)
            
        Yields:
            bytes: File chunks
        """
        with open(file_path, "rb") as file:
            file.seek(byte_start)
            if byte_end is not None:
                remaining = byte_end - byte_start + 1
                while remaining:
                    to_read = min(remaining, self.chunk_size)
                    chunk = file.read(to_read)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
            else:
                while chunk := file.read(self.chunk_size):
                    yield chunk
    
    def _parse_range_header(self, range_header: str, file_size: int) -> tuple[int, int]:
        """
        Parse HTTP Range header.
        
        Args:
            range_header: Range header value
            file_size: Total file size
            
        Returns:
            tuple: (byte_start, byte_end)
        """
        byte_start = 0
        byte_end = file_size - 1
        
        match = re.search(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            byte_start = int(match.group(1))
            if match.group(2):
                byte_end = int(match.group(2))
        
        return byte_start, byte_end
    
    def get_audio_file_path(self, theme: str, title: str) -> Path:
        """
        Get the path to an audio file.
        
        Args:
            theme: Theme name
            title: Audio title
            
        Returns:
            Path: Path to the audio file
            
        Raises:
            HTTPException: If file doesn't exist
        """
        file_path = self.data_dir / theme / f"{title}.mp3"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        return file_path
    
    def stream_audio_file(self, theme: str, title: str, request: Request) -> StreamingResponse:
        """
        Stream an audio file with support for HTTP Range requests.
        
        Args:
            theme: Theme name
            title: Audio title
            request: FastAPI request object
            
        Returns:
            StreamingResponse: Streaming response with audio data
        """
        file_path = self.get_audio_file_path(theme, title)
        file_size = file_path.stat().st_size
        range_header = request.headers.get("range")
        
        if range_header:
            byte_start, byte_end = self._parse_range_header(range_header, file_size)
            
            headers = {
                "Content-Range": f"bytes {byte_start}-{byte_end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(byte_end - byte_start + 1),
                "Content-Type": "audio/mpeg",
            }
            
            return StreamingResponse(
                self._create_file_iterator(file_path, byte_start, byte_end),
                status_code=206,
                headers=headers
            )
        else:
            headers = {
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
                "Content-Type": "audio/mpeg",
            }
            
            return StreamingResponse(
                self._create_file_iterator(file_path),
                headers=headers
            )


# Singleton instance
audio_service = AudioService()