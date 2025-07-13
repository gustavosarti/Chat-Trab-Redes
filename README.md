# Projeto: Chat Web em Tempo Real com Flask

![Status](https://img.shields.io/badge/status-concluído-brightgreen)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0-orange)
![Socket.IO](https://img.shields.io/badge/Socket.IO-4.0-yellow)

## Descrição

Este projeto é uma aplicação de chat em tempo real baseada na web. Desenvolvido com Python, Flask e WebSockets, o sistema permite que múltiplos usuários se conectem, criem salas de bate-papo (públicas ou protegidas por senha) e conversem em tempo real. As mensagens enviadas em uma sala são visíveis apenas para os participantes daquela sala, garantindo privacidade e organização.

A aplicação foi projetada para ser simples, responsiva e demonstrar os conceitos fundamentais de comunicação cliente-servidor em um ambiente web moderno.

## Tecnologias Utilizadas

A aplicação é dividida em duas partes principais: o backend (servidor) e o frontend (cliente, que roda no navegador).

### Backend
* **Python 3:** Linguagem de programação principal.
* **Flask:** Micro-framework web utilizado para servir a aplicação e gerenciar as rotas HTTP.
* **Flask-SocketIO:** Extensão que integra o Flask com a biblioteca Socket.IO, facilitando a comunicação bidirecional e em tempo real via WebSockets.
* **Eventlet:** Servidor WSGI de produção, recomendado pelo Flask-SocketIO para lidar com a natureza assíncrona das conexões de longa duração.

### Frontend
* **HTML5:** Para a estruturação semântica da página do chat.
* **CSS3:** Utilizado para a estilização básica e responsiva da interface, garantindo uma experiência de usuário agradável.
* **JavaScript (ES6):** O cérebro do lado do cliente. Responsável por estabelecer a conexão WebSocket, manipular o DOM para exibir mensagens, e enviar eventos para o servidor.
* **Socket.IO Client:** Biblioteca JavaScript que se conecta ao servidor Flask-SocketIO para a troca de mensagens em tempo real.

## Como Executar

Siga os passos abaixo para configurar e rodar o projeto em seu ambiente local.

### Pré-requisitos
* [Git](https://git-scm.com/)
* [Python 3.8](https://www.python.org/) ou superior

### Instruções de Instalação e Execução

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/SEU-USUARIO/chat-web-flask.git](https://github.com/SEU-USUARIO/chat-web-flask.git)
    ```

2.  **Navegue até a pasta do projeto:**
    ```bash
    cd chat-web-flask
    ```

3.  **Crie e ative um ambiente virtual:**
    ```bash
    # Criar o ambiente
    python -m venv venv

    # Ativar no Windows
    .\venv\Scripts\activate

    # Ativar no macOS/Linux
    source venv/bin/activate
    ```

4.  **Instale as dependências:**
    O arquivo `requirements.txt` contém todas as bibliotecas Python necessárias.
    ```bash
    pip install -r requirements.txt
    ```

5.  **Execute o servidor:**
    ```bash
    python app.py
    ```

6.  **Acesse a aplicação:**
    Abra seu navegador de internet e acesse o seguinte endereço:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Como Testar

Para testar a funcionalidade de chat em tempo real, você precisará simular múltiplos usuários.

1.  Abra duas ou mais abas ou janelas do seu navegador e acesse `http://127.0.0.1:5000` em cada uma delas.
2.  No **Cliente 1**:
    * Digite um nome de usuário (ex: "Ana").
    * Clique em "Conectar".
    * Digite um nome para a sala (ex: "jogos") e uma senha (ex: "123").
    * Clique em "Criar Sala" e depois em "Entrar na Sala".
3.  No **Cliente 2**:
    * Digite um nome de usuário diferente (ex: "Beto").
    * Clique em "Conectar".
    * Digite o mesmo nome da sala ("jogos") e a mesma senha ("123").
    * Clique em "Entrar na Sala".
4.  Agora, envie uma mensagem de qualquer um dos clientes. A mensagem deverá aparecer instantaneamente na tela do outro cliente.
5.  Observe as mensagens de status, como "[usuário] entrou na sala", que aparecem para todos os participantes.

## Estrutura e Explicação do Código

### `app.py` (Backend)

Este arquivo é o coração do servidor. Ele usa Flask para a estrutura web e Flask-SocketIO para a comunicação em tempo real.

* **Inicialização:** O código começa importando as bibliotecas necessárias e inicializando o Flask e o SocketIO.
* **Armazenamento de Estado:** Duas variáveis globais (`users_in_rooms` e `rooms`) são usadas como um "banco de dados" em memória para armazenar as informações sobre as salas criadas, suas senhas e os usuários conectados. Para um projeto em produção, isso seria substituído por um banco de dados real (como SQLite ou PostgreSQL).
* **Rota HTTP (`@app.route('/')`):** Há uma única rota HTTP que simplesmente renderiza e serve o arquivo `templates/index.html` para qualquer usuário que acesse a raiz do site.
* **Eventos WebSocket (`@socketio.on('evento')`):** Esta é a parte principal da lógica do servidor. O servidor "escuta" por eventos enviados pelo cliente (JavaScript) e reage a eles.
    * `on('create')`: Recebe o nome de uma sala e uma senha (opcional). Adiciona a nova sala ao dicionário `rooms`.
    * `on('join')`: Lida com a entrada de um usuário em uma sala. Ele verifica se a sala existe, valida a senha, e então usa a função `join_room(room)` do Socket.IO para inscrever o cliente naquele canal de comunicação. Em seguida, ele emite (envia) uma mensagem de status para todos na sala.
    * `on('text')`: Disparado quando um cliente envia uma mensagem de texto. O servidor recebe a mensagem e a retransmite para **todos os clientes na mesma sala** usando `emit('message', ..., room=room)`. Isso garante o isolamento das conversas.
    * `on('leave')`: Lida com a saída de um usuário, usando `leave_room(room)` e atualizando as estruturas de dados.

### `templates/index.html` (Frontend)

Este único arquivo contém a estrutura (HTML), a aparência (CSS) e o comportamento (JavaScript) do cliente.

* **Estrutura (HTML):** O corpo da página é dividido em duas seções principais: `#login` e `#chat-area`. A área de chat só se torna visível após o usuário fornecer um nome. A estrutura inclui uma lista não ordenada (`<ul>`) para as mensagens e formulários para interagir com o sistema.
* **Estilização (CSS):** Um bloco `<style>` contém regras de CSS para organizar os elementos na tela, criar uma aparência limpa e diferenciar as mensagens do usuário atual das mensagens de outros participantes.
* **Lógica do Cliente (JavaScript):**
    * **Conexão:** A linha `const socket = io();` é a responsável por iniciar a conexão WebSocket com o servidor.
    * **Emissão de Eventos (`socket.emit()`):** Ações do usuário, como clicar no botão "Entrar na Sala" ou "Enviar", são capturadas por `addEventListener`. Esses eventos disparam a função `socket.emit('nome_do_evento', dados)`, enviando as informações (nome do usuário, sala, mensagem) para o backend processar.
    * **Recepção de Eventos (`socket.on()`):** O cliente também "escuta" por eventos enviados pelo servidor.
        * `socket.on('message', ...)`: Quando o servidor retransmite uma mensagem, este evento é acionado. O JavaScript cria dinamicamente um novo elemento de lista (`<li>`), insere o conteúdo da mensagem e o adiciona à área de chat.
        * `socket.on('status', ...)`: Funciona de forma similar, mas para mensagens do sistema (entrada/saída de usuários).
        * `socket.on('error', ...)`: Exibe um alerta na tela do usuário caso o servidor envie uma mensagem de erro.

## Funcionalidades Implementadas

- [x] **Comunicação em Tempo Real:** Mensagens instantâneas via WebSockets.
- [x] **Múltiplas Salas:** Suporte para a criação e gerenciamento de várias salas de chat simultâneas.
- [x] **Isolamento de Salas:** Mensagens de uma sala são restritas apenas aos seus participantes.
- [x] **Salas Privadas:** Possibilidade de proteger uma sala com senha.
- [x] **Interface Web Simples:** Interface de usuário limpa e funcional que roda em qualquer navegador moderno.
- [x] **Status de Usuários:** Notificações de entrada e saída de usuários nas salas.

## Possíveis Melhorias Futuras

- **Persistência de Dados:** Integrar um banco de dados (ex: SQLite) para que as salas e o histórico de mensagens não se percam quando o servidor é reiniciado.
- **Autenticação de Usuários:** Implementar um sistema de registro e login completo, com senhas hasheadas e sessões de usuário.
- **Mensagens Privadas:** Adicionar a funcionalidade de enviar mensagens diretas entre dois usuários.
- **Lista de Salas e Usuários:** Exibir uma lista de salas disponíveis e uma lista de usuários online em cada sala.
- **Melhorias de UI/UX:** Aprimorar a interface com um framework como React ou Vue.js, e adicionar recursos como indicadores de "digitando...", emojis e envio de imagens.
- **Deploy:** Publicar a aplicação em uma plataforma de nuvem (como Heroku, PythonAnywhere ou AWS) para torná-la acessível publicamente na internet.
