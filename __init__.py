from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login = LoginManager(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
login.login_view = 'login'
login.refresh_view = 'relogin'
login.needs_refresh_message = (u"Session timedout, please re-login")
login.needs_refresh_message_category = "info"
from app import routes

if __name__ == "__main__":
    app.run(ssl_context=('cert.pem', 'key.pem'))
