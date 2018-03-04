package main

import (
	"cli-uploader/cache"
	"cli-uploader/driveclient"
	// "./drivefile"

	"github.com/urfave/cli"
	"log"
	"os"
)

var cliApp *cli.App

func init() {

	// Create CLI App
	cliApp = cli.NewApp()
	cliApp.Name = "Spectator Uploader"
	cliApp.Usage = "Upload Spectator articles"
	cliApp.Flags = []cli.Flag{
		cli.BoolFlag{
			Name:  "reload, r",
			Usage: "reload and cache Drive files?",
		},
	}

	cliApp.Action = func(c *cli.Context) error {
		driveFiles, found := cache.Get("DriveFiles")
		if c.Bool("reload") || !found {
			driveFiles = driveclient.ScanDriveFiles()
			cache.Set("DriveFiles", driveFiles)
		}
	}

}

func main() {
	err := cliApp.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
