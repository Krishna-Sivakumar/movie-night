import redis

r = redis.Redis(
    host='127.0.0.1',
    port=6000,
    db=1
)

count = 0
with open("title.basics.movie.tsv", "r") as file:
    with open("title.basics.movie.txt", "w+") as file1:
        for line in file.readlines():
            spl = line.split('	')
            id, title, title_original = spl[0], spl[2], spl[3]
            file1.write(f"{id}	{title.lower()}	{title}	{title_original}\n")

with open("title.basics.movie.txt", "r") as file:
    tot = 0
    for line in file.readlines():
        spl = line.split('	')
        id, lower_title, title, original = spl

        to_insert = dict()
        for i in range(len(lower_title)):
            to_insert[lower_title[:i+1]] = 0
        to_insert[f"{lower_title}^"] = 0
        r.zadd("zset", to_insert)
        r.set(lower_title, title)
        print(tot)

        tot += 1
    pass
