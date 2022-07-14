package main

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

func routine(fileIndex int, ch chan<- string) {
	path := fmt.Sprintf("./data/%d.txt", fileIndex)

	if fileIndex%2 == 0 {
		file, _ := os.OpenFile(path, os.O_APPEND, 0666)
		file.WriteString("Appended string\n")
	}

	file, _ := os.ReadFile(path)
	ch <- string(file)
}

func lcg(n, maxValue int) []int {
	timers := make([]int, n)
	timers[0] = 42

	m := 0x7FFFFFFF
	a := 48271
	c := 0
	for i := 1; i < n; i++ {
		timers[i] = (timers[i-1]*a + c) % m
		timers[i-1] = timers[i-1] % maxValue
	}
	timers[n-1] = timers[n-1] % maxValue

	return timers
}

func main() {
	n, _ := strconv.Atoi(os.Args[1])

	indices := lcg(n, 20)
	ch := make(chan string)
	list := make([]string, n)

	start := time.Now()
	for i := 0; i < n; i++ {
		go routine(indices[i], ch)
	}
	for i := 0; i < n; i++ {
		list[i] = <-ch
	}
	fmt.Println(time.Since(start).Microseconds())
}
