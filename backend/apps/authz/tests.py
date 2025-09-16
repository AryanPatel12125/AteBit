"""
Tests for Firebase Authentication module.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from django.test import RequestFactory
from rest_framework import exceptions

from .firebase_auth import FirebaseUser, FirebaseAuthentication

@pytest.fixture
def firebase_auth():
    return FirebaseAuthentication()

@pytest.fixture
def mock_verify_id_token():
    with patch('firebase_admin.auth.verify_id_token') as mock:
        yield mock

@pytest.fixture
def valid_token_payload():
    return {
        'uid': 'test123',
        'email': 'test@example.com',
        'email_verified': True,
        'auth_time': int(datetime.now().timestamp())
    }

def test_firebase_user_creation():
    """Test FirebaseUser object creation and properties."""
    user = FirebaseUser(
        uid='test123',
        email='test@example.com',
        is_verified=True,
        auth_time=datetime.now()
    )
    
    assert user.uid == 'test123'
    assert user.email == 'test@example.com'
    assert user.is_verified is True
    assert user.is_authenticated is True

def test_successful_authentication(firebase_auth, mock_verify_id_token, valid_token_payload):
    """Test successful authentication with valid token."""
    mock_verify_id_token.return_value = valid_token_payload
    
    request = RequestFactory().get('/')
    request.META['HTTP_AUTHORIZATION'] = 'Bearer valid_token'
    
    user, auth = firebase_auth.authenticate(request)
    
    assert isinstance(user, FirebaseUser)
    assert user.uid == 'test123'
    assert user.email == 'test@example.com'
    assert hasattr(request, 'user_uid')
    assert request.user_uid == 'test123'

def test_missing_authorization_header(firebase_auth):
    """Test that missing Authorization header returns None."""
    request = RequestFactory().get('/')
    
    result = firebase_auth.authenticate(request)
    assert result is None

def test_invalid_authorization_header(firebase_auth):
    """Test that malformed Authorization header raises exception."""
    request = RequestFactory().get('/')
    request.META['HTTP_AUTHORIZATION'] = 'Invalid'
    
    result = firebase_auth.authenticate(request)
    assert result is None

def test_invalid_token_verification(firebase_auth, mock_verify_id_token):
    """Test that invalid token verification raises AuthenticationFailed."""
    mock_verify_id_token.side_effect = exceptions.AuthenticationFailed('Invalid token')
    
    request = RequestFactory().get('/')
    request.META['HTTP_AUTHORIZATION'] = 'Bearer invalid_token'
    
    with pytest.raises(exceptions.AuthenticationFailed):
        firebase_auth.authenticate(request)