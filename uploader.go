// uploader is a command line application that assists the automatic uploading
// of articles of The Stuyvesant Spectator.
package uploader

import (
	"github.com/stuyspec/uploader/cache"
	"github.com/stuyspec/uploader/driveclient"
	"github.com/stuyspec/uploader/drivefile"
	"github.com/stuyspec/uploader/graphql"

	"github.com/urfave/cli"
	"log"
	"os"
)

var volume, issue int
var allSections []graphql.Section

var driveFilesMap map[string]*drivefile.DriveFile
var cliApp *cli.App

func init() {
	// Get DriveFiles from cache, if any exist
	driveFiles, found := cache.Get("DriveFiles")

	cliApp = createCliApp()

	// Define app behavior
	cliApp.Action = func(c *cli.Context) (err error) {
		// Rescan and update cache with Drive files if reload flag or none found
		// current cache.
		if c.Bool("reload") || !found {
			driveFiles = driveclient.ScanDriveFiles()
			err = cache.Set("DriveFiles", driveFiles)
		}
		return
	}

	var typeErr bool
	driveFilesMap, typeErr = driveFiles.(map[string]*drivefile.DriveFile)
	if !typeErr {
		log.Fatalf("Unable to type driveFiles to map. %v", typeErr)
	}
}

// createCliApp generates a CLI App.
// It returns the generated app.
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

  allSections = graphql.AllSections()
}
