// Package graphql provides a GraphQL client to the Spectator Rails API.
package graphql

import (
	"context"
	"fmt"
	"github.com/machinebox/graphql"
	"log"
)

var client *graphql.Client

// InitClient initiates the graphql.Client with an optional port parameter.
func InitClient(params ...int) {
	if len(params) > 0 {
		client = graphql.NewClient(
			fmt.Sprintf("http://localhost:%d/graphql", params[0]),
		)
	} else {
		client = graphql.NewClient("https://api.stuyspec.com")
	}
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
	ctx := context.Background()

	var res AllSectionsResponse
	if err := client.Run(ctx, req, &res); err != nil {
		log.Fatal(err)
	}

	return res.AllSections
}
