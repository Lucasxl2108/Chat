import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-segura!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)

CATEGORIZED_ROOMS = {
    "🎬 Filmes": {
        "Clássicos & Blockbusters": [
            {'name': 'Matrix', 'image': 'https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDllZjNkYzNjNTc4L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_FMjpg_UX1000_.jpg'},
            {'name': 'O Poderoso Chefão', 'image': 'https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_FMjpg_UX1000_.jpg'},
            {'name': 'Vingadores: Ultimato', 'image': 'https://m.media-amazon.com/images/M/MV5BMTc5MDE2ODcwNV5BMl5BanBnXkFtZTgwMzI2NzQ2NzM@._V1_FMjpg_UX1000_.jpg'}
        ]
    },
    "📺 Séries": {
        "Aclamadas pela Crítica": [
            {'name': 'Breaking Bad', 'image': 'https://m.media-amazon.com/images/M/MV5BYmQ4YWMxYjUtNjZmYi00MDQ1LWFjMjMtNjA5ZDdiYjdiODU5XkEyXkFqcGdeQXVyMTMzNDExODE5._V1_FMjpg_UX1000_.jpg'},
            {'name': 'Vikings', 'image': 'https://wallpapers.com/images/high/vikings-pictures-lx84id03oyttxjfp.webp'},
            {'name': 'La Casa de Papel', 'image': 'https://wallpapers.com/images/high/money-heist-professor-dali-mask-v0frorkujxu6znlv.webp'}
        ]
    },
    "🎮 Games": {
        "Títulos Populares": [
            {'name': 'Grand Theft Auto V', 'image': 'https://wallpapers.com/images/high/4k-gta-5-miriam-turner-overpass-5ljsktva6bt9ttq8.webp'},
            {'name': 'The Last of Us', 'image': 'https://wallpapers.com/images/high/girl-at-sunset-the-last-of-us-4k-0w00hui3yqsi27q7.webp'},
            {'name': 'EA Sports FC (FIFA)', 'image': 'https://wallpapers.com/images/high/fifa-17-star-players-sl7q0wlwe3ezx28s.webp'}
        ]
    }
}

ALL_ROOMS = [room['name'] for category in CATEGORIZED_ROOMS.values() for sub_category in category.values() for room in sub_category]
users_in_room = {room: set() for room in ALL_ROOMS}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return redirect(url_for('rooms'))

@app.route('/rooms')
@login_required
def rooms():
    return render_template('rooms.html', categorized_rooms=CATEGORIZED_ROOMS)

@app.route('/chat/<room_name>')
@login_required
def chat(room_name):
    if room_name not in ALL_ROOMS:
        return "Sala não encontrada!", 404
    return render_template('chat.html', room_name=room_name)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('rooms'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('rooms'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('rooms'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Este nome de usuário já existe. Tente outro.', 'danger')
            return redirect(url_for('login'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Cadastro realizado com sucesso! Sua senha é "{password}". Faça o login.', 'success')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files['file']
    room = request.form['room']
    if file:
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename
        file.save(os.path.join('uploads', unique_filename))
        socketio.emit('new_message', {
            'user': current_user.username,
            'type': 'image',
            'url': url_for('uploaded_file', filename=unique_filename)
        }, room=room)
    return 'OK'

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@socketio.on('join')
def on_join(data):
    username = current_user.username
    room = data['room']
    join_room(room)
    users_in_room[room].add(username)
    emit('update_user_list', list(users_in_room[room]), room=room)
    emit('status', {'msg': username + ' entrou na sala.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = current_user.username
    room = data['room']
    leave_room(room)
    if username in users_in_room[room]:
        users_in_room[room].remove(username)
    emit('update_user_list', list(users_in_room[room]), room=room)
    emit('status', {'msg': username + ' saiu da sala.'}, room=room)

@socketio.on('disconnect')
def on_disconnect():
    username = current_user.username
    for room in users_in_room:
        if username in users_in_room[room]:
            users_in_room[room].remove(username)
            emit('update_user_list', list(users_in_room[room]), room=room)
            emit('status', {'msg': username + ' se desconectou.'}, room=room)
            break

@socketio.on('message')
def handle_message(data):
    room = data['room']
    emit('new_message', {
        'msg': data['msg'],
        'user': current_user.username,
        'type': 'text'
    }, room=room)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)