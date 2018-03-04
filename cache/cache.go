// Packace cache manages the in-memory key:value store/cache
package cache

import (
	"../drivefile"

	"github.com/patrickmn/go-cache"
	"encoding/gob"
	"log"
	"time"
)

var c *cache.Cache

const CacheFilename = "file.cache"

func init() {
	// Create a cache with a default expiration time of 1 week, and which
	// purges expired items every weeek.
	c = cache.New(168 * time.Hour, 168 * time.Hour)
  gob.Register(&map[string]*drivefile.DriveFile{})

	// NOTE: This method is deprecated in favor of c.Items() and NewFrom()
	// (see the documentation for NewFrom().)
	err := c.LoadFile(CacheFilename)
	if err != nil {
		log.Fatalf("Unable to load file. %v", err)
	}
}

func Set(k string, x interface{}) {
	c.Set(k, x, cache.DefaultExpiration)
}

func Get(k string) (interface{}, bool) {
	return c.Get(k)
}

func SaveFile() error {
	return c.SaveFile(CacheFilename)
}

