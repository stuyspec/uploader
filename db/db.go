// Package db contains functions for interacting with the PostgreSQL database.
package db

import (
	"../driveclient"

	"log"

	"database/sql"
	_ "github.com/lib/pq"
)

var db *sql.DB
var insertDriveFileStmt *sql.Stmt

func init() {
	InitDB("user=stuyspecweb dbname=stuy-spec-uploader sslmode=disable")

	var error err
	insertDriveFileStmt, err = db.Prepare("INSERT INTO " +
		"(DriveFileID, Filename, MimeType, WebContentLink, ParentID) " +
		"VALUES(?, ?, ?, ?, ?)")
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
