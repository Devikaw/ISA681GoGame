from flask import render_template, redirect, url_for, flash, session, request, jsonify
from flask_login import current_user, login_user, login_required, logout_user
from werkzeug.security import check_password_hash
from werkzeug.urls import url_parse
from app.models import User, Game, GameMove
from app.forms import LoginForm, SignUpForm
from app.gameboard import Gameboard
from app.piece import Piece, LightPiece, DarkPiece
from app.result import Result
from datetime import timedelta
from app import db
from app import app
from app import csrf
import json

#db.drop_all()
db.create_all()
db.session.commit()

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=3)

@app.route('/')
@app.route("/index")
@app.route("/home")
@login_required
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('index.html', title='Home')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/login", methods=['GET','POST'])
def login():
    # username_re =  "(?=^.{3,20}$)^[a-zA-Z][a-zA-Z0-9]*[._-]?[a-zA-Z0-9]+$"
    # password_re = ""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.username == form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Login', form=form)

@app.route('/signup', methods=('GET', 'POST'))
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignUpForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("You are successfully registered!", "success")
        return redirect(url_for("login"))
    return render_template('signup.html', title='Sign Up', form=form)

@app.route("/create_game", methods=['GET','POST'])
def create_game():
    #gameName = request.form.get('gamename')
    user = User.query.filter_by(username=current_user.username).first_or_404()
    #game = Game(gamename=gameName, player1_id=user.id, player1_name=user.username, winner="")
    game = Game(gamename="game6", player1_id=user.id, player1_name=current_user.username, winner="")
    db.session.add(game)
    db.session.commit()
    #return jsonify({"success": True})
    #return render_template('game.html')
    # game = Game.query.filter_by(gamename='game6').first()
    gm = GameMove(game_id=game.id, turn_player_id=game.player1_id, turn_player_name=game.player1_name, player_action="Joined")
    db.session.add(gm)
    db.session.commit()
    return redirect(url_for('join_game', gameName='game6', game=game))

@app.route("/games")
def games():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    games = [game for game in Game.query.all()]
    return render_template("games.html", games=games)

# @app.route('/board/<int:board_size>')
# def play(board_size=8):
#     gameboard = Gameboard.build(board_size)
#     board = gameboard.board
#     return render_template('play.html', board=board)

@app.route("/join_game/<string:gameName>", methods=["GET","POST"])
@csrf.exempt
def join_game(gameName):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    game = Game.query.filter_by(gamename='game6').first()
    user = User.query.filter_by(username=current_user.username).first_or_404()
    if game.player1_id == user.id:
            pass
    else:
        game.player2_id = user.id
        game.player2_name = user.username
        gm = GameMove(game_id=game.id, turn_player_id=game.player1_id, turn_player_name=game.player1_name, player_action="Start")
        db.session.add(gm)
        db.session.commit()
    gameboard = Gameboard.build(9)
    board = gameboard.board
    return render_template('play.html', board=board, user=user)

@app.route('/move', methods=["POST"])
def move():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if request.method == 'POST':
        print("Hi Thereeee")
        gameboard = Gameboard(__prepare_board(request), request.form['last_move'])

        current_position = {
            'x': int(request.form['cur_x']),
            'y': int(request.form['cur_y'])
        }
        destination = {
            'x': int(request.form['dst_x']),
            'y': int(request.form['dst_y'])
        }
        move = gameboard.move(current_position, destination)

        board = gameboard.board
        last_move = gameboard.last_move
        return render_template('_gameboard.html', board=board, last_move=last_move, move_result=move.result, move_error=move.error)

@app.route('/first_move', methods=["POST"])
@csrf.exempt
def first_move():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if request.method == 'POST':
        user = User.query.filter_by(username=current_user.username).first_or_404()
        game = Game.query.filter_by(gamename='game6').first()
        gameboard = Gameboard(__prepare_board(request), request.form['last_move'])
        board = gameboard.board
        x = int(request.form['x'])
        y = int(request.form['y'])
        if(user.username == game.player1_name):
            board[y][x] = DarkPiece()
        else:
            board[y][x] = LightPiece()
        gm = GameMove(game_id=game.id, turn_player_id=game.player1_id, turn_player_name=game.player1_name,
        player_action="Moves",x_coor = x, y_coor = y, color = "dark")
        db.session.add(gm)
        db.session.commit()
        return render_template('play.html', board=board, user=user)

def __prepare_board(request):
    board_size = 9
    pieces_count = int(request.form['pieces_count'])
    prepared_board = __generate_empty_board(board_size)

    for i in range(pieces_count):
        x = int(request.form['pieces['+str(i)+'][x]'])
        y = int(request.form['pieces['+str(i)+'][y]'])
        color = request.form['pieces['+str(i)+'][color]']

        if color == 'DarkPiece':
            prepared_piece = DarkPiece()
        if color == 'LightPiece':
            prepared_piece = LightPiece()

        prepared_board[y][x] = prepared_piece

    return prepared_board

def __generate_empty_board(size):
    board = []

    for i in range(size):
        board.append([None]*size)

    return board
