// uploader is a command line application that assists the automatic uploading
// of articles of The Stuyvesant Spectator.
package main

import (
	"github.com/stuyspec/uploader/log"
	"github.com/stuyspec/uploader/driveclient"
	"github.com/stuyspec/uploader/graphql"
	"github.com/stuyspec/uploader/parser"
	"github.com/stuyspec/uploader/parser/patterns"

	"github.com/patrickmn/go-cache"
	"github.com/urfave/cli"

	"encoding/gob"
	"fmt"
	"google.golang.org/api/drive/v3"
	"os"
	"regexp"
	"strconv"
	"strings"
)

// CacheFilename is the name of the file where an encoded cache is saved.
const CacheFilename = "file.cache"

// DriveFilesMap is a mapping of Drive files; map[file id]file
var DriveFilesMap map[string]*drive.File

var volume int
var issue int

var cliApp *cli.App
var uploaderCache *cache.Cache

func init() {
	gob.Register(map[string]*drive.File{})

	cliApp = CreateCliApp()
	uploaderCache = CreateUploaderCache()
}

// GenerateDriveFilesMap generates a map[string]*drive.File from the cache
// (there is a reload option). It returns the map.
func GenerateDriveFilesMap(shouldReload bool) map[string]*drive.File {
	// Get Drive files from cache, if it exists.
	driveFiles, found := uploaderCache.Get("DriveFiles")
	// Rescan and update cache with Drive files if reload flag or none found
	// current cache.
	if shouldReload || !found {
		driveFiles = driveclient.ScanDriveFiles()
		uploaderCache.Set("DriveFiles", driveFiles, cache.DefaultExpiration)
		err := SaveCache(uploaderCache)
		if err != nil {
			log.Fatalf("Unable to save cache. %v", err)
		}
	}

	filesMap, err := driveFiles.(map[string]*drive.File)
	if !err {
		log.Fatalf("Unable to type driveFiles to map. %v", err)
	} else {
		log.Info("Loaded Drive files into map.")
	}

	return filesMap
}

// TransferFlags moves flags information to global variables.
func TransferFlags(c *cli.Context) {
	if c.IsSet("volume") {
		volume = c.Int("volume")
	}
	if c.IsSet("issue") {
		issue = c.Int("issue")
	}
}

// stringDriveFile creates a custom string representation of a Drive file.
// It returns this string.
func stringDriveFile(f *drive.File) (output string) {
	var webContentLink string
	if strings.Contains(f.MimeType, "image") {
		webContentLink = fmt.Sprintf("\n   WebContentLink: %v,", f.WebContentLink)
	}
	output = fmt.Sprintf(`{
  Id: %s,
  Name: %s,
  MimeType: %s,%s
  Parents: %v,
}`,
		f.Id, f.Name, f.MimeType, webContentLink, f.Parents,
	)
	return
}

func main() {
	err := cliApp.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}

	graphql.CreateStore()

	UploadIssue(volume, issue)
}

// UploadIssue uploads an issue of a volume.
func UploadIssue(volume, issue int) {
	issueRange := "1-9"
	if issue > 9 {
		issueRange = "10-18"
	}
	volumeFolder := MustFindDriveFileByName(
		fmt.Sprintf("Volume %d No. %s", volume, issueRange),
		"folder",
	)
	issueFolder := MustFindDriveFileByName(
		regexp.MustCompile(`Issue\s?`+strconv.Itoa(issue)),
		"folder",
		volumeFolder.Id,
	)
	sbcFolder := MustFindDriveFileByName("SBC", "folder", issueFolder.Id)
	photos := Photos(issueFolder)
	art := Art(issueFolder)

	// A slice of folder name matchers to be passed into DriveFileByName
	departmentNames := []interface{}{
		"News",
		"Opinions",
		"Features",
		patterns.AePattern,
		"Humor",
		"Sports",
	}
	for _, deptName := range departmentNames {
		deptFolder, found := DriveFileByName(deptName, "folder", sbcFolder.Id)
		if !found {
			log.Errorf(
				"No folder found for department %v. Skipping department.",
				deptName,
			)
			continue
		}
		UploadDepartment(deptFolder, volume, issue)
	}
}

// Photos returns an array of all the photos of an issue.
func Photos(issueFolder *drive.File) []*drive.File {
	photos := make([]*drive.File, 0)
	photoFolder := MustFindDriveFileByName(
		regex.MustCompile(`(?i)photo\s?(color)?`),
		"folder",
		issueFolder.Id
	)
	return DriveChildren(photoFolder.Id, "image")
}

