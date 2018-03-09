// uploader is a command line application that assists the automatic uploading
// of articles of The Stuyvesant Spectator.
package main

import (
	"github.com/stuyspec/uploader/driveclient"
	"github.com/stuyspec/uploader/graphql"

	"github.com/op/go-logging"
	"github.com/patrickmn/go-cache"
	"github.com/urfave/cli"

	"encoding/gob"
	"fmt"
	"google.golang.org/api/drive/v3"
	"os"
	"strconv"
	"strings"
)

// CacheFilename is the name of the file where an encoded cache is saved.
const CacheFilename = "file.cache"

// DriveFilesMap is a mapping of Drive files; map[file id]file
var DriveFilesMap map[string]*drive.File

var Volume, Issue int

var cliApp *cli.App
var log *logging.Logger
var uploaderCache *cache.Cache

func init() {
	gob.Register(map[string]*drive.File{})

	cliApp = CreateCliApp()
	log = CreateLogger()
	uploaderCache = CreateUploaderCache()
}

// CreateCliApp creates a new CLI app for the uploader.
// It returns the new app.
func CreateCliApp() *cli.App {
	app := cli.NewApp()
	app.Name = "stuy-spec-uploader"
	app.Usage = "Automatically upload the articles and graphics of The Spectator."
	app.Flags = []cli.Flag{
		cli.BoolFlag{
			Name:  "reload, r",
			Usage: "should reload and cache Drive files?",
		},

		cli.StringFlag{
			Name:  "local, l",
			Usage: "use locally hosted API for graphql",
		},

		cli.IntFlag{
			Name:  "volume, m",
			Usage: "volume number",
		},
		cli.IntFlag{
			Name:  "issue, i",
			Usage: "issue number",
		},
	}
	return app
}

// CreateLogger creates a logger and sets the backend formatter for logging.
// It returns the logger.
func CreateLogger() *logging.Logger {
	log := logging.MustGetLogger("stuy-spec-uploader")

	// Log format string. Everything except the message has a custom color
	// which is dependent on the log level. Many fields have a custom output
	// formatting too, eg. the time returns the hour down to the milli second.
	var format = logging.MustStringFormatter(
		`%{color}%{time:15:04:05.000} %{shortfunc} ▶ %{level:.4s} %{id:03x}%{color:reset} %{message}`,
	)

	backend := logging.NewLogBackend(os.Stderr, "", 0)
	backendFormatter := logging.NewBackendFormatter(backend, format)
	logging.SetBackend(backendFormatter) // Set backends to be used

	return log
}

func main() {
	// Define app behavior
	cliApp.Action = func(c *cli.Context) (err error) {
		DriveFilesMap = GenerateDriveFilesMap(c.Bool("reload"))

		if port, err := strconv.Atoi(c.String("local")); err == nil {
			graphql.InitClient(port)
		} else {
			graphql.InitClient()
		}

		TransferFlags(c) // Move flag information to global variables

		return
	}

	err := cliApp.Run(os.Args)
	if err != nil {
		log.Error(err)
	}

	println(Volume)
	println(Issue)
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
		Volume = c.Int("volume")
	}
	if c.IsSet("issue") {
		Issue = c.Int("issue")
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
