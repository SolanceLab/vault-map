# vault-map — Copyright (c) 2026 House of Solance. PolyForm Noncommercial 1.0.0. Required Notice: Copyright (c) 2026 House of Solance (https://github.com/SolanceLab)
"""The compact section index: reuse in one process, changed-note re-read, v2 cache round-trip. HOME is a temp dir."""
import importlib.util
import os
import pickle
import shutil
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CompactIndex(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vault-map-compact-")
        self.old_home = os.environ.get("HOME")
        os.environ["HOME"] = os.path.join(self.tmp, "home")
        os.makedirs(os.environ["HOME"])
        self.vault = os.path.join(self.tmp, "vault")
        os.makedirs(self.vault)
        self.write("a.md", "# Alpha\n\nThe heron stands in the reeds.\n\n## Pond\n\nFrogs sing at dusk.\n")
        self.write("b.md", "# Beta\n\nA kettle boils on the stove.\n")
        spec = importlib.util.spec_from_file_location("vm_compact", os.path.join(ROOT, "vault-map.py"))
        self.vm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.vm)
        self.vm.build(self.vault)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self.old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self.old_home

    def write(self, name, text):
        with open(os.path.join(self.vault, name), "w") as fh:
            fh.write(text)

    def cache_file(self):
        d = os.path.join(os.environ["HOME"], ".cache", "vault-map")
        return os.path.join(d, [f for f in os.listdir(d) if f.startswith("sections-v2-")][0])

    def test_unchanged_vault_returns_same_index(self):
        first = self.vm.section_index(self.vault)
        self.assertIs(self.vm.section_index(self.vault), first)

    def test_changed_note_is_reread_and_unchanged_arrays_shared(self):
        first = self.vm.section_index(self.vault)
        keep = [u for u in first["units"] if u.rel == "b.md"][0]
        self.write("a.md", "# Alpha\n\nThe heron stands in the reeds. Otters swim too, otters everywhere.\n")
        second = self.vm.section_index(self.vault)
        self.assertIsNot(second, first)
        self.assertEqual(self.vm.search_sections(["otters"], self.vault, 3, index=second)["results"][0]["path"], "a.md")
        self.assertEqual(self.vm.search_sections(["frogs"], self.vault, 3, index=second)["results"], [])
        self.assertIs([u for u in second["units"] if u.rel == "b.md"][0].ids, keep.ids)

    def test_v2_cache_round_trips_into_a_new_process(self):
        before = self.vm.search_sections(["kettle", "stove"], self.vault, 3)
        with open(self.cache_file(), "rb") as fh:
            data = pickle.load(fh)
        self.assertEqual(data["v"], 2)
        self.vm._MEMO.clear()  # a fresh process: nothing in memory, so the index comes from the file
        after = self.vm.search_sections(["kettle", "stove"], self.vault, 3)
        self.assertEqual(before, after)

    def test_old_format_cache_is_ignored_and_removed(self):
        self.vm.section_index(self.vault)
        v2 = self.cache_file()
        old = v2.replace("sections-v2-", "sections-")
        with open(old, "wb") as fh:
            pickle.dump({"a.md": "junk"}, fh)
        self.vm._MEMO.clear()
        with open(v2, "wb") as fh:
            fh.write(b"not a pickle")
        res = self.vm.search_sections(["heron"], self.vault, 3)
        self.assertEqual(res["results"][0]["path"], "a.md")
        self.assertFalse(os.path.exists(old))

    def test_unit_keeps_dict_style_access(self):
        u = self.vm.section_index(self.vault)["units"][0]
        self.assertEqual(u["rel"], u.rel)
        with self.assertRaises(KeyError):
            u["nope"]


if __name__ == "__main__":
    unittest.main()
