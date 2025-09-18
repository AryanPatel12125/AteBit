"""
Firebase Authentication Module for AteBit Legal Document Platform.

This module provides Firebase token verification and DRF authentication classes.
It verifies Firebase ID tokens from the Authorization header and sets user context.
"""

import logging
import os
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from functools import lru_cache

from django.conf import settings
from django.core.exceptions import PermissionDenied
from rest_framework import authentication, exceptions

# Import Firebase modules only if not in test mode
if not (getattr(settings, 'TESTING', False) or os.environ.get('TESTING')):
    from firebase_admin import credentials, initialize_app, auth, get_app
    from firebase_admin.exceptions import FirebaseError
else:
    # Mock for testing
    from unittest.mock import Mock
    credentials = Mock()
    initialize_app = Mock()
    auth = Mock()
    get_app = Mock()
    FirebaseError = Exception

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
def initialize_firebase() -> None:
    """Initialize Firebase Admin SDK with credentials from settings."""
    # Skip initialization in test mode
    if getattr(settings, 'TESTING', False) or os.environ.get('TESTING'):
        return
        
    try:
        # Check if already initialized
        get_app()
    except ValueError:
        cred = credentials.Certificate(settings.FIREBASE_CONFIG['credentials_path'])
        initialize_app(cred, {
            'projectId': settings.FIREBASE_CONFIG['project_id']
        })
        logger.info("Firebase Admin SDK initialized successfully")

# Initialize on module load
initialize_firebase()

class FirebaseUser:
    """
    Custom user class to hold Firebase user information.
    
    Attributes:
        uid (str): Firebase user ID
        email (str): User's email address
        is_verified (bool): Email verification status
        auth_time (datetime): Token authentication time
    """
    
    def __init__(
        self,
        uid: str,
        email: Optional[str] = None,
        is_verified: bool = False,
        auth_time: Optional[datetime] = None
    ):
        self.uid = uid
        self.email = email
        self.is_verified = is_verified
        self.auth_time = auth_time
    
    @property
    def is_authenticated(self) -> bool:
        """Always return True for authenticated Firebase users."""
        return True

class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    DRF Authentication class for Firebase ID token verification.
    
    Verifies the Bearer token from the Authorization header as a Firebase ID token.
    Sets the authenticated user on the request object.
    """
    
    keyword = 'Bearer'
    
    @lru_cache(maxsize=1024)
    def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token and cache the result.
        
        Args:
            id_token: The Firebase ID token to verify
            
        Returns:
            dict: Decoded token claims
            
        Raises:
            auth.InvalidIdTokenError: If token is invalid
        """
        return auth.verify_id_token(id_token)
    
    def authenticate(self, request) -> Optional[Tuple[FirebaseUser, None]]:
        """
        Authenticate the request with a Firebase ID token.
        
        Args:
            request: The incoming request object
            
        Returns:
            tuple: (FirebaseUser, None) if authentication successful
            None: If no token present (allow other auth classes to attempt)
            
        Raises:
            AuthenticationFailed: If token is invalid
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
            
        try:
            # Extract token
            auth_parts = auth_header.split()
            if len(auth_parts) != 2 or auth_parts[0].lower() != self.keyword.lower():
                return None
                
            token = auth_parts[1]
            
            # Verify token
            decoded_token = self.verify_id_token(token)
            
            # Create user object
            user = FirebaseUser(
                uid=decoded_token['uid'],
                email=decoded_token.get('email'),
                is_verified=decoded_token.get('email_verified', False),
                auth_time=datetime.fromtimestamp(decoded_token['auth_time'])
            )
            
            # Add user_uid to request for easy access
            request.user_uid = user.uid
            
            return (user, None)
            
        except (IndexError, KeyError):
            raise exceptions.AuthenticationFailed('Invalid authorization header')
            
        except auth.InvalidIdTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
            
        except FirebaseError as e:
            logger.error(f"Firebase auth error: {str(e)}")
            raise exceptions.AuthenticationFailed('Firebase authentication failed')
            
        except Exception as e:
            logger.error(f"Unexpected auth error: {str(e)}")
            raise exceptions.AuthenticationFailed('Authentication failed')