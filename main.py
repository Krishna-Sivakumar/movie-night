from datetime import datetime
from flask import Flask, request, render_template
import flask_login
import redis
import toml

config = toml.loads(
    open("config.toml", "r").read()
)

auth_dict = toml.loads(
    open("auth.toml", "r").read()
)


app = Flask(__name__)
app.secret_key = auth_dict["secret_key"]
r = redis.Redis(
    host=config["redis"]["address"],
    port=config["redis"]["port"]
)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


def update_movie_today():
    global start, movie_today, message
    now = datetime.now() - start
    if now.days >= 1:
        start = datetime.now()
        movie_today = r.srandmember('mlist', 1)

    if len(r.smembers('mlist')) == 0:
        movie_today = []

    if len(r.smembers('mlist')) > 0 and len(movie_today) == 0:
        movie_today = r.srandmember('mlist', 1)

    if len(movie_today) > 0 and not r.sismember('mlist', movie_today[0].decode()):
        movie_today = r.srandmember('mlist', 1)

    message = ""
    if len(movie_today) > 0:
        message = f"{movie_today[0].decode()}"
    else:
        message = "Add something to the list :("


start = datetime.now()
movie_today = []
update_movie_today()


autocompleteAddr = f"{config['servers']['autocomplete']['address']}:{config['servers']['autocomplete']['port']}"


@app.route('/', methods=['GET', 'POST'])
def home():
    update_movie_today()

    if request.method == 'POST':
        if 'movie' in request.form and len(request.form['movie']) > 0:
            r.sadd('mlist', request.form['movie'])
            update_movie_today()

    return render_template(
        'main.html',
        addr=autocompleteAddr,
        movie_today=message
    )


@app.route('/modify', methods=['GET', 'POST'])
def modify():
    if len(request.form) > 0:
        for key in request.form:
            r.srem('mlist', key)
            update_movie_today()

    mlist = [s.decode() for s in r.smembers('mlist')]
    return render_template(
        'modify.html',
        addr=autocompleteAddr,
        mlist=mlist
    )


@app.route('/view', methods=['GET'])
def viewList():
    mlist = [s.decode() for s in r.smembers('mlist')]
    return render_template(
        'view.html',
        addr=autocompleteAddr,
        mlist=mlist
    )


if __name__ == '__main__':
    app.run(
        host=config["servers"]["website"]["address"],
        port=config["servers"]["website"]["port"],
        debug=True
    )
