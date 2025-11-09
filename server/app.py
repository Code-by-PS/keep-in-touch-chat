# Main Flask application for Keep in Touch chat
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path

# Import our modules
from database import db
from auth import hash_password, verify_password, generate_token, require_auth, get_current_user
from ai_service import generate_ai_response, test_gemini_connection

# Create Flask app
# Get the base directory (parent of server directory)
BASE_DIR = Path(__file__).parent.parent
PUBLIC_DIR = BASE_DIR / 'public'

app = Flask(__name__, static_folder=str(PUBLIC_DIR), static_url_path='')
CORS(app)  # Enable CORS for frontend requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Test Gemini API connection on startup (don't crash if it fails)
print("Testing Gemini API connection...")
try:
    gemini_working = test_gemini_connection()
except Exception as e:
    print(f"Gemini API test failed (will use fallback): {e}")
    gemini_working = False

# Authentication routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate input data
        if not data or not all(key in data for key in ['email', 'username', 'password']):
            return jsonify({'error': 'Email, username, and password are required'}), 400
        
        email = data['email'].strip()
        username = data['username'].strip()
        password = data['password']
        
        if not email or not username or not password:
            return jsonify({'error': 'All fields are required'}), 400
        
        # Check if user already exists
        existing_user = db.get_user_by_email(email)
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Hash password before saving
        password_hash = hash_password(password)
        
        # Create new user
        user_id = db.create_user(email, username, password_hash)
        
        # Generate JWT token
        token = generate_token(user_id, email, username)
        
        # Add user to all chat rooms
        all_rooms = db.get_all_rooms()
        for room in all_rooms:
            db.add_user_to_room(user_id, room['id'])
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user': {
                'id': user_id,
                'email': email,
                'username': username
            }
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        # Validate input data
        if not data or not all(key in data for key in ['email', 'password']):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].strip()
        password = data['password']
        
        # Find user by email
        user = db.get_user_by_email(email)
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate JWT token
        token = generate_token(user['id'], user['email'], user['username'])
        
        # Ensure user is in all chat rooms
        all_rooms = db.get_all_rooms()
        for room in all_rooms:
            db.add_user_to_room(user['id'], room['id'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'username': user['username']
            }
        })
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user_info():
    """Get current user information"""
    try:
        user = get_current_user()
        user_id = user['userId']
        
        # Get user details from database
        user_data = db.get_user_by_id(user_id)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user_data['id'],
                'email': user_data['email'],
                'username': user_data['username'],
                'created_at': user_data['created_at']
            }
        })
        
    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Chat routes
@app.route('/api/chat/messages', methods=['GET'])
@require_auth
def get_messages():
    """Get all messages for a specific chat room"""
    try:
        user = get_current_user()
        user_id = user['userId']
        
        # Get room name from query parameter
        room_name = request.args.get('room', 'Kyle')  # Default to Kyle's room
        
        # Get the specific room
        room = db.get_room_by_name(room_name)
        if not room:
            return jsonify({'error': f'Chat room "{room_name}" not found'}), 404
        
        # Check if user is a member of the room
        if not db.is_user_in_room(user_id, room['id']):
            return jsonify({'error': 'You are not a member of this chat'}), 403
        
        # Get all messages for this room
        messages = db.get_room_messages(room['id'])
        
        return jsonify({'messages': messages, 'room': room})
        
    except Exception as e:
        print(f"Get messages error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/chat/messages', methods=['POST'])
@require_auth
def send_message():
    """Send a message to a specific chat room"""
    try:
        user = get_current_user()
        user_id = user['userId']
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Message text is required'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Message text cannot be empty'}), 400
        
        # Get room name from request data
        room_name = data.get('room', 'Kyle')  # Default to Kyle's room
        
        # Get the specific room
        room = db.get_room_by_name(room_name)
        if not room:
            return jsonify({'error': f'Chat room "{room_name}" not found'}), 404
        
        # Check if user is a member of the room
        if not db.is_user_in_room(user_id, room['id']):
            return jsonify({'error': 'You are not a member of this chat'}), 403
        
        # Save user message
        message_id = db.add_message(room['id'], user_id, text, is_ai=False)
        user_message = db.get_message(message_id)
        
        # Generate AI response with room name
        ai_response_text, sender_name = generate_ai_response(text, room_name)
        
        # Save AI response with sender name
        ai_message_id = db.add_message(room['id'], None, ai_response_text, is_ai=True, sender_name=sender_name)
        ai_message = db.get_message(ai_message_id)
        
        return jsonify({
            'userMessage': user_message,
            'aiMessage': ai_message
        })
        
    except Exception as e:
        print(f"Send message error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/chat/rooms', methods=['GET'])
@require_auth
def get_user_rooms():
    """Get all available chat rooms"""
    try:
        user = get_current_user()
        user_id = user['userId']
        
        # Get all available rooms
        rooms = db.get_all_rooms()
        
        return jsonify({'rooms': rooms})
        
    except Exception as e:
        print(f"Get rooms error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/chat/rooms/<int:room_id>/join', methods=['POST'])
@require_auth
def join_room(room_id):
    """Join a room"""
    try:
        user = get_current_user()
        user_id = user['userId']
        
        # Check if room exists (simplified - we only have AI chat)
        ai_room = db.get_ai_room()
        if not ai_room or ai_room['id'] != room_id:
            return jsonify({'error': 'Room not found'}), 404
        
        # Add user to room
        success = db.add_user_to_room(user_id, room_id)
        
        if success:
            return jsonify({
                'message': 'Successfully joined room',
                'room': {
                    'id': ai_room['id'],
                    'name': ai_room['name']
                }
            })
        else:
            return jsonify({'error': 'You are already a member of this room'}), 400
        
    except Exception as e:
        print(f"Join room error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# Serve static files (CSS, JS, images, etc.)
@app.route('/style.css')
def serve_css():
    """Serve CSS file"""
    return send_from_directory(str(PUBLIC_DIR), 'style.css')

@app.route('/app.js')
def serve_js():
    """Serve JavaScript file"""
    return send_from_directory(str(PUBLIC_DIR), 'app.js')

@app.route('/favicon.ico')
def serve_favicon():
    """Serve favicon"""
    return send_from_directory(str(PUBLIC_DIR), 'favicon.ico')

# Serve main HTML file for root
@app.route('/')
def serve_index():
    """Serve the main HTML file"""
    return send_from_directory(str(PUBLIC_DIR), 'index.html')


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.getenv('PORT', 3000))
    
    print(f"Starting Keep in Touch server on port {port}")
    print(f"Open your browser and navigate to http://localhost:{port}")
    print(f"The multi-chat is ready to use!")
    print(f"Gemini API status: {'Connected' if gemini_working else 'Using fallback responses'}")
    
    # Run the Flask app
    # debug=False for production (Render sets this automatically)
    app.run(host='0.0.0.0', port=port, debug=False)