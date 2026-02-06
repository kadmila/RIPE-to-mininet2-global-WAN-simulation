package main

import (
	"encoding/binary"
	"fmt"
	"io"
	"net/netip"
	"os"
	"path/filepath"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: program <directory>")
		return
	}

	dirPath := os.Args[1]

	// Read all files in the directory
	files, err := os.ReadDir(dirPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading directory: %v\n", err)
		os.Exit(1)
	}

	var filePaths []string
	for _, file := range files {
		// Skip directories, only include files
		if file.IsDir() {
			continue
		}
		filePaths = append(filePaths, filepath.Join(dirPath, file.Name()))
	}

	dictionary := make(map[uint32]bool)

	// Process each file
	for _, filePath := range filePaths {
		err := processFile(filePath, dictionary)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error processing %s: %v\n", filePath, err)
			continue
		}
	}

	for address, _ := range dictionary {
		var bytes [4]byte
		binary.NativeEndian.PutUint32(bytes[:], address)
		addr := netip.AddrFrom4(bytes)
		fmt.Printf("%s\n", addr.String())
	}
	fmt.Printf("Dictionary has %d unique address.\n", len(dictionary))
}

func processFile(filename string, dictionary map[uint32]bool) error {
	file, err := os.Open(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	const structSize = 20
	buffer := make([]byte, structSize*1024*1024) // 10MB buffer

	for {
		n, err := file.Read(buffer)
		if n == 0 {
			break
		}

		count := n / structSize
		for i := range count {
			offset := i * structSize

			dstAddr := binary.NativeEndian.Uint32(buffer[offset+12:])
			srcAddr := binary.NativeEndian.Uint32(buffer[offset+16:])
			dictionary[dstAddr] = false
			dictionary[srcAddr] = false
		}

		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}
	}
	return nil
}
