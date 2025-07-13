from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
# A secret_key é necessária para a segurança das sessões do Flask
app.config['SECRET_KEY'] = 'seu-segredo-super-secreto!' 
socketio = SocketIO(app)

# Armazenamento em memória (para simplificar, como no projeto original)
# Em um projeto real, usaríamos um banco de dados
users_in_rooms = {} # {room: {sid1, sid2, ...}}
rooms = {} # {room_name: {'password': '123'}} - senhas não hasheadas por simplicidade

@app.route('/')
def index():
    # Renderiza a nossa página de chat
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    password = data.get('password', '') # .get para ser seguro se não houver senha
    
    # Validação da sala
    if room not in rooms:
        emit('error', {'msg': f'Sala "{room}" não existe.'})
        return
        
    if rooms[room]['password'] is not None and rooms[room]['password'] != password:
        emit('error', {'msg': 'Senha incorreta!'})
        return

    sid = request.sid # ID de sessão único para cada cliente
    join_room(room)
    
    # Adicionar usuário à nossa lista
    if room not in users_in_rooms:
        users_in_rooms[room] = set()
    users_in_rooms[room].add(username) # Usando username ao invés de SID para a lista
    
    # Emitir mensagem de status para todos na sala
    emit('status', {'msg': f'{username} entrou na sala.'}, room=room)
    # Enviar a lista atualizada de usuários para todos na sala
    emit('update_user_list', {'users': list(users_in_rooms[room])}, room=room)

@socketio.on('create')
def on_create(data):
    room = data['room']
    password = data.get('password') # Pode ser None
    
    if room in rooms:
        emit('error', {'msg': f'Sala "{room}" já existe.'})
    else:
        rooms[room] = {'password': password}
        emit('status', {'msg': f'Sala "{room}" criada com sucesso!'}, to=request.sid) # Apenas para o criador

@socketio.on('text')
def on_text(data):
    username = data['username']
    room = data['room']
    msg = data['msg']
    
    # Envia a mensagem de texto para todos os clientes na sala especificada
    emit('message', {'username': username, 'msg': msg}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    sid = request.sid
    
    leave_room(room)
    
    if room in users_in_rooms and username in users_in_rooms[room]:
        users_in_rooms[room].remove(username)
        # Se a sala ficar vazia, removemos ela e a lista de usuários
        if not users_in_rooms[room]:
            del users_in_rooms[room]
            if room in rooms:
                del rooms[room] # Apaga a sala em si
        else:
            # Enviar a lista atualizada de usuários para os remanescentes
            emit('update_user_list', {'users': list(users_in_rooms[room])}, room=room)

    emit('status', {'msg': f'{username} saiu da sala.'}, room=room)

if __name__ == '__main__':
    # Usando o servidor eventlet para produção e compatibilidade com WebSockets
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)