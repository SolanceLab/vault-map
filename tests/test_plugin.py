# vault-map — Copyright (c) 2026 House of Solance. PolyForm Noncommercial 1.0.0. Required Notice: Copyright (c) 2026 House of Solance (https://github.com/SolanceLab)
"""The plugin's two manifests, the skill, pyproject and the changelog name the same version."""
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


class PluginAgrees(unittest.TestCase):
    def setUp(self):
        self.version = re.search(r"^## \[?(\d+\.\d+\.\d+)", read("CHANGELOG.md"), re.M).group(1)

    def test_manifests_carry_the_changelog_version(self):
        for path in (("plugin", ".claude-plugin", "plugin.json"), ("plugin", ".codex-plugin", "plugin.json")):
            data = json.loads(read(*path))
            self.assertEqual(data["name"], "vault-map")
            self.assertEqual(data["version"], self.version, path)

    def test_codex_manifest_is_skill_only(self):
        data = json.loads(read("plugin", ".codex-plugin", "plugin.json"))
        self.assertEqual(data["skills"], "./skills/")
        self.assertNotIn("mcpServers", data)

    def test_pyproject_version_and_script(self):
        text = read("pyproject.toml")
        self.assertIn('version = "%s"' % self.version, text)
        self.assertIn('script-files = ["vault-map.py"]', text)

    def test_skill_pins_the_release_it_ships_with(self):
        skill = read("plugin", "skills", "vault-map", "SKILL.md")
        self.assertIn("vault-map@v%s" % self.version, skill)


if __name__ == "__main__":
    unittest.main()
