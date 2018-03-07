// Package parser implements functions to parse Spectator article text.
package parser

import (
	"github.com/stuyspec/uploader/parser/patterns"

	"fmt"
	"log"
	"strings"
)

// ArticleAttributes finds the articles of an article for posting.
// It returns attributes.
func ArticleAttributes(text string) (attrs map[string]interface{}) {
	attrs = make(map[string]interface{})
	text = strings.TrimSpace(text)

	rawLines := strings.Split(text, "\n")
	content := make([]string, 0)

	attrs["title"] = patterns.CleanTitle(rawLines[0])

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
			attrs["contributors"] = ArticleContributors(line)
		} else if patterns.IsFocus(line) {
			attrs["summary"] = patterns.CleanFocus(line)
		} else if patterns.IsOutquote(line) {
			outquotes := make([]string, 0)

			// Outquotes are often put on multiple lines. We loop forwards to get all
			// outquotes.
			for j <= i {
				outquoteStr := patterns.CleanOutquote(rawLines[j])

				// If what we think is an outquote is actually another part of the
				// slug, we know we have found all the outquotes.
				if patterns.IsSlugMember(outquoteStr) {
					break
				}

				outquotes = append(outquotes, outquoteStr)
				j++
			}

			attrs["outquotes"] = outquotes
		}
	}

	return
}

// ArticleContributors finds the contributors in a byline.
// It returns the contributors.
func ArticleContributors(byline string) (contributors []map[string]string) {
	contributors = make([]map[string]string, 0)
	components := patterns.BylineComponents(byline)

	slicerIndex := 0
	for i, symbol := range components {
		if symbol == "&" || symbol == "," || symbol == "and" {
			name := strings.Join(components[slicerIndex:i], " ")
			contributors = append(contributors, nameVariables(name))
			slicerIndex = i + 1
		}
	}
	remainingName := strings.Join(components[slicerIndex:], " ")
	contributors = append(contributors, nameVariables(remainingName))

	return
}

// nameVariables splits a name of variable length into a first name and a last
// name.
// It returns the formatted name as a map with a first_name and last_name.
func nameVariables(name string) map[string]string {
	variables := make(map[string]string)

	name = patterns.CleanName(name)

	var first_name, last_name string
	components := strings.Split(name, " ")
	if len(name) == 0 {
		log.Fatalf("No name given or cleaning cleared the entire name.")
	} else	if len(components) == 1 {
		first_name, last_name = name, name
	} else if len(components) > 2 {
		first_name = strings.Join(components[0:len(components)-1], " ")
		last_name = components[len(components)-1]
	} else {
		first_name, last_name = components[0], components[1]
	}

	variables["first_name"], variables["last_name"] = first_name, last_name

	return variables
}
