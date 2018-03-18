package main

import (
	"github.com/urfave/cli"
)

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
		cli.BoolFlag{
			Name: "window, w",
			Usage: "should open core files when bulk uploading?",
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
	app.Action = func(c *cli.Context) (err error) {
		DriveFilesMap = GenerateDriveFilesMap(c.Bool("reload"))
		TransferFlags(c) // Move flag information to global variables
		return
	}
	return app
}
