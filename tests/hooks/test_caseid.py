"""What a scenario is called, on both sides of a run.

The importers share one identity function, and these are the cases that
have to agree: a written case id, a derived one, and the file it is derived
from whichever runner wrote the report.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import caseid


class WrittenIds(unittest.TestCase):
    def test_case_id_shape_with_any_prefix(self):
        for tag in ("@ACME-ADM-002", "ACME-INV-055", "@SP-INV-055", "@HARBOR-BKG-001"):
            self.assertTrue(caseid.WRITTEN.match(tag), tag)

    def test_task_keys_and_plain_tags_are_not_case_ids(self):
        for tag in ("ACME-940", "@smoke", "@wip", "acme-adm-002", "@ACME-ADM"):
            self.assertFalse(caseid.WRITTEN.match(tag), tag)

    def test_every_written_id_in_order_without_at(self):
        self.assertEqual(caseid.all_written(["@smoke", "@ACME-INV-049", "@ACME-INV-048"]),
                         ["ACME-INV-049", "ACME-INV-048"])


class DerivedIds(unittest.TestCase):
    def test_same_file_and_name_give_the_same_id(self):
        a = caseid.derived("features/harbor/booking.feature", "A berth can be reserved", "HARBOR")
        b = caseid.derived("booking.feature", "A berth can be reserved", "HARBOR")
        c = caseid.derived("booking", "  A berth   can be reserved ", "harbor")
        self.assertEqual(a, b)
        self.assertEqual(a, c)
        self.assertRegex(a, r"^HARBOR-GEN-[0-9A-F]{6}$")

    def test_renaming_the_scenario_changes_the_id(self):
        self.assertNotEqual(caseid.derived("booking.feature", "A", "HARBOR"),
                            caseid.derived("booking.feature", "B", "HARBOR"))

    def test_prefix_is_required(self):
        with self.assertRaises(TypeError):
            caseid.derived("booking.feature", "A")

    def test_identity_says_whether_somebody_wrote_it(self):
        self.assertEqual(caseid.identity(["@ACME-ADM-002"], "x.feature", "n", "ACME"), ("ACME-ADM-002", True))
        ident, told = caseid.identity(["@smoke"], "x.feature", "n", "ACME")
        self.assertFalse(told)
        self.assertEqual(ident, caseid.derived("x.feature", "n", "ACME"))


class FeatureFile(unittest.TestCase):
    """Cucumber and behave name the file differently; the id must not notice."""

    CUCUMBER = {"uri": "features/harbor/booking.feature", "name": "Berth booking", "elements": []}
    BEHAVE = {"location": "features/harbor/booking.feature:1", "name": "Berth booking", "elements": []}

    def test_both_runners_name_the_same_file(self):
        self.assertEqual(caseid.feature_file(self.CUCUMBER), "features/harbor/booking.feature")
        self.assertEqual(caseid.feature_file(self.BEHAVE), "features/harbor/booking.feature")

    def test_results_derive_what_the_features_derived(self):
        from_features = caseid.derived("booking.feature", "A booked berth cannot be double booked", "HARBOR")
        for report in (self.CUCUMBER, self.BEHAVE):
            from_results = caseid.derived(caseid.feature_file(report),
                                          "A booked berth cannot be double booked", "HARBOR")
            self.assertEqual(from_results, from_features, report)

    def test_falls_back_to_the_title_only_when_nothing_names_the_file(self):
        self.assertEqual(caseid.feature_file({"name": "Berth booking"}), "Berth booking")

    def test_tags_of_reads_both_shapes(self):
        self.assertEqual(caseid.tags_of({"tags": [{"name": "@ACME-ADM-002"}, "@smoke"]}),
                         ["@ACME-ADM-002", "@smoke"])


class ProjectKey(unittest.TestCase):
    def vault(self, projects):
        root = tempfile.mkdtemp()
        with open(os.path.join(root, "docket.yaml"), "w", encoding="utf-8") as f:
            f.write("name: X\nprojects:\n" + "".join("  - key: %s\n    name: %s\n" % (k, k) for k in projects)
                    + "statuses:\n  - name: Todo\n")
        return root

    def test_what_the_caller_said_wins(self):
        self.assertEqual(caseid.project_key(self.vault(["A", "B"]), "B"), "B")

    def test_one_project_is_one_answer(self):
        self.assertEqual(caseid.project_key(self.vault(["ACME"])), "ACME")

    def test_several_projects_ask_for_one(self):
        with self.assertRaises(SystemExit) as stop:
            caseid.project_key(self.vault(["A", "B"]))
        self.assertIn("--project", str(stop.exception))

    def test_no_vault_asks_too(self):
        with self.assertRaises(SystemExit):
            caseid.project_key(tempfile.mkdtemp())


if __name__ == "__main__":
    unittest.main()
