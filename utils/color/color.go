// Package colors provides access to color outputs.
package color

import (
	github.com/fatih/color
)

var Warning = color.New(color.FgRed).PrintfFunc()
