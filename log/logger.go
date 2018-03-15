// Package log contains useful utilities for color print(f)ing.
package log

import (
	"github.com/fatih/color"

	"fmt"
)

var noticeFace = color.New(color.FgCyan)
var Notice, Noticef = noticeFace.PrintlnFunc(), noticeFace.PrintfFunc()

var fatalFace = color.New(color.FgRed).Add(color.Bold)
var Fatal, Fatalf = fatalFace.PrintlnFunc(), fatalFace.PrintfFunc()

var errorFace = color.New(color.FgRed).
var Error, Errorf = errorFace.PrintlnFunc(), errorFace.PrintfFunc()

var Info, Infof = fmt.Println, fmt.Printf
