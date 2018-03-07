// Package graphql provides a GraphQL client to the Spectator Rails API.
package graphql

import (
	"github.com/joho/godotenv"
	"github.com/machinebox/graphql"

	"context"
	"log"
	// "net/http"
	// "net/url"
	"os"
)

var client *graphql.Client

func init() {
	err := godotenv.Load()
  if err != nil {
    log.Fatal("Error loading .env file in package graphql.")
  }

	apiUrl := "https://api.stuyspec.com"
	resource := "/graphql/"
	envApiUrl, found := os.LookupEnv("API_ENDPOINT")
	if found {
		apiUrl = envApiUrl
	}

	client = graphql.NewClient(apiUrl + resource)
	client.Log = func(s string) { log.Println(s) }
}

type Section struct {
	Id, Name string
}

type AllSectionsResponse struct {
	AllSections []Section
}

func AllSections() []Section {
	req := graphql.NewRequest(`
    query {
      allSections {
        id
        name
      }
    }
  `)
	req.Header.Set("Hi", "There")
	ctx := context.Background()

	var res AllSectionsResponse
	if err := client.Run(ctx, req, &res); err != nil {
		log.Fatal(err)
	}

	return res.AllSections
}
