import requests
import socketio
import threading
import time
import random
import string
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# --- Configurações do Teste ---
SERVER_URL = 'http://127.0.0.1:5000'
NUM_USERS = 50
NUM_ROOMS = 10
MESSAGES_PER_USER = 20
DELAY_BETWEEN_MESSAGES = 0.5

def generate_random_string(length=8):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

# --- Classe que Simula um Cliente do Chat (Agora com Criptografia) ---
class ChatClient(threading.Thread):
    def __init__(self, username, password, rooms_to_join):
        super().__init__()
        self.username = username
        self.password = password
        self.rooms_to_join = rooms_to_join
        
        self.session = requests.Session()
        self.sio = socketio.Client(http_session=self.session)
        self.is_connected = False
        self.room_key = None # ### NOVO: Para armazenar a chave da sala ###

        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('status', self.on_status)
        self.sio.on('room_key', self.on_room_key) # ### NOVO: Handler para receber a chave ###

    def on_connect(self):
        print(f"[{self.username}] Conectado.")
        self.is_connected = True

    def on_disconnect(self):
        print(f"[{self.username}] Desconectado.")
        self.is_connected = False

    def on_status(self, data):
        print(f"[{self.username}] Status: {data.get('msg')}")

    def on_room_key(self, data):
        """Recebe e decodifica a chave da sala enviada pelo servidor."""
        print(f"[{self.username}] Chave da sala recebida.")
        self.room_key = base64.b64decode(data['key'])

    def run(self):
        try:
            print(f"[{self.username}] Fazendo login...")
            resp = self.session.post(f"{SERVER_URL}/login", data={'username': self.username, 'password': self.password})
            if resp.status_code != 200:
                print(f"[{self.username}] Falha no login.")
                return

            self.sio.connect(SERVER_URL, wait_timeout=10)
            
            # Espera um pouco para a conexão ser estabelecida de fato
            for _ in range(5):
                if self.is_connected: break
                time.sleep(0.5)

            if not self.is_connected:
                print(f"[{self.username}] Falha ao conectar WebSocket.")
                return

            room_to_join = random.choice(self.rooms_to_join)
            print(f"[{self.username}] Entrando na sala '{room_to_join}'...")
            self.sio.emit('join', {'room': room_to_join})
            
            # Espera um pouco para receber a chave da sala
            for _ in range(5):
                if self.room_key: break
                time.sleep(0.5)

            if not self.room_key:
                print(f"[{self.username}] Não recebeu a chave da sala a tempo.")
                return

            print(f"[{self.username}] Enviando {MESSAGES_PER_USER} mensagens criptografadas...")
            for i in range(MESSAGES_PER_USER):
                message = f"Olá, esta é a mensagem {i+1} de {self.username}"
                
                # ### MUDANÇA: Criptografa a mensagem antes de enviar ###
                cipher = AES.new(self.room_key, AES.MODE_CBC)
                padded_data = pad(message.encode('utf-8'), AES.block_size)
                encrypted_msg = cipher.encrypt(padded_data)
                # O IV (vetor de inicialização) é prefixado no texto cifrado
                payload_b64 = base64.b64encode(cipher.iv + encrypted_msg).decode('utf-8')
                
                self.sio.emit('text', {'room': room_to_join, 'msg': payload_b64})
                time.sleep(DELAY_BETWEEN_MESSAGES)
            
            print(f"[{self.username}] Mensagens enviadas.")

        except Exception as e:
            print(f"[{self.username}] Ocorreu um erro: {e}")
        finally:
            if self.is_connected:
                self.sio.disconnect()

# --- Função Principal do Script (sem alterações) ---
def main():
    # ... (o resto do script main permanece o mesmo)
    print("--- INICIANDO TESTE DE ESTRESSE DO CHAT ---")
    
    users = [{'username': f'user_{i}', 'password': 'password123'} for i in range(NUM_USERS)]
    rooms = [f'sala_teste_{i}' for i in range(NUM_ROOMS)]
    
    print("\n[FASE 1] Registrando usuários e criando salas...")
    for user in users:
        try:
            requests.post(f"{SERVER_URL}/register", data=user)
        except requests.exceptions.ConnectionError as e:
            print(f"ERRO: Não foi possível conectar ao servidor em {SERVER_URL}. Ele está rodando?")
            return
    print(f"{NUM_USERS} usuários registrados.")

    print("Criando salas...")
    session = requests.Session()
    session.post(f"{SERVER_URL}/login", data=users[0])
    sio_creator = socketio.Client(http_session=session)
    sio_creator.connect(SERVER_URL)
    time.sleep(1)
    for room_name in rooms:
        sio_creator.emit('create', {'room': room_name, 'password': ''})
        time.sleep(0.1)
    sio_creator.disconnect()
    print(f"{NUM_ROOMS} salas criadas.")

    print("\n[FASE 2] Iniciando simulação de clientes...")
    threads = []
    for user in users:
        client_thread = ChatClient(user['username'], user['password'], rooms)
        threads.append(client_thread)
        client_thread.start()
        time.sleep(0.1)

    for t in threads:
        t.join()
        
    print("\n--- TESTE DE ESTRESSE CONCLUÍDO ---")

if __name__ == '__main__':
    main()