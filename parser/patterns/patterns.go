// Package patterns provides regular expressions and pattern-matching utils.
package patterns

import (
	"regexp"
	"strings"
)

// slugPattern matches any line that is part of an article slug.
var slugPattern = regexp.MustCompile(`(?i)(outquote(\(s\))?s?:)|(focus\s+sentence:)|(word(s)?:?\s\d{2,4})|(\d{2,4}\swords[^\.])|(word count:?\s?\d{2,4})|focus:|article:|(Art|Photo)(\/Art|\/Photo)? Request:?`)

// aePattern matches any string that may represent the Arts & Entertainment
// department.
var aePattern = regexp.MustCompile(`Arts\s?&\s?Entertainment|A&?E`)

// Paddings are patterns we want to remove from the desired value
// (e.g. "Title: ", "Outquote(s): ").
var titlePadding = regexp.MustCompile(`Title:\s+`)
var bylinePadding = regexp.MustCompile(`By:?\s+`)
var focusPadding = regexp.MustCompile(`(?i)Focus Sentence:?\s+`)
var outquotePadding = regexp.MustCompile(`(?i)outquote\(?s?\)?:?`)
var nicknamePadding = regexp.MustCompile(`\([\w\s-]*\)\s`)

// Captures are the opposite of paddings. For some information, it is easier to
// extract it than to remove the padding of it.
var departmentCapture = regexp.MustCompile(`The Spectator\s*\/([^\/]+)\s*\/`)

// Components are patterns that can split a string into easy-to-read components.
var bylineComponent = regexp.MustCompile(`[\w\p{L}\p{M}']+|[.,!-?;]`)

// IsSlugMember determines whether a string is a member of an article slug.
// It returns true or false.
func IsSlugMember(str string) bool {
	return len(slugPattern.FindStringSubmatch(str)) > 0
}

// IsDepartmentMarker determines whether a string marks the department.
// (e.g. "The Spectator/Opinions/Issue 10")
func IsDepartmentMarker(str string) bool {
	return len(departmentCapture.FindStringSubmatch(str)) > 0
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
	return len(aePattern.FindStringSubmatch(str)) > 0
}

// CleanTitle rids a title of its paddings (e.g. "Title:").
// It returns the cleaned title.
func CleanTitle(title string) string {
	return titlePadding.ReplaceAllString(title, "")
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
// (e.g. "Ying Zi (Jessy) Mei").
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

// DepartmentName extracts the department name of a slug line.
// It returns the department name.
func DepartmentName(marker string) string {
	name := strings.TrimSpace(departmentCapture.FindStringSubmatch(marker)[0])
	if IsAE(marker) {
		name = "Arts & Entertainment"
	}
	return name
}
