import os
import sys
import asyncio
import logging
from flask import Flask, render_template, jsonify
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Add parent directory to path to import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.sheets import get_preps

app = Flask(__name__)

# Production logging setup
if not app.debug:
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'webapp.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Dodo Web App startup')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'dodo-webapp',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/preps')
def api_preps():
    """Get preparations data for current day"""
    try:
        now = datetime.now()
        is_morning = now.hour < 15
        day_index = now.weekday()
        
        # Run async functions in sync Flask context
        morning_preps = asyncio.run(get_preps(day_index, True))
        evening_preps = asyncio.run(get_preps(day_index, False))
        
        return jsonify({
            'morning': morning_preps,
            'evening': evening_preps,
            'is_morning': is_morning
        })
    except Exception as e:
        app.logger.error(f"Error fetching preps: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch preparations data'}), 500



if __name__ == '__main__':
    # Production mode - run with gunicorn in production
    # This is only for development/testing
    app.run(host='0.0.0.0', port=5001, debug=False)
