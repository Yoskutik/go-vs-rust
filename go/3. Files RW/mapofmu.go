// This code has been taken from SO answer: https://stackoverflow.com/a/62562831/11589183

package main

import (
	"fmt"
	"sync"
)

type M struct {
	ml sync.Mutex
	ma map[interface{}]*mentry
}

type mentry struct {
	m   *M
	el  sync.Mutex
	cnt int
	key interface{}
}

type Unlocker interface {
	Unlock()
}

func New() *M {
	return &M{ma: make(map[interface{}]*mentry)}
}

func (m *M) Lock(key interface{}) Unlocker {
	m.ml.Lock()
	e, ok := m.ma[key]
	if !ok {
		e = &mentry{m: m, key: key}
		m.ma[key] = e
	}
	e.cnt++
	m.ml.Unlock()
	e.el.Lock()
	return e
}

func (me *mentry) Unlock() {
	m := me.m
	m.ml.Lock()
	e, ok := m.ma[me.key]
	if !ok {
		m.ml.Unlock()
		panic(fmt.Errorf("Unlock requested for key=%v but no entry found", me.key))
	}
	e.cnt--
	if e.cnt < 1 {
		delete(m.ma, me.key)
	}
	m.ml.Unlock()
	e.el.Unlock()
}
