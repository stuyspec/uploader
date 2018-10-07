package main

import (
	"github.com/stuyspec/uploader/log"
	"github.com/stuyspec/uploader/driveclient"
	"github.com/stuyspec/uploader/graphql"
	"github.com/stuyspec/uploader/parser"

	"bufio"
	"fmt"
	"google.golang.org/api/drive/v3"
	"os"
	"strconv"
	"strings"
)

// UploadArticle uploads an article of an issue of a volume via its ID.
func UploadArticle(
	fileID string,
	volume, issue int,
	photos, art []*drive.File,
	options ...string,
) {
	rawText := driveclient.DownloadGoogleDoc(fileID)
	articleAttrs, missingAttrs := parser.ArticleAttributes(rawText)
	if len(missingAttrs) > 0 {
		// If we know this article is a staff-ed (which have irregular slugs),
		// we patch up articleAttrs.
		if len(options) > 0 && options[0] == "staff-ed" {
			sectionID, found := graphql.SectionIDByName("Staff Editorials")
			if found {
				articleAttrs["sectionID"] = sectionID
			} else {
				log.Error("Unable to find section with name 'Staff Editorials'.")
				return
			}
			if stringSliceContains(missingAttrs, "contributors") {
				contributors := parser.Contributors("By The Editorial Board")
				if len(contributors) > 0 {
					articleAttrs["contributors"] = contributors
				} else {
					log.Error("No contributors found in 'By The Editorial Board'.")
					return
				}
			}
		} else {
			log.Errorf(
				"Unable to parse article with id %s; missing attributes %v.\n\n",
				fileID,
				missingAttrs,
			)
			for {
				uploadConfig := Input("open/reload? (o/r/n): ")
				if uploadConfig == "r" {
					// [RELOAD]: Article content changed, download again
					log.Println()
					UploadArticle(fileID, volume, issue, photos, art)
					return
				} else if uploadConfig == "o" {
					// [OPEN]: Open Drive file in browser (often used before RELOAD for
					// fixing article content).
					OpenDriveFileManual(fileID, "document")
				} else if uploadConfig == "n" {
					// [NO]: Ignore article, do not upload.
					log.Println()
					return
				} else {
					log.Errorf("[%s] is not a valid option.\n", uploadConfig)
				}
			}
		}
	}

	if _, found := graphql.ArticleByContent(articleAttrs["content"].(string));
	  found {
		log.Errorf("%s already exists.\n\n", articleAttrs["title"])
		return
	}
	PrintArticleInfo(articleAttrs)
	articleAttrs["volume"] = volume
	articleAttrs["issue"] = issue

	articleAttrs["sectionID"] = PickSubsectionByIssue(
		articleAttrs["sectionID"].(int),
		issue,
	)

	for {
		uploadConfig := Input("upload? (y/n/r/o): ")
		if uploadConfig == "y" {
			// [YES]: Upload article
			break
		} else if uploadConfig == "n" {
			// [NO]: Skip article
			log.Println() // aesthetic line break between articles
			return
		} else if uploadConfig == "r" {
			// [RELOAD]: Article content changed, download again
			log.Println()
			UploadArticle(fileID, volume, issue, photos, art)
			return
		} else if uploadConfig == "o" {
			// [OPEN]: Open Drive file in browser (often used before RELOAD for
			// fixing article content).
			OpenDriveFileManual(fileID, "document")
		} else {
			log.Errorf("[%s] is not a valid option.\n", uploadConfig)
		}
	}

	article, err := graphql.CreateArticle(articleAttrs)
	if err != nil {
		log.Errorf("Unable to create article with id %s. %v\n", fileID,	err)

		// If there is an error, reload the article. It could be solved by a simple
		// open -> edit -> reload. If not, then it can be skipped.
		log.Println()
		UploadArticle(fileID, volume, issue, photos, art)
		return
	} else {
		log.Noticef("Created article #%s.\n", article.ID)
	}

	CreateArticleMedia(article, photos, art)

	log.Println()
}

// PickSubsection lets the user choose to which subsection an article belongs.
func PickSubsection(sectionID int) int {
	return PickSubsectionByIssue(sectionID, -1)
}

