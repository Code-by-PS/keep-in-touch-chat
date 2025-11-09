/**
 * Keep in Touch Chat Application - Frontend JavaScript
 * 
 * This file handles all the frontend functionality for the chat application.
 * It manages user authentication, message sending/receiving, room switching,
 * and all the UI interactions. The app communicates with the Flask backend
 * through REST API endpoints.
 * 
 * Main features:
 * - User registration and login with JWT tokens
 * - Real-time messaging with AI personas (Kyle, Jane, Sam, David)
 * - Room switching between different chat rooms
 * - Message history loading and display
 * - Auto-refresh of messages every 30 seconds
 */

// Global state management
// These variables store the current application state
let currentUser = null;        // Currently logged in user object
let authToken = null;           // JWT token for authentication
let currentRoomName = 'Kyle';   // Current chat room (defaults to Kyle)
let messages = [];              // Array of messages for the current room

// Base URL for API requests - uses the current origin (works for localhost and production)
const API_BASE_URL = window.location.origin;

// DOM element references
// These are cached so we don't have to query the DOM repeatedly
const authModal = document.getElementById('authModal');           // Login/register modal
const chatApp = document.getElementById('chatApp');               // Main chat interface
const loginForm = document.getElementById('loginForm');            // Login form element
const registerForm = document.getElementById('registerForm');     // Registration form element
const loginTab = document.getElementById('loginTab');             // Login tab button
const registerTab = document.getElementById('registerTab');       // Register tab button
const messagesContainer = document.getElementById('messagesContainer');  // Container for chat messages
const messageInput = document.getElementById('messageInput');     // Message input field
const sendButton = document.getElementById('sendButton');          // Send message button
const logoutButton = document.getElementById('logoutButton');      // Logout button
const userInfo = document.getElementById('userInfo');             // User info display
const loadingSpinner = document.getElementById('loadingSpinner'); // Loading spinner
const toastContainer = document.getElementById('toastContainer'); // Toast notification container

/**
 * Initialize the application when the page loads.
 * 
 * This event listener waits for the DOM to be fully loaded before running
 * any code that manipulates DOM elements. This prevents errors from trying
 * to access elements that don't exist yet.
 */
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
});

/**
 * Initialize the application state.
 * 
 * Checks if the user has a saved authentication token in localStorage.
 * If they do, it restores their session and shows the chat interface.
 * If not, it shows the login/register modal.
 * 
 * This allows users to stay logged in even after closing the browser.
 */
function initializeApp() {
    // Check if user is already logged in (from previous session)
    const savedToken = localStorage.getItem('authToken');
    const savedUser = localStorage.getItem('currentUser');
    
    if (savedToken && savedUser) {
        // Restore the user's session
        authToken = savedToken;
        currentUser = JSON.parse(savedUser);  // Parse the JSON string back to an object
        
        // Show the chat interface and load messages
        showChatApp();
        loadMessages();
        setupChatRoomListeners();
    } else {
        // No saved session, show login/register modal
        showAuthModal();
    }
}


/**
 * Set up all event listeners for user interactions.
 * 
 * This function attaches event handlers to buttons, forms, and input fields.
 * It's called once when the page loads to set up all the interactive elements.
 */
function setupEventListeners() {
    // Auth form tab switching - allows users to switch between login and register
    loginTab.addEventListener('click', () => switchAuthTab('login'));
    registerTab.addEventListener('click', () => switchAuthTab('register'));
    
    // Form submission handlers
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    
    // Chat functionality
    sendButton.addEventListener('click', sendMessage);  // Send button click
    
    // Allow sending messages with Enter key (Shift+Enter for new line)
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();  // Prevent form submission or new line
            sendMessage();
        }
    });
    
    // Logout button
    logoutButton.addEventListener('click', handleLogout);
    
    // Note: Auth modal doesn't close on outside click - user must authenticate
}

/**
 * Switch between login and register tabs in the authentication modal.
 * 
 * This function handles the tab switching UI - when you click "Login" or "Register",
 * it shows the appropriate form and highlights the active tab.
 * 
 * @param {string} tab - Either 'login' or 'register'
 */
