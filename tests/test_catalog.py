from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "catalog.py"
SPEC = importlib.util.spec_from_file_location("harness_catalog", MODULE_PATH)
assert SPEC and SPEC.loader
catalog_module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = catalog_module
SPEC.loader.exec_module(catalog_module)
Catalog = catalog_module.Catalog


TAXONOMY = """
schema_version = 1
default_review_days = 90
statuses = ["managed", "excluded", "retired"]
relationship_types = ["depends-on", "uses", "replaces", "backs-up-to", "published-to"]
profile_tiers = ["required", "standard", "optional"]
platforms = ["windows", "cross-platform", "not-applicable"]
preference_sources = ["owner-declared", "verified-public", "unknown"]
provenance_types = ["owner-produced", "third-party"]
software_install_forms = ["portable", "installer", "unknown"]
release_channels = ["lts", "stable", "beta", "unknown"]
development_tool_kinds = ["version-control", "package-manager", "cli"]

[[asset_types]]
id = "rule"
label = "Rule"
active = true

[[asset_types]]
id = "skill"
label = "Skill"
active = true

[[asset_types]]
id = "workflow"
label = "Workflow"
active = true

[[asset_types]]
id = "software"
label = "Software"
active = true

[[asset_types]]
id = "development-tool"
label = "Development tool"
active = true

[[asset_types]]
id = "hardware"
label = "Hardware"
active = false

[[domains]]
id = "ai-agent"
label = "AI"

[[domains]]
id = "development"
label = "Development"

[[domains]]
id = "creative-media"
label = "Creative"
"""


def _asset_common(
    asset_id: str,
    asset_type: str,
    name: str,
    domain: str,
    *,
    verified: str = "2026-08-15",
    status: str = "managed",
    preference: str = "owner-declared",
    provenance: str = "owner-produced",
    upstream_updates: bool = False,
) -> str:
    return f"""
schema_version = 1
id = "{asset_id}"
type = "{asset_type}"
name = "{name}"
domain = "{domain}"
status = "{status}"
purpose = "fixture purpose"
platforms = ["windows"]
fact_source = "test fixture"
preference_source = "{preference}"
provenance = "{provenance}"
upstream_updates = {str(upstream_updates).lower()}
declared_on = "2026-08-01"
last_verified_on = "{verified}"
review_days = 90
notes = "fixture"
"""


