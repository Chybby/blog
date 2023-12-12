import os
import io
import json
import datetime
import re
import hashlib

from urllib.parse import urlparse, urljoin

from flask import (
    Flask,
    g,
    abort,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
)

from flask_cachecontrol import (
    FlaskCacheControl,
    cache,
    dont_cache)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user)

import markdown
import psycopg
from psycopg.rows import class_row, dict_row
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from jinja2 import pass_context


class AssetNotFound(Exception):
    pass


class RevAssets(object):
    '''
    Map the source -> hashed assets

    :param base_url: From where the hashed assets are served.
    :param reload: Reload the manifest each time an asset is requested.
    :param manifest: Path and filename of the manifest file.
    :param quiet: If False, a missing asset will raise an exception

    '''

    def __init__(self, base_url='/static', force_reload=False,
                 manifest='manifest.json', quiet=True):
        self.base_url = base_url.rstrip('/')
        self.force_reload = force_reload
        self.manifest = manifest
        self.assets = {}
        self.quiet = quiet

    def _load_manifest(self):
        with io.open(self.manifest, 'rt', encoding='utf-8') as mf:
            return json.loads(mf.read())

    @pass_context
    def debug_asset_url(self, context, asset):
        return self.asset_url(asset)

    def asset_url(self, asset):
        if not self.assets or self.force_reload:
            self.assets = self._load_manifest()
        asset = asset.strip('/')
        path = self.assets.get(asset)
        if not path:
            if self.quiet:
                return ''
            msg = 'Asset file {!r} not found'.format(asset)
            raise AssetNotFound(msg)

        return '{}/{}'.format(
            self.base_url,
            path.lstrip('/'),
        )


Flask.env.cache = None

app = Flask(__name__)
app.config.from_object('config')

rev = RevAssets(force_reload=app.debug, manifest='rev-manifest.json')
app.jinja_env.filters['asset_url'] = rev.debug_asset_url if app.debug else rev.asset_url

flask_cache_control = FlaskCacheControl()
flask_cache_control.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = psycopg.connect(
            user='postgres',
            password='postgres',
            dbname='postgres',
            host='db')
    return db


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().execute(f.read())
        db.commit()


class User(UserMixin):
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return '<User {}>'.format(self.id)


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', next=request.args.get('next'))

    username = request.form.get('username')
    password = request.form.get('password')
    next_page = request.form.get('next')

    db = get_db()
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        if user:
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                user['salt'],
                100000,
            )

            print(user['salt'])
            print(user['password_hash'])
            print(password_hash)

            if password_hash != user['password_hash']:
                return render_template('login.html', error='Invalid username or password')

            login_user(load_user(user['id']), remember=True)

            if not is_safe_url(next_page):
                return abort(400)

            return redirect(next_page or url_for('homepage'))
        else:
            return render_template('login.html', error='Invalid username or password')


@dataclass_json
@dataclass
class BlogPost:
    id: int
    title: str
    md_contents: str
    html_contents: str
    created_at: datetime.datetime
    draft: bool

    @property
    def created_at_datetime(self):
        return self.created_at.strftime('%Y-%m-%d')

    @property
    def created_at_display(self):
        print(self.created_at)
        return self.created_at.strftime('%A, %B %d, %Y')


@app.route('/', methods=['GET'])
@dont_cache()
def homepage():
    # TODO: homepage design.
    return render_template('homepage.html')


@app.route('/index', methods=['GET'])
@dont_cache()
def index():
    # TODO: display the index.
    db = get_db()
    with db.cursor(row_factory=class_row(BlogPost)) as cur:
        cur.execute(
            'SELECT * FROM blogposts WHERE NOT draft ORDER BY created_at DESC')
        return render_template('index.html', posts=cur.fetchall())


@app.route('/post/<int:post_id>', methods=['GET'])
@dont_cache()
def get_post(post_id):
    db = get_db()
    with db.cursor(row_factory=class_row(BlogPost)) as cur:
        cur.execute(
            'SELECT * FROM blogposts WHERE id=%s AND NOT draft', (post_id,))
        if cur.rowcount == 0:
            abort(404)
        return render_template('post.html', post=cur.fetchone())


