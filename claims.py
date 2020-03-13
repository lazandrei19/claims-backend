from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room, send, emit, leave_room
from flask_cors import CORS
from typing import Dict, List
from game.Game import Game, Player

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=5, ping_interval=1)

games: Dict[str, Game] = {}
clients: Dict[str, str] = {}

@app.route('/join/<game_uuid>', methods=['POST'])
def join_game(game_uuid: str):
    if game_uuid not in games: #game does not exist
        return '', 404
    if games[game_uuid].has_player(request.json['username']): # user with the same name is already connected
        return '', 401
    return jsonify(games[game_uuid].game_players)

@app.route('/host/<game_uuid>', methods=['POST'])
def host_game(game_uuid: str):
    if game_uuid in games: # game is already in progress
        return '', 403
    games[game_uuid] = Game(game_uuid)
    return '', 200

@socketio.on('join')
def on_join(room: str, username: str):
    games[room].players[request.sid] = Player(username, request.sid)
    clients[request.sid] = room
    emit('newPlayer', {"username": username, "uuid": request.sid}, room=room, json=True)
    join_room(room)
    send('You have entered the room.', room=room)

@socketio.on('connect')
def connection():
    emit('connect', request.sid)

@socketio.on('disconnect')
def disconnect():
    if request.sid not in clients:
        return
    room = clients[request.sid]
    leave_room(room)
    games[room].remove_player(request.sid)
    emit('delPlayer', request.sid, room=room)
    if len(games[room].players) == 0:
        print('Game ' + room + ' deleted')
        del games[room]
    del clients[request.sid]

@socketio.on('start')
def start_game(game_id: str):
    games[game_id].new_game()

@socketio.on('move')
def move(cards: List[str], pile: str):
    games[clients[request.sid]].move(request.sid, cards, pile)

@socketio.on('claims')
def claims():
    games[clients[request.sid]].claims(request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
