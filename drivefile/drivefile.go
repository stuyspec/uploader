// Package drivefile contains the DriveFile struct.
package drivefile

import (
	"google.golang.org/api/drive/v3"
	"fmt"
	"strings"
)

type DriveFile struct {
	Id string
	Name string
	MimeType string
	Parents []string
	WebContentLink string
}

func (file *DriveFile) String() string {
	return "{\n" +
		"  id: " + file.Id +
		",\n  name: " + file.Name +
		",\n  mimeType: " + file.MimeType +
		",\n  parents: " + fmt.Sprint(file.Parents) +
		",\n  webContentLink: " + file.WebContentLink +
		",\n }"
}

// NewDriveFile creates a DriveFile from a Drive file.
// It returns the DriveFile.
func NewDriveFile(f *drive.File) *DriveFile {
	return &DriveFile{
		f.Id,
		f.Name,
		f.MimeType,
		f.Parents,
		f.WebContentLink,
	}
}

// TrueParent finds the true parent of a DriveFile. Drive files often have
// multiple parents, and parents are crucial to knowing which files belong to
// issues.
// It returns the true parent.
func (f *drive.File) TrueParent(driveFileMap *map[string]*DriveFile) *DriveFile {
	
}
