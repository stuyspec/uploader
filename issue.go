package main

import (
	"google.golang.org/api/drive/v3"
	"fmt"
	"regexp"
	"strconv"
)

type Issue struct {
	SbcFolder *drive.File
	NewspaperPdf *drive.File
	PhotoFolder *drive.File
	ArtFolder *drive.File
	StaffEd *drive.File
	Photos []*drive.File
	Art []*drive.File
}

func NewIssue(volumeNum, issueNum int) *Issue {
	issue := new(Issue)

	// Get issue folder
	issueRange := "1-9"
	if issueNum > 9 {
		issueRange = "10-18"
	}
	volumeFolder := MustFindDriveFileByName(
		fmt.Sprintf("Volume %d No. %s", volumeNum, issueRange),
		"folder",
	)
	issueFolder := MustFindDriveFileByName(
		regexp.MustCompile(`Issue\s?`+strconv.Itoa(issueNum)),
		"folder",
		volumeFolder.Id,
	)

	// Find SBC, newspaper PDF, and staff-ed
	issue.SbcFolder = MustFindDriveFileByName("SBC", "folder", issueFolder.Id)
	issue.NewspaperPdf = MustFindDriveFileByName(
		regexp.MustCompile(`(?i)Issue\s?\d{1,2}(\.pdf)$`),
		"application/pdf",
		issueFolder.Id,
	)
	issue.StaffEd = MustFindDriveFileByName(
		regexp.MustCompile(`(?i)staff\s?ed`),
		"document",
		issue.SbcFolder.Id,
	)

	// Find photos and art
	photoFolder := MustFindDriveFileByName(
		regexp.MustCompile(`(?i)photo\s?color`),
		"folder",
		issueFolder.Id,
	)
	issue.Photos = DriveChildren(photoFolder.Id, "image")
	issue.PhotoFolder = photoFolder

	artFolder := MustFindDriveFileByName(
		"Art",
		"folder",
		issueFolder.Id,
	)
	issue.Art = DriveChildren(artFolder.Id, "image")
	issue.ArtFolder = artFolder

	return issue
}

