package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/pelletier/go-toml"
)

var ctx = context.Background()

var rdb *redis.Client

type myJSON struct {
	Array []string
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func getAutocomplete(foo string) []string {
	rank, err := rdb.ZRank(ctx, "zset", foo).Result()
	if err != nil {
		return []string{""}
	}

	rng, err := rdb.ZRange(ctx, "zset", rank-1, rank+1000).Result()
	if err != nil {
		return []string{""}
	}

	response := []string{}
	terminateCount := 0
	for _, str := range rng {
		Min := min(len(str), len(foo))
		if str[len(str)-1] == '^' {
			if str[:Min] == foo[:Min] {
				title, _ := rdb.Get(ctx, str[:len(str)-1]).Result()
				response = append(response, title)
				terminateCount++
			}
		}

		if terminateCount > 8 {
			break
		}
	}

	return response
}

func handler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	query := r.URL.Query()["query"]
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	autocomplete := myJSON{Array: getAutocomplete(strings.ToLower(query[0]))}
	bytes, _ := json.Marshal(autocomplete)
	response := fmt.Sprintf("%s", bytes)

	w.Write([]byte(response))
	fmt.Println(time.Since(start))
}

func main() {
	redisConfigFile, err := ioutil.ReadFile("config.toml")
	if err != nil {
		panic(err)
	}

	redisConfig, err := toml.Load(string(redisConfigFile))
	if err != nil {
		panic(err)
	}

	redisAddr, redisPort, dbIndex := redisConfig.Get("redis.address").(string), redisConfig.Get("redis.port").(int64), redisConfig.Get("redis.autocomplete_index").(int64)

	serverAddr, serverPort := redisConfig.Get("servers.autocomplete.address").(string), redisConfig.Get("servers.autocomplete.port").(int64)

	rdb = redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%d", redisAddr, redisPort),
		DB:   int(dbIndex),
	})

	fmt.Printf("Server running on %s:%d...\n", serverAddr, serverPort)

	http.HandleFunc("/", handler)
	log.Fatal(http.ListenAndServe(fmt.Sprintf("%s:%d", serverAddr, serverPort), nil))
}
