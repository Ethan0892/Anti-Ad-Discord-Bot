"""
Admin Portal for Anti-Ad Bot
Modern dark blue UI for uploading training images and managing configuration
Includes user authentication and management for owner/devs
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path
import os
import json
import logging
from functools import wraps
from datetime import datetime
import shutil
import secrets

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('admin_portal')

app = Flask(__name__)

# Configuration
ROOT_PATH = Path(__file__).parent
TRAINING_DATA_PATH = ROOT_PATH / 'Training-Data'
CONFIG_PATH = ROOT_PATH / 'config'
DATA_PATH = ROOT_PATH / 'data.json'
USERS_FILE = ROOT_PATH / 'users.json'
UPLOAD_FOLDER = TRAINING_DATA_PATH
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['SECRET_KEY'] = os.getenv('WEB_SECRET_KEY', secrets.token_hex(32))

# Security token for API access
API_TOKEN = os.getenv('WEB_API_TOKEN', 'your-secure-token-here')

def token_required(f):
    """Decorator to require API token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-API-Token')
        if not token or token != API_TOKEN:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def login_required(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator to require admin privileges (owner or dev)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        
        user = get_user(session['username'])
        if not user or user.get('role') not in ['owner', 'dev']:
            return jsonify({'error': 'Unauthorized - Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated

def load_users():
    """Load users from JSON file"""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def get_user(username):
    """Get user by username"""
    users = load_users()
    return users.get(username)

def user_exists(username):
    """Check if user exists"""
    users = load_users()
    return username in users

def create_user(username, password, role='user'):
    """Create a new user"""
    users = load_users()
    if username in users:
        return False, 'User already exists'
    
    users[username] = {
        'password_hash': generate_password_hash(password),
        'role': role,  # 'owner', 'dev', or 'user'
        'created': datetime.now().isoformat()
    }
    save_users(users)
    logger.info(f"Created user: {username} (role: {role})")
    return True, 'User created successfully'

def verify_password(username, password):
    """Verify user password"""
    user = get_user(username)
    if not user:
        return False
    return check_password_hash(user['password_hash'], password)

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============ Authentication Routes ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error='Username and password required'), 400
        
        if not verify_password(username, password):
            return render_template('login.html', error='Invalid credentials'), 401
        
        session['username'] = username
        user = get_user(username)
        session['role'] = user.get('role', 'user')
        logger.info(f"User logged in: {username}")
        
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    username = session.get('username')
    session.clear()
    if username:
        logger.info(f"User logged out: {username}")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    user = get_user(session['username'])
    training_images = sorted([
        f.name for f in TRAINING_DATA_PATH.iterdir() 
        if f.is_file() and allowed_file(f.name)
    ]) if TRAINING_DATA_PATH.exists() else []
    
    return render_template('dashboard.html', 
                         username=session['username'],
                         role=session.get('role'),
                         training_images=training_images,
                         image_count=len(training_images))

@app.route('/users')
@admin_required
def users_page():
    """User management page (admin only)"""
    users = load_users()
    user_list = [
        {
            'username': u,
            'role': data.get('role', 'user'),
            'created': data.get('created')
        }
        for u, data in users.items()
    ]
    
    return render_template('users.html',
                         username=session['username'],
                         role=session.get('role'),
                         users=user_list)

@app.route('/')
def index():
    """Redirect to dashboard or login"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/api/training-images', methods=['GET'])
def get_training_images():
    """Get list of training images"""
    if not TRAINING_DATA_PATH.exists():
        return jsonify({'images': []}), 200
    
    images = []
    for f in sorted(TRAINING_DATA_PATH.iterdir()):
        if f.is_file() and allowed_file(f.name):
            images.append({
                'name': f.name,
                'size': f.stat().st_size,
                'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    
    return jsonify({'images': images}), 200

@app.route('/api/training-images/upload', methods=['POST'])
@token_required
def upload_image():
    """Upload new training image"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = TRAINING_DATA_PATH / filename
        file.save(str(filepath))
        
        logger.info(f"Uploaded training image: {filename}")
        
        return jsonify({
            'success': True,
            'message': f'Uploaded {filename}',
            'filename': filename
        }), 201
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/training-images/<filename>', methods=['DELETE'])
@token_required
def delete_image(filename):
    """Delete training image"""
    filename = secure_filename(filename)
    filepath = TRAINING_DATA_PATH / filename
    
    if not filepath.exists():
        return jsonify({'error': 'File not found'}), 404
    
    try:
        filepath.unlink()
        logger.info(f"Deleted training image: {filename}")
        
        return jsonify({
            'success': True,
            'message': f'Deleted {filename}'
        }), 200
    
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500

@app.route('/api/config', methods=['GET'])
@token_required
def get_config():
    """Get current configuration"""
    try:
        env_file = CONFIG_PATH / '.env'
        config_data = {}
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config_data[key.strip()] = value.strip()
        
        return jsonify(config_data), 200
    
    except Exception as e:
        logger.error(f"Error reading config: {e}")
        return jsonify({'error': f'Failed to read config: {str(e)}'}), 500

@app.route('/api/config', methods=['PUT'])
@token_required
def update_config():
    """Update configuration"""
    try:
        data = request.get_json()
        env_file = CONFIG_PATH / '.env'
        
        # Read existing config
        config_data = {}
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config_data[key.strip()] = value.strip()
        
        # Update with new values
        config_data.update(data)
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.write("# Auto-generated configuration\n")
            f.write(f"# Last updated: {datetime.now().isoformat()}\n\n")
            for key, value in sorted(config_data.items()):
                f.write(f"{key}={value}\n")
        
        logger.info("Configuration updated")
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully'
        }), 200
    
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'error': f'Failed to update config: {str(e)}'}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get bot status"""
    training_count = len([
        f for f in TRAINING_DATA_PATH.iterdir() 
        if f.is_file() and allowed_file(f.name)
    ]) if TRAINING_DATA_PATH.exists() else 0
    
    return jsonify({
        'status': 'online',
        'training_images': training_count,
        'timestamp': datetime.now().isoformat()
    }), 200

# ============ User Management API Routes ============

@app.route('/api/users', methods=['GET'])
@admin_required
def api_get_users():
    """Get all users (admin only)"""
    users = load_users()
    user_list = [
        {
            'username': u,
            'role': data.get('role', 'user'),
            'created': data.get('created')
        }
        for u, data in users.items()
    ]
    
    return jsonify({'users': user_list}), 200

@app.route('/api/users', methods=['POST'])
@admin_required
def api_create_user():
    """Create new user (admin only)"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if role not in ['owner', 'dev', 'user']:
        return jsonify({'error': 'Invalid role'}), 400
    
    success, message = create_user(username, password, role)
    if not success:
        return jsonify({'error': message}), 400
    
    return jsonify({'success': True, 'message': message}), 201

