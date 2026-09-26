import re
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

DATA_DIR = Path("data")
DATASET_FILE = "datasets.txt"
OUTPUT_DIR = Path("trees_output")

pattern = re.compile(r"(CVL|PLA)-\d+")


def load_datasets(dataset_file=DATASET_FILE):
    with open(dataset_file, encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def build_tree(dataset, data_dir=DATA_DIR, output_dir=OUTPUT_DIR):
    tree_file = data_dir / f"{dataset}-Alignment-tree.newick"

    if not tree_file.exists():
        return f"{dataset} tree not found"

    from ete3 import NodeStyle, TextFace, Tree, TreeStyle

    output_dir.mkdir(parents=True, exist_ok=True)

    t = Tree(str(tree_file))
    t.ladderize()

    for node in t.traverse():

        node.dist = 1
        style = NodeStyle()

        style["hz_line_color"] = "black"
        style["vt_line_color"] = "black"
        style["hz_line_width"] = 3
        style["vt_line_width"] = 1

        style["size"] = 0

        if node.is_leaf():

            if node.name.startswith("CVL"):
                style["fgcolor"] = "blue"
                style["size"] = 6

            elif node.name.startswith("PLA"):
                style["fgcolor"] = "red"
                style["size"] = 6

            match = pattern.search(node.name)
            label = match.group(0) if match else ""

            face = TextFace(label, fsize=10)
            node.add_face(face, column=0, position="branch-right")

        node.set_style(style)

    ts = TreeStyle()

    ts.mode = "r"
    ts.show_leaf_name = False
    ts.show_branch_length = True
    ts.show_branch_support = False
    ts.show_scale = True

    ts.scale = 40
    ts.scale_length = 0.0005
    ts.branch_vertical_margin = 6

    svg_output = output_dir / f"{dataset}.svg"
    png_output = output_dir / f"{dataset}.png"

    t.render(str(svg_output), tree_style=ts, w=500)
    t.render(str(png_output), tree_style=ts, w=500)

    return f"{dataset} tree built"


def worker(dataset):
    return build_tree(dataset)


if __name__ == "__main__":

    datasets = load_datasets()

    workers = max(1, os.cpu_count() - 1)

    print(f"Building trees with {workers} parallel workers")

    with ProcessPoolExecutor(max_workers=workers) as executor:

        futures = [executor.submit(worker, d) for d in datasets]

        for f in as_completed(futures):
            print(f.result())
