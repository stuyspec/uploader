package main

import (
	"cli-uploader/driveclient"

	"github.com/urfave/cli"
	"log"
	"os"

	"database/sql"
	_ "github.com/lib/pq"
)

func main() {
	connectionStr := "user=stuyspecweb dbname=stuy-spec-uploader sslmode=disable"
	db, err := sql.Open("postgres", connectionStr)
	if err != nil {
		log.Fatal(err)
	}
	err = db.Ping()
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	RunCLIApp()
}

// RunCLIApp generates a cli app and runs it.
func RunCLIApp() {
	app := cli.NewApp()
	app.Name = "Spectator Uploader"
	app.Usage = "Automagically upload Spec articles"
	app.Flags = []cli.Flag{
		cli.BoolFlag{
			Name:  "memoize, m",
			Usage: "should memoize/reload Drive files?",
		},
	}

	app.Action = func(c *cli.Context) error {
		if c.Bool("memoize") {
			driveclient.MemoizeDriveFiles()
		}
		return nil
	}

	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