@app.route('/admin', methods=['GET'])
@cache(max_age=3600, public=True)
@login_required
def admin():
    return render_template('admin.html')


@app.route('/admin/new', methods=['GET', 'POST'])
@cache(max_age=3600, public=True)
@login_required
def admin_new():
    if request.method == 'GET':
        return render_template('admin_new.html')
    else:
        form_data = dict(request.form)

        db = get_db()
        with db.cursor() as cur:
            cur.execute('INSERT INTO blogposts (title, md_contents, html_contents, created_at) VALUES (%s, %s, %s, %s) RETURNING id',
                        (form_data['title'],
                         form_data['md_contents'],
                         markdown.markdown(form_data['md_contents']),
                         datetime.datetime.now()))
            db.commit()
            post_id = cur.fetchone()
        return redirect(url_for('get_post', post_id=post_id))


@app.route('/admin/draft', methods=['POST'])
@cache(max_age=3600, public=True)
@login_required
def admin_draft():
    form_data = dict(request.form)

    db = get_db()
    with db.cursor() as cur:
        cur.execute('INSERT INTO blogposts (title, md_contents, html_contents, created_at, draft) VALUES (%s, %s, %s, %s, %s)',
                    (form_data['title'],
                     form_data['md_contents'],
                     markdown.markdown(form_data['md_contents']),
                     datetime.datetime.now(),
                     True))
        db.commit()
    return redirect(url_for('admin_manage'))


@app.route('/admin/publish_draft/<int:post_id>', methods=['GET'])
@cache(max_age=3600, public=True)
@login_required
def admin_publish_draft(post_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute('UPDATE blogposts SET draft = FALSE, created_at = %s WHERE id=%s',
                    (datetime.datetime.now(), post_id))
        db.commit()
    return redirect(url_for('get_post', post_id=post_id))


@app.route('/admin/manage', methods=['GET'])
@dont_cache()
@login_required
def admin_manage():
    db = get_db()
    with db.cursor(row_factory=class_row(BlogPost)) as cur:
        cur.execute(
            'SELECT * FROM blogposts WHERE NOT draft ORDER BY created_at DESC')
        posts = cur.fetchall()
        cur.execute(
            'SELECT * FROM blogposts WHERE draft ORDER BY created_at DESC')
        drafts = cur.fetchall()
        return render_template('admin_manage.html', posts=posts, drafts=drafts)


@app.route('/admin/edit/<int:post_id>', methods=['GET', 'POST'])
@dont_cache()
@login_required
def admin_edit(post_id):
    if request.method == 'GET':
        db = get_db()
        with db.cursor(row_factory=class_row(BlogPost)) as cur:
            cur.execute('SELECT * FROM blogposts WHERE id=%s', (post_id,))
            return render_template('admin_edit.html', post=cur.fetchone())
    else:
        form_data = dict(request.form)

        db = get_db()
        with db.cursor() as cur:
            cur.execute('UPDATE blogposts SET title = %s, md_contents = %s, html_contents = %s WHERE id=%s',
                        (form_data['title'],
                         form_data['md_contents'],
                         markdown.markdown(form_data['md_contents']),
                         post_id))
            db.commit()
            cur.execute('SELECT draft FROM blogposts WHERE id=%s', (post_id,))
            if cur.fetchone()[0]:
                return redirect(url_for('admin_manage'))
            return redirect(url_for('get_post', post_id=post_id))


@app.route('/admin/delete/<int:post_id>', methods=['GET'])
@dont_cache()
@login_required
def admin_delete(post_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute('DELETE FROM blogposts WHERE id=%s', (post_id,))
        db.commit()
    return redirect(url_for('admin_manage'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('homepage'))


@app.route('/favicon.ico')
@cache(max_age=3600, public=True)
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/favicon'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(extra_files=[rev.manifest])
