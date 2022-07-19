package main

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

func routine(millis int, ch chan<- float64) {
	var n float64 = 0
	for i := 0; i < 100_000; i++ {
		if i%2 == 0 {
			n /= float64(i)
			n += 1.0
		} else {
			n *= float64(i)
		}
	}
	time.Sleep(time.Duration(millis) * time.Millisecond)
	ch <- n
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

	timers := lcg(n, 300)
	ch := make(chan float64)

	start := time.Now()
	for i := 0; i < n; i++ {
		go routine(timers[i], ch)
	}

	list := make([]float64, n)
	for i := 0; i < n; i++ {
		list[i] = <-ch
	}

	_ = len(list)

	fmt.Println(time.Since(start).Microseconds())
}
