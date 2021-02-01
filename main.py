from datetime import datetime
from flask import Flask, request, render_template
import redis
import toml

config = toml.loads(
    open("config.toml", "r").read()
)


app = Flask(__name__)
r = redis.Redis(
    host=config["servers"]["redis_address"],
    port=config["servers"]["redis_port"]
)


def update_movie_today():
    global start, movie_today, message
    now = datetime.now() - start
    if now.days > 0:
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


@app.route('/', methods=['GET', 'POST'])
def home():
    update_movie_today()

    if request.method == 'POST':
        if 'movie' in request.form and len(request.form['movie']) > 0:
            r.sadd('mlist', request.form['movie'])
            update_movie_today()

    return render_template(
        'main.html',
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
        mlist=mlist
    )


@app.route('/view', methods=['GET'])
def viewList():
    mlist = [s.decode() for s in r.smembers('mlist')]
    return render_template(
        'view.html',
        mlist=mlist
    )


if __name__ == '__main__':
    app.run(
        host=config["servers"]["server_address"],
        port=config["servers"]["flask_server_port"],
        debug=True
    )
