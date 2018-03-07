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
}

type Section struct {
	Id, Name string
}

type AllSectionsResponse struct {
	AllSections []Section
}

func AllSections() []Section {
	client := graphql.NewClient("http://localhost:3000/graphql")
	req := graphql.NewRequest(`
    query {
      allSections {
        id
        name
      }
    }
  `)
	ctx := context.Background()

	var res AllSectionsResponse
	if err := client.Run(ctx, req, &res); err != nil {
		log.Fatal(err)
	}

	return res.AllSections
}
