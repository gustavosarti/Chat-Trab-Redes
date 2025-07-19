# Projeto: Chat Web Seguro em Tempo Real com Flask

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.x-orange)
![Socket.IO](https://img.shields.io/badge/Socket.IO-4.x-yellow)
![Cryptography](https://img.shields.io/badge/Criptografia-AES-purple)

## Descrição

Este projeto é uma aplicação web completa de chat em tempo real, construída com Python e Flask. A aplicação vai além de um simples chat, incorporando um robusto sistema de **autenticação de usuários com sessões**, **salas de chat privadas protegidas por senha** e **criptografia de ponta a ponta (nível de aplicação) para as mensagens trocadas nas salas**.

A interface é reativa e dividida em dois estados principais: um "Lobby", onde os usuários podem ver quem está online no servidor e gerenciar salas, e uma "Sala de Chat", para a comunicação. O projeto também inclui funcionalidades avançadas como mensagens privadas (sussurros), cálculo de latência (ping) em tempo real, e uma página de monitoramento de recursos do servidor.

## Funcionalidades Implementadas

- ✅ **Sistema de Autenticação:** Registro e Login de usuários com senhas seguras (hashed) e persistência de sessão.
- ✅ **Múltiplas Salas:** Criação de salas públicas ou privadas (protegidas por senha).
- ✅ **Lobby Interativo:** Visualização de todos os usuários online no servidor e de todas as salas disponíveis.
- ✅ **Criptografia de Mensagens:** As mensagens trocadas dentro das salas são criptografadas com o algoritmo **AES**, garantindo a confidencialidade. As chaves são gerenciadas por sala e distribuídas de forma segura aos participantes.
- ✅ **Sussurros (Mensagens Privadas):** Capacidade de enviar mensagens diretas para outros usuários, clicando em seus nomes.
- ✅ **Visualização de Latência (Ping):** As mensagens enviadas pelo usuário exibem o tempo de ida e volta (RTT) em milissegundos.
- ✅ **Interface Reativa:** A interface do usuário muda dinamicamente dependendo se o usuário está no lobby ou dentro de uma sala de chat.
- ✅ **Página de Monitoramento:** Uma rota oculta (`/memory`) exibe um gráfico em tempo real do uso de memória do servidor, útil para testes de carga.
- ✅ **Script de Teste de Estresse:** Inclui um script (`stress_test.py`) para simular dezenas de usuários simultâneos, testando a capacidade e a estabilidade da aplicação.

## Tecnologias Utilizadas

### Backend
* **Python 3:** Linguagem de programação principal.
* **Flask:** Micro-framework web para gerenciamento de rotas HTTP e sessões.
* **Flask-SocketIO:** Para comunicação bidirecional em tempo real via WebSockets.
* **pycryptodome:** Biblioteca utilizada para a criptografia AES no lado do servidor.
* **psutil:** Para coletar métricas de uso de memória do servidor para a página de monitoramento.
* **hashlib:** Para o hashing seguro das senhas dos usuários.
* **Eventlet:** Servidor WSGI para produção e execução de tarefas em background.

### Frontend
* **HTML5 / CSS3:** Estruturação e estilização da interface.
* **JavaScript (ES6):** Lógica do lado do cliente para interatividade e comunicação com o servidor.
* **Socket.IO Client:** Biblioteca JavaScript para a conexão WebSocket.
* **CryptoJS:** Biblioteca JavaScript para criptografia e descriptografia AES no navegador.
* **Chart.js:** Para a renderização do gráfico de uso de memória na página de monitoramento.

### Testes
* **requests:** Para simular requisições HTTP de login/registro no script de teste.
* **python-socketio[client]:** Para simular clientes WebSocket completos no script de teste.

## Como Executar

### Pré-requisitos
* [Git](https://git-scm.com/)
* [Python 3.8](https://www.python.org/) ou superior

### Instruções de Instalação e Execução

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git](https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git)
    cd SEU-REPOSITORIO
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Criar
    python -m venv venv
    # Ativar no Windows
    .\venv\Scripts\activate
    # Ativar no macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    O arquivo `requirements.txt` contém todas as bibliotecas necessárias.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute o servidor:**
    ```bash
    python app.py
    ```

5.  **Acesse a aplicação:**
    Abra seu navegador e acesse: [http://127.0.0.1:5000](http://127.0.0.1:5000)
    Você será direcionado para a página de login.

## Como Testar

A aplicação foi projetada para ser testada de várias maneiras.

### Teste Funcional Manual
1.  Acesse a aplicação e **registre** dois ou mais usuários em abas/navegadores diferentes.
2.  **Faça login** com os usuários. Eles aparecerão na lista "Usuários Online" no lobby.
3.  Com o Usuário A, **crie uma sala privada**. Ela aparecerá na lista de "Salas Disponíveis" com um cadeado (🔒).
4.  Com o Usuário B, **clique na sala criada** e digite a senha correta para entrar.
5.  **Envie mensagens** na sala e observe que elas são recebidas pelo outro usuário e exibem o ping para o remetente.
6.  **Teste o sussurro:** Clique no nome de um usuário em qualquer lista e envie uma mensagem privada. Observe a formatação especial no chat.
7.  Com um dos usuários, clique em **"Sair da Sala"**. Observe que a interface dele retorna ao lobby instantaneamente, e o outro usuário vê uma notificação de saída.

### Teste de Criptografia
1.  Siga as instruções no [guia de teste de criptografia](link_para_um_gist_ou_outro_arquivo_se_quiser) ou use as Ferramentas de Desenvolvedor (F12) do navegador.
2.  Na aba "Network" (Rede), filtre por "WS" e inspecione as mensagens.
3.  As mensagens de sala (evento `text`) terão o campo `msg` com um longo texto criptografado.
4.  As mensagens de sussurro (evento `private_message`) terão o campo `msg` em texto plano.

### Teste de Carga e Memória
1.  Com o servidor `app.py` rodando, abra um **novo terminal**.
2.  Execute o script de teste de estresse: `python stress_test.py`.
3.  Observe o terminal do servidor sendo inundado com mensagens de bots, e verifique se a aplicação permanece estável.
4.  Durante o teste, acesse a página **`http://127.0.0.1:5000/memory`** para ver o gráfico de uso de memória do servidor em tempo real.

## Estrutura do Código

* **`app.py`**: O servidor backend. Lida com as rotas HTTP para autenticação (`/login`, `/register`, `/logout`), a rota de monitoramento (`/memory`), e todos os eventos Socket.IO para a lógica do chat, gerenciamento de estado e criptografia.
* **`templates/login.html`**: Página de entrada da aplicação, com formulários para registro e login.
* **`templates/index.html`**: A aplicação de página única (SPA) do chat. Contém todo o HTML, CSS e JavaScript para a interface, incluindo a lógica para alternar entre as visões de Lobby e Sala de Chat, e para criptografar/descriptografar mensagens com CryptoJS.
* **`templates/memory.html`**: A página de monitoramento, que usa Chart.js para desenhar o gráfico com dados recebidos via WebSocket.
* **`stress_test.py`**: Script independente que simula múltiplos clientes para testar a carga e a estabilidade do servidor.

## Possíveis Melhorias Futuras

-   **Persistência de Dados:** Substituir os dicionários em memória por um banco de dados (ex: SQLite, PostgreSQL) para que usuários, salas e mensagens persistam entre reinicializações do servidor.
-   **Sistema de Chat Privado 1-para-1:** Melhorar os sussurros para abrirem janelas de chat dedicadas.
-   **Indicador de "Digitando...":** Adicionar um feedback visual quando um usuário está digitando uma mensagem.
-   **Deploy na Nuvem:** Publicar a aplicação em uma plataforma como Heroku, Render ou PythonAnywhere, configurando um servidor de produção (como Gunicorn) e um certificado SSL para habilitar HTTPS/WSS.
