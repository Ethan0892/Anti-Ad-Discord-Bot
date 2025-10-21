"""
Web interface for Anti-Ad Bot
Modern dark blue UI for uploading training images and managing configuration
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
import os
import json
import logging
from functools import wraps
from datetime import datetime
import shutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('web_server')

app = Flask(__name__)

# Configuration
ROOT_PATH = Path(__file__).parent
TRAINING_DATA_PATH = ROOT_PATH / 'Training-Data'
CONFIG_PATH = ROOT_PATH / 'config'
UPLOAD_FOLDER = TRAINING_DATA_PATH
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

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

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page"""
    training_images = sorted([
        f.name for f in TRAINING_DATA_PATH.iterdir() 
        if f.is_file() and allowed_file(f.name)
    ])
    
    return render_template('index.html', 
                         training_images=training_images,
                         image_count=len(training_images))

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
    
    logger.info(f"Starting web server on http://localhost:5000")
    logger.info(f"API Token: {API_TOKEN}")
    logger.info(f"Training data path: {TRAINING_DATA_PATH}")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
