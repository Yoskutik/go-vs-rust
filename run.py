from tqdm import tqdm
from ProcessMaker import ProcessMaker
from utils import *


timers = {
    "labels": [],
    10: [],
    100: [],
    1_000: [],
    10_000: [],
    100_000: [],
    1_000_000: [],
}

memory = {
    "labels": [],
    10: [],
    100: [],
    1_000: [],
    10_000: [],
    100_000: [],
    1_000_000: [],
}


def test(lang: str,folder: str, /, update_fn = None, max_routines: int = None):
    print(f'Test {folder}')
    timers["labels"].append(f'{lang}: {folder}')
    memory["labels"].append(f'{lang}: {folder}')

    lang = lang.lower()
    os.chdir(f'./{lang}/{folder}')
    if lang == 'rust':
        subprocess.run('cargo build -qr', shell=True)
    else:
        subprocess.run('go build .', shell=True)
    os.chdir('../../')
    
    for power in range(6):
        results = []
        mems = []
        n_routines = 10 ** (power + 1)
        if max_routines and n_routines > max_routines:
            timers[n_routines].append(-1)
            memory[n_routines].append(-1)
            continue
        for i in tqdm(range(8), desc=f'{n_routines:<9,}'):
            if update_fn is not None:
                update_fn()
            process = ProcessMaker(lang, folder, n_routines)
            results.append(process.result)
            mems.append(process.memory)
            time.sleep(process.result / 1_000_000)
        delete_last_line()
        result = min(results)
        secs = f'{(result / 1_000_000):,.3f}s'
        print(f"{n_routines:<9,}: {secs:<10}{max(mems):,.2f}Mb")
        timers[n_routines].append(result)
        memory[n_routines].append(max(mems))

    print()


if __name__ == '__main__':
    print('Preparing test data...')
    prepare_text_data()
    prepare_databases()
    print()

    for lang in ['Go', 'Rust']:
        print(f'Benchmarking {lang}')
        test(lang, '1. Sleep')
        test(lang, '2. Files R', update_fn=update_text_data)
        test(lang, '3. Files RW', update_fn=update_text_data, max_routines=100_000)
        os.environ['DATABASE_URL'] = f'sqlite:{os.getcwd()}/database.db'
        test(lang, '4. SQLite', update_fn=update_sqlite, max_routines=1_000)
        os.environ['DATABASE_URL'] = 'mysql://root:root@localhost/database'
        test(lang, '5. MySQL', update_fn=update_mysql, max_routines=100_000)
        print()

    save_data(timers, 'timers')
    save_data(memory, 'memory')
    print_results(timers, memory)
    cleanup()
