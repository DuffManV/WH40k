import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from werkzeug.security import check_password_hash
from database import get_db, init_db
from gigachat_service import generate_post, generate_mock_post, get_available_topics, is_configured

app = Flask(__name__)
app.secret_key = 'wh40k-secret-key-2026'

init_db()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

@app.context_processor
def inject_globals():
    db = get_db()
    recent_posts = db.execute(
        "SELECT id, title, created_at FROM blog_posts ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    db.close()
    return {'recent_blog_posts': recent_posts}

@app.route('/')
def index():
    db = get_db()
    factions = db.execute("SELECT * FROM factions LIMIT 3").fetchall()
    characters = db.execute("SELECT * FROM characters LIMIT 3").fetchall()
    db.close()
    return render_template('index.html', factions=factions, characters=characters)

@app.route('/universe')
def universe():
    db = get_db()
    paragraphs = db.execute("SELECT content FROM universe_paragraphs ORDER BY ord").fetchall()
    db.close()
    return render_template('universe.html', paragraphs=[p['content'] for p in paragraphs])

@app.route('/factions')
def factions():
    db = get_db()
    factions = db.execute("SELECT * FROM factions").fetchall()
    db.close()
    return render_template('factions.html', factions=factions)

@app.route('/characters')
def characters():
    db = get_db()
    characters = db.execute("SELECT * FROM characters").fetchall()
    db.close()
    return render_template('characters.html', characters=characters)

@app.route('/timeline')
def timeline():
    db = get_db()
    events = db.execute("SELECT * FROM timeline_events").fetchall()
    db.close()
    return render_template('timeline.html', events=events)

@app.route('/gallery')
def gallery():
    db = get_db()
    items = db.execute("SELECT * FROM gallery_items").fetchall()
    db.close()
    return render_template('gallery.html', items=items)

@app.route('/blog')
def blog():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    posts = db.execute(
        "SELECT * FROM blog_posts ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (per_page, offset)
    ).fetchall()
    total = db.execute("SELECT COUNT(*) as cnt FROM blog_posts").fetchone()['cnt']
    db.close()
    return render_template('blog.html', posts=posts, page=page, total=total, per_page=per_page)

@app.route('/blog/<int:post_id>')
def blog_post(post_id):
    db = get_db()
    post = db.execute("SELECT * FROM blog_posts WHERE id = ?", (post_id,)).fetchone()
    db.close()
    if not post:
        return redirect(url_for('blog'))
    return render_template('blog_post.html', post=post)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        db.close()
        if user and check_password_hash(user['password'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Вы вошли как администратор.', 'success')
            return redirect(url_for('admin_panel'))
        flash('Неверный логин или пароль.', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Вы вышли из панели администратора.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_panel():
    db = get_db()
    post_count = db.execute("SELECT COUNT(*) as cnt FROM blog_posts").fetchone()['cnt']
    faction_count = db.execute("SELECT COUNT(*) as cnt FROM factions").fetchone()['cnt']
    char_count = db.execute("SELECT COUNT(*) as cnt FROM characters").fetchone()['cnt']
    posts = db.execute("SELECT id, title, created_at FROM blog_posts ORDER BY created_at DESC LIMIT 10").fetchall()
    db.close()
    return render_template('admin_panel.html', post_count=post_count, faction_count=faction_count, char_count=char_count, posts=posts)

@app.route('/admin/posts/new', methods=['GET', 'POST'])
@login_required
def admin_new_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not content:
            flash('Заголовок и содержание не могут быть пустыми.', 'error')
            return render_template('admin_edit_post.html', post=None)
        db = get_db()
        db.execute(
            "INSERT INTO blog_posts (title, content, author) VALUES (?, ?, ?)",
            (title, content, session.get('admin_username', 'admin'))
        )
        db.commit()
        db.close()
        flash('Пост опубликован!', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('admin_edit_post.html', post=None)

@app.route('/admin/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_post(post_id):
    db = get_db()
    post = db.execute("SELECT * FROM blog_posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        db.close()
        return redirect(url_for('admin_panel'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not content:
            flash('Заголовок и содержание не могут быть пустыми.', 'error')
            return render_template('admin_edit_post.html', post=post)
        db.execute("UPDATE blog_posts SET title = ?, content = ? WHERE id = ?", (title, content, post_id))
        db.commit()
        db.close()
        flash('Пост обновлён!', 'success')
        return redirect(url_for('admin_panel'))
    db.close()
    return render_template('admin_edit_post.html', post=post)

@app.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def admin_delete_post(post_id):
    db = get_db()
    db.execute("DELETE FROM blog_posts WHERE id = ?", (post_id,))
    db.commit()
    db.close()
    flash('Пост удалён.', 'info')
    return redirect(url_for('admin_panel'))

@app.route('/admin/posts/generate', methods=['GET', 'POST'])
@login_required
def admin_generate_post():
    topics = get_available_topics()
    gigachat_connected = is_configured()
    result = None

    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        style = request.form.get('style', 'lore')
        mode = request.form.get('mode', 'gigachat')
        if not topic:
            flash('Выберите или укажите тему.', 'error')
            return render_template('admin_generate.html', topics=topics, result=None, gigachat_connected=gigachat_connected)

        if mode == 'mock':
            result = generate_mock_post(topic)
            if result:
                flash('Пост сгенерирован (эмуляция)!', 'success')
        else:
            result = generate_post(topic, style)
            if result:
                flash('Пост сгенерирован через GigaChat!', 'success')
            else:
                flash('GigaChat недоступен. Используйте эмуляцию.', 'error')

    return render_template('admin_generate.html', topics=topics, result=result, gigachat_connected=gigachat_connected)

@app.route('/admin/posts/generate/save', methods=['POST'])
@login_required
def admin_save_generated():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    if not title or not content:
        flash('Заголовок и содержание не могут быть пустыми.', 'error')
        return redirect(url_for('admin_generate_post'))
    db = get_db()
    db.execute(
        "INSERT INTO blog_posts (title, content, author) VALUES (?, ?, ?)",
        (title, content, session.get('admin_username', 'admin'))
    )
    db.commit()
    db.close()
    flash('Сгенерированный пост опубликован!', 'success')
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
