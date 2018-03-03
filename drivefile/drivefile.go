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
	WebContentLink string
	Parents []string
}

func (file *DriveFile) String() string {
	return "{\n" +
		"  id: " + file.Id +
		",\n  name: " + file.Name +
		",\n  mimeType: " + file.MimeType +
		",\n  webContentLink: " + file.WebContentLink +
		",\n  parents: " + fmt.Sprint(file.Parents) +
		",\n }"
}

// NewDriveFile creates a DriveFile from a Drive file.
// It returns the DriveFile.
func NewDriveFile(
	id,
	name,
	mimeType,
	webContentLink string,
	parents []string) *DriveFile {
	return &DriveFile{
		id,
		name,
		mimeType,
		webContentLink,
		parents,
	}
}

// NewDriveFileFromDrive creates a DriveFile from a Drive file.
func NewDriveFileFromDrive(file *drive.File) *DriveFile {
	return NewDriveFile(
		file.Id,
		file.Name,
		file.MimeType,
		file.WebContentLink,
		file.Parents,
	)
}

// TrueParent finds the true parent of a DriveFile. Drive files often have
// multiple parents, and parents are crucial to knowing which files belong to
// issues.
// It returns the true parent.
func (f *DriveFile) TrueParent(driveFileMap *map[string]*DriveFile) (parent *DriveFile, err bool) {
	parents := f.Parents
	for i := 0; i < len(parents); i++ {
		_, ok := (*driveFileMap)[parents[i]]
		if !ok {
			// If no such parent exists, remove the parentID
			parents = append(parents[:i], parents[i+1:]...)
		}
	}

	if len(parents) < 2 {
		if len(parents) == 1 {
			parent = (*driveFileMap)[parents[0]]
		} else {
			err = true
		}
		return
	}

	// If the file is an image, we want the parent that is a Photo/Art folder.
	if strings.Contains(f.MimeType, "image") {

	}

	err = true
	return
}
