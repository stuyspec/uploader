// Package graphql provides a GraphQL client to the Spectator Rails API.
package graphql

import (
	"github.com/machinebox/graphql"

	"context"
	"fmt"
	"log"
	"strconv"
	"time"
)

var IssueDates = map[int]map[int]string{
	105: map[int]string{
		13: "2015-04-17",
		14: "2015-05-06",
	},
	106: map[int]string{
		3: "2015-10-16",
		4: "2015-10-30",
		6: "2015-12-02",
	},
	107: map[int]string{
		1: "2017-09-09",
		2: "2017-09-30",
		3: "2016-10-17",
		11: "2017-03-10",
		12: "2017-03-31",
		13: "2017-04-21",
		14: "2017-05-08",
		15: "2017-05-26",
		16: "2017-06-09",
	},
	108: map[int]string{
		1: "2017-09-11",
		2: "2017-09-29",
		3: "2017-10-17",
		4: "2017-10-31",
		5: "2017-11-10",
		6: "2017-12-01",
		7: "2017-12-20",
		8: "2018-01-19",
		9: "2018-02-02",
		10: "2018-02-15",
	},
}

var client *graphql.Client

// Sections is an array of all the sections.
var Sections []Section

// CreateStore creates a store for commonly accessed information
// (e.g. all sections, all users).
func CreateStore() {
	Sections = AllSections()
}

// Article represents an article.
type Article struct {
	ID, Title, Content, Slug string
}

// Section represents a department/section of the newspaper.
type Section struct {
	ID, Name, Slug string
}

type allSectionsResponse struct {
	AllSections []Section
}

type createArticleResponse struct {
	Article Article
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

// SectionIDByName returns a section's ID by its name.
func SectionIDByName(name string) (id int, found bool) {
	for _, section := range Sections {
		if section.Name == name {
			intID, err := strconv.Atoi(section.ID)
			if err != nil {
				panic(err)
			}
			return intID, true
		}
	}
	return -1, false
}

// CreateArticle constructs a GraphQL mutation and creates an article.
// It returns an error if any is encountered.
func CreateArticle(attrs map[string]interface{}) (article Article, err error) {
	req := graphql.NewRequest(`
  mutation (
    $title: String!,
    $content: String!,
    $summary: String,
    $outquotes: [String],
    $contributors: [Int]!,
    $volume: Int!,
    $issue: Int!,
    $sectionID: Int!,
  ) {
    createArticle(
      title: $title,
      content: $content,
      summary: $summary,
      outquotes: $outquotes,
      contributors: $contributors,
      volume: $volume,
      issue: $issue,
      section_id: $sectionID
    ) {
      id
    }
  }
`)
	for k, v := range attrs {
		fmt.Printf("(%T, %v), (%T, %v)", k, k, v, v)
		req.Var(k, v)
	}
	req.Var("contributors", []int{1, 2})

	ctx := context.Background()
	var res createArticleResponse
	if err = client.Run(ctx, req, &res); err != nil {
		return article, err
	}
	article = res.Article
	return
}
