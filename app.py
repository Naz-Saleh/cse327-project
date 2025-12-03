from flask import Flask, render_template, url_for, redirect

from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

from tables import db, User
from flask_bcrypt import Bcrypt
from form import FormFactory, bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///dailydash.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = 'habijabi' 

db.init_app(app)
bcrypt.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'# takes the user back to login page if he/she tries to access something that requires login

@login_manager.user_loader
def load_user(user_id): # flask login will call this whenever it needs the current logged in user 
    return User.query.get(int(user_id)) # everytime the page relods flask login does it





@app.route("/", methods=['GET','POST'])
def hello_world():
    return render_template('index.html')

@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    form_factory = FormFactory()
    form = form_factory.create_form('signup')

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form_factory = FormFactory()
    form = form_factory.create_form('login')
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)