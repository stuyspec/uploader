package main

import (
	"./cache"
	"./driveclient"
	"./drivefile"

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
		if c.Bool("reload") {
			driveFiles := driveclient.ScanDriveFiles()
			cache.Set("DriveFiles", driveFiles)
			err := cache.SaveFile()
			if err != nil {
				log.Fatalf("Unable to save cache. %v", err)
			}
		} else {
			driveFiles, found := cache.Get("DriveFiles")
			if found {
				log.Println(driveFiles.(*map[string]*drivefile.DriveFile))
			}
		}
		return nil
	}
}

func main() {
	err := cliApp.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
