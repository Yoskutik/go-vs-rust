use std::time::{Duration, Instant};

use tokio::task::JoinHandle;
use tokio::time::sleep;

async fn routine(millis: u64) -> f64 {
    let mut n: f64 = 0.;
    for i in 1..100_000 {
        if i % 2 == 0 {
            n /= i as f64;
            n += 1.;
        } else {
            n *= i as f64;
        }
    }
    sleep(Duration::from_millis(millis)).await;
    n
}

fn lcg(n: usize, max_value: i128) -> Vec<i32> {
    let mut list: Vec<i128> = Vec::with_capacity(n);
    list.push(42);

    let m = 0x7FFFFFFF;
    let a = 48271;
    let c = 0;
    for i in 1..n {
        list.push((list[i - 1] * a + c) % m);
        list[i - 1] = list[i - 1] % max_value;
    }
    list[n - 1] = list[n - 1] % max_value;

    list.iter().map(|it| *it as i32).collect()
}

#[tokio::main]
async fn main() {
    tokio::spawn(routine(1)).await.unwrap();

    let n = std::env::args().nth(1).unwrap().parse().unwrap();
    let generated = lcg(n, 300);
    let timers = generated.iter();

    tokio::spawn(routine(0)).await.unwrap();
    let start = Instant::now();

    let handles: Vec<JoinHandle<_>> = timers.map(|i| {
        tokio::spawn(routine(*i as u64))
    }).collect();

    for handle in handles {
        handle.await.unwrap();
    }

    println!("{:?}", start.elapsed().as_micros());
}