function switchAuthTab(tab) {
    if (tab === 'login') {
        // Show login form
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
    } else {
        // Show register form
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        registerForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
    }
}

/**
 * Handle user login form submission.
 * 
 * This function is called when the user submits the login form. It sends
 * the email and password to the backend API, and if successful, saves
 * the authentication token and user info, then shows the chat interface.
 * 
 * @param {Event} e - The form submission event
 */
async function handleLogin(e) {
    e.preventDefault();  // Prevent default form submission (page reload)
    
    // Get form values
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    
    try {
        // Show loading spinner while processing
        showLoading(true);
        errorDiv.textContent = '';  // Clear any previous errors
        
        // Send login request to backend
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'  // Tell server we're sending JSON
            },
            body: JSON.stringify({ email, password })  // Convert object to JSON string
        });
        
        // Parse the JSON response
        const data = await response.json();
        
        if (response.ok) {
            // Login successful - save token and user info
            authToken = data.token;
            currentUser = data.user;
            
            // Save to localStorage so user stays logged in after page refresh
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            // Show the chat interface
            showChatApp();
            loadMessages();  // Load existing messages for the current room
            setupChatRoomListeners();  // Set up room switching
            
            showToast('Login successful!', 'success');
        } else {
            // Login failed - show error message
            errorDiv.textContent = data.error || 'Login failed';
        }
    } catch (error) {
        // Network error or other exception
        console.error('Login error:', error);
        errorDiv.textContent = 'Network error. Please try again.';
    } finally {
        // Always hide loading spinner, whether success or failure
        showLoading(false);
    }
}

/**
 * Handle user registration form submission.
 * 
 * This function is called when the user submits the registration form.
 * It sends the email, username, and password to the backend API to create
 * a new user account. If successful, it automatically logs the user in.
 * 
 * @param {Event} e - The form submission event
 */
async function handleRegister(e) {
    e.preventDefault();  // Prevent default form submission
    
    // Get form values
    const email = document.getElementById('registerEmail').value;
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;
    const errorDiv = document.getElementById('registerError');
    
    try {
        showLoading(true);
        errorDiv.textContent = '';  // Clear previous errors
        
        // Send registration request to backend
        const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Registration successful - user is automatically logged in
            authToken = data.token;
            currentUser = data.user;
            
            // Save to localStorage
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            // Show chat interface
            showChatApp();
            loadMessages();
            setupChatRoomListeners();
            
            showToast('Registration successful!', 'success');
        } else {
            // Registration failed - show error
            errorDiv.textContent = data.error || 'Registration failed';
        }
    } catch (error) {
        console.error('Registration error:', error);
        errorDiv.textContent = 'Network error. Please try again.';
    } finally {
        showLoading(false);
    }
}


/**
 * Handle user logout.
 * 
 * Clears all stored authentication data and resets the application state.
 * Returns the user to the login/register screen.
 */
function handleLogout() {
    // Clear stored authentication data from browser
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    // Reset application state
    authToken = null;
    currentUser = null;
    messages = [];
    
    // Show the login/register modal
    showAuthModal();
    
    showToast('Logged out successfully', 'success');
}

/**
 * Show the authentication modal (login/register screen).
 * 
 * Hides the chat interface and shows the login/register modal.
 * This is called when the user is not logged in or after logout.
 */
function showAuthModal() {
    authModal.classList.remove('hidden');
    chatApp.classList.add('hidden');
}

/**
 * Show the main chat application interface.
 * 
 * Hides the authentication modal and shows the chat interface.
 * Also updates the user info display with the current user's username.
 */
function showChatApp() {
    authModal.classList.add('hidden');
    chatApp.classList.remove('hidden');
    
    // Update user info display in the header
    if (currentUser) {
        userInfo.textContent = `Welcome, ${currentUser.username}`;
    }
}

