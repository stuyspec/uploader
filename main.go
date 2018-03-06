// Package main automatically uploads Spectator articles.
package main

import (
	"cli-uploader/cache"
	"cli-uploader/driveclient"
	"cli-uploader/drivefile"
	"cli-uploader/graphql"
	"cli-uploader/parser"

	"github.com/urfave/cli"
	"log"
	"os"
)

var volume, issue int

func init() {
	graphql.AllSections()
}

func main() {
	// Get DriveFiles from cache, if any exist
	driveFiles, foundDriveFiles := cache.Get("DriveFiles")

	// Create CLI App
	cliApp := cli.NewApp()
	cliApp.Name = "Spectator Uploader"
	cliApp.Usage = "Upload Spectator articles"
	cliApp.Flags = []cli.Flag{
		cli.BoolFlag{
			Name:  "reload, r",
			Usage: "should reload and cache Drive files?",
		},
	}

	// Define app behavior
	cliApp.Action = func(c *cli.Context) (err error) {
		// Rescan and update cache with Drive files if reload flag or none found
		// current cache.
		if c.Bool("reload") || !foundDriveFiles {
			driveFiles = driveclient.ScanDriveFiles()
			err = cache.Set("DriveFiles", driveFiles)
		}
		return
	}

	driveFilesMap, typeErr := driveFiles.(map[string]*drivefile.DriveFile)
	if !typeErr {
		log.Fatalf("Unable to type driveFiles to map. %v", typeErr)
	}

	file, ok := driveFilesMap["1cVqKaP6JVXHELBG2IEU5SEz1Xt9bLVZmrwtSLly_P7Y"]
	if !ok {
		log.Fatalf("No file found. %v", file)
	}
	content := driveclient.DownloadGoogleDoc(file)
	attributes := parser.ArticleAttributes(content)
	if attributes != nil {
		println()
	}

	err := cliApp.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
