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

var driveFilesMap map[string]*drive.File
var cliApp *cli.App

// CacheFilename is the name of the file where an encoded cache is saved.
const CacheFilename = "file.cache"

func init() {
	gob.Register(map[string]*drive.File{})

	cliApp = CreateCliApp()
	log = CreateLogger()
	uploaderCache := CreateUploaderCache()

	// Get Drive files from cache, if any exist
	driveFiles, found := uploaderCache.Get("DriveFiles")

	// Define app behavior
	cliApp.Action = func(c *cli.Context) (err error) {
		// Rescan and update cache with Drive files if reload flag or none found
		// current cache.
		if c.Bool("reload") || !found {
			driveFiles = driveclient.ScanDriveFiles()
			uploaderCache.Set("DriveFiles", driveFiles, cache.DefaultExpiration)
			err = SaveCache(uploaderCache)
			if err != nil {
				log.Errorf("Unable to save cache. %v", err)
			}
		}

		var typeErr bool
		driveFilesMap, typeErr = driveFiles.(map[string]*drive.File)
		if !typeErr {
			log.Errorf("Unable to type driveFiles to map. %v", typeErr)
		} else {
			log.Info("Loaded Drive files into map.")
		}

		if port, err := strconv.Atoi(c.String("local")); err == nil {
			graphql.InitClient(port)
		} else {
			graphql.InitClient()
		}

		return
	}
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

}

func main() {
	err := cliApp.Run(os.Args)
	if err != nil {
		log.Error(err)
	}

	i := graphql.AllSections()
	fmt.Printf("%T, %v", hi, hi)
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
