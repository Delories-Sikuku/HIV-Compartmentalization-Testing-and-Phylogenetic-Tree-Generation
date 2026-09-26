import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_trees
import run_tests


class WorkflowTests(unittest.TestCase):
    def test_load_datasets_skips_blank_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_file = Path(directory) / "datasets.txt"
            dataset_file.write_text("CVL-1-and-PLA-1\n\nCVL-2-and-PLA-2\n", encoding="utf-8")

            self.assertEqual(
                build_trees.load_datasets(dataset_file),
                ["CVL-1-and-PLA-1", "CVL-2-and-PLA-2"],
            )

    def test_build_tree_reports_missing_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                build_trees.build_tree("CVL-1-and-PLA-1", data_dir=Path(directory)),
                "CVL-1-and-PLA-1 tree not found",
            )

    def test_extract_fields_uses_last_match(self):
        fields = {"association_index": r"Association Index:\s*([0-9.]+)"}
        stdout = "Association Index: 0.1\nAssociation Index: 0.25\n"

        self.assertEqual(run_tests.extract_fields(stdout, fields), {"association_index": "0.25"})

    def test_run_test_rejects_missing_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(run_tests, "DATA_DIR", Path(directory)):
                with self.assertRaisesRegex(FileNotFoundError, "missing required alignment, tree"):
                    run_tests.run_test("CVL-1-and-PLA-1", {"name": "FST", "menu_path": []})

    def test_run_test_collects_synthetic_output(self):
        test = {
            "name": "Synthetic",
            "menu_path": ["7", "1"],
            "inputs": [{"value": "{alignment}"}, {"value": "{tree}"}],
            "fields": {"association_index": r"Association Index:\s*([0-9.]+)"},
        }
        sample = "CVL-1-and-PLA-1"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_dir = root / "data"
            output_dir = root / "output"
            data_dir.mkdir()
            (data_dir / f"{sample}-Alignment.nex").write_text("#NEXUS\n", encoding="utf-8")
            (data_dir / f"{sample}-Alignment-tree.newick").write_text("(CVL-1,PLA-1);\n", encoding="utf-8")
            completed = subprocess.CompletedProcess(["hyphy"], 0, "Association Index: 0.25\n", "")

            with patch.object(run_tests, "DATA_DIR", data_dir), patch.object(run_tests, "OUTPUT_DIR", output_dir), patch(
                "run_tests.subprocess.run", return_value=completed
            ) as mocked_run:
                rows = run_tests.run_test(sample, test)

            self.assertEqual(rows[0]["field_value"], "0.25")
            self.assertIn(str(data_dir / f"{sample}-Alignment.nex"), mocked_run.call_args.kwargs["input"])
            self.assertTrue((output_dir / f"{sample}_Synthetic.log").exists())


if __name__ == "__main__":
    unittest.main()