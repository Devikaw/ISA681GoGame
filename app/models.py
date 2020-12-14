from app import db, login, bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password = db.Column(db.String(128))
    win = db.Column(db.Integer, default=0)
    loss = db.Column(db.Integer, default=0)
    draw = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password, 10).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

@login.user_loader
def load_user(id):
    return User.query.get(id)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gamename = db.Column(db.String, nullable=False)
    player1_name = db.Column(db.String, nullable=False, default="Not Joined Yet")
    player2_name = db.Column(db.String, nullable=False, default="Not Joined Yet")
    player1_id = db.Column(db.Integer)
    player2_id = db.Column(db.Integer)
    player1_score = db.Column(db.Integer, default=0)
    player2_score = db.Column(db.Integer, default=0)
    completed = db.Column(db.Integer, default=0)
    winner = db.Column(db.String)

    def __repr__(self):
        return '<Game %r>' % self.id

class GameMove(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow())
    turn_player_id = db.Column(db.Integer, nullable=False)
    turn_player_name = db.Column(db.String, nullable=False)
    player_action = db.Column(db.String)
    x_coor = db.Column(db.Integer)
    y_coor = db.Column(db.Integer)
    color = db.Column(db.String)
    player1_move = db.Column(db.String)
    player2_move = db.Column(db.String)

    def __repr__(self):
        return '<Move %r>' % self.id
