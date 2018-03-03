// Package db contains functions for interacting with the PostgreSQL database.
package db

import (
	"../drivefile"

	"log"

	"database/sql"
	_ "github.com/lib/pq"
)

var db *sql.DB
var insertDriveFileStmt, insertDriveFileWithParentStmt, findDriveFileStmt *sql.Stmt

func init() {
	InitDB("user=stuyspecweb dbname=stuy-spec-uploader sslmode=disable")

	var err error
	insertDriveFileStmt, err = db.Prepare(
		`INSERT INTO DriveFiles (DriveFileID, Filename, MimeType, WebContentLink)
VALUES ($1, $2, $3, $4);`)
	if err != nil {
		log.Fatalf("Unable to prepare insert statement. %v", err)
	}

	insertDriveFileWithParentStmt, err = db.Prepare(
		`INSERT INTO DriveFiles (DriveFileID, Filename, MimeType, WebContentLink, ParentID)
VALUES ($1, $2, $3, $4, $5);`)
	if err != nil {
		log.Fatalf("Unable to prepare insert statement. %v", err)
	}

	findDriveFileStmt, err = db.Prepare(
		`SELECT Filename from DriveFiles WHERE DriveFileID = $1`)
	if err != nil {
		log.Fatalf("Unable to prepare insert statement. %v", err)
	}
}

// InitDB opens the database, preparing it for later use.
func InitDB(dataSourceName string) {
    var err error
    db, err = sql.Open("postgres", dataSourceName)
    if err != nil {
        log.Panic(err)
    }

    if err = db.Ping(); err != nil {
        log.Panic(err)
    }
}

// InsertDriveFile inserts a Drive file after creating its parents.
func InsertDriveFile(
	file *drivefile.DriveFile,
	driveFileMap *map[string]*drivefile.DriveFile) {

	log.Printf("Inserting %s.", file.Name)

	parent, parentErr := file.TrueParent(driveFileMap)
	if parentErr || parent == nil {
		// No parent found.
		_, err := insertDriveFileStmt.Exec(
			file.Id,
			file.Name,
			file.MimeType,
			file.WebContentLink,
		)
		if err != nil {
			log.Printf("Unable to execute insert statement. %v\n", err)
		}
	} else {
		err := findDriveFileStmt.QueryRow(parent.Id).Scan()
		if err != nil {
			_, ok := (*driveFileMap)[parent.Id]
			if ok {
				// No parent exists in the database, but we found a parent in Drive.
				InsertDriveFile(parent, driveFileMap)
			}
		}
		_, err = insertDriveFileWithParentStmt.Exec(
			file.Id,
			file.Name,
			file.MimeType,
			file.WebContentLink,
			parent.Id,
		)
		if err != nil {
			log.Printf("Unable to execute insert statement. %v\n", err)
		}
	}
}

// InsertDriveFiles inserts DriveFile records into the DB.
func InsertDriveFiles(driveFiles *map[string]*drivefile.DriveFile) {
	for _, driveFile := range *driveFiles {
		InsertDriveFile(driveFile, driveFiles)
	}
}

// CloseDB closes the database and all connections/resources.
func CloseDB() {
	insertDriveFileStmt.Close()
	findDriveFileStmt.Close()
	db.Close()
}
