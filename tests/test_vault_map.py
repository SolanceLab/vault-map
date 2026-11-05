# vault-map — Copyright (c) 2026 House of Solance. PolyForm Noncommercial 1.0.0. Required Notice: Copyright (c) 2026 House of Solance (https://github.com/SolanceLab)
# Copyright (c) 2026 House of Solance. Required Notice: Copyright (c) 2026 House of Solance (https://github.com/SolanceLab)
"""Smoke tests: build a tiny temp vault, check search() and search_sections() run. No network; HOME is a temp dir."""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NOTES = {
    "backups.md": "# Backup rotation\n\nWe rotate the backups every week.\n\n## Decision\n\nKeep four weekly copies and one monthly copy on the NAS.\n\n## Links\n\nSee [[nas]].\n",
    "nas.md": "# NAS incident\n\n#storage\n\nThe NAS disk failed in March. See [[backups]].\n\n## Cause\n\nA worn drive and no alert.\n",
    "garden.md": "# Garden\n\nTomatoes need sun and water.\n",
}


class VaultMapSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="vault-map-test-")
        cls.old_home = os.environ.get("HOME")
        os.environ["HOME"] = os.path.join(cls.tmp, "home")  # the section cache lands in tmp
        os.makedirs(os.environ["HOME"])
        cls.vault = os.path.join(cls.tmp, "vault")
        os.makedirs(cls.vault)
        for name, body in NOTES.items():
            with open(os.path.join(cls.vault, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        spec = importlib.util.spec_from_file_location("vault_map", os.path.join(ROOT, "vault-map.py"))
        cls.vm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.vm)
        cls.vm.build(cls.vault)

    @classmethod
    def tearDownClass(cls):
        if cls.old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = cls.old_home
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_search_finds_the_right_note(self):
        res = self.vm.search(["backup", "rotation"], self.vault, 5)
        self.assertGreaterEqual(res["hits"], 1)
        self.assertEqual(res["results"][0]["path"], "backups.md")
        for key in ("path", "title", "score", "snippet", "links", "backlinks"):
            self.assertIn(key, res["results"][0])

    def test_search_sections_returns_a_section(self):
        res = self.vm.search_sections(["monthly", "copy"], self.vault, 5)
        self.assertGreaterEqual(res["hits"], 1)
        top = res["results"][0]
        self.assertEqual(top["path"], "backups.md")
        for key in ("section", "text", "also_in", "snippet", "path", "title", "score"):
            self.assertIn(key, top)
        self.assertIn("monthly", top["text"])

    def test_section_index_is_cached_under_home(self):
        self.vm.search_sections(["garden"], self.vault, 3)
        cache = os.path.join(os.environ["HOME"], ".cache", "vault-map")
        self.assertTrue(os.path.isdir(cache))
        self.assertTrue(any(f.endswith(".pickle") for f in os.listdir(cache)))

    def test_no_match_is_empty(self):
        res = self.vm.search_sections(["zzzqqq"], self.vault, 3)
        self.assertEqual(res["results"], [])


    def _run_query(self, **kw):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.vm.query(["backup", "rotation"], self.vault, 5, **kw)
        return buf.getvalue()

    def test_query_sections_prints_heading_and_text(self):
        out = self._run_query(sections=True)
        self.assertIn("backups.md", out)
        self.assertIn("section: Decision", out)
        self.assertIn("four weekly copies", out)

    def test_query_sections_json(self):
        data = json.loads(self._run_query(sections=True, as_json=True))
        self.assertGreaterEqual(data["hits"], 1)
        self.assertIn("section", data["results"][0])
        self.assertIn("text", data["results"][0])

    def test_plain_query_unchanged(self):
        data = json.loads(self._run_query(as_json=True))
        self.assertEqual(data, self.vm.search(["backup", "rotation"], self.vault, 5))
        self.assertNotIn("section:", self._run_query())

    def test_sections_with_nonpositive_n_is_empty_not_a_crash(self):
        for n in (0, -3):
            res = self.vm.search_sections(["backup", "rotation"], self.vault, n)
            self.assertEqual(res["results"], [])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.vm.query(["backup", "rotation"], self.vault, 0, sections=True)
        self.assertIn("no notes match", buf.getvalue())

if __name__ == "__main__":
    unittest.main()
