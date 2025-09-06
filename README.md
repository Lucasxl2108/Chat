Bem-vindo ao PopChat! Esta é uma aplicação web de chat em tempo real para fãs de filmes, séries e jogos.

## ✨ Funcionalidades Principais

* Cadastro e Login de usuários.
* Navegação por categorias e salas de chat com pôsteres.
* Envio de mensagens, emojis e imagens em tempo real.
* Lista de usuários ativos em cada sala.

## 🛠️ Tecnologias

* **Backend:** Python, Flask, Socket.IO
* **Banco de Dados:** SQLite
* **Frontend:** HTML, CSS, JavaScript

## 🚀 Como Executar

1.  **Crie e ative um ambiente virtual:**
    ```bash
    # No Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

2.  **Instale as dependências:**
    ```bash
    pip install Flask Flask-SocketIO Flask-SQLAlchemy Flask-Login eventlet
    ```

3.  **Rode o servidor:**
    ```bash
    python app.py
    ```

4.  **Acesse no navegador:**
    Abra o endereço [http://127.0.0.1:5000](http://127.0.0.1:5000)
