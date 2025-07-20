# ==============================================================================
# PROJETO CHAT TRABALHO REDES - SERVIDOR PRINCIPAL (app.py)
# ==============================================================================
# Autores: Gustavo Sarti e Andre Nemer
# Descrição: Este é o servidor backend para a aplicação de chat em tempo real.
#            Ele utiliza Flask para as rotas HTTP e Flask-SocketIO para
#            a comunicação via WebSockets. Gerencia usuários, salas,
#            autenticação, criptografia e monitoramento de recursos.
# ==============================================================================

# --- Importações de Bibliotecas ---
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
import hashlib  # Usado para hashing seguro de senhas
import os       # Usado para gerar chaves de criptografia seguras
import base64   # Usado para codificar/decodificar dados binários (chaves) para envio
import psutil   # Usado para obter informações do sistema, como uso de memória
import time     # Usado para o loop de monitoramento
from threading import Lock # Usado para controle de concorrência na thread de monitoramento

# --- Inicialização da Aplicação ---
app = Flask(__name__)
# A SECRET_KEY é essencial para a segurança das sessões do Flask.
app.config['SECRET_KEY'] = 'seu-segredo-super-secreto-e-longo-e-diferente!'
# O async_mode='threading' é especificado para garantir compatibilidade com tarefas em background.
socketio = SocketIO(app, async_mode='threading')

# --- Variáveis Globais para Controle de Threads e Estado ---
thread = None
thread_lock = Lock()

# --- Estruturas de Dados em Memória ---
# Em um projeto de produção, estas estruturas seriam substituídas por um banco de dados.
user_credentials = {} # Armazena {username: hashed_password}
rooms = {}  # Armazena {room_name: {'password': '...', 'users': {...}, 'key': b'...'}}
online_users = {}  # Mapeia {username: sid}, onde SID é o ID da conexão do Socket.IO

# --- Funções Auxiliares de Emissão ---
def update_global_user_list():
    """Emite a lista de todos os usuários online para todos os clientes no namespace do chat."""
    # socketio.emit é usado para emitir de fora de um handler de evento.
    socketio.emit('global_user_list_update', {'users': list(online_users.keys())}, namespace='/')

def update_room_list():
    """Emite a lista de salas disponíveis (sem dados sensíveis) para todos os clientes."""
    public_rooms = [{"name": name, "has_password": bool(details["password"])} for name, details in rooms.items()]
    socketio.emit('room_list_update', {'rooms': public_rooms}, namespace='/')

# --- Rotas HTTP (Autenticação e Páginas) ---
@app.route('/')
def index():
    """Serve a página principal do chat. Protegida por login."""
    # Verifica se o 'username' está na sessão. Se não, o usuário não está logado.
    if 'username' not in session:
        return redirect(url_for('login_page'))
    # Se logado, renderiza a página do chat, passando o nome do usuário.
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Exibe a página de login e processa o formulário de login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Gera o hash da senha inserida para comparar com o hash armazenado.
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if username in user_credentials and user_credentials[username] == hashed_password:
            # Se as credenciais estiverem corretas, armazena o usuário na sessão.
            session['username'] = username
            print(f"[AUTH] Login bem-sucedido para o usuário: '{username}'")
            return redirect(url_for('index'))
        else:
            print(f"[AUTH] Falha no login para o usuário: '{username}'")
            return "Usuário ou senha inválidos. <a href='/login'>Tente novamente</a>"
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    """Processa o formulário de registro de novos usuários."""
    username = request.form['username']
    password = request.form['password']
    if username in user_credentials:
        print(f"[AUTH] Tentativa de registro de usuário já existente: '{username}'")
        return "Usuário já existe. <a href='/login'>Tente outro nome</a>"
    # Armazena o hash da senha, nunca a senha em texto plano.
    user_credentials[username] = hashlib.sha256(password.encode()).hexdigest()
    print(f"[AUTH] Novo usuário registrado: '{username}'")
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    """Remove o usuário da sessão, efetivamente fazendo o logout."""
    username = session.pop('username', None)
    print(f"[AUTH] Usuário '{username}' fez logout.")
    return redirect(url_for('login_page'))

@app.route('/memory')
def memory():
    """Serve a página oculta de monitoramento de memória."""
    return render_template('memory.html')

# --- Lógica de Monitoramento em Background ---
def memory_monitor_thread():
    """
    Thread que roda em segundo plano para coletar e emitir dados de memória.
    """
    process = psutil.Process(os.getpid())
    while True:
        # Coleta o uso de memória RSS (Resident Set Size) e converte para MB.
        memory_mb = process.memory_info().rss / (1024 * 1024)
        # Emite os dados para o namespace '/memory' a cada 2 segundos.
        socketio.emit('memory_update',
                      {'memory': round(memory_mb, 2), 'time': time.strftime('%H:%M:%S')},
                      namespace='/memory')
        socketio.sleep(2)

# --- Eventos do Socket.IO ---

@socketio.on('connect', namespace='/memory')
def memory_connect():
    """Inicia a thread de monitoramento quando o primeiro cliente se conecta a /memory."""
    global thread
    with thread_lock: # Garante que a thread seja iniciada apenas uma vez.
        if thread is None:
            thread = socketio.start_background_task(target=memory_monitor_thread)
    print('[MONITOR] Cliente conectado ao monitor de memória.')

