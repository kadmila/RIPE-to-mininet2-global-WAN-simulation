package main

import (
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"math"
	"os"
	"path/filepath"
)

type LatencyInfo struct {
	Mean   float64
	StdDev float64
}

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

	dictionary := make(map[uint64][]float32)

	// Process each file
	for _, filePath := range filePaths {
		err := processFile(filePath, dictionary)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error processing %s: %v\n", filePath, err)
			continue
		}
	}

	fmt.Printf("Dictionary has %d unique address pairs.\n", len(dictionary))

	// TODO: uint64 key -> ip address -> city -> link
	result := make(map[uint64]LatencyInfo)
	c := 0
	for key, value := range dictionary {
		mean, stddev, err := SigmaClipMeanStdDev(value, 3, 3)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			os.Exit(1)
		}
		result[key] = LatencyInfo{Mean: mean, StdDev: stddev}
		c++
		if c < 10 {
			fmt.Printf("mean: %fmS, stddev: %fmS\n", mean, stddev)
		}
	}
}

func processFile(filename string, dictionary map[uint64][]float32) error {
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

			// Read floats directly as uint32, then convert
			rtt1 := float32frombits(buffer[offset:])
			rtt2 := float32frombits(buffer[offset+4:])
			rtt3 := float32frombits(buffer[offset+8:])

			// Read addresses
			dstAddr := binary.NativeEndian.Uint32(buffer[offset+12:])
			srcAddr := binary.NativeEndian.Uint32(buffer[offset+16:])

			// Create key with smaller address first
			var key uint64
			if dstAddr < srcAddr {
				key = (uint64(dstAddr) << 32) | uint64(srcAddr)
			} else {
				key = (uint64(srcAddr) << 32) | uint64(dstAddr)
			}

			// Append all three RTTs at once
			dictionary[key] = append(dictionary[key], rtt1, rtt2, rtt3)
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

func SigmaClipMeanStdDev(
	data []float32,
	k float64,
	maxIter int,
) (mean, stddev float64, err error) {
	for iter := 0; iter < maxIter; iter++ {
		n := float64(len(data))
		if n == 0 {
			err = errors.New("empty")
			return
		}

		// Mean
		mean = 0
		for _, v := range data {
			mean += float64(v)
		}
		if math.IsInf(mean, 0) {
			err = errors.New("overflow - sum")
			return
		}
		mean /= n

		// Stddev (MLE)
		stddev = 0
		for _, v := range data {
			diff := float64(v) - mean
			stddev += diff * diff
		}
		if math.IsInf(stddev, 0) {
			err = errors.New("overflow - stddev")
			return
		}
		stddev = math.Sqrt(stddev / n)

		// Clip
		filtered := make([]float32, 0, len(data)) // 필수: 길이 할당
		threshold := k * stddev
		for _, v := range data {
			if math.Abs(float64(v)-mean) <= threshold {
				filtered = append(filtered, v)
			}
		}

		// Converged?
		if len(filtered) == len(data) {
			break
		}

		data = filtered
	}

	return
}

func float32frombits(b []byte) float32 {
	bits := binary.NativeEndian.Uint32(b)
	return math.Float32frombits(bits)
}
