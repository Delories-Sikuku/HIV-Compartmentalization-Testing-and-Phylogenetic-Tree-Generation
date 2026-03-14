import json
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

DATA_DIR = Path("data")
OUTPUT_DIR = Path("tests_output")
CONFIG_FILE = "tests_config.json"
DATASET_FILE = "datasets.txt"

OUTPUT_DIR.mkdir(exist_ok=True)

config = json.load(open(CONFIG_FILE))

datasets = [x.strip() for x in open(DATASET_FILE) if x.strip()]


def run_test(dataset, test):

    alignment = DATA_DIR / f"{dataset}-Alignment.nex"
    tree = DATA_DIR / f"{dataset}-Alignment-tree.newick"

    answers = []

    # navigate hyphy menu
    answers.extend(test["menu_path"])

    # feed inputs
    for inp in test["inputs"]:

        value = inp["value"]

        value = value.replace("{alignment}", str(alignment))
        value = value.replace("{tree}", str(tree))

        answers.append(value)

    answers.append("")  # return to menu

    log_file = OUTPUT_DIR / f"{dataset}_{test['name']}.log"

    print(f"Running {test['name']} for {dataset}")

    with open(log_file, "w") as log:
        subprocess.run(
            ["hyphy"],
            input="\n".join(answers) + "\n",
            text=True,
            stdout=log,
            stderr=log
        )

    return f"{dataset} {test['name']} completed"


def jobs():
    for dataset in datasets:
        for test in config["tests"]:
            yield dataset, test


def worker(args):
    return run_test(*args)


if __name__ == "__main__":

    workers = max(1, os.cpu_count() - 1)

    print(f"Running with {workers} parallel workers")

    with ProcessPoolExecutor(max_workers=workers) as executor:

        futures = [executor.submit(worker, j) for j in jobs()]

        for f in as_completed(futures):
            print(f.result())
