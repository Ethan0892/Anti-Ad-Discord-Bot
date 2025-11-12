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
import subprocess

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
WEB_DATA_PATH = ROOT_PATH / 'web-data'
USERS_FILE = WEB_DATA_PATH / 'users.json'
UPLOAD_FOLDER = TRAINING_DATA_PATH
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure web-data directory exists
WEB_DATA_PATH.mkdir(parents=True, exist_ok=True)

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

def dev_or_owner_required(f):
    """Decorator to require dev or owner role for training data management"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized - Login required'}), 401
        
        user = get_user(session['username'])
        if not user or user.get('role') not in ['owner', 'dev']:
            return jsonify({'error': 'Unauthorized - Dev or Owner access required'}), 403
        
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

@app.route('/Training-Data/<filename>')
@login_required
def serve_training_image(filename):
    """Serve training images"""
    filename = secure_filename(filename)
    file_path = TRAINING_DATA_PATH / filename
    
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    if not allowed_file(filename):
        return jsonify({'error': 'Invalid file type'}), 403
    
    try:
        return send_from_directory(str(TRAINING_DATA_PATH), filename)
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        return jsonify({'error': 'Error serving file'}), 500

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
@dev_or_owner_required
def upload_image():
    """Upload new training image - accessible to dev and owner roles"""
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
        
        logger.info(f"Uploaded training image: {filename} by user {session.get('username')}")
        
        return jsonify({
            'success': True,
            'message': f'Uploaded {filename}',
            'filename': filename
        }), 201
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/training-images/<filename>', methods=['DELETE'])
@dev_or_owner_required
def delete_image(filename):
    """Delete training image - accessible to dev and owner roles"""
    filename = secure_filename(filename)
    filepath = TRAINING_DATA_PATH / filename
    
    if not filepath.exists():
        return jsonify({'error': 'File not found'}), 404
    
    try:
        filepath.unlink()
        logger.info(f"Deleted training image: {filename} by user {session.get('username')}")
        
        return jsonify({
            'success': True,
            'message': f'Deleted {filename}'
        }), 200
    
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500

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

@app.route('/api/updates/check', methods=['GET'])
@login_required
def check_updates():
    """Check for updates from GitHub"""
    try:
        import subprocess
        
        # Check git status
        result = subprocess.run(
            ['git', 'fetch', 'origin'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT_PATH)
        )
        
        # Compare local vs remote
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD..origin/main'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT_PATH)
        )
        
        commits_behind = int(result.stdout.strip() or '0')
        
        # Get latest commit info
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%B', 'origin/main'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT_PATH)
        )
        
        latest_commit = result.stdout.strip() or 'No commit info'
        
        return jsonify({
            'update_available': commits_behind > 0,
            'commits_behind': commits_behind,
            'latest_commit': latest_commit
        }), 200
    except Exception as e:
        logger.error(f"Error checking updates: {e}")
        return jsonify({'update_available': False, 'error': str(e)}), 200

@app.route('/api/updates/pull', methods=['POST'])
@admin_required
def pull_updates():
    """Pull latest updates from GitHub"""
    try:
        import subprocess
        
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(ROOT_PATH)
        )
        
        if result.returncode == 0:
            logger.info("Successfully pulled latest updates from GitHub")
            return jsonify({
                'success': True,
                'message': 'Updates pulled successfully. Please restart the bot.'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Pull failed: {result.stderr}'
            }), 400
    except Exception as e:
        logger.error(f"Error pulling updates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
@login_required
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
                        key = key.strip()
                        value = value.strip()
                        # Hide sensitive values
                        if any(x in key.upper() for x in ['TOKEN', 'PASSWORD', 'SECRET', 'KEY']):
                            value = '***HIDDEN***'
                        config_data[key] = value
        
        return jsonify(config_data), 200
    except Exception as e:
        logger.error(f"Error reading config: {e}")
        return jsonify({'error': f'Failed to read config: {str(e)}'}), 500

@app.route('/api/config', methods=['PUT'])
@admin_required
def update_config():
    """Update configuration (admin only)"""
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
        
        # Update with new values (skip hidden values)
        for key, value in data.items():
            if value != '***HIDDEN***':
                config_data[key] = value
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.write("# Auto-generated configuration\n")
            f.write(f"# Last updated: {datetime.now().isoformat()}\n\n")
            for key, value in sorted(config_data.items()):
                f.write(f"{key}={value}\n")
        
        logger.info(f"Configuration updated by {session.get('username')}")
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully. Restart bot to apply changes.'
        }), 200
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'error': f'Failed to update config: {str(e)}'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({'error': f'File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB'}), 413

@app.route('/api/training-images/sync-github', methods=['POST'])
@dev_or_owner_required
def sync_training_data():
    """Sync training data from GitHub repository"""
    try:
        logger.info("Starting GitHub sync for training data...")
        app_path = Path(__file__).parent
        
        # Simple git pull to get latest Training-Data
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            cwd=str(app_path),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        logger.info(f"Git pull result: {result.returncode}")
        if result.stdout:
            logger.info(f"Git pull stdout: {result.stdout}")
        if result.stderr:
            logger.info(f"Git pull stderr: {result.stderr}")
        
        # Count training images
        image_count = len([f for f in TRAINING_DATA_PATH.glob('*') if f.is_file()])
        
        logger.info(f"GitHub sync complete. Training images: {image_count}")
        
        return jsonify({
            'success': True,
            'message': f'Synced training data from GitHub. Found {image_count} images.',
            'image_count': image_count
        }), 200
    
    except subprocess.TimeoutExpired:
        logger.error("Git operation timeout - took too long")
        return jsonify({'error': 'Sync timeout - operation took too long'}), 504
    except Exception as e:
        logger.error(f"Error syncing from GitHub: {e}", exc_info=True)
        return jsonify({'error': f'Sync failed: {str(e)}'}), 500

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