// Art returns an array of all the art of an issue.
func Art(issueFolder *drive.File) []*drive.File {
	art := make([]*drive.File, 0)
	artFolder := MustFindDriveFileByName(
		regex.MustCompile(`(?i)photo\s?(color)?`),
		"folder",
		issueFolder.Id
	)
	return DriveChildren(artFolder.Id, "image")
}

// UploadDepartment uploads a department of an issue of a volume.
func UploadDepartment(deptFolder *drive.File, volume, issue int) {
	children := DriveChildren(deptFolder.Id, "document")
	log.Headerf(
		"Uploading [%s], %d/%d\n\n",
		strings.ToUpper(deptFolder.Name),
		volume,
		issue,
	)
	for _, f := range children {
		UploadArticle(f.Id, volume, issue)
	}
}

// UploadArticle uploads an article of an issue of a volume via its ID.
func UploadArticle(fileID string, volume, issue int) {
	rawText := driveclient.DownloadGoogleDoc(fileID)
	articleAttrs, missingAttrs := parser.ArticleAttributes(rawText)
	if len(missingAttrs) > 0 {
		log.Errorf(
			"Unable to parse article with id %s; missing attributes %v.\n",
			fileID,
			missingAttrs,
		)
		return
	}
	title, _ := articleAttrs["title"]
	log.Header(title)
	PrintArticleInfo(articleAttrs)
	articleAttrs["volume"] = volume
	articleAttrs["issue"] = issue

	article, err := graphql.CreateArticle(articleAttrs)
	if err != nil {
		log.Errorf("Unable to create article with id %s. %v\n", fileID,	err)
	} else {
		log.Noticef("Successfully created Article with ID %s.", article.ID)
	}
}

// PrintArticleInfo prints article attributes, usually to prevent mistakes.
func PrintArticleInfo(attrs map[string]interface{}) {
	var contributors string
	var contributors string
	for i, nameVars := attrs["contributors"].([][]string) {
		contributors += strings.Join(nameVars, " ")
		if i > 0 {
			contributors += ","
		}
	}
	fmt.Println(fmt.Sprint(attrs["contributors"]))
}

// DriveChildren finds all direct children of a Drive file.
// It returns the children in a slice.
func DriveChildren(parentID string, args ...string) []*drive.File {
	var mimeType string
	output := make([]*drive.File, 0)
	if len(args) > 0 {
		mimeType = GetMimeType(args[0])
	}
	for _, f := range DriveFilesMap {
		if stringSliceContains(f.Parents, parentID) &&
			(mimeType == "" || f.MimeType == mimeType) {
			output = append(output, f)
		}
	}
	return output
}

// DriveFileByName finds a Drive file by its name (and optional MIME type and
// parent ID).
// It returns the Drive file.
func DriveFileByName(name interface{}, args ...string) (*drive.File, bool) {
	var parentID, mimeType string
	if len(args) > 0 {
		mimeType = GetMimeType(args[0])
		if len(args) > 1 {
			parentID = args[1]
		}
	}
	var matchFunc func(string) bool
	switch name.(type) {
	default:
		log.Fatalf("Unexpected matcher type in DriveFileByName: %T", name)
	case string:
		matchFunc = func(str string) bool {
			return name == str
		}
	case *regexp.Regexp:
		pattern := name.(*regexp.Regexp)
		matchFunc = func(str string) bool {
			return len(pattern.FindStringSubmatch(str)) > 0
		}
	}
	for _, f := range DriveFilesMap {
		if matchFunc(f.Name) &&
			(parentID == "" || stringSliceContains(f.Parents, parentID)) &&
			(mimeType == "" || mimeType == f.MimeType) {
			return f, true
		}
	}
	return nil, false
}

// GetMimeType allows us to use shortcuts for MIME types
// (e.g. "document" instead of "application/vnd.google-apps.document").
// It returns the intended. MIME type.
func GetMimeType(str string) string {
	switch str {
	case "folder":
		return "application/vnd.google-apps.folder"
	case "document":
		return "application/vnd.google-apps.document"
	default:
		return str
	}
}

// MustFindDriveFileByName is like DriveFileByName but panics if no file is
// found. If one is found, it returns the Drive file.
func MustFindDriveFileByName(name interface{}, args ...string) *drive.File {
	file, found := DriveFileByName(name, args...)
	if !found {
		log.Fatalf("No Drive file of name %v found.", name)
	}
	return file
}

// stringSliceContains returns true if a string slice contains a specified
// string.
func stringSliceContains(slice []string, str string) bool {
	for _, v := range slice {
		if v == str {
			return true
		}
	}
	return false
}
