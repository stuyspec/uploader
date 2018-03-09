// uploader is a command line application that assists the automatic uploading
// of articles of The Stuyvesant Spectator.
package main

import (
	"github.com/stuyspec/uploader/driveclient"

	"github.com/urfave/cli"
	"github.com/patrickmn/go-cache"
	"github.com/op/go-logging"

	"encoding/gob"
	"fmt"
	"google.golang.org/api/drive/v3"
	"os"
	"strings"
)

// CacheFilename is the name of the file where an encoded cache is saved.
const CacheFilename = "file.cache"

// DriveFilesMap is a mapping of Drive files; map[file id]file
var DriveFilesMap map[string]*drive.File

var volume int
var issue int

var cliApp *cli.App
var log *logging.Logger
var uploaderCache *cache.Cache

func init() {
	gob.Register(map[string]*drive.File{})

	cliApp = CreateCliApp()
	log = CreateLogger()
	uploaderCache = CreateUploaderCache()
}

func main() {
	err := cliApp.Run(os.Args)
	if err != nil {
		log.Error(err)
	}

	println(volume)
	println(issue)
}

// GenerateDriveFilesMap generates a map[string]*drive.File from the cache
// (there is a reload option). It returns the map.
func GenerateDriveFilesMap(shouldReload bool) map[string]*drive.File {
	// Get Drive files from cache, if it exists.
	driveFiles, found := uploaderCache.Get("DriveFiles")
	// Rescan and update cache with Drive files if reload flag or none found
	// current cache.
	if shouldReload || !found {
		driveFiles = driveclient.ScanDriveFiles()
		uploaderCache.Set("DriveFiles", driveFiles, cache.DefaultExpiration)
		err := SaveCache(uploaderCache)
		if err != nil {
			log.Errorf("Unable to save cache. %v", err)
		}
	}

	filesMap, err := driveFiles.(map[string]*drive.File)
	if !err {
		log.Errorf("Unable to type driveFiles to map. %v", err)
	} else {
		log.Notice("Loaded Drive files into map.")
	}

	return filesMap
}

// TransferFlags moves flags information to global variables.
func TransferFlags(c *cli.Context) {
	if c.IsSet("volume") {
		volume = c.Int("volume")
	}
	if c.IsSet("issue") {
		issue = c.Int("issue")
	}
}

// stringDriveFile creates a custom string representation of a Drive file.
// It returns this string.
func stringDriveFile(f *drive.File) (output string) {
	var webContentLink string
	if strings.Contains(f.MimeType, "image") {
		webContentLink = fmt.Sprintf("\n   WebContentLink: %v,", f.WebContentLink)
	}
	output = fmt.Sprintf(`{
  Id: %s,
  Name: %s,
  MimeType: %s,%s
  Parents: %v,
}`,
		f.Id, f.Name, f.MimeType, webContentLink, f.Parents,
	)
	return
}
