use std::error::Error;
use std::time::Instant;
use tokio::task::JoinHandle;
use sqlx::sqlite::SqlitePool;

async fn routine(pool: &SqlitePool, age: i32, id: i32) -> Result<String, Box<dyn Error>> {
    if age % 2 == 0 {
        sqlx::query!("UPDATE users SET salary = salary + 1 WHERE id = ?1", id)
            .execute(pool)
            .await?;
        let row = sqlx::query!("SELECT salary FROM users WHERE id = ?1", id)
            .fetch_one(pool)
            .await?;
        Ok(format!("{}: {}", id, row.salary))
    } else {
        let res = sqlx::query!("SELECT salary FROM users WHERE age = ?1 ORDER BY id", age)
            .fetch_all(pool)
            .await?
            .iter()
            .map(|it| it.salary.to_string())
            .collect::<Vec<String>>()
            .join(", ");
        Ok(res)
    }
}

fn lcg(n: usize, max_value: i128, seed: i128) -> Vec<i32> {
    let mut list: Vec<i128> = Vec::with_capacity(n);
    list.push(seed);

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
    let n = std::env::args().nth(1).unwrap().parse().unwrap();
    let pool = SqlitePool::connect("sqlite://database.db").await.unwrap();
    let ages = lcg(n, 100, 42);
    let ids = lcg(n, 10_000, 17);

    let start = Instant::now();
    let handles: Vec<JoinHandle<_>> = (0..n).map(|i| {
        let pool = pool.clone();
        let age = ages[i];
        let id = ids[i];
        tokio::spawn(async move {
            routine(&pool, age, id).await.unwrap()
        })
    }).collect();

    for handle in handles {
        handle.await.unwrap();
    }

    println!("{:?}", start.elapsed().as_micros());
}
