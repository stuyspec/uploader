// uploader is a command line application that assists the automatic uploading
// of articles of The Stuyvesant Spectator.
package main

import (
	"github.com/stuyspec/uploader/driveclient"
	"github.com/stuyspec/uploader/graphql"
	"github.com/stuyspec/uploader/parser"
	"github.com/stuyspec/uploader/parser/patterns"

	"github.com/op/go-logging"
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
var log *logging.Logger
var uploaderCache *cache.Cache

func init() {
	gob.Register(map[string]*drive.File{})

	cliApp = CreateCliApp()
	log = CreateLogger()
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
			log.Errorf("Unable to save cache. %v", err)
		}
	}

	filesMap, err := driveFiles.(map[string]*drive.File)
	if !err {
		log.Errorf("Unable to type driveFiles to map. %v", err)
	} else {
		log.Notice("Loaded Drive files into map.")
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
		log.Error(err)
	}

	graphql.CreateStore()

	// UploadIssue(volume, issue)
	UploadArticle(
		"1Y0Pt7CD3Ic29acfvK3C5BI6yW_fP787ASYGUbooexYw",
		108,
		9,
	)
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

// UploadDepartment uploads a department of an issue of a volume.
func UploadDepartment(deptFolder *drive.File, volume, issue int) {
	children := DriveChildren(deptFolder.Id, "document")
	log.Noticef(
		"Uploading %s of Volume %d Issue %d.",
		deptFolder.Name,
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
	article, err := graphql.CreateArticle(articleAttrs)
	if err != nil {
		log.Errorf("Unable to create article with id %s. %v\n", fileID,	err)
	}
	log.Infof("%v", article)
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
