package main

import (
	"database/sql"
	"fmt"
	_ "github.com/lib/pq"
	"os"
	"strconv"
	"strings"
	"time"
)

func routine(db *sql.DB, age, id int, ch chan<- string) {
	if age%2 == 0 {
		queryUpdate := fmt.Sprintf("UPDATE users SET salary = salary + 1 WHERE id = %d", id)
		db.Exec(queryUpdate)

		querySelect := fmt.Sprintf("SELECT salary FROM users WHERE id = %d", id)
		var salary string
		db.QueryRow(querySelect).Scan(&salary)
		ch <- fmt.Sprintf("%d: %s", id, salary)
	} else {
		query := fmt.Sprintf("SELECT salary FROM users WHERE age = %d ORDER BY id", age)
		rows, err := db.Query(query)
		if err != nil {
			panic(err)
		}
		defer rows.Close()

		var salaries []string
		for rows.Next() {
			var salary string
			rows.Scan(&salary)
			salaries = append(salaries, salary)
		}

		ch <- strings.Join(salaries, ", ")
	}
}

func lcg(n, maxValue, seed int) []int {
	timers := make([]int, n)
	timers[0] = seed

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

	ages := lcg(n, 100, 42)
	ids := lcg(n, 10_000, 17)

	db, err := sql.Open("postgres", "postgresql://root:root@localhost/db?sslmode=disable")
	if err != nil {
		panic(err)
	}
	db.SetMaxOpenConns(100)
	db.SetConnMaxLifetime(time.Second * 600)
	defer db.Close()

	start := time.Now()
	var chs []chan string
	for i := 0; i < n; i++ {
		ch := make(chan string, 1)
		chs = append(chs, ch)
		go routine(db, ages[i], ids[i], ch)
	}

	list := make([]string, n)
	for i := 0; i < n; i++ {
		list[i] = <-chs[i]
	}

	_ = len(list)

	fmt.Println(time.Since(start).Microseconds())
}
