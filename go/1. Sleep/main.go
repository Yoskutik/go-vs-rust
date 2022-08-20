package main

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

func routine(millis int, ch chan<- float64) {
	var n float64 = 0
	for i := 0; i < 50_000; i++ {
		if n > 1000 {
			n /= 850
		}
		n *= 4
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

	start := time.Now()
	var chs []chan float64
	for i := 0; i < n; i++ {
		ch := make(chan float64, 1)
		chs = append(chs, ch)
		go routine(timers[i], ch)
	}

	list := make([]float64, n)
	for i := 0; i < n; i++ {
		list[i] = <-chs[i]
	}

	_ = len(list)

	fmt.Println(time.Since(start).Microseconds())
}
