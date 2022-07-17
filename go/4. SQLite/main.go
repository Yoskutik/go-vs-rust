package main

import (
	"database/sql"
	"fmt"
	_ "github.com/mattn/go-sqlite3"
	"os"
	"strconv"
	"strings"
	"time"
)

func routine(db *sql.DB, age, id int, ch chan<- string) {
	if age%2 == 0 {
		update, _ := db.Prepare("UPDATE users SET salary = salary + 1 WHERE id = (?)")
		defer update.Close()
		update.Exec(id)

		get, _ := db.Prepare("SELECT salary FROM users WHERE id = (?)")
		defer get.Close()
		var salary string
		get.QueryRow(id).Scan(&salary)
		ch <- salary
	} else {
		rows, _ := db.Query("SELECT salary FROM users WHERE age = 10 ORDER BY id")
		defer rows.Close()

		salaries := []string{}
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
	n, _ := strconv.Atoi(os.Args[1])

	ages := lcg(n, 100, 42)
	ids := lcg(n, 10_000, 42)
	ch := make(chan string)
	list := make([]string, n)

	db, _ := sql.Open("sqlite3", "database.db")
	defer db.Close()

	start := time.Now()
	for i := 0; i < n; i++ {
		go routine(db, ages[i], ids[i], ch)
	}
	for i := 0; i < n; i++ {
		list[i] = <-ch
	}
	fmt.Println(time.Since(start).Microseconds())
}
