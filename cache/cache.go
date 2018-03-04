// Packace cache manages the in-memory key:value store/cache
package cache

import (
	"cli-uploader/drivefile"

	"bytes"
	"encoding/gob"
	"encoding/base64"
	"github.com/patrickmn/go-cache"
	"io/ioutil"
	"log"
	"time"
)

var c *cache.Cache

const CacheFilename = "file.cache"

func init() {
	// Create a cache from a deserialized items map. It is given a default
	// expiration duration of one week and a cleanup interval of one week.
	cacheBytes, readErr := ioutil.ReadFile(CacheFilename)
	if readErr != nil {
		log.Fatalf("Unable to read file. %v", readErr)
	}

  gob.Register(map[string]*drivefile.DriveFile{})
	if itemsMap, err := GOB64ToCacheMap(string(cacheBytes)); err != nil {
		c = cache.New(168 * time.Hour, 168 * time.Hour)
	} else {
		c = cache.NewFrom(168 * time.Hour, 168 * time.Hour, itemsMap)
	}
}

// Set adds an item to the cache, replacing any existing item.
func Set(k string, x interface{}) {
	c.Set(k, x, cache.DefaultExpiration)
}

// Get gets an item from the cache.
// It returns the item or nil and a bool indicating whether the key was found.
func Get(k string) (interface{}, bool) {
	return c.Get(k)
}

// SaveCache saves the cache map.
func SaveCache() (err error) {
	var encodedBinary string
	encodedBinary, err = CacheMapToGOB64(c.Items())
	if err != nil {
		return
	}
	bytesSlice := []byte(encodedBinary)
	err = ioutil.WriteFile(CacheFilename, bytesSlice, 0644)
	return
}

// GOB64ToCacheMap decodes Go binary into a cache map.
// It returns the cache map.
func GOB64ToCacheMap(str string) (m map[string]cache.Item, e error) {
	bytesSlice, err := base64.StdEncoding.DecodeString(str)
	if err != nil {
		// Failed base64 decode
		e = err
		return
	}
	b := bytes.Buffer{}
	b.Write(bytesSlice)
	decoder := gob.NewDecoder(&b)
	err = decoder.Decode(&m)
	if err != nil {
		// Failed gob decode
		e = err
	}
	return
}

// CacheMapToGOB64 encodes a cache map into Go binary.
// It returns a string encoding of the GOB.
func CacheMapToGOB64(m map[string]cache.Item) (str string, e error) {
	b := bytes.Buffer{}
	encoder := gob.NewEncoder(&b)
	err := encoder.Encode(m)
	if err != nil {
		// Failed gob encode
		e = err
		return
	}
	str = base64.StdEncoding.EncodeToString(b.Bytes())
	return
}
