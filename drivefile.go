package main

import (
	"google.golang.org/api/drive/v3"
	"fmt"
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
