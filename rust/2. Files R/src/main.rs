use std::time::Instant;

use tokio::task::JoinHandle;
use tokio::fs;

async fn routine(file_index: i32) -> String {
    let path = format!("./data/{file_index}.txt");
    fs::read_to_string(path).await.unwrap()
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
    let generated = lcg(n, 20);
    let indices = generated.iter();

    let start = Instant::now();

    let handles: Vec<JoinHandle<_>> = indices.map(|i| {
        tokio::spawn(routine(*i))
    }).collect();

    for handle in handles {
        handle.await.unwrap();
    }

    println!("{:?}", start.elapsed().as_micros());
}
