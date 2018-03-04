// Package driveclient contains useful functions for creating and interacting
// with the Drive client API.
package driveclient

import (
	"cli-uploader/drivefile"

	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/user"
	"path/filepath"

	"golang.org/x/net/context"
	"golang.org/x/oauth2"
	"golang.org/x/oauth2/google"
	"google.golang.org/api/drive/v3"

	"github.com/skratchdot/open-golang/open"
)

var driveService *drive.Service

// getClient uses a Context and Config to retrieve an auth Token
// then generate a Drive Client object. It returns the generated Client.
func getClient(ctx context.Context, config *oauth2.Config) *http.Client {
	cacheFile, err := tokenCacheFile()
	if err != nil {
		log.Fatalf("Unable to get path to cached credential file. %v", err)
	}
	tok, err := tokenFromFile(cacheFile)
	if err != nil {
		tok = getTokenFromWeb(config)
		saveToken(cacheFile, tok)
	}
	return config.Client(ctx, tok)
}

// getTokenFromWeb uses Config to request a Token to use with the Drive Client.
// It returns the retrieved Token.
func getTokenFromWeb(config *oauth2.Config) *oauth2.Token {
	authURL := config.AuthCodeURL("state-token", oauth2.AccessTypeOffline)
	open.Run(authURL) // opens authURL in default browser
	fmt.Printf("Type the authorization code: ")

	var code string
	if _, err := fmt.Scan(&code); err != nil {
		log.Fatalf("Unable to read authorization code %v", err)
	}

	tok, err := config.Exchange(oauth2.NoContext, code)
	if err != nil {
		log.Fatalf("Unable to retrieve token from web %v", err)
	}
	return tok
}

// tokenCacheFile generates credential file path/filename.
// It returns the generated credential path/filename.
func tokenCacheFile() (string, error) {
	usr, err := user.Current()
	if err != nil {
		return "", err
	}
	tokenCacheDir := filepath.Join(usr.HomeDir, ".credentials")
	os.MkdirAll(tokenCacheDir, 0700)
	return filepath.Join(tokenCacheDir,
		url.QueryEscape("drive-go-quickstart.json")), err
}

// tokenFromFile retrieves a Token from a given file path.
// It returns the retrieved Token and any read error encountered.
func tokenFromFile(file string) (*oauth2.Token, error) {
	f, err := os.Open(file)
	if err != nil {
		return nil, err
	}
	t := &oauth2.Token{}
	err = json.NewDecoder(f).Decode(t)
	defer f.Close()
	return t, err
}

// saveToken uses a file path to create a file and store the
// token in it.
func saveToken(file string, token *oauth2.Token) {
	fmt.Printf("Saving credential file to: %s\n", file)
	f, err := os.OpenFile(file, os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
	if err != nil {
		log.Fatalf("Unable to cache oauth token: %v", err)
	}
	defer f.Close()
	json.NewEncoder(f).Encode(token)
}

func init() {
	ctx := context.Background()

	b, readErr := ioutil.ReadFile("client_secret.json")
	if readErr != nil {
		log.Fatalf("Unable to read client secret file: %v", readErr)
	}

	// If modifying these scopes, delete your previously saved credentials
	// at ~/.credentials/drive-go-quickstart.json
	config, err := google.ConfigFromJSON(b, drive.DriveMetadataReadonlyScope)
	if err != nil {
		log.Fatalf("Unable to parse client secret file to config: %v", err)
	}
	httpClient := getClient(ctx, config)

	var driveErr error
	driveService, driveErr = drive.New(httpClient)
	if driveErr != nil {
		log.Fatalf("Unable to retrieve drive Client %v", driveErr)
	}
}

// ScanDriveFiles reads metadata on all Drive files from the Drive client.
// It returns the DriveFiles.
func ScanDriveFiles() map[string]*drivefile.DriveFile {
	driveFiles := map[string]*drivefile.DriveFile{
		"1cVqKaP6JVXHELBG2IEU5SEz1Xt9bLVZmrwtSLly_P7Y": drivefile.NewDriveFile(
			"1cVqKaP6JVXHELBG2IEU5SEz1Xt9bLVZmrwtSLly_P7Y",
			"[CLOSED] Issue9_News_BigSibConstitution",
			"application/vnd.google-apps.document",
			"",
			[]string{"1DSDSpkPIq_7R69BXO_pLwPKT-cxK0D8H"},
		),
		"1DSDSpkPIq_7R69BXO_pLwPKT-cxK0D8H": drivefile.NewDriveFile(
			"1DSDSpkPIq_7R69BXO_pLwPKT-cxK0D8H",
			"News",
			"application/vnd.google-apps.folder",
			"",
			[]string{"12OIh37WDtC2l-v5ifMTNxZNaHam-G5B1"},
		),
		"12OIh37WDtC2l-v5ifMTNxZNaHam-G5B1": drivefile.NewDriveFile(
			"12OIh37WDtC2l-v5ifMTNxZNaHam-G5B1",
			"SBC",
			"application/vnd.google-apps.folder",
			"",
			[]string{"1fuzEQFBcKBNiysFjaI_zzFN-jNVEPAS"},
		),
		"1fuzEQFBcKBNiysFjaI_zzFN-jNVEPAS": drivefile.NewDriveFile(
			"1fuzEQFBcKBNiysFjaI_zzFN-jNVEPAS",
			"Issue 9",
			"application/vnd.google-apps.folder",
			"",
			[]string{"0B_nzfPsNLo6oTEhVdmJNV1diY28"},
		),
		"0B_nzfPsNLo6oTEhVdmJNV1diY28": drivefile.NewDriveFile(
			"0B_nzfPsNLo6oTEhVdmJNV1diY28",
			"Volume 108 No. 1-9",
			"application/vnd.google-apps.folder",
			"",
			[]string{},
		),
	}
	return driveFiles

	/*
	// Loop through pages of files
	var nextPageToken string
	for {
		query := driveService.Files.List().PageSize(100).
			Fields("nextPageToken, " +
			"files(id, name, parents, mimeType, webContentLink)")
		if len(nextPageToken) > 0 {
			query = query.PageToken(nextPageToken)
		}

		r, err := query.Do()
		if err != nil {
			log.Fatalf("Unable to retrieve files: %v", err)
			break
		}

		if len(r.NextPageToken) == 0 {
			fmt.Println("No more files.")
			break
		}

		for _, f := range r.Files {
			driveFiles = append(driveFiles, NewDriveFile(f))
		}

		fmt.Printf("Scanned %d Drive files.\n", len(driveFiles))

		nextPageToken = r.NextPageToken
	}
*/
}

