import logging
import sys
from datetime import datetime
from tqdm import tqdm
from utils import *
from data import data, idx_to_name, save_data


shutil.rmtree(f'results', ignore_errors=True)
os.mkdir(f'results')

logger = logging.getLogger()
logger.addHandler(logging.FileHandler('results/output.log', mode='w'))
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)


UPDATE_FNS = [
    None,
    update_text_data,
    update_text_data,
    update_sqlite,
    update_mysql,
    update_postgresql,
]


def test(lang: str, idx: int, max_routines: int = None):
    folder = idx_to_name(idx)
    logger.info(f'Test {folder}')

    os.chdir(f'./{lang.lower()}/{folder}')
    if lang == 'Rust':
        subprocess.run('cargo build -qr', shell=True)
    else:
        subprocess.run('go build .', shell=True)
    os.chdir('../../')
    logger.info('Build done.')
    
    for power in range(6):
        durations = []
        memories = []
        n_routines = 10 ** (power + 1)
        if max_routines and n_routines > max_routines:
            continue
        for i in tqdm(range(9 - power), desc=f'{n_routines:<9,}'):
            if UPDATE_FNS[idx]:
                UPDATE_FNS[idx]()
            try:
                duration, mem = get_process_info(lang.lower(), folder, n_routines)
                time.sleep(duration / 1_000_000)
            except ValueError:
                duration, mem = sys.maxsize, -1
            durations.append(duration)
            memories.append(mem)
        delete_last_line()
        duration = min(durations)
        logger.info(f"{n_routines:<9,}: {(duration / 1_000_000):<8,.2f}{max(memories):,.2f}")
        data['duration'][idx].loc[n_routines, lang] = duration
        data['memory'][idx].loc[n_routines, lang] = max(memories)

    logger.info('')


if __name__ == '__main__':
    now = datetime.now()
    startup()

    for lang in ['Go', 'Rust']:
        logger.info(f'Benchmarking {lang}')
        for x in range(6):
            test(lang, x, 1_000 if x == 3 else None)
        logger.info('')

    save_data()
    print_results()
    cleanup()

    logger.info(f'Total time elapsed: {datetime.now() - now}')
