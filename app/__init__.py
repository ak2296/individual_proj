from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from elasticsearch import Elasticsearch
from config import Config
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_ckeditor import CKEditor
from flask_mail import Mail


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)
ckeditor = CKEditor(app)
moment = Moment(app)
mail = Mail(app)
app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None

from app import routes, models, errors