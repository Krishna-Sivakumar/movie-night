from datetime import datetime
from flask import Flask, request, render_template
import flask
import flask_login
import hashlib
import redis
import toml

config = toml.loads(
    open("config.toml", "r").read()
)

auth_dict = toml.loads(
    open("auth.toml", "r").read()
)
admins = auth_dict['admin']
admin_dict = {}
for i in admins:
    admin_dict[i["username"]] = i


app = Flask(__name__)
app.secret_key = auth_dict["secret_key"]
r = redis.Redis(
    host=config["redis"]["address"],
    port=config["redis"]["port"],
    db=config["redis"]["mlist_index"]
)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


def update_movie_today():
    global start, movie_today, message
    now = datetime.now() - start
    if now.days >= 1:
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
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


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(name):
    if name not in admin_dict.keys():
        return

    user = User()
    user.id = name
    return user


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
@flask_login.login_required
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    def validate(username, password):
        if username in admin_dict.keys() and hashlib.sha256(password.encode()).hexdigest() == admin_dict[username]["password"]:
            return True
        return False

    if request.method == 'GET':
        # Return a login form here
        if flask_login.current_user.is_authenticated:
            return flask.redirect('/')
        return render_template('login.html')
    elif request.method == 'POST':
        if 'username' in request.form.keys() and 'password' in request.form.keys():
            if validate(request.form["username"], request.form["password"]):
                user = user_loader(request.form["username"])
                flask_login.login_user(user, remember=False)

                return flask.redirect('/')
        return flask.redirect('/login')


@app.route('/logout', methods=['GET'])
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return flask.redirect('/')


if __name__ == '__main__':
    app.run(
        host=config["servers"]["website"]["address"],
        port=config["servers"]["website"]["port"],
        debug=True
    )
