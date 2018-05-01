// Package parser implements functions to parse the text of Spectator articles.
package parser

import (
	"github.com/op/go-logging"
	"github.com/stuyspec/uploader/graphql"
	"github.com/stuyspec/uploader/parser/patterns"

	"fmt"
	"os"
	"strings"
)

var log *logging.Logger

func init() {
	log = logging.MustGetLogger("stuy-spec-uploader-cli")

	// Log format string. Everything except the message has a custom color
	// which is dependent on the log level. Many fields have a custom output
	// formatting too, eg. the time returns the hour down to the milli second.
	var format = logging.MustStringFormatter(`%{message}%{color:reset}`)

	backend := logging.NewLogBackend(os.Stderr, "", 0)
	backendFormatter := logging.NewBackendFormatter(backend, format)
	logging.SetBackend(backendFormatter) // Set backends to be used
}

// ArticleAttributes finds the articles of an article for posting.
// It returns attributes.
func ArticleAttributes(text string) (map[string]interface{}, []string) {
	attrs := make(map[string]interface{})
	text = strings.TrimSpace(text)

	rawLines := strings.Split(text, "\n")
	content := make([]string, 0)

	attrs["title"] = patterns.CleanTitle(rawLines[0])

	// TODO: Turn the below loop into a function by passing &int.

	// Start from the end of the article and add lines of content until we reach
	// the slug (header).
	i := len(rawLines) - 1
	for ; i >= 0; i-- {
		line := strings.TrimSpace(rawLines[i])
		if len(line) == 0 {
			continue
		}
		if patterns.IsSlugMember(line) {
			break
		}
		// Prepend line to content
		content = append([]string{line}, content...)
	}

	attrs["content"] = fmt.Sprintf("<p>%s</p>", strings.Join(content, "</p><p>"))

	// After we've found the last index of the slug, read article information from
	// the top to the end of the slug.
	for j := 1; j <= i; j++ {
		line := strings.TrimSpace(rawLines[j])
		if len(line) == 0 {
			continue
		}

		if patterns.IsByline(line) {
			attrs["contributors"] = Contributors(line)
		} else if patterns.IsFocus(line) {
			attrs["summary"] = patterns.CleanFocus(line)
		} else if patterns.IsOutquote(line) {
			attrs["outquotes"] = Outquotes(rawLines, j, i)
		} else if patterns.IsDepartmentMarker(line) {
			sectionID, found := graphql.SectionIDByName(
				patterns.DepartmentName(line),
			)
			if found {
				attrs["sectionID"] = sectionID
			}
		}
	}

	return attrs, MissingAttributes(attrs)
}

// Contributors finds the contributors in a byline.
// It returns the contributors.
func Contributors(byline string) (contributors [][]string) {
	contributors = make([][]string, 0)
	components := patterns.BylineComponents(byline)

	slicerIndex := 0
	for i, symbol := range components {
		if symbol == "&" || symbol == "," || symbol == "and" {
			name := strings.Join(components[slicerIndex:i], " ")
			slicerIndex = i + 1
			if len(name) == 0 {
				continue
			}
			contributors = append(contributors, patterns.NameVariables(name))
		}
	}
	remainingName := strings.Join(components[slicerIndex:], " ")
	contributors = append(contributors, patterns.NameVariables(remainingName))

	return
}

// Outquotes looks for outquotes in an array of lines between two indices.
// We search through an entire area of content because outquotes are often put
// on multiple lines. We loop forwards to get all outquotes.
// It returns the outquotes as a string slice.
func Outquotes(lines []string, start, end int) (outquotes []string) {
	outquotes = make([]string, 0)
	for start <= end {
		outquoteStr := patterns.CleanOutquote(lines[start])

		// If what we think is an outquote is actually another part of the
		// slug, we know we have found all the outquotes.
		if patterns.IsSlugMember(outquoteStr) {
			break
		}

		outquotes = append(outquotes, outquoteStr)
		start++
	}
	return
}

// MissingAttributes warns the user if not all attributes of an article were
// found.
func MissingAttributes(attrs map[string]interface{}) []string {
	requiredKeys := []string{
		"title",
		"content",
		"contributors",
		"sectionID",
	}
	badKeys := make([]string, 0)
	for _, key := range requiredKeys {
		if _, ok := attrs[key]; !ok {
			badKeys = append(badKeys, key)
		}
	}
	return badKeys
}
