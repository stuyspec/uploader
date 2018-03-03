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
func (f *drive.File) TrueParent(driveFileMap *map[string]*DriveFile) (parent *DriveFile, err error) {
	parents := f.Parents
	for i := 0; i < len(parents); i++ {
		_, ok := (*driveFileMap)[parents[i]]
		if !ok {
			// If no such parent exists, remove the parentID
			parents = append(parents[:i], parents[i+1:])
		}
	}

	if len(parents) < 2 {
		if len(parents) == 1 {
			parent = parents[0]
		} else {
			err = log.Output(1, "No parent found.")
		}
		return
	}

	// If the file is an image, we want the parent that is a Photo/Art folder.
	if strings.Contain(f.MimeType, "image") {
		
	} else if strings.Contain(f.Mime)
}