@app.route('/api/users/<username>', methods=['PUT'])
@admin_required
def api_update_user(username):
    """Update user (admin only)"""
    data = request.get_json()
    users = load_users()
    
    if username not in users:
        return jsonify({'error': 'User not found'}), 404
    
    # Prevent deleting owner
    if username == 'owner' and data.get('role') and data.get('role') != 'owner':
        return jsonify({'error': 'Cannot change owner role'}), 403
    
    if 'role' in data:
        if data['role'] not in ['owner', 'dev', 'user']:
            return jsonify({'error': 'Invalid role'}), 400
        users[username]['role'] = data['role']
    
    if 'password' in data and data['password']:
        users[username]['password_hash'] = generate_password_hash(data['password'])
    
    save_users(users)
    logger.info(f"Updated user: {username}")
    
    return jsonify({'success': True, 'message': f'User {username} updated'}), 200

@app.route('/api/users/<username>', methods=['DELETE'])
@admin_required
def api_delete_user(username):
    """Delete user (admin only)"""
    # Prevent deleting owner
    if username == 'owner':
        return jsonify({'error': 'Cannot delete owner account'}), 403
    
    users = load_users()
    if username not in users:
        return jsonify({'error': 'User not found'}), 404
    
    del users[username]
    save_users(users)
    logger.info(f"Deleted user: {username}")
    
    return jsonify({'success': True, 'message': f'User {username} deleted'}), 200

@app.route('/api/profile', methods=['GET'])
@login_required
def api_get_profile():
    """Get current user profile"""
    username = session.get('username')
    user = get_user(username)
    
    return jsonify({
        'username': username,
        'role': user.get('role', 'user'),
        'created': user.get('created')
    }), 200

@app.route('/api/profile/password', methods=['PUT'])
@login_required
def api_change_password():
    """Change current user password"""
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    username = session.get('username')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current and new password required'}), 400
    
    if not verify_password(username, current_password):
        return jsonify({'error': 'Invalid current password'}), 401
    
    users = load_users()
    users[username]['password_hash'] = generate_password_hash(new_password)
    save_users(users)
    
    logger.info(f"Password changed for user: {username}")
    
    return jsonify({'success': True, 'message': 'Password changed successfully'}), 200

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({'error': f'File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB'}), 413

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure training data folder exists
    TRAINING_DATA_PATH.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting Admin Portal on http://localhost:5000")
    logger.info(f"API Token: {API_TOKEN}")
    logger.info(f"Training data path: {TRAINING_DATA_PATH}")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
