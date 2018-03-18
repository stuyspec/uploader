// Package graphql provides a GraphQL client to the Spectator Rails API.
package graphql

import (
	"github.com/joho/godotenv"
	"github.com/jkao1/go-graphql"

	"github.com/stuyspec/uploader/log"

	"context"
	"fmt"
	"math/rand"
	"net/http"
	"net/url"
	"os"
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

var deviseHeader = http.Header{}

var apiEndpoint string

// Sections is an array of all the sections.
var Sections []Section

// Article represents an article.
type Article struct {
	ID string
	Title string
	Content string
	Slug string
	CreatedAt string

	// We create articles with summaries, but article records initiate themselves
	// with Previews. This resolves the many problems with simply using article
	// focus sentences as previews on the website (if focus sentences are empty,
  // Rails can generate a Preview using the article's content).
	Preview string
	Outquotes []string
}

func (a Article) String() string {
	return fmt.Sprintf("{ID: %s, Slug: %s}",
		a.ID,
		a.Slug,
	)
}

// Section represents a department/section of the newspaper.
type Section struct {
	ID, Name, Slug string
}

// User represents a contributor, illustrator, or photographer.
type User struct {
	ID string
	FirstName string
	LastName string
	Email string
}

// AllSectionsResponse is a structure to unmarshall the JSON of an allSections
// query.
type AllSectionsResponse struct {
	AllSections []Section
}

// CreateArticleResponse is a structure to unmarshall the JSON of a
// createArticle mutation.
type CreateArticleResponse struct {
	CreateArticle Article
}

// CreateUserResponse is a structure to unmarshall the JSON of a createUser
// mutation.
type CreateUserResponse struct {
	CreateUser User
}

// UserByFirstLastResponse is a structure to unmarshall the JSON of an
// userByFirstLast query.
type UserByFirstLastResponse struct {
	UserByFirstLast User
}

func init() {
	err := godotenv.Load()
  if err != nil {
    log.Fatal("Error loading .env file.")
  }

	if endpoint := os.Getenv("API_ENDPOINT"); endpoint == "" {
		apiEndpoint = "https://api.stuyspec.com"
	} else {
		apiEndpoint = endpoint
	}

	// Initialize the generator with a random seed
	rand.Seed(time.Now().UTC().UnixNano())

	// Initialize Devise header by signing in
	authVals := url.Values{}
	authVals.Set("email", os.Getenv("EMAIL"))
	authVals.Set("password", os.Getenv("PASSWORD"))
	resp, err := http.PostForm(apiEndpoint + "/auth/sign_in", authVals)
	if err != nil {
		log.Fatal("Unable to sign in.")
	} else if resp.StatusCode == 401 {
		log.Fatal("Sign in unauthorized.")
	} else if resp.StatusCode != 200 {
		log.Fatal("Unknown error occurred during sign-in. Check the API logs.")
	}

	for _, authHeader := range []string{
		"Access-Token",
		"Client",
		"Expiry",
		"Uid",
	} {
		deviseHeader.Set(authHeader, resp.Header.Get(authHeader))
	}
	fmt.Println(deviseHeader)

	// Initialize GraphQL client
	client = graphql.NewClient(fmt.Sprintf(apiEndpoint + "/graphql"))
	client.Log = func(s string) { log.Println(s) }
}

// CreateStore creates a store for commonly accessed information
// (e.g. all sections, all users).
func CreateStore() {
	Sections = AllSections()
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

	var res AllSectionsResponse
	if err := RunGraphqlQuery(req, &res); err != nil {
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

// UserIDByFirstLast returns a user's ID by his or her first and last names.
func UserIDByFirstLast(first, last string) (id int, err error) {
	req := graphql.NewRequest(`
  query ($firstName: String!, $lastName: String!) {
    userByFirstLast(first_name: $firstName, last_name: $lastName) {
      id
    }
  }
`)
	req.Var("firstName", first)
	req.Var("lastName", last)

	var res UserByFirstLastResponse
	if err = RunGraphqlQuery(req, &res); err != nil {
		return
	}
	if id, err = strconv.Atoi(res.UserByFirstLast.ID); err == nil {
		return
	}

	// By now we know the user does not exist, so we create one.
	var user User
	if user, err = CreateUser(first, last); err != nil {
		return
	}
	return strconv.Atoi(user.ID)
}

// CreateUser constructs a GraphQL mutation and creates a user.
// It returns an error if any is encountered.
func CreateUser(first, last string) (user User, err error)  {
	log.Promptf("Enter email for %s %s: ", first, last)
	var email string
	if _, err := fmt.Scan(&email); err != nil {
		log.Fatalf("Unable to read email. %v", err)
	}

	req := graphql.NewRequest(`
  mutation (
    $firstName: String!,
    $lastName: String!
    $email: String!,
    $password: String!,
    $passwordConfirmation: String!
  ) {
    createUser(
      first_name: $firstName,
      last_name: $lastName,
      email: $email,
      password: $password,
      password_confirmation: $passwordConfirmation,
    ) {
      id
    }
  }
`)
	req.Var("firstName", first)
	req.Var("lastName", last)
	req.Var("email", email)

	pword := GeneratePassword()
	req.Var("password", pword)
	req.Var("passwordConfirmation", pword)

	var res CreateUserResponse
	if err = RunGraphqlQuery(req, &res); err != nil {
		return
	}
	log.Promptf("Created user %s %s.\n", first, last)
	user = res.CreateUser
	return
}

// GeneratePassword creates a random alphanumeric, 16-letter password.
func GeneratePassword() string {
	alphaNums := []rune(
		"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
	)
	pword := make([]rune, 16)
	for i := range pword {
		pword[i] = alphaNums[rand.Intn(len(alphaNums))]
	}
	return string(pword)
}

// CreateArticle constructs a GraphQL mutation and creates an article.
// It returns an error if any is encountered.
func CreateArticle(attrs map[string]interface{}) (article Article, err error) {
	// We don't need to check for missing attributes because that is already done
	// in main.UploadArticle before CreateArticle is called.
	volume, _ := attrs["volume"]
	issue, _ := attrs["issue"]

	// We give the article a date based on the day it was printed and distributed.
	attrs["created_at"] = PublicationTime(volume.(int), issue.(int))
	req := graphql.NewRequest(`
  mutation (
    $title: String!,
    $content: String!,
    $summary: String,
    $outquotes: [String],
    $contributors: [Int]!,
    $volume: Int!,
    $issue: Int!,
    $created_at: String!,
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
      created_at: $created_at,
      section_id: $sectionID
    ) {
      id
      slug
    }
  }
`)
	for k, v := range attrs {
		if k == "contributors" {
			contIDs := make([]int, 0)
			contributors := v.([][]string)
			for _, c := range contributors {
				var userID int
				if userID, err = UserIDByFirstLast(c[0], c[1]); err != nil {
					return
				} else {
					contIDs = append(contIDs, userID)
				}
			}
			req.Var(k, contIDs)
		} else {
			req.Var(k, v)
		}
	}

	var res CreateArticleResponse
	if err = RunGraphqlQuery(req, &res); err != nil {
		return
	}
	article = res.CreateArticle
	return
}

// PublicationTime returns the timestamp for an article of a volume and issue.
// It uses the day the article was printed and distributed as the date and the
// current time as the time.
func PublicationTime(volume, issue int) (timestamp string) {
	if volDates, found := IssueDates[volume]; found {
		var issueDate string
		if issueDate, found = volDates[issue]; found {
			timestamp = fmt.Sprintf("%sT%s", issueDate, time.Now().Format("04:20:00"))
			return
		}
	}
	log.Fatalf("No issue date found for Volume %d, Issue %d.", volume, issue)
	return
}

// RunGraphqlQuery takes a GraphQL request and executes it. It pours the
// response into a given address.
func RunGraphqlQuery(req *graphql.Request, resp interface{}) error {
	ctx := context.Background()
	for _, authHeader := range []string{
		"Access-Token",
		"Client",
		"Expiry",
		"Uid",
	} {
		req.Header.Set(authHeader, deviseHeader.Get(authHeader))
	}
	var headers http.Header
	if err := client.Run(ctx, req, resp, &headers); err != nil {
		return err
	}
	for _, authHeader := range []string{
		"Access-Token",
		"Client",
		"Expiry",
		"Uid",
	} {
		if headers.Get(authHeader) != "" {
			deviseHeader.Set(authHeader, headers.Get(authHeader))
		}
	}
	return nil
}
