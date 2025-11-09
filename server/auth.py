# Authentication utilities for the chat application
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

# JWT secret from environment
JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-here')

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_token(user_id: int, email: str, username: str) -> str:
    """Generate a JWT token for a user"""
    payload = {
        'userId': user_id,
        'email': email,
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=7)  # Token expires in 7 days
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')

def get_token_from_request():
    """Extract JWT token from request headers"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    # Check if it's a Bearer token
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    
    return None

def require_auth(f):
    """Decorator to require authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({'error': 'Access token required'}), 401
        
        try:
            # Verify the token
            payload = verify_token(token)
            # Add user info to request context
            request.user = payload
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({'error': str(e)}), 403
    
    return decorated_function

def get_current_user():
    """Get current user from request context"""
    if hasattr(request, 'user'):
        return request.user
    return None