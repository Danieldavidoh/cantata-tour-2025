# server.py
from flask import Flask
from flask_socketio import SocketIO, emit
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@app.route('/trigger_refresh', methods=['POST'])
def trigger_refresh():
    socketio.emit('refresh')
    return "OK", 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
