import os
import sys
import asyncio
from flask import Flask, render_template, jsonify
from datetime import datetime

# Add parent directory to path to import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.sheets import get_preps

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/preps')
def api_preps():
    # Determine if morning or evening based on current time
    # Morning: 00:00 - 15:00 (approx, logic from bot might differ but let's stick to simple for now)
    # Actually, let's just return both or let the frontend decide?
    # The bot logic:
    # is_morning = True if query.data == 'preps_morning' else False
    
    # Let's get current time to decide default
    now = datetime.now()
    is_morning = now.hour < 15
    
    day_index = now.weekday()
    
    # We need to run async functions in sync flask
    # Using asyncio.run for now, might need better handling if high load but for tablet it's fine
    try:
        morning_preps = asyncio.run(get_preps(day_index, True))
        evening_preps = asyncio.run(get_preps(day_index, False))
        
        return jsonify({
            'morning': morning_preps,
            'evening': evening_preps,
            'is_morning': is_morning
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
