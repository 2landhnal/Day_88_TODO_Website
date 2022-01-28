from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from wtforms import StringField, SubmitField, DecimalField, URLField, IntegerField, BooleanField, validators
from wtforms.validators import DataRequired
from functools import wraps
from forms import RegisterForm, LoginForm, Form
from flask_wtf import FlaskForm
from random import choice
import os

app = Flask(__name__)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL1', 'sqlite:///todos.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    todos = relationship("Todo", back_populates="author")

class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    todo = db.Column(db.String(250), nullable=False)
    finished = db.Column(db.Boolean, nullable=False)
    color = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship("User", back_populates='todos')

db.create_all()

colors = [
   'background-color: #FA8BFF; background-image: linear-gradient(19deg, #FA8BFF 0%, #2BD2FF 52%, #2BFF88 90%); color:white;',
   'background-color: #21D4FD; background-image: linear-gradient(19deg, #21D4FD 0%, #B721FF 100%); color:white;',
   'background-color: #FEE140; background-image: linear-gradient(19deg, #FEE140 0%, #FA709A 100%); color:white;',
   'background-color: #FEE140; background-image: linear-gradient(19deg, #FEE140 0%, #FA709A 100%); color:white;',
   'background-color: #4158D0; background-image: linear-gradient(19deg, #4158D0 0%, #C850C0 46%, #FFCC70 100%); color:white;',
   'background-color: #F4D03F; background-image: linear-gradient(19deg, #F4D03F 0%, #16A085 100%); color:white',
   'background-color: #74EBD5; background-image: linear-gradient(19deg, #74EBD5 0%, #9FACE6 100%); color:white',
   'background-image: linear-gradient( 19deg,  rgba(61,245,167,1) 11.2%, rgba(9,111,224,1) 91.1% ); color:white',
   'background-image: linear-gradient( 19deg,  rgba(245,116,185,1) 14.7%, rgba(89,97,223,1) 88.7% ); color:white',
   'background-image: linear-gradient( 19deg,  rgba(71,139,214,1) 23.3%, rgba(37,216,211,1) 84.7% ); color:white',
   'background-image: linear-gradient( 19deg,  rgba(201,37,107,1) 15.4%, rgba(116,16,124,1) 74.7% ); color:white',
   'background-image: linear-gradient( 19deg,  rgba(115,18,81,1) 10.6%, rgba(28,28,28,1) 118% ); color:white',
   'background-image: linear-gradient( 19deg,  rgba(31,212,248,1) 11%, rgba(218,15,183,1) 74.9% ); color:white',
   'background-image: linear-gradient( 19deg,  rgba(24,138,141,1) 11.2%, rgba(96,221,142,1) 91.1% ); color:white',
]


@app.route('/', methods=['POST', 'GET'])
def home():
    todos = None
    leng = 1
    if current_user.is_authenticated:
        todos = current_user.todos
        leng = (len(todos)-1) % 4 +1
    if request.method == 'POST':
        form = request.form
        new_todo = Todo(
            todo = form['todo'],
            finished = False,
            color = choice(colors),
            date = date.today().strftime("%B %d, %Y"),
            author = current_user,
        )
        db.session.add(new_todo)
        db.session.commit()
        todos = current_user.todos
        leng = (len(todos)-1) % 4 +1
        return redirect(url_for('home', current_user=current_user, todos=todos, leng=leng))
    return render_template('index.html', todos=todos, current_user=current_user, leng=leng)

@app.route('/add', methods=['GET', 'POST'])
def add():
    form = Form()
    if form.validate_on_submit():
        new_todo = Todo(
            todo = form.todo.data,
            finished = False,
            color = choice(colors),
            date = date.today().strftime("%B %d, %Y"),
        )
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add.html', form=form)

@app.route('/finished/<int:id>', methods=['GET', 'POST'])
def finished(id):
    todo_finished = Todo.query.get(id)
    todo_finished.finished = True
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form = request.form
        new_user = User(
            email = form['email'],
            password = generate_password_hash(form['password'], method='pbkdf2:sha256', salt_length=8),
            name = form['username'],
        )
        is_matched = User.query.filter_by(email=form['email']).first()
        if not is_matched:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
        else:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form = request.form
        user = User.query.filter_by(email=form['email']).first()
        if user:
            hashed_pass = user.password
            if check_password_hash(hashed_pass, form['password']):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('email or Password is incorrect')
                return redirect(url_for('login'))
        else:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/delete/<int:id>", methods=['POST', 'GET'])
def delete(id):
    todo_to_delete = Todo.query.get(id)
    db.session.delete(todo_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
