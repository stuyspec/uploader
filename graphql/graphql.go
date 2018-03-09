// Package graphql provides a GraphQL client to the Spectator Rails API.
package graphql

import (
	"context"
	"fmt"
	"github.com/machinebox/graphql"
	"log"
)

var client *graphql.Client

// Article represents an article.
type Article struct {
	ID, Title, Content, Slug string
}

// Section represents a department/section of the newspaper.
type Section struct {
	ID, Name, Slug string
}

// InitClient initiates the graphql.Client with an optional port parameter.
func InitClient(params ...int) {
	if len(params) > 0 {
		client = graphql.NewClient(
			fmt.Sprintf("http://localhost:%d/graphql", params[0]),
		)
	} else {
		client = graphql.NewClient("https://api.stuyspec.com/graphql")
	}
}


type allSectionsResponse struct {
	AllSections []Section
}

// AllSections creates an allSections GraphQL query.
// It returns the resulting sections.
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

	var res allSectionsResponse
	if err := client.Run(ctx, req, &res); err != nil {
		log.Fatal(err)
	}

	return res.AllSections
}
