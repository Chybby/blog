import os
import datetime

from flask import (
    Flask,
    g,
    render_template,
    send_from_directory,
)

from flask_cachecontrol import (
    FlaskCacheControl,
    cache,
    dont_cache)

from rev_assets import RevAssets

import psycopg
from psycopg.rows import class_row
from dataclasses import dataclass
from dataclasses_json import dataclass_json

app = Flask(__name__)
app.config.from_object('config')

rev = RevAssets(reload=app.config['DEBUG'], manifest='rev-manifest.json')
app.jinja_env.filters['asset_url'] = rev.asset_url

flask_cache_control = FlaskCacheControl()
flask_cache_control.init_app(app)


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


@dataclass_json
@dataclass
class BlogPost:
    id: int
    title: str
    contents: str
    created_at: str


@app.route('/', methods=['GET'])
@dont_cache()
def homepage():
    return render_template('homepage.html')


@app.route('/index', methods=['GET'])
@dont_cache()
def index():
    return render_template('index.html')


@app.route('/post/<int:post_id>', methods=['GET'])
@cache(max_age=3600, public=True)
def get_post(post_id):
    db = get_db()
    with db.cursor(row_factory=class_row(BlogPost)) as cur:
        cur.execute('SELECT * FROM blogposts WHERE id=%s', (post_id,))
        return render_template('post.html', post=cur.fetchone())


@app.route('/post', methods=['GET'])
@dont_cache()
def post_post():
    db = get_db()
    with db.cursor() as cur:
        cur.execute('INSERT INTO blogposts (title, contents) VALUES (%s, %s)',
                    ('A brand new post!',
                     'This post was created at ' + str(datetime.datetime.now())))
        db.commit()
    return 'success'


@app.route('/admin', methods=['GET'])
@cache(max_age=3600, public=True)
def admin():
    return render_template('admin.html')


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
