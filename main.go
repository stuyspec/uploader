// uploader is a command line application that assists the automatic uploading
// of articles of The Stuyvesant Spectator.
package main

import (
	"github.com/stuyspec/uploader/driveclient"
	"github.com/stuyspec/uploader/graphql"

	"encoding/gob"
	// "github.com/op/go-logging"
	"log"
	"github.com/patrickmn/go-cache"
	"github.com/urfave/cli"
	"google.golang.org/api/drive/v3"
	"os"
	"strconv"
)

var volume, issue int
var allSections []graphql.Section

var driveFilesMap map[string]*drive.File
var cliApp *cli.App

// CacheFilename is the name of the file where an encoded cache is saved.
const CacheFilename = "file.cache"

func init() {
	gob.Register(map[string]*drive.File{})

	cliApp = CreateCliApp()
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
				log.Fatalf("Unable to save cache. %v", err)
			}
		}

		var typeErr bool
		driveFilesMap, typeErr = driveFiles.(map[string]*drive.File)
		if !typeErr {
			log.Fatalf("Unable to type driveFiles to map. %v", typeErr)
		} else {
			log.Println("Successfully loaded Drive files into map.")
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
      Name: "local, l",
      Usage: "use locally hosted API for graphql",
    },
	}
	return app
}


func main() {
	err := cliApp.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}

	// TODO: AUTH
}
