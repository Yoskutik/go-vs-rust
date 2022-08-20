import matplotlib.pyplot as plt
import pandas as pd
import shutil
import os


LABELS = [
    'Sleep',
    'Files R',
    'Files RW',
    'SQLite',
    'MySQL',
    'PostgreSQL',
]


def idx_to_name(idx: int) -> str:
    return f'{idx + 1}. {LABELS[idx]}'


def _create_blank_metric():
    return [
        pd.DataFrame(
            [],
            columns=['Go', 'Rust'],
            index=[10 ** x for x in range(6)],
        )
        for _ in range(6)
    ]


data = {
    'memory': _create_blank_metric(),
    'duration': _create_blank_metric(),
}


def save_data() -> None:
    for metric in ['memory', 'duration']:
        shutil.rmtree(f'results/{metric}', ignore_errors=True)
        os.mkdir(f'results/{metric}')

        plt.figure(figsize=[10, 6])
        plt.title(f'Rust to Go {metric} ratio', {'fontsize': 'xx-large'})
        plt.xticks(range(6), [f'$10^{x}$' for x in range(6)], parse_math=True, size='large')
        plt.yticks([])

        plt.hlines(1, 0, 5, linestyles='dotted', colors='g')
        plt.text(5, 1, 'Go', va='bottom', ha='right', size='xx-large', alpha=0.5)
        plt.text(5, 1, 'Rust', va='top', ha='right', size='xx-large', alpha=0.5)

        for i, df in enumerate(data[metric]):
            name = idx_to_name(i)
            path = f'results/{metric}/{name}'
            df.to_csv(f'{path}.csv')
            row = df.Rust / df.Go
            plt.plot(range(6), row, label=name)

        plt.legend()
        plt.savefig(f'results/{metric}.png', bbox_inches='tight')
