// Package patterns provides regular expressions and pattern-matching utils.
package patterns

import (
	"github.com/stuyspec/uploader/log"

	"errors"
	"regexp"
	"strings"
)

// Patterns are used to determine whether a string matches.
var slugPattern = regexp.MustCompile(`(?i)(outquote(\(s\))?s?:)|(focus\s+sentence:)|(word(s)?:?\s\d{2,4})|(\d{2,4}\swords)|(word count:?\s?\d{2,4})|focus:|article:|(Art|Photo)(\/Art|\/Photo)? Request:?`)
var AePattern = regexp.MustCompile(`Arts\s?&\s?Entertainment|A&?E`)
var UnwantedFilePattern = regexp.MustCompile(`(?i)worldbeat|survey|newsbeat|spookbeat|sportsbeat|playlist|calendar|\[IGNORE\]|corrections|timeline`)

// Paddings are patterns we want to remove from the desired value
// (e.g. "Title: ", "Outquote(s): ").
var titlePadding = regexp.MustCompile(`Title:\s+`)
var bylinePadding = regexp.MustCompile(`^By:?\s+`)
var focusPadding = regexp.MustCompile(`(?i)^Focus Sentence:?\s+`)
var outquotePadding = regexp.MustCompile(`(?i)^outquote\(?s?\)?:?[\s]*`)
var nicknamePadding = regexp.MustCompile(`\([\w\s-]*\)\s`)

// Captures are the opposite of paddings. For some information, it is easier to
// extract it than to remove the padding of it.
var departmentCapture1 = regexp.MustCompile(`The Spectator\s*\/([^\/\d]+)\s*\/`)
var departmentCapture2 = regexp.MustCompile(`The Spectator\s*\/\s*Issue\s*#?\d{1,2}\s*\/(.*)`)
var hrefCapture = regexp.MustCompile(`(?i)<a href="([^"]*)">`)
var driveIDCapture = regexp.MustCompile(`[-\w]{25,}`)

// Components are patterns that can split a string into easy-to-read components.
var bylineComponent = regexp.MustCompile(`[\w\p{L}\p{M}'-]+|[.,!?;]`)

// IsSlugMember determines whether a string is a member of an article slug.
// It returns true or false.
func IsSlugMember(str string) bool {
	return len(slugPattern.FindStringSubmatch(str)) > 0 ||
		IsByline(str) ||
		IsDepartmentMarker(str)
}

// IsDepartmentMarker determines whether a string marks the department.
// (e.g. "The Spectator/Opinions/Issue 10")
func IsDepartmentMarker(str string) bool {
	return len(departmentCapture1.FindStringSubmatch(str)) > 0 ||
		len(departmentCapture2.FindStringSubmatch(str)) > 0
}

// IsByline determines whether a string is a byline.
// It returns true or false.
func IsByline(str string) bool {
	return len(bylinePadding.FindStringSubmatch(str)) > 0
}

// IsOutquote determines whether a string is an outquote.
// It returns true or false.
func IsOutquote(str string) bool {
	return len(outquotePadding.FindStringSubmatch(str)) > 0
}

// IsFocus determines whether a string is a focus sentence.
// It returns true or false.
func IsFocus(str string) bool {
	return len(focusPadding.FindStringSubmatch(str)) > 0
}

// IsAE determines whether a string represents the Arts & Entertainment
// department.
// It returns true or false.
func IsAE(str string) bool {
	return len(AePattern.FindStringSubmatch(str)) > 0
}

// IsFileUnwanted determines whether the name of a Drive file contains an
// unwanted article.
func IsFileUnwanted(filename string) bool {
	return len(UnwantedFilePattern.FindStringSubmatch(filename)) > 0
}

// CleanTitle rids a title of its paddings (e.g. "Title:").
// It returns the cleaned title.
func CleanTitle(title string) string {
	title = titlePadding.ReplaceAllString(title, "")
	return strings.TrimSpace(strings.Replace(title, "\r", "", -1))
}

// CleanByline rids a byline of its paddings (e.g. "By:").
// It returns the cleaned byline.
func CleanByline(byline string) string {
	return bylinePadding.ReplaceAllString(byline, "")
}

// CleanOutquote rids an outquote of its paddings (e.g. "Outquote(s):").
// It returns the cleaned outquote.
func CleanOutquote(outquote string) string {
	return outquotePadding.ReplaceAllString(outquote, "")
}

// CleanFocus rids a focus sentence of its paddings (e.g. "Focus Sentence:").
// It returns the cleaned focus sentence.
func CleanFocus(focusSentence string) string {
	return focusPadding.ReplaceAllString(focusSentence, "")
}

// CleanName rids a name of nicknames and redundant spaces
// (e.g. "Ying Zi (Jessy) Mei"). It returns the cleaned name.
func CleanName(name string) string {
	name = strings.Join(strings.Fields(name), " ")    // Remove redundant spaces
	return nicknamePadding.ReplaceAllString(name, "") // Remove nicknames
}

// BylineComponents extracts the components of a byline crucial to parsing
// (e.g. ampersands, words/names, commas).
// It returns a slice of the components.
func BylineComponents(byline string) []string {
	byline = CleanByline(byline)
	return bylineComponent.FindAllString(byline, -1)
}

// HrefCapture extracts the href of an a tag in HTML. It returns the href.
func HrefCapture(html string) string {
	matches := hrefCapture.FindStringSubmatch(html)
	if len(matches) > 1 {
		return matches[1]
	}
	return ""
}

// DepartmentName extracts the department name of a slug line.
// It returns the department name.
func DepartmentName(marker string) string {
	matches := departmentCapture1.FindStringSubmatch(marker)
	if len(matches) == 0 {
		matches = departmentCapture2.FindStringSubmatch(marker)
	}
	name := matches[1]
	if IsAE(marker) {
		name = "Arts & Entertainment"
	}
	return strings.TrimSpace(name)
}

// DriveID extracts the Drive ID of a URL of a Google Apps Script.
// It returns the ID.
func DriveID(url string) (id string, err error) {
	matches := driveIDCapture.FindStringSubmatch(url)
	if len(matches) > 0 {
		id = matches[0]
	} else {
		err = errors.New("No Drive ID found.")
	}
	return
}

// NameVariables splits a name of variable length into a first name and a last
// name. It returns a slice with the first element as the first name and the
// second element as the last name.
func NameVariables(name string) []string {
	if strings.Contains(name, "Department") || strings.Contains(name, "Board") {
		return []string{name, ""}
	}

	variables := make([]string, 2)
	name = CleanName(name)

	var firstName, lastName string
	components := strings.Split(name, " ")
	if len(name) == 0 {
		log.Fatalf("No name given or cleaning cleared the entire name.")
	} else if len(components) == 1 {
		firstName, lastName = name, name
	} else if len(components) > 2 {
		firstName = strings.Join(components[0:len(components)-1], " ")
		lastName = components[len(components)-1]
	} else {
		firstName, lastName = components[0], components[1]
	}

	variables[0], variables[1] = firstName, lastName

	return variables
}
