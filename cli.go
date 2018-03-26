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

		cli.StringFlag{
      Name: "url",
      Usage: "individual article Drive url",
    },
	}
	app.Action = func(c *cli.Context) (err error) {
		if !app.IsSet("volume")  && !app.IsSet("issue") {
			log.Fatalf("Must provide both a volume and an issue.")
		}
		DriveFilesMap = GenerateDriveFilesMap(c.Bool("reload"))
		TransferFlags(c) // Move flag information to global variables

		if app.IsSet("url") {
			UploadArticleByUrl(id)
		}
		return
	}
	return app
}
