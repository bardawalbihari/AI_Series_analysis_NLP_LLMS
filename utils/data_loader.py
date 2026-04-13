from glob import glob
import os

import pandas as pd


def _extract_episode_number(path):
    filename = os.path.basename(path)
    return int(filename.split('-')[-1].split('.')[0].strip())


def _load_ass_script(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()[27:]
    dialogue_lines = [",".join(line.split(',')[9:]).strip() for line in lines if line.strip()]
    return " ".join(line.replace('\\N', ' ') for line in dialogue_lines)


def _load_srt_script(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()

    dialogue_lines = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.isdigit() or '-->' in line:
            continue
        dialogue_lines.append(line)

    return " ".join(dialogue_lines)


def load_subtitles_dataset(dataset_path):
    subtitles_paths = sorted(glob(dataset_path + '/*.ass') + glob(dataset_path + '/*.srt'))

    scripts = []
    episode_num = []

    for path in subtitles_paths:
        if path.endswith('.ass'):
            script = _load_ass_script(path)
        else:
            script = _load_srt_script(path)

        scripts.append(script)
        episode_num.append(_extract_episode_number(path))

    df = pd.DataFrame.from_dict({"episode": episode_num, "script": scripts})
    return df.sort_values('episode').reset_index(drop=True)