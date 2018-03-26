// uploader is a command line application that assists the automatic uploading
// of articles of The Stuyvesant Spectator.
package main

import (
	"github.com/stuyspec/uploader/log"
	"github.com/stuyspec/uploader/driveclient"
	"github.com/stuyspec/uploader/graphql"
	"github.com/stuyspec/uploader/parser/patterns"

	"github.com/urfave/cli"
	"github.com/patrickmn/go-cache"
	"github.com/skratchdot/open-golang/open"

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

var cliApp *cli.App
var uploaderCache *cache.Cache

// Global variables set by CLI
var volume int
var issue int

// Refers to opening core files of the bulk uploading process
// (e.g. photo folders, newspaper PDF).
var shouldOpenFiles bool

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
	if c.IsSet("window") {
		shouldOpenFiles = c.Bool("window")
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
	graphql.CreateStore()
	err := cliApp.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}

	UploadIssue(volume, issue)
}


// UploadIssue uploads an issue of a volume.
func UploadIssue(volumeNum, issueNum int) {
	issue := NewIssue(volumeNum, issueNum)

	// shouldOpenFiles is a global variable defined during CLI's run.
	if shouldOpenFiles {
		OpenDriveFiles(issue.NewspaperPdf, issue.PhotoFolder, issue.ArtFolder)
	}

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
		deptFolder, found := DriveFileByName(deptName, "folder", issue.SbcFolder.Id)
		if !found {
			log.Errorf(
				"No folder found for department %v. Skipping department.",
				deptName,
			)
			continue
		}
		UploadDepartment(deptFolder, volumeNum, issueNum, issue.Photos, issue.Art)
	}
}

// UploadDepartment uploads a department of an issue of a volume.
func UploadDepartment(
	deptFolder *drive.File,
	volume, issue int,
	photos, art []*drive.File,
) {
	children := DriveChildren(deptFolder.Id, "document")
	log.Headerf(
		"Uploading [%s], %d/%d\n\n",
		strings.ToUpper(deptFolder.Name),
		volume,
		issue,
	)
	for _, f := range children {
		if patterns.IsFileUnwanted(f.Name) {
			log.Errorf("Skipping unwanted file: %s.\n\n", f.Name)
			continue
		}
		UploadArticle(f.Id, volume, issue, photos, art)
	}
}

// UploadArticleByUrl uploads an article by its url.
func UploadArticleByUrl(volume, issue int, url string) {
  id, err := patterns.DriveID(url)
	if err != nil {
		log.Fatalf("No Drive ID found in url %s.\n", url)
	}
}

// OpenDriveFiles opens several Drive files in the browser (for convenience).
func OpenDriveFiles(files ...*drive.File) {
	for _, f := range files {
		OpenDriveFile(f)
	}
}

// OpenDriveFile opens a Drive file in the browser with a Drive file as the
// argument.
func OpenDriveFile(f *drive.File) {
	OpenDriveFileManual(f.Id, f.MimeType)
}

// OpenDriveFileManual opens a Drive file in the browser with ID and MIME type
// as arguments.
func OpenDriveFileManual(id, mimeType string) {
	var format string
	if strings.Contains(mimeType, "folder") {
		format = "https://drive.google.com/drive/u/0/folders/%s"
	} else if strings.Contains(mimeType, "document") {
		format = "https://docs.google.com/document/d/%s"
	} else if strings.Contains(mimeType, "image") {
		format = "https://drive.google.com/uc?id=%s"
	} else if mimeType == "application/pdf" {
		format = "https://drive.google.com/file/d/%s"
	} else {
		log.Errorf(
			"I don't yet know how to open a Drive file of MIME type %s.\n",
			mimeType,
		)
	}
	open.Run(fmt.Sprintf(format, id))
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
		if stringSliceContains(f.Parents, parentID) {
			if mimeType == "" ||
				mimeType == "image" && strings.Contains(f.MimeType, mimeType) ||
				mimeType == f.MimeType {
				output = append(output, f)
			}
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
// found. It takes the optional arguments MIME type and parent ID. If a Drive
// file is found, it returns the Drive file. If one is not found, the program
// exits.
func MustFindDriveFileByName(name interface{}, args ...string) *drive.File {
	file, found := DriveFileByName(name, args...)
	if !found {
		log.Fatalf("No Drive file of name %v found.\n", name)
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
