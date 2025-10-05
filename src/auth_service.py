"""
Authentication service for the FastAPI application.
"""

import os
import secrets
from fastapi import HTTPException, status
from fastapi.security import HTTPBasicCredentials


class AuthService:
    """Authentication service for admin users."""
    
    def __init__(self):
        self.admin_username = "admin"
        self.admin_password = os.getenv("PASSWORD", "")
    
    def verify_admin_credentials(self, credentials: HTTPBasicCredentials) -> str:
        """
        Verify admin credentials using constant-time comparison.
        
        Args:
            credentials: HTTPBasicCredentials object containing username and password
            
        Returns:
            str: Username if credentials are valid
            
        Raises:
            HTTPException: If credentials are invalid
        """
        correct_username = secrets.compare_digest(credentials.username, self.admin_username)
        correct_password = secrets.compare_digest(credentials.password, self.admin_password)
        
        if not (correct_username and correct_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username


# Singleton instance
auth_service = AuthService()