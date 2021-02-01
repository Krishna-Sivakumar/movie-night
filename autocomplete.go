package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/go-redis/redis/v8"
)

var arr []int = []int{1, 2, 3, 4, 5}
var ctx = context.Background()
var i = 0

var rdb *redis.Client = redis.NewClient(&redis.Options{
	Addr: "127.0.0.1:6000",
	DB:   1,
})

type myJSON struct {
	Array []string
}

func getFoo(foo string) []string {
	val, err := rdb.LRange(ctx, foo, 0, -1).Result()
	if err != nil {
		panic(err)
	}
	return val
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
	http.HandleFunc("/", handler)
	log.Fatal(http.ListenAndServe("192.168.0.101:7000", nil))
}
