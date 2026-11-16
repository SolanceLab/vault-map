# vault-map — Copyright (c) 2026 House of Solance. PolyForm Noncommercial 1.0.0. Required Notice: Copyright (c) 2026 House of Solance (https://github.com/SolanceLab)
"""A fresh process loading the saved section cache gets exactly the index the writing process had,
including notes whose headings repeat (the writer then back-references the same heading inside one record)."""
import importlib.util
import os
import shutil
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fresh_module():
    spec = importlib.util.spec_from_file_location("vm_reload", os.path.join(ROOT, "vault-map.py"))
    vm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vm)
    return vm


def shape(ix):
    return [(u.rel, u.heading, u.start, u.end, [ix["words"][i] for i in u.ids], list(u.cnt)) for u in ix["units"]]


class CacheReload(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vault-map-reload-")
        self.old_home = os.environ.get("HOME")
        os.environ["HOME"] = os.path.join(self.tmp, "home")
        os.makedirs(os.environ["HOME"])
        self.vault = os.path.join(self.tmp, "vault")
        os.makedirs(self.vault)
        long_para = " ".join(f"word{i} heron kettle" for i in range(400))   # longer than one section: split, same heading
        notes = {
            "a.md": "# Notes\n\nThe heron waits.\n\n# Notes\n\nThe heron waits again.\n\n## Notes\n\n" + long_para + "\n",
            "b.md": "# Notes\n\nA kettle boils.\n\n# Log\n\nA kettle boils.\n",
        }
        for n, t in notes.items():
            with open(os.path.join(self.vault, n), "w") as fh:
                fh.write(t)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self.old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self.old_home

    def test_reload_matches_writer(self):
        vm1 = fresh_module()
        vm1.build(self.vault)
        first = vm1.section_index(self.vault)
        vm2 = fresh_module()              # a new process: nothing in memory, the cache file is read
        second = vm2.section_index(self.vault)
        self.assertTrue(vm2._MEMO[os.path.abspath(self.vault)]["files"])   # it did load from the cache
        self.assertEqual(shape(first), shape(second))
        self.assertEqual(list(first["df"]), list(second["df"]))
        r1 = vm1.search_sections(["heron", "kettle"], self.vault, 5, index=first)
        r2 = vm2.search_sections(["heron", "kettle"], self.vault, 5, index=second)
        self.assertEqual(r1, r2)


if __name__ == "__main__":
    unittest.main()
