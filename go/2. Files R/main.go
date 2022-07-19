package main

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

func routine(fileIndex int, ch chan<- string) {
	path := fmt.Sprintf("./data/%d.txt", fileIndex)
	file, err := os.ReadFile(path)
	if err != nil {
		panic(err)
	}

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
	n, err := strconv.Atoi(os.Args[1])
	if err != nil {
		panic(err)
	}

	indices := lcg(n, 20)
	ch := make(chan string)

	start := time.Now()
	for i := 0; i < n; i++ {
		go routine(indices[i], ch)
	}

	list := make([]string, n)
	for i := 0; i < n; i++ {
		list[i] = <-ch
	}

	_ = len(list)

	fmt.Println(time.Since(start).Microseconds())
}
