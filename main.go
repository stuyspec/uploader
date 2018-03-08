// uploader is a command line application that assists the automatic uploading
// of articles of The Stuyvesant Spectator.
package main

import (
	"github.com/stuyspec/uploader/driveclient"
	"github.com/stuyspec/uploader/graphql"

	"github.com/patrickmn/go-cache"
	"github.com/urfave/cli"
	"google.golang.org/api/drive/v3"
	"log"
	"os"
)

var volume, issue int
var allSections []graphql.Section

var driveFilesMap map[string]*drive.File
var cliApp *cli.App

// CacheFilename is the name of the file where an encoded cache is saved.
const CacheFilename = "file.cache"

gob.Register(map[string]drive.File{})

func init() {
	cliApp = createCliApp()
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
		}
		return
	}
}

func createCliApp() *cli.App {
	app := cli.NewApp()
	app.Name = "stuy-spec-uploader"
	app.Usage = "Automatically upload articles and graphics of The Spectator."
	app.Flags = []cli.Flag{
		cli.BoolFlag{
			Name:  "reload, r",
			Usage: "should reload and cache Drive files?",
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

	driveFiles := driveclient.ScanDriveFiles()

	log.Printf("%T: %v\n", driveFiles, driveFiles)
}
