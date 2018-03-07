// Package colors provides access to color outputs.
package color

import (
	"github.com/fatih/color"
)

// These are all functions that print the passed arguments as colorized with
// color.Printf().

var Info = color.New(color.FgCyan).PrintfFunc()

var Success = color.New(color.FgGreen).Add(color.Bold).PrintfFunc()

var Danger = color.New(color.FgRed).Add(color.Bold).PrintfFunc()
