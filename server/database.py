# Database setup and operations for the chat application
# This file handles all the database stuff - creating tables, storing users, messages, etc.
# I used SQLite because it's simple and doesn't need a separate server
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self, db_path: str = None):
        # Use environment variable or default path
        # This lets us configure where the database file goes
        self.db_path = db_path or os.getenv('DATABASE_URL', './chat.db')
        self.init_database()  # Create tables when we start up
    
    def get_connection(self):
        """Get a database connection"""
        # Connect to the SQLite database file
        conn = sqlite3.connect(self.db_path)
        # This makes it so we can access columns by name instead of just numbers
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise
        
        try:
            # Users table - stores user account information
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Rooms table - stores chat rooms (we'll have one AI chat room)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Room members table - tracks which users are in which rooms
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS room_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (room_id) REFERENCES rooms (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(room_id, user_id)
                )
            ''')
            
            # Messages table - stores all chat messages
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER NOT NULL,
                    sender_id INTEGER,
                    text TEXT NOT NULL,
                    is_ai BOOLEAN DEFAULT 0,
                    sender_name TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (room_id) REFERENCES rooms (id),
                    FOREIGN KEY (sender_id) REFERENCES users (id)
                )
            ''')
            
            
            conn.commit()
            print("Database tables initialized successfully")
            
            # Add sender_name column if it doesn't exist (for existing databases)
            self.migrate_add_sender_name_column()
            
            # Create default AI chat room if it doesn't exist
            self.create_default_room()
            
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def migrate_add_sender_name_column(self):
        """Add sender_name column to messages table if it doesn't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if sender_name column exists
            cursor.execute("PRAGMA table_info(messages)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'sender_name' not in columns:
                cursor.execute('ALTER TABLE messages ADD COLUMN sender_name TEXT')
                conn.commit()
                print("Added sender_name column to messages table")
            else:
                print("sender_name column already exists in messages table")
                
        except Exception as e:
            print(f"Error adding sender_name column: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def create_default_room(self):
        """Create the default chat rooms with human names"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # List of chat rooms to create
            chat_rooms = ['Kyle', 'Jane', 'Sam', 'David']
            
            for room_name in chat_rooms:
                # Check if room exists
                cursor.execute('SELECT id FROM rooms WHERE name = ?', (room_name,))
                room = cursor.fetchone()
                
                if not room:
                    # Create the chat room
                    cursor.execute('INSERT INTO rooms (name) VALUES (?)', (room_name,))
                    room_id = cursor.lastrowid
                    print(f"Chat room '{room_name}' created with ID: {room_id}")
                else:
                    print(f"Chat room '{room_name}' already exists")
            
            conn.commit()
                
        except Exception as e:
            print(f"Error creating default rooms: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    
    # User operations
    def create_user(self, email: str, username: str, password_hash: str) -> int:
        """Create a new user and return user ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)',
                (email, username, password_hash)
            )
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            raise ValueError("User with this email already exists")
        finally:
            conn.close()
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT id, email, username, password_hash, created_at FROM users WHERE email = ?',
                (email,)
            )
            user = cursor.fetchone()
            return dict(user) if user else None
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT id, email, username, created_at FROM users WHERE id = ?',
                (user_id,)
            )
            user = cursor.fetchone()
            return dict(user) if user else None
        finally:
            conn.close()
    
    # Room operations
    def get_ai_room(self) -> Optional[Dict[str, Any]]:
        """Get the first available chat room (for backward compatibility)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id, name FROM rooms ORDER BY id LIMIT 1')
            room = cursor.fetchone()
            return dict(room) if room else None
        finally:
            conn.close()
    
    def get_room_by_name(self, room_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific room by name"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id, name FROM rooms WHERE name = ?', (room_name,))
            room = cursor.fetchone()
            return dict(room) if room else None
        finally:
            conn.close()
    
    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """Get all available chat rooms"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id, name FROM rooms ORDER BY name')
            rooms = cursor.fetchall()
            return [dict(room) for room in rooms]
        finally:
            conn.close()
    
    def add_user_to_room(self, user_id: int, room_id: int) -> bool:
        """Add user to a room"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO room_members (room_id, user_id) VALUES (?, ?)',
                (room_id, user_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # User already in room
            return False
        finally:
            conn.close()
    
    def is_user_in_room(self, user_id: int, room_id: int) -> bool:
        """Check if user is in a room"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT id FROM room_members WHERE room_id = ? AND user_id = ?',
                (room_id, user_id)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()
    
    def get_user_rooms(self, user_id: int) -> List[Dict[str, Any]]:
        """Get rooms where user is a member"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    r.id,
                    r.name,
                    r.created_at,
                    COUNT(m.id) as message_count
                FROM rooms r
                INNER JOIN room_members rm ON r.id = rm.room_id
                LEFT JOIN messages m ON r.id = m.room_id
                WHERE rm.user_id = ?
                GROUP BY r.id, r.name, r.created_at
                ORDER BY r.created_at ASC
            ''', (user_id,))
            
            rooms = cursor.fetchall()
            return [dict(room) for room in rooms]
        finally:
            conn.close()
    
    # Message operations
    def get_room_messages(self, room_id: int) -> List[Dict[str, Any]]:
        """Get all messages for a room"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    m.id,
                    m.text,
                    m.timestamp,
                    m.is_ai,
                    CASE 
                        WHEN m.is_ai = 1 THEN m.sender_name
                        ELSE u.username
                    END as sender_name
                FROM messages m
                LEFT JOIN users u ON m.sender_id = u.id
                WHERE m.room_id = ?
                ORDER BY m.timestamp ASC
            ''', (room_id,))
            
            messages = cursor.fetchall()
            return [dict(msg) for msg in messages]
        finally:
            conn.close()
    
    def add_message(self, room_id: int, sender_id: Optional[int], text: str, is_ai: bool = False, sender_name: Optional[str] = None) -> int:
        """Add a message to a room and return message ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO messages (room_id, sender_id, text, is_ai, sender_name) VALUES (?, ?, ?, ?, ?)',
                (room_id, sender_id, text, is_ai, sender_name)
            )
            message_id = cursor.lastrowid
            conn.commit()
            return message_id
        finally:
            conn.close()
    
    def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    m.id,
                    m.text,
                    m.timestamp,
                    m.is_ai,
                    CASE 
                        WHEN m.is_ai = 1 THEN m.sender_name
                        ELSE u.username
                    END as sender_name
                FROM messages m
                LEFT JOIN users u ON m.sender_id = u.id
                WHERE m.id = ?
            ''', (message_id,))
            
            message = cursor.fetchone()
            return dict(message) if message else None
        finally:
            conn.close()
    

# Global database instance
db = Database()