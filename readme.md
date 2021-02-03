# Movie Night
Adds your movies to a list, and picks a random one everyday!
There's autocomplete for movies, so no wrong spellings at least. 

I implemented autocomplete with the help of [this](http://oldblog.antirez.com/post/autocomplete-with-redis.html) article. Simple, but really effective!

This project depends on Flask, Go and Redis. The servers are configured with TOML files.


<br>
<hr>


### Configuring the servers
There are two TOML files that need to exist; auth.toml and config.toml.
config.toml configures the server addresses and ports, and auth.toml is for adding admins.

This is the format for config.toml:
```toml
[redis]
address = "your_redis_server_address_here"
port = "your_redis_server_address_here"
mlist_index = "the_index_that_flask_uses_to_keep_track_of_the_added_movies"
autocomplete_index = "the_index_for_storing_autocomplete_prefixes"

[servers]
    [servers.autocomplete]
    address = "autocomplete_server_address"
    port = "autocomplete_server_port"

    [servers.website]
    address = "flask_server_address"
    port = "flask_server_port"
```

And this is the format for auth.toml:
```toml
secret_key = "something_or_the_other"

[[admin]]
    username = "your_admins_username_here"
    password = "sha256_hash_of_the_admins_password_here"
```

<br>
<hr>


### Preparing the IMDb dataset, and loading it onto Redis

1. Download title.basics.tsv from https://datasets.imdbws.com/
2. Install the python requirements
3. Setup config.toml and start up your redis server
4. Run the following commands (it takes a while)
```
    fgrep "movie" title.basics.tsv > title.basics.movie.tsv
    python3 dump-to-redis.py
```

<br>
<hr>


### Building the project (On Linux / Mac os)

#### Python Requirements
```
virutalenv venv
. venv/bin/activate
pip3 install -r requirements.txt
```

#### Go Requirements
```
go mod init something/something
go get github.com/go-redis/redis/v8
go get github.com/pelletier/go-toml
```

#### Build Go Server 
```
go build autcomplete.go
```

<br>
<hr>

### Running the Project (On Linux / Mac os)

The Redis server needs to be running first.

#### Flask Server
```
. venv/bin/activate
python3 main.py
```

#### Go Autocomplete Server
```
./autocomplete
```