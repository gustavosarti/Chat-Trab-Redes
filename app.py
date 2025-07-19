from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
import hashlib
import os
import base64
import psutil
import time
from threading import Lock

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seu-segredo-super-secreto-e-longo-e-diferente!'
socketio = SocketIO(app, async_mode='threading')

thread = None
thread_lock = Lock()

# --- Estruturas de Dados em Memória ---
user_credentials = {}
rooms = {}
online_users = {}

# --- Funções Auxiliares de Emissão ---
def update_global_user_list():
    """Emite a lista de todos os usuários online para todos os clientes no namespace do chat."""
    # ### MUDANÇA 1: Removido 'broadcast=True' ###
    socketio.emit('global_user_list_update', {'users': list(online_users.keys())}, namespace='/')

def update_room_list():
    """Emite a lista de salas disponíveis para todos os clientes no namespace do chat."""
    public_rooms = [{"name": name, "has_password": bool(details["password"])} for name, details in rooms.items()]
    # ### MUDANÇA 2: Removido 'broadcast=True' ###
    socketio.emit('room_list_update', {'rooms': public_rooms}, namespace='/')

# --- Rotas HTTP ---
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if username in user_credentials and user_credentials[username] == hashed_password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return "Usuário ou senha inválidos. <a href='/login'>Tente novamente</a>"
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    if username in user_credentials:
        return "Usuário já existe. <a href='/login'>Tente outro nome</a>"
    user_credentials[username] = hashlib.sha256(password.encode()).hexdigest()
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_page'))

@app.route('/memory')
def memory():
    return render_template('memory.html')

# --- Lógica de Monitoramento em Background ---
def memory_monitor_thread():
    process = psutil.Process(os.getpid())
    while True:
        memory_mb = process.memory_info().rss / (1024 * 1024)
        socketio.emit('memory_update',
                      {'memory': round(memory_mb, 2), 'time': time.strftime('%H:%M:%S')},
                      namespace='/memory')
        socketio.sleep(2)

# --- Eventos do Socket.IO ---

@socketio.on('connect', namespace='/memory')
def memory_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=memory_monitor_thread)
    print('Cliente conectado ao monitor de memória.')

# ### MUDANÇA 3: Adicionado argumento 'auth=None' ###
@socketio.on('connect', namespace='/')
def on_connect(auth=None):
    username = session.get('username')
    if not username: return False
    online_users[username] = request.sid
    update_global_user_list()
    update_room_list()

@socketio.on('create', namespace='/')
def on_create(data):
    if 'username' not in session: return
    room, password = data['room'], data.get('password')
    if room not in rooms:
        key = os.urandom(16)
        rooms[room] = {'password': password, 'users': {}, 'key': key}
        emit('status', {'msg': f'Sala "{room}" criada com sucesso!'}, to=request.sid)
        update_room_list()
    else:
        emit('error', {'msg': f'Sala "{room}" já existe.'})

@socketio.on('join', namespace='/')
def on_join(data):
    username = session.get('username')
    if not username: return
    room, password, sid = data['room'], data.get('password', ''), request.sid
    
    if room not in rooms or (rooms[room]['password'] is not None and rooms[room]['password'] != password):
        emit('error', {'msg': f'Não foi possível entrar na sala "{room}".'})
        return

    join_room(room)
    rooms[room]['users'][sid] = username
    
    room_key = rooms[room]['key']
    key_b64 = base64.b64encode(room_key).decode('utf-8')
    emit('room_key', {'key': key_b64}, to=sid)
    
    user_list = list(rooms[room]['users'].values())
    emit('status', {'msg': f'{username} entrou na sala.', 'room': room}, room=room)
    emit('user_list_update', {'users': user_list}, room=room)

@socketio.on('leave', namespace='/')
def on_leave():
    username = session.get('username')
    sid = request.sid
    if not username: return

    for room_name, details in list(rooms.items()):
        if sid in details['users']:
            leave_room(room_name)
            del rooms[room_name]['users'][sid]
            emit('status', {'msg': f'{username} saiu da sala.'}, room=room_name)

            if not rooms[room_name]['users']:
                del rooms[room_name]
                update_room_list()
            else:
                user_list = list(rooms[room_name]['users'].values())
                emit('user_list_update', {'users': user_list}, room=room_name)
            
            public_rooms = [{"name": name, "has_password": bool(details["password"])} for name, details in rooms.items()]
            online_user_list = list(online_users.keys())
            emit('room_list_update', {'rooms': public_rooms}, to=sid)
            emit('global_user_list_update', {'users': online_user_list}, to=sid)
            break

@socketio.on('disconnect', namespace='/')
def on_disconnect():
    sid = request.sid
    username_to_remove = None
    for user, user_sid in list(online_users.items()):
        if user_sid == sid:
            username_to_remove = user
            break
    
    if username_to_remove:
        on_leave() 
        if username_to_remove in online_users:
            del online_users[username_to_remove]
        update_global_user_list()

@socketio.on('text', namespace='/')
def on_text(data):
    username = session.get('username')
    if not username: return
    emit('message', {
        'username': username, 
        'msg': data['msg'],
        'id': data.get('id')
    }, room=data['room'])

@socketio.on('whisper', namespace='/')
def on_whisper(data):
    sender_username = session.get('username')
    if not sender_username: return
    target_username = data['target_username']
    message = data['msg']
    recipient_sid = online_users.get(target_username)
    if recipient_sid:
        emit('private_message', {'sender': sender_username, 'recipient': target_username, 'msg': message}, to=recipient_sid)
        emit('private_message', {'sender': sender_username, 'recipient': target_username, 'msg': message}, to=request.sid)
    else:
        emit('error', {'msg': f'Usuário "{target_username}" não está online.'}, to=request.sid)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)