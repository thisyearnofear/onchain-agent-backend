import os
import constants

from flask import request, jsonify
from functools import wraps

AUTH_HEADER = os.getenv(constants.AUTH_HEADER)

def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No Authorization header'}), 401
        
        try:
            # Expected format: "Bearer <token>"
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                return jsonify({'error': 'Invalid authorization scheme'}), 401
            if token != AUTH_HEADER:
                return jsonify({'error': 'Invalid API key'}), 401
        except ValueError:
            return jsonify({'error': 'Invalid Authorization header format'}), 401
            
        return f(*args, **kwargs)
    return decorated_function