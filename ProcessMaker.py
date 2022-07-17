import subprocess
import signal
import psutil
import time
import os


class ProcessMaker:
    def __init__(self, lang: str, folder: str, n_routines: int):    
        path = f'results/{lang}/{folder}'
        os.makedirs(path, exist_ok=True)

        prefix = 'target/release/' if lang == 'rust' else ''
        process = subprocess.Popen(
            [f'./{lang}/{folder}/{prefix}coroutine.exe', str(n_routines)],
            shell=True,
            stdout=subprocess.PIPE,
        )
        
        try:
            with open(f'{path}/{n_routines}.csv', 'w') as file:
                memory = 0
                while process.poll() is None:
                    try:
                        usage = ProcessMaker._get_usage(psutil.Process(process.pid))
                    except psutil.NoSuchProcess:
                        usage = 0
                    file.write(f'{usage}\n')
                    memory = max(memory, usage)
                    time.sleep(.1)
        except KeyboardInterrupt:
            os.kill(process.pid, signal.SIGTERM)
        
        self.result = int(process.communicate()[0])
        self.memory = memory / 1024 / 1024
        
    @staticmethod
    def _get_usage(process):
        children = process.children()
        try:
            if len(children) == 0:
                return process.memory_info().rss
            total = 0
            for x in children:
                total += ProcessMaker._get_usage(x)
            return total
        except psutil.NoSuchProcess:
            return 0