// PickSubsectionByIssue lets the user choose to which subsection an article
// belongs. The issue number can reduce the number of choices.
func PickSubsectionByIssue(sectionID, issue int) int {
	section := graphql.Section{}
	subsections := make([]graphql.Section, 0)
	strID := strconv.Itoa(sectionID)
	for _, s := range graphql.Sections {
		if s.ID == strID {
			section = s
			break
		}
	}
	if section.ID == "" { // No section found
		return sectionID
	}
	if section.Name == "Humor" && issue != 12 && issue != 4 {
		// Humor only has subsections Disrespectator and Spooktator in issues 12 and
		// 4, respectively.
		return sectionID
	}
	for _, s := range graphql.Sections {
		if section.Name == "Humor" &&
			((issue == 12 && s.Name == "Disrespectator") ||
			(issue == 4 && s.Name == "Spooktator")) {
			sID, _ := strconv.Atoi(s.ID)
			return sID
		}
		if s.Parent_ID == strID {
			subsections = append(subsections, s)
		}
	}
	if len(subsections) == 0 { // Section is already a subsection
		return sectionID
	}
	if section.Name == "Opinions" && len(subsections) == 1 {
		// We upload the staff editorial separately from the Opinions section.
		// Therefore, if there is no other subsection, we don't need to pick one.
		return sectionID
	}
	log.Info("optional subsections ->")
	for i, s := range subsections {
		fmt.Printf("  [%d] %s\n", i, s.Name)
	}
	choice := Input("subsection (leave blank if none): ")
	index, err := strconv.Atoi(choice)
	if choice == "" || err != nil {
		return sectionID
	}
	if index < len(subsections) && index >= 0 {
		id, _ := strconv.Atoi(subsections[index].ID)
		return id
	}
	return sectionID
}

// CreateArticleMedia lets the user choose which media accompanies an article.
func CreateArticleMedia(article graphql.Article, photos, art []*drive.File) {
	for {
		if mediaConfig := Input("add media? (y/n): "); mediaConfig == "y" {
			// [YES]: Upload media
			break
		} else if mediaConfig == "n" {
			// [NO]: Skip article
			return
		}
	}

	for {
		log.Info("==========")
		mediaAttrs := map[string]string{
			"articleID": article.ID,
		}
		filename := Input("-> filename: ")
		if filename == "" {
			return
		}
		for _, p := range photos {
			if p.Name == filename {
				mediaAttrs["mediaType"] = "photo"
				mediaAttrs["webContentLink"] = p.WebContentLink
				mediaAttrs["mimeType"] = p.MimeType
			}
		}
		if _, found := mediaAttrs["mediaType"]; !found {
			// No matching photo found, let's check art...
			for _, a := range art {
				if a.Name == filename {
					mediaAttrs["mediaType"] = "illustration"
					mediaAttrs["webContentLink"] = a.WebContentLink
					mediaAttrs["mimeType"] = a.MimeType
				}
			}
		}
		if _, found := mediaAttrs["mediaType"]; !found {
			log.Errorf("Unable to find media with name %s.\n", filename)
			continue
		}
		mediaAttrs["title"] = Input("-> title: ")
		mediaAttrs["caption"] = Input("-> caption: ")
		for {
			if artistName := Input("-> artist: "); artistName != "" {
				mediaAttrs["artistName"] = artistName
				break
			}
		}
		medium, err := graphql.CreateMedium(mediaAttrs)
		if err != nil {
			log.Errorf("Unable to create media. %v\n",	err)
			continue
		} else {
			log.Noticef("Created Medium #%s.\n", medium.ID)
		}
	}
}

// PrintArticleInfo prints article attributes, usually to prevent mistakes.
func PrintArticleInfo(attrs map[string]interface{}) {
	log.Headerf("%v\n", attrs["title"])
	log.Infof("contributors: ")
	var contributors string
	for i, nameVars := range attrs["contributors"].([][]string) {
		if i > 0 {
			contributors += ", "
		}
		contributors += strings.Join(nameVars, " ")
	}
	log.Printf("%s\n", contributors)

	log.Infof("summary: ")
	log.Printf("%v\n", attrs["summary"])

	log.Infof("content: ")
	truncatedContent := attrs["content"].(string)
	if words := strings.Split(truncatedContent, " "); len(words) > 20 {
		truncatedContent = strings.Join(words[:20], " ") + "..."
	}
	log.Printf("%s\n", truncatedContent)
}

// Input lets the user respond to a prompt. It returns the user's response.
// If there were a scanning error, it returns an empty string.
func Input(prompt string) string {
	reader := bufio.NewReader(os.Stdin)
	log.Infof(prompt)
	text, err := reader.ReadString('\n')
	if err != nil {
		log.Fatalf("Unable to read response. %v\n", err)
	}
	return strings.Trim(text, "\r\n")
}
