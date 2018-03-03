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

// InsertDriveFiles inserts DriveFile records into the DB.
func InsertDriveFiles(driveFiles *map[string]*driveclient.DriveFile) {
	insertDriveFileStmt.Exec()
}

// CloseDB closes the database.
func CloseDB() {
	db.Close()
}
