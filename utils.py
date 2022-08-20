import subprocess
import logging
import platform
import cpuinfo
import signal
import psutil
import time
import sys
import os
import pandas as pd
from prepare import *
from data import idx_to_name, data


def delete_last_line() -> None:
    sys.stdout.write('\x1b[1A')
    sys.stdout.write('\x1b[2K')


def _print_result(idx: int) -> None:
    def get_item(lang: str, n_routines: int) -> str:
        duration = data['duration'][idx].loc[n_routines, lang] / 1_000_000
        memory = data['memory'][idx].loc[n_routines, lang]
        duration_text = f'{duration:.3f}s' if duration < 60 else f'{(duration / 60):.3f}m'
        memory_text = f'{(memory / 1024):.2f}Gb' if memory > 1000 else f'{memory:.2f}Mb'
        return f'| {duration_text:<7} | {memory_text:<8} '

    def get_diff(n_routines: int) -> str:
        df_duration = data['duration'][idx]
        dur_diff = df_duration.loc[n_routines, 'Rust'] / df_duration.loc[n_routines, 'Go'] * 100 - 100
        dur_diff = f'{"+" if dur_diff > 0 else ""}{dur_diff:.1f}%'

        df_memory = data['memory'][idx]
        mem_diff = df_memory.loc[n_routines, 'Rust'] / df_memory.loc[n_routines, 'Go'] * 100 - 100
        mem_diff = f'{"+" if mem_diff > 0 else ""}{mem_diff:.1f}%'

        return f'| {dur_diff:<7} | {mem_diff:<7} |'

    def p(n: int) -> str:
        return '+' + '-' * n

    logger = logging.getLogger()
    logger.info(f'{idx_to_name(idx)} results:')
    logger.info(f'{p(11)}{p(20)}{p(20)}{p(19)}+')
    logger.info('| routines  ' + '|' + ' Rust' + ' ' * 15 + '|' + ' Go' + ' ' * 17 + '| Ratio' + ' ' * 13 + '|')
    logger.info(f'{p(11)}{p(9)}{p(10)}{p(9)}{p(10)}{p(9)}{p(9)}+')

    for x in range(6):
        n_routines = 10 ** (x + 1)
        if pd.isna(data['duration'][idx].loc[n_routines, 'Go']):
            break
        logger.info(f'| {n_routines:<9,} {get_item("Rust", n_routines)}{get_item("Go", n_routines)}{get_diff(n_routines)}')
    logger.info(f'{p(11)}{p(9)}{p(10)}{p(9)}{p(10)}{p(9)}{p(9)}+')
    logger.info('')


def print_results() -> None:
    for x in range(6):
        _print_result(x)


def _get_usage(process):
    try:
        children = process.children()
        if len(children) == 0:
            return process.memory_info().rss
        total = 0
        for x in children:
            total += _get_usage(x)
        return total
    except psutil.NoSuchProcess:
        return 0


def startup():
    prepare_data()
    print()

    logger = logging.getLogger()
    logger.info('System info:')
    info = cpuinfo.get_cpu_info()
    logger.info(f'CPU: {info["brand_raw"]}, {os.cpu_count()} cores x {info["hz_advertised_friendly"]}')
    logger.info(f'RAM: {(psutil.virtual_memory().total / 1024 / 1024 / 1024):.2f}GiB')
    uname = platform.uname()
    logger.info(f'OS: {uname.system}, v. {uname.version}, {uname.machine}')
    logger.info(f'Arch: {platform.architecture()[0]}')
    logger.info('')


def get_process_info(lang: str, folder: str, n_routines: int):
    prefix = 'target/release/' if lang == 'rust' else ''
    cmd = [f'{lang}/{folder}/{prefix}coroutine.exe', str(n_routines)] if os.name == 'nt' \
        else f'"{lang}/{folder}/{prefix}coroutine" {n_routines}'
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    memory = 0
    try:
        while process.poll() is None:
            try:
                usage = _get_usage(psutil.Process(process.pid))
            except psutil.NoSuchProcess:
                usage = 0
            memory = max(memory, usage)
            time.sleep(0.001)
    except KeyboardInterrupt:
        os.kill(process.pid, signal.SIGTERM)

    result = int(process.communicate()[0])
    memory = memory / 1_000_000 if memory > 0 else pd.NA

    return result, memory
