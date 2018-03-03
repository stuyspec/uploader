// Packace cache manages the in-memory key:value store/cache
package cache

import (
	"github.com/patrickmn/go-cache"
	"time"
)

var c *cache.Cache

func main() {
	// Create a cache with a default expiration time of 1 week, and which
	// purges expired items every weeek.
	c = cache.New(time.Week, time.Week)
}

func Set(k string, x interface{}) {
	c.Set(k, x, cache.DefaultExpiration)
}

func Get(k string) (interface{}, bool) {
	return c.Get(k)
}

