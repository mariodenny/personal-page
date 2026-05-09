import os
import uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Profile, Skill, Project, BlogPost, Media
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret')

# Database configuration
db_user = os.getenv('MYSQL_USER', 'portfolio_user')
db_password = os.getenv('MYSQL_PASSWORD', 'portfolio_pass')
db_host = os.getenv('DB_HOST', 'localhost')
db_name = os.getenv('MYSQL_DATABASE', 'portfolio_db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload Configuration
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db.init_app(app)

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Admin Auth Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def create_initial_data():
    try:
        if Profile.query.count() == 0:
            default_profile = Profile(
                hero_title="Hi, I'm Denny Mario.<br>I build digital systems with code.",
                hero_description="Passionate about backend engineering, IoT systems, Linux servers, and modern web technologies. Currently exploring Flask, Docker, Express.js, MQTT, and scalable server architecture while building projects through Coreva.",
                about_description="I'm a technology enthusiast focused on backend development, IoT engineering, and Linux server ecosystems. I enjoy building systems that connect hardware and software together — from ESP32 monitoring systems to scalable Flask APIs deployed on VPS infrastructure.",
                contact_text="Open for collaboration, experimentation, and building interesting systems around backend engineering and IoT."
            )
            db.session.add(default_profile)

        if Skill.query.count() == 0:
            skills = ["Python", "Flask", "Express.js", "MongoDB", "Docker", "Linux", "ESP32", "MQTT", "React Native", "Bootstrap", "Git", "nginx"]
            for s in skills:
                db.session.add(Skill(name=s))
                
        if Project.query.count() == 0:
            projects = [
                Project(title="Smart Soil Monitoring System", description="Mobile-based IoT monitoring system for pakcoy plants using ESP32, MQTT, soil moisture sensors, and automated watering controls.", icon_class="bi-droplet-half", date="April 2026", category="iot"),
                Project(title="JWT Authentication System", description="Fullstack Express.js authentication system with MongoDB, JWT, Pug templating, and responsive Bootstrap UI.", icon_class="bi-shield-lock-fill", date="March 2026", category="web")
            ]
            db.session.add_all(projects)
            
        if BlogPost.query.count() == 0:
            post = BlogPost(title="Welcome to my new portfolio!", content="<p>This is my first blog post. I'll be sharing updates about my projects, IoT experiments, and backend systems here.</p>", slug="welcome-to-my-new-portfolio")
            db.session.add(post)
            
        db.session.commit()
    except Exception as e:
        print(f"Error creating initial data: {e}")

with app.app_context():
    try:
        db.drop_all() 
        db.create_all()
        create_initial_data()
    except Exception as e:
        print(f"Database connection error on startup: {e}")

# ---- PUBLIC ROUTES ----

@app.route('/')
def index():
    profile = Profile.query.first()
    skills = Skill.query.all()
    projects = Project.query.order_by(Project.id.desc()).all()
    for p in projects:
        p.images = Media.query.filter_by(entity_type='project', entity_id=p.id).all()
        
    latest_posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).limit(3).all()
    for post in latest_posts:
        post.image = Media.query.filter_by(entity_type='blog', entity_id=post.id).first()
        
    return render_template('index.html', profile=profile, skills=skills, projects=projects, latest_posts=latest_posts)

@app.route('/blog')
def blog():
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    for post in posts:
        post.image = Media.query.filter_by(entity_type='blog', entity_id=post.id).first()
    return render_template('blog.html', posts=posts)

@app.route('/blog/<slug>')
def post(slug):
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    post.image = Media.query.filter_by(entity_type='blog', entity_id=post.id).first()
    return render_template('post.html', post=post)

# ---- ADMIN ROUTES ----

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('You were successfully logged in', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('admin/login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out', 'success')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    profile = Profile.query.first()
    return render_template('admin/dashboard.html', profile=profile)

@app.route('/admin/profile/update', methods=['POST'])
@login_required
def admin_update_profile():
    profile = Profile.query.first()
    if profile:
        profile.hero_title = request.form['hero_title']
        profile.hero_description = request.form['hero_description']
        profile.about_description = request.form['about_description']
        profile.contact_text = request.form['contact_text']
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/projects')
@login_required
def admin_projects():
    projects = Project.query.all()
    return render_template('admin/projects.html', projects=projects)

@app.route('/admin/projects/add', methods=['POST'])
@login_required
def admin_add_project():
    new_project = Project(
        title=request.form['title'],
        description=request.form['description'],
        icon_class=request.form['icon_class'],
        date=request.form['date'],
        category=request.form['category']
    )
    db.session.add(new_project)
    db.session.commit()
    
    files = request.files.getlist('images')
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(os.path.join(app.root_path, file_path))
            
            media = Media(filename=filename, file_path=file_path, entity_type='project', entity_id=new_project.id)
            db.session.add(media)
    
    db.session.commit()
    flash('Project added successfully!', 'success')
    return redirect(url_for('admin_projects'))

@app.route('/admin/projects/delete/<int:id>')
@login_required
def admin_delete_project(id):
    project = Project.query.get_or_404(id)
    medias = Media.query.filter_by(entity_type='project', entity_id=project.id).all()
    for media in medias:
        try:
            os.remove(os.path.join(app.root_path, media.file_path))
        except:
            pass
        db.session.delete(media)
        
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('admin_projects'))

@app.route('/admin/skills')
@login_required
def admin_skills():
    skills = Skill.query.all()
    return render_template('admin/skills.html', skills=skills)

@app.route('/admin/skills/add', methods=['POST'])
@login_required
def admin_add_skill():
    new_skill = Skill(name=request.form['name'])
    db.session.add(new_skill)
    db.session.commit()
    flash('Skill added successfully!', 'success')
    return redirect(url_for('admin_skills'))

@app.route('/admin/skills/delete/<int:id>')
@login_required
def admin_delete_skill(id):
    skill = Skill.query.get_or_404(id)
    db.session.delete(skill)
    db.session.commit()
    flash('Skill deleted successfully!', 'success')
    return redirect(url_for('admin_skills'))

@app.route('/admin/blog')
@login_required
def admin_blog():
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()
    return render_template('admin/blog.html', posts=posts)

@app.route('/admin/blog/add', methods=['POST'])
@login_required
def admin_add_post():
    from slugify import slugify
    title = request.form['title']
    content = request.form['content']
    slug = slugify(title)
    
    if BlogPost.query.filter_by(slug=slug).first():
        import random
        slug = f"{slug}-{random.randint(1000,9999)}"

    new_post = BlogPost(title=title, content=content, slug=slug)
    db.session.add(new_post)
    db.session.commit()
    
    file = request.files.get('image')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(os.path.join(app.root_path, file_path))
        
        media = Media(filename=filename, file_path=file_path, entity_type='blog', entity_id=new_post.id)
        db.session.add(media)
        db.session.commit()
        
    flash('Blog post added successfully!', 'success')
    return redirect(url_for('admin_blog'))

@app.route('/admin/blog/delete/<int:id>')
@login_required
def admin_delete_post(id):
    post = BlogPost.query.get_or_404(id)
    media = Media.query.filter_by(entity_type='blog', entity_id=post.id).first()
    if media:
        try:
            os.remove(os.path.join(app.root_path, media.file_path))
        except:
            pass
        db.session.delete(media)
        
    db.session.delete(post)
    db.session.commit()
    flash('Blog post deleted successfully!', 'success')
    return redirect(url_for('admin_blog'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
