package main

import (
	"./db"
	"./driveclient"

	"github.com/urfave/cli"
	"log"
	"os"
)

func main() {
	defer db.CloseDB()

	app := cli.NewApp()
	app.Name = "Spectator Uploader"
	app.Usage = "Automagically upload Spec articles"
	app.Flags = []cli.Flag{
		cli.BoolFlag{
			Name:  "reload, r",
			Usage: "should reload/memoize Drive files?",
		},
	}

	app.Action = func(c *cli.Context) error {
		if c.Bool("reload") {
			driveFiles := driveclient.ScanDriveFiles()
			db.InsertDriveFiles(driveFiles)
		}
		return nil
	}

	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
