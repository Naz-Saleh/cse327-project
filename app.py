from flask import Flask, render_template, url_for, redirect, request
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from tables import db, User, Article
from form import FormFactory, bcrypt
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///dailydash.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'habijabi' 

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)

# Login Manager Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

# --- API CONFIGURATION ---
NEWS_API_KEY = 'eeb2ea5807824ff3b5e877fb1767466c'

@login_manager.user_loader
def load_user(user_id): 
    return User.query.get(int(user_id)) 

# --- Helper Function ---
def get_news_headlines(category='general'):
    # 1. Check Database for cached news of this specific category
    try:
        last_article = Article.query.filter_by(category=category).order_by(Article.fetched_at.desc()).first()
        
        # If we have data and it's less than 48 hours old, use DB
        if last_article and (datetime.utcnow() - last_article.fetched_at) < timedelta(hours=48):
            print(f"Using cached {category} news from Database...")
            db_articles = Article.query.filter_by(category=category).all()
            
            articles_formatted = []
            for a in db_articles:
                articles_formatted.append({
                    'title': a.title,
                    'url': a.url,
                    'urlToImage': a.urlToImage,
                    'description': a.description,
                    'source': {'name': a.source_name}, 
                    'publishedAt': a.published_at
                })
            return articles_formatted
    except Exception as e:
        print(f"Database check failed: {e}")

    # 2. Fetch fresh news from API
    print(f"Fetching fresh {category} news from API...")
    url = f"https://newsapi.org/v2/top-headlines?country=us&category={category}&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get('status') == 'ok':
            articles = data.get('articles', [])
            
            # 3. Save to Database
            # First, clear ONLY the old news for this specific category
            try:
                db.session.query(Article).filter_by(category=category).delete()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print("Error clearing old news:", e)

            # Now add the new articles
            for art in articles:
                if art.get('title') and art.get('url'): 
                    new_article = Article(
                        title=art.get('title'),
                        url=art.get('url'),
                        urlToImage=art.get('urlToImage'),
                        source_name=art.get('source', {}).get('name', 'Unknown'),
                        description=art.get('description'),
                        published_at=art.get('publishedAt'),
                        category=category # Save the category!
                    )
                    db.session.add(new_article)
            db.session.commit()
            
            return articles
        else:
            print(f"NewsAPI Error: {data.get('message')}")
            return []
    except Exception as e:
        print("Request failed:", e)
        return []

# --- Routes ---
@app.route("/", methods=['GET','POST'])
def hello_world():
    return render_template('index.html')

@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    # Get the category from the URL (e.g., /dashboard?category=sports)
    # Default to 'general' if no category is clicked
    selected_category = request.args.get('category', 'general')
    
    # Fetch news for that category
    articles = get_news_headlines(selected_category)
    
    return render_template('dashboard.html', articles=articles, current_category=selected_category)

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