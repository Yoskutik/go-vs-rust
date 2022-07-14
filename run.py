import subprocess
import shutil
import time
import csv
import sys
import os

from tqdm import tqdm


data = {
    "labels": [],
    10: [],
    100: [],
    1000: [],
    10000: [],
    100000: [],
    1000000: [],
}


def delete_last_line():
    sys.stdout.write('\x1b[1A')
    sys.stdout.write('\x1b[2K')


def test(label: str, lang: str, dir: str, update_data: bool = False):
    print(label)
    data["labels"].append(f'{lang}: {dir}')

    lang = lang.lower()
    os.chdir(f'./{lang}/{dir}')
    if lang == 'rust':
        subprocess.run(['cargo', 'build', '--release'], shell=True)
    else:
        subprocess.run(['go', 'build', '.'], shell=True)
    os.chdir('../../')
    
    for power in range(6):
        results = []
        n_routines = 10 ** (power + 1)
        for i in tqdm(range(7), desc=f'{n_routines:<9,}'):
            if update_data:
                shutil.rmtree('data', ignore_errors=True)
                shutil.unpack_archive('data.zip', 'data')
            prefix = 'target/release/' if lang == 'rust' else ''
            microsecs = int(subprocess.check_output([f'./{lang}/{dir}/{prefix}coroutine.exe', str(n_routines)], shell=True))
            results.append(microsecs)
            time.sleep(microsecs / 1000000)
        delete_last_line()
        result = min(results)
        print(f"{n_routines:<9,}: {result}")
        data[n_routines].append(result)

    print()


for lang in ['Rust', 'Go']:
    print(f'Benchmarking {lang}')
    test('Test 1. With sleeping', lang, '1. Sleep')
    test('Test 2. Reading files', lang, '2. Files R', True)
    test('Test 3. Reading + writting files', lang, '3. Files RW', True)
    print()

with open('results.csv', 'w') as file:
    writer = csv.writer(file, delimiter=';', lineterminator='\n')
    writer.writerow(['n_routines'] + data['labels'])
    for power in range(6):
        n_routines = 10 ** (power + 1)
        writer.writerow([n_routines] + data[n_routines])