/**
 * Load messages from the server for the current chat room.
 * 
 * This function fetches all messages for the currently selected room
 * from the backend API. It requires authentication (JWT token) to work.
 * 
 * The messages are stored in the global `messages` array and then
 * displayed using the `displayMessages()` function.
 */
async function loadMessages() {
    try {
        // Send GET request to fetch messages for the current room
        const response = await fetch(`${API_BASE_URL}/api/chat/messages?room=${currentRoomName}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`  // Include JWT token for authentication
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Success - update messages array and display them
            messages = data.messages;
            displayMessages();
        } else {
            // Error - show error message
            showToast(data.error || 'Failed to load messages', 'error');
        }
    } catch (error) {
        // Network error or other exception
        console.error('Load messages error:', error);
        showToast('Failed to load messages', 'error');
    }
}

/**
 * Display all messages in the chat container.
 * 
 * This function clears the messages container and then creates and displays
 * each message. If there are no messages, it shows a welcome message instead.
 * 
 * After displaying messages, it automatically scrolls to the bottom so the
 * user sees the most recent messages.
 */
function displayMessages() {
    // Clear any existing messages
    messagesContainer.innerHTML = '';
    
    // If no messages, show welcome message
    if (messages.length === 0) {
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <h3>Welcome to ${currentRoomName}'s Chat!</h3>
                <p>Start a conversation with ${currentRoomName}. They're online and ready to chat!</p>
            </div>
        `;
        return;
    }
    
    // Create and display each message
    messages.forEach(message => {
        const messageElement = createMessageElement(message);
        messagesContainer.appendChild(messageElement);
    });
    
    // Auto-scroll to bottom to show the latest messages
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Create a DOM element for a single message.
 * 
 * This function takes a message object and creates the HTML structure
 * to display it. Messages are styled differently based on whether they're
 * from the user or from the AI (different colors and alignment).
 * 
 * @param {Object} message - The message object with text, timestamp, sender, etc.
 * @returns {HTMLElement} - The created message element
 */
function createMessageElement(message) {
    // Create the main message container div
    const messageDiv = document.createElement('div');
    
    // Add CSS class based on whether it's an AI or user message
    // This determines the styling (color, alignment, etc.)
    messageDiv.className = `message ${message.is_ai ? 'ai' : 'user'}`;
    
    // Format the timestamp to show just hours and minutes (e.g., "2:30 PM")
    const time = new Date(message.timestamp).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    // Create the HTML structure for the message
    // escapeHtml() prevents XSS attacks by escaping any HTML in the message text
    messageDiv.innerHTML = `
        <div class="message-bubble">
            <div class="message-info">
                <span class="message-sender">${message.sender_name || 'You'}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-text">${escapeHtml(message.text)}</div>
        </div>
    `;
    
    return messageDiv;
}

/**
 * Send a message to the current chat room.
 * 
 * This function takes the text from the input field, sends it to the backend,
 * and then displays both the user's message and the AI's response. The backend
 * handles saving the message to the database and generating the AI response.
 * 
 * The function disables the send button while processing to prevent duplicate
 * messages, and re-enables it when done.
 */
async function sendMessage() {
    // Get the message text and remove leading/trailing whitespace
    const text = messageInput.value.trim();
    
    // Don't send empty messages
    if (!text) return;
    
    // Clear input field and disable send button to prevent double-sending
    messageInput.value = '';
    sendButton.disabled = true;
    
    try {
        // Send POST request to backend with the message
        const response = await fetch(`${API_BASE_URL}/api/chat/messages`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,  // JWT token for authentication
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                text: text, 
                room: currentRoomName  // Which chat room to send to (Kyle, Jane, Sam, or David)
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Success - the backend returns both the user message and AI response
            // The response has 'userMessage' and 'aiMessage' properties
            const userMsg = data.userMessage;
            const aiMsg = data.aiMessage;
            
            // Add both to our messages array
            if (userMsg) messages.push(userMsg);
            if (aiMsg) messages.push(aiMsg);
            
            // Create DOM elements for both messages
            if (userMsg) {
                const userMessageElement = createMessageElement(userMsg);
                messagesContainer.appendChild(userMessageElement);
            }
            if (aiMsg) {
                const aiMessageElement = createMessageElement(aiMsg);
                messagesContainer.appendChild(aiMessageElement);
            }
            
            // Scroll to bottom to show the new messages
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } else {
            // Error - show error message
            showToast(data.error || 'Failed to send message', 'error');
        }
    } catch (error) {
        // Network error or other exception
        console.error('Send message error:', error);
        showToast('Failed to send message', 'error');
    } finally {
        // Always re-enable the send button and focus the input field
        sendButton.disabled = false;
        messageInput.focus();
    }
}


/**
 * Show or hide the loading spinner.
 * 
 * The loading spinner appears when making API requests to give visual
 * feedback that something is happening.
 * 
 * @param {boolean} show - True to show spinner, false to hide it
 */
function showLoading(show) {
    if (show) {
        loadingSpinner.classList.remove('hidden');
    } else {
        loadingSpinner.classList.add('hidden');
    }
}

/**
 * Show a toast notification to the user.
 * 
 * Toast notifications appear in the top-right corner and automatically
 * disappear after 3 seconds. They're used for success messages, errors,
 * and other feedback.
 * 
 * @param {string} message - The message to display
 * @param {string} type - The type of toast: 'success', 'error', or 'info' (default)
 */
function showToast(message, type = 'info') {
    // Create a new toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;  // Add type class for styling
    toast.textContent = message;
    
    // Add it to the toast container
    toastContainer.appendChild(toast);
    
    // Automatically remove it after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

/**
 * Escape HTML characters to prevent XSS (Cross-Site Scripting) attacks.
 * 
 * This function takes user input and escapes any HTML characters so they
 * are displayed as text rather than being interpreted as HTML code. This
 * prevents malicious users from injecting scripts into the page.
 * 
 * @param {string} text - The text to escape
 * @returns {string} - The escaped HTML-safe text
 */
function escapeHtml(text) {
    // Create a temporary div element
    const div = document.createElement('div');
    
    // Set the text content (this automatically escapes HTML)
    div.textContent = text;
    
    // Return the innerHTML (which is now escaped)
    return div.innerHTML;
}

/**
 * Set up event listeners for chat room switching.
 * 
 * This function attaches click handlers to each chat room item in the sidebar.
 * When a user clicks on a different room (Kyle, Jane, Sam, or David), it
 * switches to that room and loads its messages.
 */
function setupChatRoomListeners() {
    // Get all chat room items from the sidebar
    const chatItems = document.querySelectorAll('.chat-item');
    
    // Add click handler to each room
    chatItems.forEach(item => {
        item.addEventListener('click', () => {
            // Get the room name from the data attribute
            const roomName = item.getAttribute('data-room-name');
            
            // Only switch if it's a different room
            if (roomName && roomName !== currentRoomName) {
                switchToRoom(roomName);
            }
        });
    });
}

/**
 * Switch to a different chat room.
 * 
 * This function handles switching between chat rooms. It updates the UI
 * to show which room is active, loads the messages for that room, and
 * clears the message input field.
 * 
 * @param {string} roomName - The name of the room to switch to (Kyle, Jane, Sam, or David)
 */
function switchToRoom(roomName) {
    // Update the current room name
    currentRoomName = roomName;
    
    // Update the active state in the sidebar
    // Remove 'active' class from all rooms
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add 'active' class to the selected room
    document.querySelector(`[data-room-name="${roomName}"]`).classList.add('active');
    
    // Load messages for the new room
    loadMessages();
    
    // Clear the message input field
    messageInput.value = '';
}

/**
 * Auto-refresh messages every 30 seconds.
 * 
 * This interval function automatically reloads messages from the server
 * every 30 seconds. This ensures that if someone sends a message from
 * another device or browser tab, it will appear in the current view.
 * 
 * It only runs if the user is logged in (has authToken and currentUser).
 */
setInterval(() => {
    // Only refresh if user is logged in
    if (currentUser && authToken) {
        loadMessages();
    }
}, 30000);  // 30,000 milliseconds = 30 seconds