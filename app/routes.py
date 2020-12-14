from flask import render_template, redirect, url_for, flash, session, request, jsonify, Response, g
from flask_login import current_user, login_user, login_required, logout_user
from werkzeug.security import check_password_hash
from werkzeug.urls import url_parse
from app.models import User, Game, GameMove
from app.forms import LoginForm, SignUpForm
from app.gameboard import Gameboard
from app.piece import Piece, LightPiece, DarkPiece
from app.result import Result
from datetime import timedelta
from app import app, db, csrf
import json, time, re

#db.drop_all()
db.create_all()
db.session.commit()

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=2)
    session.modified = True
    g.user = current_user

@app.after_request
def apply_caching(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
@app.route("/index")
@app.route("/home")
@login_required
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=current_user.username).first_or_404()
    users = User.query.all()
    return render_template('index.html', title='Home', user=user, users=users)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/login", methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.username == form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
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
        username_re_match =  re.fullmatch("^(?!.*[-_]{2,})(?=^[^-_].*[^-_]$)[\w\s-]{5,8}$", form.username.data)
        password_re_match = re.fullmatch("^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%&])[A-Za-z\d@$!%&]{8,15}$", form.password.data)
        if not bool(username_re_match):
            flash("Username must contain a length of at least 5 characters and a maximum of 8 characters."
            "Username must contain at least one special character like - or _. "
            "Username must not start or end with these special characters and they can't be one after", 'error')
            return redirect(url_for('signup'))
        if not bool(password_re_match):
            flash("Password must contain a length of at least 8 characters and a maximum of 15 characters."
            "Password must contain at least one lowercase character"
            "Password must contain at least one uppercase character"
            "Password must contain at least one digit [0-9]."
            "Password must contain at least one special character like ! @ # & $ %.", 'error')
            return redirect(url_for('signup'))
        user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("You are successfully registered!", "success")
        return redirect(url_for("login"))
    return render_template('signup.html', title='Sign Up', form=form)

@app.route("/create_game", methods=['POST'])
def create_game():
    gameName = request.form.get('gamename')
    gameName_re_match = re.match("^[A-Za-z0-9]{5,10}$",gameName)
    if not bool(gameName_re_match):
        flash("GameName must contain a length of at least 5 characters and a maximum of 10 characters.", 'error')
        return redirect(url_for('index'))
    user = User.query.filter_by(username=current_user.username).first_or_404()
    game = Game(gamename=gameName, player1_id=user.id, player1_name=user.username, winner="")
    db.session.add(game)
    db.session.commit()
    flash("Game is successfully created!", "success")
    gm = GameMove(game_id=game.id, turn_player_id=game.player1_id, turn_player_name=game.player1_name, player_action="Created")
    db.session.add(gm)
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/games")
def games():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    games = [game for game in Game.query.all()]
    return render_template("games.html", games=games)

@app.route("/show_moves/<string:gamename>")
def show_moves(gamename):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    game = Game.query.filter_by(gamename=gamename).first()
    gameMoves = GameMove.query.all()
    return render_template('moves.html', title='Moves', game=game, gameMoves=gameMoves)

@app.route("/completed_games")
def completed_games():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    games = Game.query.filter_by(completed=1).all()
    return render_template('game_moves.html', title='Completed Games', games=games)

@app.route("/join_game/<string:gameName>", methods=["GET","POST"])
@csrf.exempt
def join_game(gameName):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    game = Game.query.filter_by(gamename=gameName).first()
    user = User.query.filter_by(username=current_user.username).first_or_404()
    if game.player1_id == user.id:
            pass
    else:
        game.player2_id = user.id
        game.player2_name = user.username
        gm = GameMove(game_id=game.id, turn_player_id=game.player1_id, turn_player_name=game.player1_name, player_action="StartGame")
        db.session.add(gm)
        db.session.commit()
    gameboard = Gameboard.build(9)
    board = gameboard.board
    return render_template('play.html', board=board, user=user, gamename=game.gamename)

@app.route('/move', methods=["POST"])
def move():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if request.method == 'POST':
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

