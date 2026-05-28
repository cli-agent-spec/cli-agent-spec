import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "cli-agent-report" / "scripts" / "aggregate_findings.py"
FIXTURE = ROOT / "tests" / "fixtures" / "aggregate_findings" / "findings.md"


class AggregateFindingsTest(unittest.TestCase):
    def run_script(self, *args: str) -> dict:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(FIXTURE), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_aggregates_sample_findings(self) -> None:
        data = self.run_script()

        self.assertEqual(data["summary"]["all"]["total"], 4)
        self.assertEqual(data["summary"]["Critical"]["fail"], 1)
        self.assertEqual(data["summary"]["High"]["partial"], 1)
        self.assertEqual(data["summary"]["Medium"]["pass"], 1)
        self.assertEqual(data["summary"]["Medium"]["indeterminate"], 1)
        self.assertEqual(data["average_score"], 1.7)
        self.assertEqual(data["sorted"]["severity_desc_score_asc"], [1, 12, 65, 34])

    def test_scope_filters_by_severity(self) -> None:
        data = self.run_script("--scope", "medium")

        self.assertEqual([row["section"] for row in data["rows"]], [34, 65])
        self.assertEqual(data["summary"]["all"]["total"], 2)


if __name__ == "__main__":
    unittest.main()