# Os eventos abaixo pertencem ao namespace padrão '/' (o chat principal).
@socketio.on('connect', namespace='/')
def on_connect(auth=None):
    """Lida com a conexão de um novo cliente ao chat."""
    username = session.get('username')
    if not username: return False # Rejeita conexão se não estiver logado.
    online_users[username] = request.sid
    print(f"[CONNECT] Usuário '{username}' conectou (SID: {request.sid})")
    # Atualiza as listas para todos os usuários.
    update_global_user_list()
    update_room_list()

@socketio.on('create', namespace='/')
def on_create(data):
    """Lida com a criação de uma nova sala de chat."""
    if 'username' not in session: return
    username = session.get('username')
    room, password = data['room'], data.get('password')
    if room not in rooms:
        # Gera uma chave de criptografia AES segura de 16 bytes.
        key = os.urandom(16)
        rooms[room] = {'password': password, 'users': {}, 'key': key}
        print(f"[ROOM] Usuário '{username}' criou a sala '{room}'")
        emit('status', {'msg': f'Sala "{room}" criada com sucesso!'}, to=request.sid)
        update_room_list()
    else:
        emit('error', {'msg': f'Sala "{room}" já existe.'})

@socketio.on('join', namespace='/')
def on_join(data):
    """Lida com a entrada de um usuário em uma sala."""
    username = session.get('username')
    if not username: return
    room, password, sid = data['room'], data.get('password', ''), request.sid
    
    # Validação da sala e senha.
    if room not in rooms or (rooms[room]['password'] is not None and rooms[room]['password'] != password):
        emit('error', {'msg': f'Não foi possível entrar na sala "{room}".'})
        return

    join_room(room)
    rooms[room]['users'][sid] = username
    print(f"[ROOM] Usuário '{username}' entrou na sala '{room}'")
    
    # Envia a chave secreta da sala de forma segura, apenas para o cliente que acabou de entrar.
    room_key = rooms[room]['key']
    key_b64 = base64.b64encode(room_key).decode('utf-8')
    emit('room_key', {'key': key_b64}, to=sid)
    
    # Atualiza a lista de usuários para todos na sala.
    user_list = list(rooms[room]['users'].values())
    emit('status', {'msg': f'{username} entrou na sala.', 'room': room}, room=room)
    emit('user_list_update', {'users': user_list}, room=room)

@socketio.on('leave', namespace='/')
def on_leave():
    """Lida com a saída de um usuário de uma sala."""
    username = session.get('username')
    sid = request.sid
    if not username: return

    for room_name, details in list(rooms.items()):
        if sid in details['users']:
            print(f"[ROOM] Usuário '{username}' saiu da sala '{room_name}'")
            leave_room(room_name)
            del rooms[room_name]['users'][sid]
            emit('status', {'msg': f'{username} saiu da sala.'}, room=room_name)

            # Se a sala ficar vazia, ela é removida.
            if not rooms[room_name]['users']:
                del rooms[room_name]
                print(f"[ROOM] Sala '{room_name}' vazia, foi removida.")
                update_room_list()
            else:
                emit('user_list_update', {'users': list(rooms[room_name]['users'].values())}, room=room_name)
            
            # Envia os dados atualizados do lobby para o cliente que acabou de sair.
            emit('room_list_update', {'rooms': [{"name": name, "has_password": bool(details["password"])} for name, details in rooms.items()]}, to=sid)
            emit('global_user_list_update', {'users': list(online_users.keys())}, to=sid)
            break

@socketio.on('disconnect', namespace='/')
def on_disconnect():
    """Lida com a desconexão total de um cliente (fechar aba, etc.)."""
    sid = request.sid
    username_to_remove = None
    for user, user_sid in list(online_users.items()):
        if user_sid == sid:
            username_to_remove = user
            break
    
    if username_to_remove:
        print(f"[DISCONNECT] Usuário '{username_to_remove}' desconectado (SID: {sid})")
        # Primeiro, processa a saída da sala para notificar os outros membros.
        on_leave() 
        # Depois, remove o usuário da lista global de online.
        if username_to_remove in online_users:
            del online_users[username_to_remove]
        update_global_user_list()

@socketio.on('text', namespace='/')
def on_text(data):
    """Recebe mensagens de sala (criptografadas) e as retransmite."""
    username = session.get('username')
    if not username: return
    print(f"[MESSAGE] Recebido de '{username}': {data}")
    emit('message', {'username': username, 'msg': data['msg'], 'id': data.get('id')}, room=data['room'])

@socketio.on('whisper', namespace='/')
def on_whisper(data):
    """Recebe sussurros (texto plano) e os envia para o destinatário específico."""
    sender_username = session.get('username')
    if not sender_username: return
    print(f"[WHISPER] Recebido de '{sender_username}': {data}")
    target_username = data['target_username']
    message = data['msg']
    recipient_sid = online_users.get(target_username)
    if recipient_sid:
        # Envia a mensagem para o destinatário e uma cópia para o remetente.
        emit('private_message', {'sender': sender_username, 'recipient': target_username, 'msg': message}, to=recipient_sid)
        emit('private_message', {'sender': sender_username, 'recipient': target_username, 'msg': message}, to=request.sid)
    else:
        emit('error', {'msg': f'Usuário "{target_username}" não está online.'}, to=request.sid)

# --- Ponto de Entrada da Aplicação ---
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
