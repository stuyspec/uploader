// Package patterns provides regular expressions and pattern-matching utils.
package patterns

import (
	"regexp"
	"strings"
)

var slugPattern *regexp.Regexp = regexp.MustCompile(`(?i)(outquote(\(s\))?s?:)|(focus\s+sentence:)|(word(s)?:?\s\d{2,4})|(\d{2,4}\swords[^\.])|(word count:?\s?\d{2,4})|focus:|article:`)
var outquotePattern *regexp.Regexp = regexp.MustCompile(`(?i)outquote\(?s?\)?:?`)
var nicknamePattern *regexp.Regexp = regexp.MustCompile(`\([\w\s-]*\)\s`)

// Paddings are patterns we want to remove from the desired value
// (e.g. "Title: ", "Outquote(s): ")
var bylinePadding *regexp.Regexp = regexp.MustCompile(`By:?\s+`)
var focusPadding *regexp.Regexp = regexp.MustCompile(`(?i)Focus Sentence:?\s+`)
var titlePadding *regexp.Regexp = regexp.MustCompile(`Title:\s+`)

// Components are patterns that can split a string into easy-to-read components.
var bylineComponent *regexp.Regexp = regexp.MustCompile(`[\w\p{L}\p{M}']+|[.,!-?;]`)

// IsSlugMember determines whether a string is a member of an article slug.
// It returns true or false.
func IsSlugMember(str string) bool {
	return len(slugPattern.FindStringSubmatch(str)) > 0
}

// IsByline determines whether a string is a byline.
// It returns true or false.
func IsByline(str string) bool {
	return len(bylinePadding.FindStringSubmatch(str)) > 0
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

// CleanName rids a name of nicknames and redundant spaces
// (e.g. "Ying Zi (Jessy) Mei").
func CleanName(name string) string {
	name = strings.Join(strings.Fields(name), " ") // Remove redundant spaces
	return nicknamePattern.ReplaceAllString(name, "") // Remove nicknames
}

// BylineComponents extracts the components of a byline crucial to parsing
// (e.g. ampersands, words/names, commas).
// It returns a slice of the components.
func BylineComponents(byline string) []string {
	byline = CleanByline(byline)
	return bylineComponent.FindAllString(byline, -1)
}
