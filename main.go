package main

import (
	// "cli-uploader/driveclient"
	"fmt"
	"log"
	"os"

	"github.com/urfave/cli"
)

func main() {
	app := cli.NewApp()
  app.Name = "Spectator Uploader"
  app.Usage = "Automagically upload Spec articles"
  app.Action = func(c *cli.Context) error {
    fmt.Println("boom! I say!")
    return nil
  }

  err := app.Run(os.Args)
  if err != nil {
    log.Fatal(err)
  }
}
