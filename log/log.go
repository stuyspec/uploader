// Package log contains useful utilities for color print(f)ing.
package log

import (
	"github.com/fatih/color"

	"fmt"
	"os"
)

var headerFace = color.New(color.FgCyan).Add(color.Underline).Add(color.Bold)
var Header, Headerf = headerFace.PrintlnFunc(), headerFace.PrintfFunc()

var noticeFace = color.New(color.FgCyan)
var Notice, Noticef = noticeFace.PrintlnFunc(), noticeFace.PrintfFunc()

var fatalFace = color.New(color.FgRed).Add(color.Bold)
func Fatal(a ...interface{}) {
	fatalFace.Println(a...)
	os.Exit(1)
}
func Fatalf(format string, a ...interface{}) {
	fatalFace.Printf(format, a...)
	os.Exit(1)
}

var errorFace = color.New(color.FgRed)
var Error, Errorf = errorFace.PrintlnFunc(), errorFace.PrintfFunc()

var promptFace = color.New(color.FgYellow)
var Prompt, Promptf = promptFace.PrintlnFunc(), promptFace.PrintfFunc()

var infoFace = color.New(color.FgGreen)
var Info, Infof = infoFace.PrintlnFunc(), infoFace.PrintfFunc()

var Println, Printf = fmt.Println, fmt.Printf
