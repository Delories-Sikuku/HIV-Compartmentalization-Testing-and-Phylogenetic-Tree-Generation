import json
import subprocess
import re
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from openpyxl import Workbook

DATA_DIR = Path("data")
OUTPUT_DIR = Path("tests_output")
CONFIG_FILE = "tests_config.json"
DATASET_FILE = "datasets.txt"

OUTPUT_DIR.mkdir(exist_ok=True)

config = json.load(open(CONFIG_FILE))
samples = [x.strip() for x in open(DATASET_FILE) if x.strip()]


def extract_fields(stdout, field_patterns):

    results = {}

    for field_name, pattern in field_patterns.items():

        matches = re.findall(pattern, stdout, re.MULTILINE)

        if matches:
            results[field_name] = matches[-1]
        else:
            results[field_name] = None

    return results


def run_test(sample, test):

    alignment = DATA_DIR / f"{sample}-Alignment.nex"
    tree = DATA_DIR / f"{sample}-Alignment-tree.newick"

    required_files = {"alignment": alignment, "tree": tree}
    missing_files = [name for name, path in required_files.items() if not path.exists()]
    if missing_files:
        missing = ", ".join(missing_files)
        raise FileNotFoundError(f"{sample}: missing required {missing} input file(s) in {DATA_DIR}")

    answers = []

    answers.extend(test["menu_path"])

    for inp in test.get("inputs", []):
        value = inp["value"]
        value = value.replace("{alignment}", str(alignment))
        value = value.replace("{tree}", str(tree))
        answers.append(value)

    answers.append("")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log_file = OUTPUT_DIR / f"{sample}_{test['name']}.log"

    print(f"Running {test['name']} for {sample}")

    try:
        proc = subprocess.run(
            ["hyphy"],
            input="\n".join(answers) + "\n",
            text=True,
            capture_output=True
        )
    except FileNotFoundError as error:
        raise RuntimeError("HyPhy was not found on PATH. Install it from environment.yml.") from error

    stdout = proc.stdout
    stderr = proc.stderr

    with open(log_file, "w") as log:
        log.write(stdout)
        log.write(stderr)

    if proc.returncode != 0:
        raise RuntimeError(f"{sample} {test['name']} failed; see {log_file}")

    fields = extract_fields(stdout, test.get("fields", {}))

    results = []

    for field_name, value in fields.items():
        results.append({
            "sample_name": sample,
            "test_name": test["name"],
            "field_name": field_name,
            "field_value": value
        })

    return results


def jobs():
    for sample in samples:
        for test in config["tests"]:
            yield sample, test


def worker(args):
    return run_test(*args)


def write_excel(all_results):

    wb = Workbook()
    ws = wb.active
    ws.title = "HyPhy Results"

    ws.append([
        "sample_name",
        "test_name",
        "field_name",
        "field_value"
    ])

    for row in all_results:
        ws.append([
            row["sample_name"],
            row["test_name"],
            row["field_name"],
            row["field_value"]
        ])

    wb.save(OUTPUT_DIR / "hyphy_results.xlsx")


if __name__ == "__main__":

    workers = max(1, os.cpu_count() - 1)

    print(f"Running with {workers} parallel workers")

    all_results = []

    with ProcessPoolExecutor(max_workers=workers) as executor:

        futures = [executor.submit(worker, j) for j in jobs()]

        for f in as_completed(futures):

            result_rows = f.result()

            for r in result_rows:
                print(f"{r['sample_name']} {r['test_name']} {r['field_name']}")

            all_results.extend(result_rows)

    write_excel(all_results)

    print("Excel report written to tests_output/hyphy_results.xlsx")
