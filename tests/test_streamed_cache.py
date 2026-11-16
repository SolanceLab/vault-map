# vault-map — Copyright (c) 2026 House of Solance. PolyForm Noncommercial 1.0.0. Required Notice: Copyright (c) 2026 House of Solance (https://github.com/SolanceLab)
"""The streamed section cache: header then one record per file; short or old-layout files are ignored."""
import importlib.util
import os
import pickle
import shutil
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class StreamedCache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vault-map-stream-")
        self.old_home = os.environ.get("HOME")
        os.environ["HOME"] = os.path.join(self.tmp, "home")
        os.makedirs(os.environ["HOME"])
        self.vault = os.path.join(self.tmp, "vault")
        os.makedirs(self.vault)
        for n, t in (("a.md", "# A\n\nThe heron waits.\n"), ("b.md", "# B\n\nA kettle boils.\n")):
            with open(os.path.join(self.vault, n), "w") as fh:
                fh.write(t)
        spec = importlib.util.spec_from_file_location("vm_stream", os.path.join(ROOT, "vault-map.py"))
        self.vm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.vm)
        self.vm.build(self.vault)
        self.vm.section_index(self.vault)
        self.cp = self.vm._cache_path(self.vault)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if self.old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self.old_home

    def load(self):
        memo = {"words": [], "wid": {}, "files": {}}
        self.vm._load_cache(self.cp, memo)
        return memo

    def test_header_then_one_record_per_file(self):
        with open(self.cp, "rb") as fh:
            head = pickle.load(fh)  # one pickle per record, read with a fresh memo each
            self.assertEqual((head["v"], head["count"]), (2, 2))
            self.assertEqual(sorted(pickle.load(fh)[0] for _ in range(2)), ["a.md", "b.md"])
        self.assertEqual(sorted(self.load()["files"]), ["a.md", "b.md"])

    def test_truncated_cache_is_ignored(self):
        with open(self.cp, "rb") as fh:
            data = fh.read()
        with open(self.cp, "wb") as fh:
            fh.write(data[:len(data) - 20])
        self.assertEqual(self.load()["files"], {})

    def test_old_single_dict_layout_is_ignored_then_rewritten(self):
        with open(self.cp, "wb") as fh:
            pickle.dump({"v": 2, "words": [], "files": {}}, fh)
        self.assertEqual(self.load()["files"], {})
        self.vm._MEMO.clear()
        self.assertEqual(self.vm.search_sections(["heron"], self.vault, 3)["results"][0]["path"], "a.md")


if __name__ == "__main__":
    unittest.main()