class FixtureRepo:
    def __init__(self, root: Path):
        self.root = root
        self.write("inventory/taxonomy.toml", TAXONOMY)
        self.write("global/AGENTS.md", "# test rules\n")
        self.write("skills/test-skill/SKILL.md", "---\nname: test-skill\ndescription: test capability\n---\n")

    def write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")

    def workflow(self, *, relationships: str = "relationships = []") -> None:
        self.write("workflows/restore.md", f"""
            +++
            {_asset_common("workflow:restore", "workflow", "Restore", "ai-agent")}
            {relationships}
            +++
            # Restore
            """)

    def software(self, *, status: str = "managed", preference: str = "owner-declared", backup: str = "Cloud / Workbench / App") -> None:
        self.write("inventory/assets/software/design-app.toml", _asset_common(
            "software:design-app", "software", "Design App", "creative-media", status=status, preference=preference
        ) + f"""
            relationships = []
            [software]
            install_form = "portable"
            release_channel = "lts"
            minimum_verified_version = "4.0"
            pinned_version = ""
            avoid_versions = []
            official_source = "https://example.test/download"
            config_restore = "Import preferences manually"
            backup_location = "{backup}"
            post_restore_checks = ["Open a fixture"]
            """)

    def dev_tool(self, *, verified: str = "2026-08-15", relation_target: str = "") -> None:
        relation = "relationships = []"
        if relation_target:
            relation = f'[[relationships]]\ntype = "depends-on"\ntarget = "{relation_target}"'
        self.write("inventory/assets/development-tool/version-tool.toml", _asset_common(
            "development-tool:version-tool", "development-tool", "Version Tool", "development", verified=verified
        ) + f"""
            {relation}
            [development_tool]
            tool_kind = "version-control"
            commands = ["vcs"]
            install_source = "official installer"
            package_id = "Vendor.Tool"
            version_constraint = ">=2"
            update_channel = "stable"
            environment_variables = ["PATH"]
            config_reference = "Cloud / Workbench / Version Tool"
            verification_commands = ["vcs --version"]
            """)

    def profile(self, entries: list[tuple[str, str]]) -> None:
        rows = []
        for asset_id, tier in entries:
            rows.append(f'[[assets]]\nid = "{asset_id}"\ntier = "{tier}"')
        self.write("inventory/profiles/main.toml", f"""
            schema_version = 1
            id = "main"
            name = "Main workstation"
            description = "Fixture profile"
            platforms = ["windows"]
            last_verified_on = "2026-08-15"
            review_days = 90
            {chr(10).join(rows)}
            """)


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = FixtureRepo(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def load(self) -> object:
        return Catalog(self.root, today=date(2026, 9, 4)).load()

    def assert_valid(self, catalog: object) -> None:
        self.assertEqual([], [problem.display(self.root) for problem in catalog.problems])

    def test_native_schema_and_future_asset_share_one_catalog(self) -> None:
        self.repo.write("skills/test-skill/SKILL.md", """
            ---
            name: test-skill
            description: |
              First sentence describes the real capability.
              Second line contains a Markdown | separator and more detail.
            ---
            """)
        self.repo.workflow()
        self.repo.write("inventory/assets/hardware/test-rig.toml", _asset_common(
            "hardware:test-rig", "hardware", "Test Rig", "development"
        ) + "relationships = []\n")
        catalog = self.load()
        self.assert_valid(catalog)
        self.assertTrue({"rule:global-agents", "skill:test-skill", "workflow:restore", "hardware:test-rig"}.issubset(catalog.assets))
        self.assertIn("First sentence describes", catalog.assets["skill:test-skill"].purpose)
        rendered = catalog.render_text()
        self.assertIn("First sentence describes the real capability.", rendered)
        self.assertNotIn("Second line contains", rendered)
        self.assertIn("| 来源性质 | 上游更新 |", rendered)
        self.assertEqual("owner-produced", catalog.assets["rule:global-agents"].provenance)
        self.assertFalse(catalog.assets["rule:global-agents"].upstream_updates)
        self.assertEqual("owner-produced", catalog.assets["skill:test-skill"].provenance)
        self.assertIn("用户自产 | 不适用", rendered)

    def test_vendor_and_structured_assets_expose_upstream_policy(self) -> None:
        self.repo.write("vendor/vendor-skill/SKILL.md", "---\nname: vendor-skill\ndescription: vendor capability\n---\n")
        self.repo.write("inventory/assets/hardware/vendor-rig.toml", _asset_common(
            "hardware:vendor-rig",
            "hardware",
            "Vendor Rig",
            "development",
            provenance="third-party",
            upstream_updates=True,
        ) + "relationships = []\n")
        catalog = self.load()
        self.assert_valid(catalog)
        self.assertEqual("third-party", catalog.assets["skill:vendor-skill"].provenance)
        self.assertTrue(catalog.assets["skill:vendor-skill"].upstream_updates)
        self.assertIn("第三方 | 跟踪", catalog.render_text())
        with redirect_stdout(stdout := io.StringIO()), redirect_stderr(stderr := io.StringIO()):
            code = catalog_module.main(["--root", str(self.root), "list"])
        self.assertEqual(0, code, stderr.getvalue())
        self.assertIn("skill:vendor-skill\tmanaged\tcurrent\t第三方\t跟踪\tvendor-skill", stdout.getvalue())

    def test_owner_produced_asset_cannot_claim_upstream_updates(self) -> None:
        self.repo.write("inventory/assets/hardware/test-rig.toml", _asset_common(
            "hardware:test-rig",
            "hardware",
            "Test Rig",
            "development",
            upstream_updates=True,
        ) + "relationships = []\n")
        catalog = self.load()
        self.assertTrue(any("用户自产资产没有上游更新" in problem.message for problem in catalog.problems))

    def test_software_and_development_tool_extensions(self) -> None:
        self.repo.software()
        self.repo.dev_tool(relation_target="software:design-app")
        catalog = self.load()
        self.assert_valid(catalog)
        self.assertEqual("portable", catalog.assets["software:design-app"].data["software"]["install_form"])
        self.assertEqual([("depends-on", "software:design-app")], catalog.assets["development-tool:version-tool"].relationships)

    def test_cross_type_dangling_relation_and_dependency_cycle_fail(self) -> None:
        self.repo.software()
        self.repo.dev_tool(relation_target="software:design-app")
        software_path = self.root / "inventory/assets/software/design-app.toml"
        software_path.write_text(software_path.read_text(encoding="utf-8").replace(
            "relationships = []", '[[relationships]]\ntype = "depends-on"\ntarget = "development-tool:version-tool"'
        ), encoding="utf-8")
        catalog = self.load()
        self.assertTrue(any("依赖环" in problem.message for problem in catalog.problems))
        software_path.write_text(software_path.read_text(encoding="utf-8").replace(
            'target = "development-tool:version-tool"', 'target = "service:missing"'
        ), encoding="utf-8")
        catalog = self.load()
        self.assertTrue(any("不存在的资产" in problem.message for problem in catalog.problems))

    def test_profile_filters_and_plan_sections_with_dependency_order(self) -> None:
        self.repo.software()
        self.repo.dev_tool(relation_target="software:design-app")
        self.repo.profile([
            ("development-tool:version-tool", "required"),
            ("software:design-app", "required"),
        ])
        catalog = self.load()
        self.assert_valid(catalog)
        plan = catalog.plan_text("main")
        self.assertIn("## 需要恢复", plan)
        self.assertIn("## 已经满足", plan)
        self.assertLess(plan.index("software:design-app"), plan.index("development-tool:version-tool"))
        self.assertEqual({"development-tool:version-tool", "software:design-app"}, catalog_module._profile_asset_ids(catalog, "main"))

    def test_profile_missing_dependency_fails_instead_of_silent_plan(self) -> None:
        self.repo.software()
        self.repo.dev_tool(relation_target="software:design-app")
        self.repo.profile([("development-tool:version-tool", "required")])
        catalog = self.load()
        self.assertTrue(any("必需依赖" in problem.message for problem in catalog.problems))

    def test_satisfied_assets_are_runtime_input(self) -> None:
        self.repo.software()
        self.repo.profile([("software:design-app", "required")])
        catalog = self.load()
        self.assert_valid(catalog)
        plan = catalog.plan_text("main", ["software:design-app"])
        self.assertIn("用户自产；上游更新不适用", plan)
        satisfied_section = plan.split("## 已经满足", 1)[1].split("## 可选", 1)[0]
        self.assertIn("software:design-app", satisfied_section)
        with redirect_stdout(stdout := io.StringIO()), redirect_stderr(stderr := io.StringIO()):
            code = catalog_module.main([
                "--root", str(self.root), "plan", "main",
                "--satisfied", "software:design-app",
            ])
        self.assertEqual(0, code, stderr.getvalue())
        self.assertIn("software:design-app", stdout.getvalue().split("## 已经满足", 1)[1])
        with self.assertRaisesRegex(catalog_module.CatalogError, "不在配置档中"):
            catalog.plan_text("main", ["development-tool:missing"])

    def test_stale_and_unknown_preference_are_computed_not_written(self) -> None:
        self.repo.dev_tool(verified="2026-01-01")
        self.repo.software(preference="unknown")
        catalog = self.load()
        self.assert_valid(catalog)
        self.assertTrue(catalog.assets["development-tool:version-tool"].stale)
        self.assertTrue(catalog.assets["software:design-app"].incomplete)
        rendered = catalog.render_text()
        self.assertIn("`stale`", rendered)
        self.assertIn("`incomplete`", rendered)
        self.assertNotIn("computed_freshness", (self.root / "inventory/assets/software/design-app.toml").read_text(encoding="utf-8"))

    def test_sensitive_key_value_and_absolute_logical_reference_fail(self) -> None:
        self.repo.software(backup=r"C:\\Users\\owner\\Backup")
        path = self.root / "inventory/assets/software/design-app.toml"
        with path.open("a", encoding="utf-8") as handle:
            handle.write('api_token = "ghp_abcdefghijklmnopqrstuvwxyz123456"\n')
        catalog = self.load()
        messages = "\n".join(problem.message for problem in catalog.problems)
        self.assertIn("敏感字段", messages)
        self.assertIn("绝对路径", messages)

        text = path.read_text(encoding="utf-8")
        text = text.replace(r'C:\\Users\\owner\\Backup', "https://cloud.example/private-share?id=123")
        text = text.replace('fact_source = "test fixture"', 'fact_source = "C:/Users/owner/source"')
        path.write_text(text, encoding="utf-8")
        catalog = self.load()
        messages = "\n".join(problem.message for problem in catalog.problems)
        self.assertIn("绝对路径或 URL", messages)
        self.assertIn("fact_source", messages)

    def test_skill_directory_must_match_frontmatter_name(self) -> None:
        self.repo.write("skills/wrong-name/SKILL.md", "---\nname: declared-name\ndescription: test\n---\n")
        catalog = self.load()
        self.assertTrue(any("目录名必须与 frontmatter name 一致" in problem.message for problem in catalog.problems))

    def test_invalid_enums_and_filename_identity_fail(self) -> None:
        self.repo.software()
        path = self.root / "inventory/assets/software/design-app.toml"
        text = path.read_text(encoding="utf-8").replace('install_form = "portable"', 'install_form = "magic"')
        renamed = path.with_name("wrong-name.toml")
        renamed.write_text(text, encoding="utf-8")
        path.unlink()
        catalog = self.load()
        messages = "\n".join(problem.message for problem in catalog.problems)
        self.assertIn("未知 software.install_form", messages)
        self.assertIn("文件名必须与资产 slug 一致", messages)

    def test_render_and_check_are_deterministic(self) -> None:
        self.repo.workflow()
        self.repo.software()
        catalog = self.load()
        self.assert_valid(catalog)
        expected = catalog.render_text()
        (self.root / "CATALOG.md").write_text(expected, encoding="utf-8", newline="\n")
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = catalog_module.main(["--root", str(self.root), "check"])
        self.assertEqual(0, code, stderr.getvalue())
        self.assertIn("检查通过", stdout.getvalue())
        (self.root / "CATALOG.md").write_text(expected + "drift\n", encoding="utf-8")
        with redirect_stdout(io.StringIO()), redirect_stderr(stderr := io.StringIO()):
            code = catalog_module.main(["--root", str(self.root), "check"])
        self.assertEqual(1, code)
        self.assertIn("不同步", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
