DROP TABLE IF EXISTS DriveFiles;

CREATE TABLE DriveFiles (
       DriveFileID varchar(63) NOT NULL PRIMARY KEY,
       Filename text NOT NULL,
       MimeType varchar(63) NOT NULL,
       WebContentLink text,
       ParentID varchar(63),
       FOREIGN KEY (ParentID) REFERENCES DriveFiles (DriveFileID)
);