@app.route('/first_move/<string:gameName>', methods=["POST"])
@csrf.exempt
def first_move(gameName):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if request.method == 'POST':
        user = User.query.filter_by(username=current_user.username).first_or_404()
        game = Game.query.filter_by(gamename=gameName).first()
        gameboard = Gameboard(__prepare_board(request), request.form['last_move'])
        board = gameboard.board
        x = int(request.form['x'])
        y = int(request.form['y'])
        if(user.username == game.player1_name):
            board[y][x] = DarkPiece()
            last_move = 'dark'
            gm = GameMove(game_id=game.id, turn_player_id=game.player1_id, turn_player_name=game.player1_name,
            player_action="Moves",x_coor = x, y_coor = y, color = "dark")
        else:
            board[y][x] = LightPiece()
            last_move = 'light'
            gm = GameMove(game_id=game.id, turn_player_id=game.player2_id, turn_player_name=game.player2_name,
            player_action="Moves",x_coor = x, y_coor = y, color = "light")
        db.session.add(gm)
        db.session.commit()
        return render_template('play.html', board=board, user=user, last_move=last_move, gamename=game.gamename)

@app.route('/update_board/<string:gameName>', methods=["POST"])
@csrf.exempt
def update_board(gameName):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if request.method == 'POST':
        user = User.query.filter_by(username=current_user.username).first_or_404()
        game = Game.query.filter_by(gamename=gameName).first()
        game_moves = GameMove.query.filter_by(game_id=game.id).order_by(GameMove.id.desc())

        this_game_moves = [gm for gm in game_moves if gm.x_coor != None]
        gameboard = __prepare_updated_board(this_game_moves)
        if(user.username == game.player1_name):
            last_move = 'dark'
        else:
            last_move = 'light'
        return render_template('play.html', board=gameboard, user=user, last_move=last_move, gamename=game.gamename)

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

def __prepare_updated_board(moves):
    board_size = 9
    #pieces_count = int(request.form['pieces_count'])
    prepared_board = __generate_empty_board(board_size)

    for mv in moves:
        x = mv.x_coor
        y = mv.y_coor
        color = mv.color

        if color == 'dark':
            prepared_piece = DarkPiece()
        if color == 'light':
            prepared_piece = LightPiece()

        prepared_board[y][x] = prepared_piece

    return prepared_board

def __generate_empty_board(size):
    board = []

    for i in range(size):
        board.append([None]*size)

    return board

@app.route('/stream/<string:params>',methods=["GET","POST"])
def stream(params):
    gameName, username = params.split("&")
    user = User.query.filter_by(username= username).first_or_404()
    game = Game.query.filter_by(gamename=gameName).first()

    def event_stream(game, user):
        while True:
            yield 'data: {}\n\n'.format(detect_move(game, user))
    return Response(event_stream(game, user), mimetype="text/event-stream")

def detect_move(game, user):
    time.sleep(10)
    gm = GameMove.query.filter_by(game_id=game.id).order_by(GameMove.id.desc()).first()
    return "Waiting" + ";" + str(gm.color)

@app.route("/stop_game/<string:gameName>", methods=["POST"])
@csrf.exempt
def stop_game(gameName):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    game = Game.query.filter_by(gamename=gameName).first()
    user = User.query.filter_by(username=current_user.username).first_or_404()
    light_pieces = request.form['light_pieces']
    dark_pieces = request.form['dark_pieces']
    if(light_pieces > dark_pieces):
        game.completed = 1
        game.player2_score = light_pieces
        game.player1_score = dark_pieces
        game.winner = game.player2_name
        gmove = GameMove(game_id=game.id, turn_player_id=game.player2_id, turn_player_name=game.player2_name, player_action="Gameover")
        user_player = User.query.filter_by(id=game.player2_id).first_or_404()
        user_player.win = 1
    else:
        game.completed=1
        game.player1_score=dark_pieces
        game.player2_score = light_pieces
        game.winner=game.player1_name
        gmove = GameMove(game_id=game.id, turn_player_id=game.player1_id, turn_player_name=game.player1_name, player_action="Gameover")
        user_player = User.query.filter_by(id=game.player1_id).first_or_404()
        user_player.win = 1
    flash("Game is stopped!", "success")
    db.session.add(gmove)
    db.session.commit()
    return redirect(url_for('index'))
