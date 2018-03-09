package main

import (
	"github.com/stuyspec/uploader/graphql"

	"github.com/urfave/cli"

	"strconv"
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
	app.Action = func(c *cli.Context) (err error) {
		DriveFilesMap = GenerateDriveFilesMap(c.Bool("reload"))
		if port, err := strconv.Atoi(c.String("local")); err == nil {
			graphql.InitClient(port)
		} else {
			graphql.InitClient()
		}
		TransferFlags(c) // Move flag information to global variables
		return
	}
	return app
}
