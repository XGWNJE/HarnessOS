#!/usr/bin/env python3
"""Build and validate the HarnessOS managed-asset catalog.

The catalog is deliberately read-only except for ``render``.  In particular,
``plan`` describes restoration work but never installs or changes anything.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent.parent
CATALOG_NAME = "CATALOG.md"
CATALOG_HTML_NAME = "catalog.html"
CATALOG_HTML_TEMPLATE = Path(__file__).resolve().parent / "catalog_template.html"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9-]*$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
UNC_RE = re.compile(r"^(?:\\\\|//)[^\\/]+[\\/][^\\/]+")
URL_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.I)
RELATION_TYPES = {
    "depends-on",
    "uses",
    "replaces",
    "backs-up-to",
    "published-to",
}
STATUSES = {"managed", "excluded", "retired"}
PROFILE_TIERS = {"required", "standard", "optional"}
PROVENANCE_TYPES = {"owner-produced", "third-party"}
SENSITIVE_KEY_PARTS = {
    "api-key",
    "api_key",
    "access-key",
    "access_key",
    "password",
    "passwd",
    "private-key",
    "private_key",
    "secret",
    "token",
    "credential",
    "license-key",
    "license_key",
}
SENSITIVE_VALUE_RES = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\b(?:gh[oprsu]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})\b"),
    re.compile(r"^[a-z][a-z0-9+.-]*://[^/@\s:]+:[^/@\s]+@", re.I),
)
LOGICAL_REFERENCE_KEYS = {
    "backup_location",
    "config_reference",
    "backup_reference",
    "logical_reference",
    "fact_source",
}


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    exact = {part.replace("-", "_") for part in SENSITIVE_KEY_PARTS}
    return normalized in exact or any(normalized.endswith(f"_{part}") for part in exact)


class CatalogError(Exception):
    """A source file cannot be parsed as a catalog input."""


@dataclass(slots=True)
class Problem:
    path: Path
    message: str

    def display(self, root: Path) -> str:
        try:
            shown = self.path.relative_to(root)
        except ValueError:
            shown = self.path
        return f"{shown}: {self.message}"


@dataclass(slots=True)
class Asset:
    id: str
    type: str
    name: str
    domain: str
    status: str
    purpose: str
    platforms: list[str]
    provenance: str
    upstream_updates: bool
    source: str
    path: Path
    data: dict[str, Any] = field(default_factory=dict)
    relationships: list[tuple[str, str]] = field(default_factory=list)
    native: bool = False
    stale: bool = False
    incomplete: bool = False


@dataclass(slots=True)
class ProfileEntry:
    id: str
    tier: str
    notes: str = ""


@dataclass(slots=True)
class Profile:
    id: str
    name: str
    description: str
    platforms: list[str]
    entries: list[ProfileEntry]
    path: Path
    data: dict[str, Any] = field(default_factory=dict)
    stale: bool = False


@dataclass(slots=True)
class Taxonomy:
    asset_types: set[str]
    domains: set[str]
    statuses: set[str]
    relationship_types: set[str]
    profile_tiers: set[str]
    platforms: set[str]
    preference_sources: set[str]
    provenance_types: set[str]
    software_install_forms: set[str]
    release_channels: set[str]
    development_tool_kinds: set[str]
    upstream_channels: set[str]
    default_review_days: int
    asset_type_labels: dict[str, str] = field(default_factory=dict)
    domain_labels: dict[str, str] = field(default_factory=dict)


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _is_stale(data: dict[str, Any], default_days: int, today: date) -> bool:
    verified = _date(data.get("last_verified_on", data.get("verified_at")))
    if not verified:
        return False
    days = data.get("review_days", default_days)
    return isinstance(days, int) and days >= 0 and (today - verified).days > days


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CatalogError(str(exc)) from exc


def _frontmatter(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CatalogError(str(exc)) from exc
    lines = text.splitlines()
    if not lines or lines[0].strip() != "+++":
        raise CatalogError("workflow 必须以 +++ TOML frontmatter 开始")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "+++")
    except StopIteration as exc:
        raise CatalogError("workflow TOML frontmatter 缺少结束 +++") from exc
    try:
        return tomllib.loads("\n".join(lines[1:end]))
    except tomllib.TOMLDecodeError as exc:
        raise CatalogError(f"TOML frontmatter 无效: {exc}") from exc


def _skill_frontmatter(path: Path) -> dict[str, str]:
    """Read the tiny YAML subset needed for standard SKILL.md identity."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise CatalogError(str(exc)) from exc
    if not lines or lines[0].strip() != "---":
        raise CatalogError("SKILL.md 缺少 YAML frontmatter")
    result: dict[str, str] = {}
    index = 1
    while index < len(lines):
        line = lines[index]
        if line.strip() == "---":
            break
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if match:
            key, raw = match.group(1), match.group(2)
            if raw in {"|", "|-", "|+", ">", ">-", ">+"}:
                block: list[str] = []
                index += 1
                while index < len(lines):
                    child = lines[index]
                    if child.strip() == "---":
                        break
                    if child and not child[0].isspace():
                        break
                    block.append(child.strip())
                    index += 1
                separator = " " if raw.startswith(">") else "\n"
                result[key] = separator.join(block).strip()
                continue
            result[key] = raw.strip("'\"")
        index += 1
    if "name" not in result:
        raise CatalogError("SKILL.md frontmatter 缺少 name")
    return result


def _relations(data: dict[str, Any]) -> list[tuple[str, str]]:
    raw = data.get("relationships", [])
    result: list[tuple[str, str]] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                result.append((_text(item.get("type")), _text(item.get("target"))))
        return result
    if isinstance(raw, dict):
        for relation, targets in raw.items():
            result.extend((relation.replace("_", "-"), target) for target in _string_list(targets))
    return result


def _taxonomy_ids(items: Any) -> set[str]:
    if not isinstance(items, list):
        return set()
    return {_text(item.get("id")) for item in items if isinstance(item, dict) and item.get("id")}


def _taxonomy_labels(items: Any) -> dict[str, str]:
    if not isinstance(items, list):
        return {}
    return {
        _text(item.get("id")): _text(item.get("label")) or _text(item.get("id"))
        for item in items
        if isinstance(item, dict) and item.get("id")
    }


class Catalog:
    def __init__(self, root: Path, *, today: date | None = None):
        self.root = root.resolve()
        self.today = today or date.today()
        self.problems: list[Problem] = []
        self.taxonomy: Taxonomy | None = None
        self.assets: dict[str, Asset] = {}
        self.profiles: dict[str, Profile] = {}

    def problem(self, path: Path, message: str) -> None:
        self.problems.append(Problem(path, message))

    def load(self) -> "Catalog":
        self.problems.clear()
        self.assets.clear()
        self.profiles.clear()
        self._load_taxonomy()
        self._load_native_rule()
        self._load_skills()
        self._load_workflows()
        self._load_asset_files()
        self._load_profiles()
        self._validate_references()
        self._validate_profile_dependencies()
        self._validate_dependency_cycles()
        return self

    def _load_taxonomy(self) -> None:
        path = self.root / "inventory" / "taxonomy.toml"
        if not path.is_file():
            self.problem(path, "缺少 taxonomy.toml")
            self.taxonomy = Taxonomy(set(), set(), STATUSES, RELATION_TYPES, PROFILE_TIERS, set(), set(), PROVENANCE_TYPES, set(), set(), set(), set(), 90)
            return
        try:
            data = _read_toml(path)
        except CatalogError as exc:
            self.problem(path, str(exc))
            self.taxonomy = Taxonomy(set(), set(), STATUSES, RELATION_TYPES, PROFILE_TIERS, set(), set(), PROVENANCE_TYPES, set(), set(), set(), set(), 90)
            return
        if data.get("schema_version") != 1:
            self.problem(path, "schema_version 必须为 1")
        self._validate_taxonomy_tables(path, data)
        days = data.get("default_review_days", 90)
        if not isinstance(days, int) or days < 1:
            self.problem(path, "default_review_days 必须为正整数")
            days = 90
        self.taxonomy = Taxonomy(
            _taxonomy_ids(data.get("asset_types")),
            _taxonomy_ids(data.get("domains")),
            set(_string_list(data.get("statuses"))) or STATUSES,
            set(_string_list(data.get("relationship_types"))) or RELATION_TYPES,
            set(_string_list(data.get("profile_tiers"))) or PROFILE_TIERS,
            set(_string_list(data.get("platforms"))),
            set(_string_list(data.get("preference_sources"))),
            set(_string_list(data.get("provenance_types"))) or PROVENANCE_TYPES,
            set(_string_list(data.get("software_install_forms"))),
            set(_string_list(data.get("release_channels"))),
            set(_string_list(data.get("development_tool_kinds"))),
            set(_string_list(data.get("upstream_channels"))),
            days,
            asset_type_labels=_taxonomy_labels(data.get("asset_types")),
            domain_labels=_taxonomy_labels(data.get("domains")),
        )
        required_types = {"rule", "skill", "workflow", "software", "development-tool"}
        missing_types = required_types - self.taxonomy.asset_types
        if missing_types:
            self.problem(path, f"asset_types 缺少: {', '.join(sorted(missing_types))}")
        if not self.taxonomy.domains:
            self.problem(path, "domains 不能为空")
        if not RELATION_TYPES.issubset(self.taxonomy.relationship_types):
            self.problem(path, "relationship_types 缺少标准关系")
        if self.taxonomy.statuses != STATUSES:
            self.problem(path, "statuses 必须且只能包含 managed、excluded、retired")
        if self.taxonomy.profile_tiers != PROFILE_TIERS:
            self.problem(path, "profile_tiers 必须且只能包含 required、standard、optional")
        if self.taxonomy.provenance_types != PROVENANCE_TYPES:
            self.problem(path, "provenance_types 必须且只能包含 owner-produced、third-party")
        if not self.taxonomy.upstream_channels:
            self.problem(path, "upstream_channels 不能为空")

    def _validate_taxonomy_tables(self, path: Path, data: dict[str, Any]) -> None:
        for key in ("asset_types", "domains"):
            items = data.get(key)
            if not isinstance(items, list) or not items:
                self.problem(path, f"{key} 必须是非空数组表")
                continue
            seen: set[str] = set()
            for item in items:
                if not isinstance(item, dict):
                    self.problem(path, f"{key} 项必须是表")
                    continue
                item_id = _text(item.get("id"))
                if not SLUG_RE.fullmatch(item_id):
                    self.problem(path, f"{key} id 必须是 slug: {item_id or '<empty>'}")
                if item_id in seen:
                    self.problem(path, f"{key} id 重复: {item_id}")
                seen.add(item_id)
                if not item.get("label"):
                    self.problem(path, f"{key} {item_id or '<empty>'} 缺少 label")
                if key == "asset_types" and not isinstance(item.get("active"), bool):
                    self.problem(path, f"asset_types {item_id or '<empty>'} 的 active 必须是布尔值")

    def _add_asset(self, asset: Asset) -> None:
        if asset.id in self.assets:
            self.problem(asset.path, f"资产 ID 重复: {asset.id}")
            return
        self.assets[asset.id] = asset

    def _load_native_rule(self) -> None:
        path = self.root / "global" / "AGENTS.md"
        if not path.is_file():
            self.problem(path, "缺少全局 Rule 源文件")
            return
        self._add_asset(Asset(
            id="rule:global-agents",
            type="rule",
            name="全局 Agent Rules",
            domain="ai-agent",
            status="managed",
            purpose="跨项目协作约束",
            platforms=["cross-platform"],
            provenance="owner-produced",
            upstream_updates=False,
            source="global/AGENTS.md",
            path=path,
            native=True,
        ))

    def _load_skills(self) -> None:
        seen_paths: set[Path] = set()
        for base_name in ("skills", "vendor"):
            base = self.root / base_name
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("SKILL.md")):
                resolved = path.resolve()
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)
                try:
                    meta = _skill_frontmatter(path)
                except CatalogError as exc:
                    self.problem(path, str(exc))
                    continue
                slug = meta["name"]
                if not SLUG_RE.fullmatch(slug):
                    self.problem(path, f"skill name 不是有效 slug: {slug}")
                    continue
                if path.parent.name != slug:
                    self.problem(path, f"skill 目录名必须与 frontmatter name 一致: {slug}")
                    continue
                self._add_asset(Asset(
                    id=f"skill:{slug}",
                    type="skill",
                    name=slug,
                    domain="ai-agent",
                    status="managed",
                    purpose=meta.get("description", "Agent 可调用能力"),
                    platforms=["cross-platform"],
                    provenance="third-party" if base_name == "vendor" else "owner-produced",
                    upstream_updates=base_name == "vendor",
                    source=path.relative_to(self.root).as_posix(),
                    path=path,
                    native=True,
                ))

    def _load_workflows(self) -> None:
        base = self.root / "workflows"
        if not base.is_dir():
            return
        for path in sorted(base.glob("*.md")):
            try:
                data = _frontmatter(path)
            except CatalogError as exc:
                self.problem(path, str(exc))
                continue
            self._asset_from_data(path, data, expected_type="workflow")

    def _load_asset_files(self) -> None:
        base = self.root / "inventory" / "assets"
        if not base.is_dir():
            return
        for path in sorted(base.glob("*/*.toml")):
            try:
                data = _read_toml(path)
            except CatalogError as exc:
                self.problem(path, str(exc))
                continue
            self._asset_from_data(path, data, expected_type=path.parent.name)

    def _asset_from_data(self, path: Path, data: dict[str, Any], expected_type: str) -> None:
        required = ("id", "type", "name", "domain", "status", "purpose")
        for key in required:
            if not data.get(key):
                self.problem(path, f"缺少必填字段 {key}")
        asset_id = _text(data.get("id"))
        asset_type = _text(data.get("type"))
        if data.get("schema_version") != 1:
            self.problem(path, "schema_version 必须为 1")
        if not ID_RE.fullmatch(asset_id):
            self.problem(path, f"ID 必须符合 <type>:<slug>: {asset_id or '<empty>'}")
        if asset_id and asset_type and asset_id.split(":", 1)[0] != asset_type:
            self.problem(path, "ID 前缀必须与 type 一致")
        if asset_type != expected_type:
            self.problem(path, f"type 应为 {expected_type}，实际为 {asset_type or '<empty>'}")
        if asset_id and path.stem != asset_id.split(":", 1)[-1]:
            self.problem(path, f"文件名必须与资产 slug 一致: {asset_id.split(':', 1)[-1]}")
        self._validate_common(path, data)
        self._validate_extensions(path, data, asset_type)
        self._validate_upstream(path, data)
        self._validate_sensitive(path, data)
        incomplete = self._is_incomplete(data, asset_type)
        asset = Asset(
            id=asset_id,
            type=asset_type,
            name=_text(data.get("name")),
            domain=_text(data.get("domain")),
            status=_text(data.get("status")),
            purpose=_text(data.get("purpose")),
            platforms=_string_list(data.get("platforms")),
            provenance=_text(data.get("provenance")),
            upstream_updates=data.get("upstream_updates") is True,
            source=_text(data.get("fact_source")),
            path=path,
            data=data,
            relationships=_relations(data),
            stale=_is_stale(data, self.taxonomy.default_review_days if self.taxonomy else 90, self.today),
            incomplete=incomplete,
        )
        if asset_id:
            self._add_asset(asset)

    def _validate_common(self, path: Path, data: dict[str, Any]) -> None:
        taxonomy = self.taxonomy
        if taxonomy is None:
            return
        asset_type = _text(data.get("type"))
        domain = _text(data.get("domain"))
        status = _text(data.get("status"))
        if asset_type and asset_type not in taxonomy.asset_types:
            self.problem(path, f"未知资产类型: {asset_type}")
        if domain and domain not in taxonomy.domains:
            self.problem(path, f"未知功能领域: {domain}")
        if status and status not in taxonomy.statuses:
            self.problem(path, f"未知状态: {status}")
        platforms = data.get("platforms")
        if not isinstance(platforms, list) or not platforms:
            self.problem(path, "platforms 必须是非空数组")
        elif taxonomy.platforms:
            unknown = set(_string_list(platforms)) - taxonomy.platforms
            if unknown:
                self.problem(path, f"未知平台: {', '.join(sorted(unknown))}")
        preference = data.get("preference_source")
        if preference and taxonomy.preference_sources and preference not in taxonomy.preference_sources:
            self.problem(path, f"未知 preference_source: {preference}")
        provenance = data.get("provenance")
        if not provenance:
            self.problem(path, "缺少必填字段 provenance")
        elif taxonomy.provenance_types and provenance not in taxonomy.provenance_types:
            self.problem(path, f"未知 provenance: {provenance}")
        if "upstream_updates" not in data:
            self.problem(path, "缺少必填字段 upstream_updates")
        elif not isinstance(data["upstream_updates"], bool):
            self.problem(path, "upstream_updates 必须是布尔值")
        elif provenance == "owner-produced" and data["upstream_updates"]:
            self.problem(path, "用户自产资产没有上游更新，upstream_updates 必须为 false")
        for key in ("declared_on", "last_verified_on"):
            if key in data and _date(data[key]) is None:
                self.problem(path, f"{key} 必须是 ISO 日期")
        if "review_days" in data and (not isinstance(data["review_days"], int) or data["review_days"] < 1):
            self.problem(path, "review_days 必须为正整数")
        raw_relations = data.get("relationships", [])
        if not isinstance(raw_relations, list):
            self.problem(path, "relationships 必须是数组表")
        else:
            for item in raw_relations:
                if not isinstance(item, dict) or not item.get("type") or not item.get("target"):
                    self.problem(path, "relationships 项必须包含 type 与 target")
        for relation, target in _relations(data):
            if relation not in taxonomy.relationship_types:
                self.problem(path, f"未知关系类型: {relation or '<empty>'}")
            if not ID_RE.fullmatch(target):
                self.problem(path, f"关系目标不是有效资产 ID: {target or '<empty>'}")

    def _validate_extensions(self, path: Path, data: dict[str, Any], asset_type: str) -> None:
        if asset_type == "software":
            extension = data.get("software")
            if not isinstance(extension, dict):
                self.problem(path, "software 资产必须包含 [software]")
                return
            for key in ("post_restore_checks", "avoid_versions"):
                if key in extension and not isinstance(extension[key], list):
                    self.problem(path, f"software.{key} 必须是数组")
            install_form = extension.get("install_form")
            release_channel = extension.get("release_channel")
            if install_form and self.taxonomy and self.taxonomy.software_install_forms and install_form not in self.taxonomy.software_install_forms:
                self.problem(path, f"未知 software.install_form: {install_form}")
            if release_channel and self.taxonomy and self.taxonomy.release_channels and release_channel not in self.taxonomy.release_channels:
                self.problem(path, f"未知 software.release_channel: {release_channel}")
        elif asset_type == "development-tool":
            extension = data.get("development_tool")
            if not isinstance(extension, dict):
                self.problem(path, "development-tool 资产必须包含 [development_tool]")
                return
            for key in ("commands", "environment_variables", "verification_commands"):
                if key in extension and not isinstance(extension[key], list):
                    self.problem(path, f"development_tool.{key} 必须是数组")
            tool_kind = extension.get("tool_kind")
            if tool_kind and self.taxonomy and self.taxonomy.development_tool_kinds and tool_kind not in self.taxonomy.development_tool_kinds:
                self.problem(path, f"未知 development_tool.tool_kind: {tool_kind}")

    def _validate_upstream(self, path: Path, data: dict[str, Any]) -> None:
        upstream = data.get("upstream")
        if upstream is None:
            return
        if not isinstance(upstream, dict):
            self.problem(path, "upstream 必须是表")
            return
        if data.get("upstream_updates") is not True:
            self.problem(path, "只有跟踪上游更新的资产才能包含 [upstream]")
            return
        allowed = self.taxonomy.upstream_channels if self.taxonomy else set()
        channel = _text(upstream.get("channel"))
        if not channel:
            self.problem(path, "[upstream] 缺少 channel")
        elif allowed and channel not in allowed:
            self.problem(path, f"未知 upstream.channel: {channel}")
        identifier = _text(upstream.get("identifier"))
        latest = _text(upstream.get("latest_stable"))
        if channel == "unavailable":
            if identifier or latest:
                self.problem(path, "upstream.channel 为 unavailable 时不得填写 identifier 或 latest_stable")
        elif channel and not identifier:
            self.problem(path, f"[upstream] channel={channel} 缺少 identifier")
        pending = _text(upstream.get("pending_channel"))
        if pending:
            if allowed and pending not in allowed:
                self.problem(path, f"未知 upstream.pending_channel: {pending}")
            if pending == channel:
                self.problem(path, "upstream.pending_channel 不能与 channel 相同")
            if pending != "unavailable" and not _text(upstream.get("pending_identifier")):
                self.problem(path, "[upstream] 存在 pending_channel 时缺少 pending_identifier")
            if not _text(upstream.get("pending_note")):
                self.problem(path, "[upstream] 待切换渠道必须写明 pending_note 生效条件")

    def _is_incomplete(self, data: dict[str, Any], asset_type: str) -> bool:
        common = ("fact_source", "preference_source", "provenance", "declared_on", "last_verified_on")
        if any(not data.get(key) for key in common):
            return True
        if "upstream_updates" not in data:
            return True
        if data.get("preference_source") == "unknown":
            return True
        if asset_type == "software":
            extension = data.get("software", {})
            critical = ("install_form", "release_channel", "official_source", "minimum_verified_version")
            return any(not extension.get(key) or extension.get(key) == "unknown" for key in critical)
        if asset_type == "development-tool":
            extension = data.get("development_tool", {})
            return any(not extension.get(key) for key in ("tool_kind", "commands", "install_source", "version_constraint", "verification_commands"))
        return False

    def _validate_sensitive(self, path: Path, value: Any, keys: tuple[str, ...] = ()) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = str(key).lower()
                if _is_sensitive_key(normalized):
                    self.problem(path, f"禁止保存敏感字段: {'.'.join((*keys, str(key)))}")
                self._validate_sensitive(path, child, (*keys, str(key)))
            return
        if isinstance(value, list):
            for child in value:
                self._validate_sensitive(path, child, keys)
            return
        if not isinstance(value, str):
            return
        if any(regex.search(value) for regex in SENSITIVE_VALUE_RES):
            self.problem(path, f"疑似包含敏感值: {'.'.join(keys)}")
        key = keys[-1].lower() if keys else ""
        if key in LOGICAL_REFERENCE_KEYS and (
            WINDOWS_ABSOLUTE_RE.match(value)
            or UNC_RE.match(value)
            or value.startswith("/")
            or URL_RE.match(value)
        ):
            self.problem(path, f"{key} 必须是逻辑引用，不能是绝对路径或 URL")

    def _load_profiles(self) -> None:
        base = self.root / "inventory" / "profiles"
        if not base.is_dir():
            return
        for path in sorted(base.glob("*.toml")):
            try:
                data = _read_toml(path)
            except CatalogError as exc:
                self.problem(path, str(exc))
                continue
            if data.get("schema_version") != 1:
                self.problem(path, "schema_version 必须为 1")
            profile_id = _text(data.get("id"))
            if not SLUG_RE.fullmatch(profile_id):
                self.problem(path, f"profile id 必须是 slug: {profile_id or '<empty>'}")
            elif path.stem != profile_id:
                self.problem(path, f"文件名必须与 profile id 一致: {profile_id}")
            for key in ("name", "description"):
                if not data.get(key):
                    self.problem(path, f"缺少必填字段 {key}")
            platforms = data.get("platforms")
            if not isinstance(platforms, list) or not platforms:
                self.problem(path, "platforms 必须是非空数组")
            elif self.taxonomy and self.taxonomy.platforms:
                unknown = set(_string_list(platforms)) - self.taxonomy.platforms
                if unknown:
                    self.problem(path, f"未知平台: {', '.join(sorted(unknown))}")
            for key in ("last_verified_on",):
                if key in data and _date(data[key]) is None:
                    self.problem(path, f"{key} 必须是 ISO 日期")
            if "review_days" in data and (not isinstance(data["review_days"], int) or data["review_days"] < 1):
                self.problem(path, "review_days 必须为正整数")
            entries: list[ProfileEntry] = []
            raw_entries = data.get("assets", [])
            if not isinstance(raw_entries, list):
                self.problem(path, "assets 必须是数组表")
                raw_entries = []
            seen: set[str] = set()
            for item in raw_entries:
                if not isinstance(item, dict):
                    self.problem(path, "assets 项必须是表")
                    continue
                asset_id = _text(item.get("id"))
                tier = _text(item.get("tier"))
                if asset_id in seen:
                    self.problem(path, f"profile 资产重复: {asset_id}")
                seen.add(asset_id)
                if tier not in (self.taxonomy.profile_tiers if self.taxonomy else PROFILE_TIERS):
                    self.problem(path, f"未知 profile tier: {tier or '<empty>'}")
                entries.append(ProfileEntry(asset_id, tier, _text(item.get("notes"))))
            profile = Profile(
                profile_id,
                _text(data.get("name")),
                _text(data.get("description")),
                _string_list(data.get("platforms")),
                entries,
                path,
                data,
                _is_stale(data, self.taxonomy.default_review_days if self.taxonomy else 90, self.today),
            )
            if profile_id in self.profiles:
                self.problem(path, f"profile ID 重复: {profile_id}")
            elif profile_id:
                self.profiles[profile_id] = profile
            self._validate_sensitive(path, data)

    def _validate_references(self) -> None:
        for asset in self.assets.values():
            for relation, target in asset.relationships:
                if target and target not in self.assets:
                    self.problem(asset.path, f"关系 {relation} 指向不存在的资产: {target}")
        for profile in self.profiles.values():
            for entry in profile.entries:
                if entry.id not in self.assets:
                    self.problem(profile.path, f"profile 引用不存在的资产: {entry.id}")

    def _validate_profile_dependencies(self) -> None:
        for profile in self.profiles.values():
            selected = {entry.id for entry in profile.entries}
            for entry in profile.entries:
                asset = self.assets.get(entry.id)
                if not asset:
                    continue
                for relation, target in asset.relationships:
                    if relation == "depends-on" and target not in selected:
                        self.problem(
                            profile.path,
                            f"profile 缺少 {asset.id} 的必需依赖: {target}",
                        )

    def _validate_dependency_cycles(self) -> None:
        graph: dict[str, list[str]] = defaultdict(list)
        for asset in self.assets.values():
            graph[asset.id].extend(target for relation, target in asset.relationships if relation == "depends-on")
        visiting: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = []
        reported: set[tuple[str, ...]] = set()

        def visit(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                start = stack.index(node)
                cycle = tuple(stack[start:] + [node])
                if cycle not in reported:
                    reported.add(cycle)
                    self.problem(self.assets[node].path, f"depends-on 依赖环: {' -> '.join(cycle)}")
                return
            visiting.add(node)
            stack.append(node)
            for target in graph.get(node, []):
                if target in self.assets:
                    visit(target)
            stack.pop()
            visiting.remove(node)
            visited.add(node)

        for asset_id in sorted(graph):
            visit(asset_id)

    def render_text(self) -> str:
        by_type: dict[str, list[Asset]] = defaultdict(list)
        for asset in self.assets.values():
            by_type[asset.type].append(asset)
        lines = [
            "# HarnessOS 受管资产目录",
            "",
            "> 此文件由 `python scripts/catalog.py render` 生成，请修改原生事实源而不是本文件。",
            "",
            f"共 {len(self.assets)} 项资产、{len(self.profiles)} 个配置档。",
            "",
        ]
        for asset_type in sorted(by_type):
            lines.extend((
                f"## {asset_type}",
                "",
                "| ID | 名称 | 领域 | 来源性质 | 上游更新 | 状态 | 时效 | 偏好来源 | 用途 |",
                "|---|---|---|---|---|---|---|---|---|",
            ))
            for asset in sorted(by_type[asset_type], key=lambda item: item.id):
                freshness = "stale" if asset.stale else "incomplete" if asset.incomplete else "current"
                preference = _text(asset.data.get("preference_source")) if asset.data else "—"
                lines.append(
                    f"| `{asset.id}` | {_cell(asset.name)} | `{asset.domain}` | {_provenance_label(asset)} | {_upstream_label(asset)} | `{asset.status}` | `{freshness}` | {_cell(preference or '—')} | {_cell(_summary(asset.purpose))} |"
                )
            lines.append("")
        lines.extend(("## 关系", ""))
        relation_rows = [
            (asset.id, relation, target)
            for asset in self.assets.values()
            for relation, target in asset.relationships
        ]
        if relation_rows:
            lines.extend(("| 来源 | 关系 | 目标 |", "|---|---|---|"))
            for source, relation, target in sorted(relation_rows):
                lines.append(f"| `{source}` | `{relation}` | `{target}` |")
        else:
            lines.append("暂无显式关系。")
        lines.extend(("", "## 配置档", ""))
        if self.profiles:
            lines.extend(("| ID | 名称 | 平台 | 资产数 | 时效 |", "|---|---|---|---:|---|"))
            for profile in sorted(self.profiles.values(), key=lambda item: item.id):
                freshness = "stale" if profile.stale else "current"
                lines.append(
                    f"| `{profile.id}` | {_cell(profile.name)} | {_cell(', '.join(profile.platforms))} | {len(profile.entries)} | `{freshness}` |"
                )
        else:
            lines.append("暂无配置档。")
        attention = [asset for asset in self.assets.values() if asset.stale or asset.incomplete]
        lines.extend(("", "## 待复核", ""))
        if attention:
            for asset in sorted(attention, key=lambda item: item.id):
                reason = "已过复核周期" if asset.stale else "偏好或动态事实不完整"
                lines.append(f"- `{asset.id}`：{reason}")
        else:
            lines.append("暂无。")
        return "\n".join(lines).rstrip() + "\n"

    def render_html(self) -> str:
        assets: list[dict[str, Any]] = []
        for asset in sorted(self.assets.values(), key=lambda item: item.id):
            data = asset.data or {}
            details: list[dict[str, Any]] = []

            def add_detail(label: str, value: Any, kind: str = "text") -> None:
                if value in (None, "", []):
                    return
                if isinstance(value, (date, datetime)):
                    value = value.isoformat()
                details.append({"label": label, "value": value, "kind": kind})

            add_detail("事实源", asset.source, "path")
            add_detail("平台", asset.platforms, "list")
            add_detail("偏好来源", data.get("preference_source"))
            add_detail("声明日期", data.get("declared_on"))
            add_detail("最后核验", data.get("last_verified_on", data.get("verified_at")))
            review_days = data.get("review_days")
            add_detail("复核周期", f"{review_days} 天" if review_days else "")
            add_detail("备注", data.get("notes"))
            upstream = data.get("upstream") or {}
            add_detail("上游渠道", upstream.get("channel"))
            add_detail("渠道定位符", upstream.get("identifier"), "code")
            add_detail("渠道最新稳定版", upstream.get("latest_stable"), "code")
            add_detail("待切换渠道", upstream.get("pending_channel"))
            add_detail("待切换定位符", upstream.get("pending_identifier"), "code")
            add_detail("切换生效条件", upstream.get("pending_note"))
            if asset.relationships:
                add_detail(
                    "关系",
                    [f"{relation} → {target}" for relation, target in asset.relationships],
                    "list",
                )

            if asset.type == "software":
                extension = data.get("software", {})
                add_detail("安装形态", extension.get("install_form"))
                add_detail("发布通道", extension.get("release_channel"))
                add_detail("最低验证版本", extension.get("minimum_verified_version"))
                add_detail("固定版本", extension.get("pinned_version"))
                add_detail("避开版本", extension.get("avoid_versions"), "list")
                add_detail("官方来源", extension.get("official_source"), "url")
                add_detail("配置恢复", extension.get("config_restore"))
                add_detail("备份位置", extension.get("backup_location"))
                add_detail("恢复后检查", extension.get("post_restore_checks"), "list")
            elif asset.type == "development-tool":
                extension = data.get("development_tool", {})
                add_detail("工具类型", extension.get("tool_kind"))
                add_detail("命令", extension.get("commands"), "codes")
                add_detail("安装来源", extension.get("install_source"))
                add_detail("包 ID", extension.get("package_id"), "code")
                add_detail("版本约束", extension.get("version_constraint"), "code")
                add_detail("更新通道", extension.get("update_channel"))
                add_detail("环境变量", extension.get("environment_variables"), "codes")
                add_detail("配置引用", extension.get("config_reference"))
                add_detail("验证命令", extension.get("verification_commands"), "codes")

            freshness = "stale" if asset.stale else "incomplete" if asset.incomplete else "current"
            assets.append({
                "id": asset.id,
                "name": asset.name,
                "type": asset.type,
                "domain": asset.domain,
                "status": asset.status,
                "freshness": freshness,
                "purpose": asset.purpose,
                "provenance": _provenance_label(asset),
                "upstream": _upstream_label(asset),
                "details": details,
            })

        payload = json.dumps(
            {
                "assetCount": len(self.assets),
                "profileCount": len(self.profiles),
                "labels": {
                    "type": self.taxonomy.asset_type_labels if self.taxonomy else {},
                    "domain": self.taxonomy.domain_labels if self.taxonomy else {},
                },
                "assets": assets,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        payload = (
            payload.replace("&", "\\u0026")
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029")
        )
        try:
            template = CATALOG_HTML_TEMPLATE.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise CatalogError(f"缺少 HTML 模板: {CATALOG_HTML_TEMPLATE}") from exc
        marker = "__CATALOG_DATA__"
        if template.count(marker) != 1:
            raise CatalogError("HTML 模板必须且只能包含一个 __CATALOG_DATA__ 占位符")
        return template.replace(marker, payload)

    def plan_text(self, profile_id: str, satisfied: Iterable[str] = ()) -> str:
        profile = self.profiles.get(profile_id)
        if not profile:
            raise CatalogError(f"找不到配置档: {profile_id}")
        satisfied_ids = set(satisfied)
        profile_ids = {entry.id for entry in profile.entries}
        unknown_satisfied = satisfied_ids - profile_ids
        if unknown_satisfied:
            raise CatalogError(f"--satisfied 不在配置档中: {', '.join(sorted(unknown_satisfied))}")
        sections: dict[str, list[tuple[ProfileEntry, Asset]]] = {
            "需要恢复": [],
            "已经满足": [],
            "可选": [],
            "明确不恢复": [],
            "需要决定": [],
            "信息过期": [],
        }
        entries = self._dependency_order(profile.entries)
        for entry in entries:
            asset = self.assets.get(entry.id)
            if asset is None:
                continue
            if asset.status in {"excluded", "retired"}:
                section = "明确不恢复"
            elif asset.stale or profile.stale:
                section = "信息过期"
            elif asset.incomplete:
                section = "需要决定"
            elif entry.tier == "optional":
                section = "可选"
            elif asset.id in satisfied_ids:
                section = "已经满足"
            else:
                section = "需要恢复"
            sections[section].append((entry, asset))
        lines = [
            f"# {profile.name} 恢复计划",
            "",
            "> 此清单只用于规划；不会安装软件、连接服务或恢复数据。执行前须实时核验来源、兼容性、支持版本和许可条件。",
            "",
            profile.description,
            "",
        ]
        for title, items in sections.items():
            lines.extend((f"## {title}", ""))
            if not items:
                lines.append("- 无")
            else:
                for entry, asset in items:
                    suffix = f" — {entry.notes}" if entry.notes else ""
                    lines.append(
                        f"- `{asset.id}` {asset.name}（{entry.tier}；{_provenance_label(asset)}；上游更新{_upstream_label(asset)}）{suffix}"
                    )
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _dependency_order(self, entries: list[ProfileEntry]) -> list[ProfileEntry]:
        """Place in-profile dependencies before their consumers, stably."""
        selected = {entry.id for entry in entries}
        entry_by_id = {entry.id: entry for entry in entries}
        ordered: list[ProfileEntry] = []
        visited: set[str] = set()

        def add(asset_id: str) -> None:
            if asset_id in visited:
                return
            visited.add(asset_id)
            asset = self.assets.get(asset_id)
            if asset:
                for relation, target in asset.relationships:
                    if relation == "depends-on" and target in selected:
                        add(target)
            ordered.append(entry_by_id[asset_id])

        for entry in entries:
            add(entry.id)
        return ordered


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _summary(value: str, limit: int = 120) -> str:
    single_line = " ".join(value.split())
    match = re.search(r"[。.!?！？](?:\s|$)", single_line)
    if match:
        single_line = single_line[:match.end()].strip()
    if len(single_line) <= limit:
        return single_line
    return single_line[: limit - 1].rstrip() + "…"


def _provenance_label(asset: Asset) -> str:
    return "用户自产" if asset.provenance == "owner-produced" else "第三方"


def _upstream_label(asset: Asset) -> str:
    if asset.provenance == "owner-produced":
        return "不适用"
    if not asset.upstream_updates:
        return "不跟踪"
    upstream = (asset.data or {}).get("upstream") or {}
    channel = _text(upstream.get("channel"))
    if channel == "unavailable":
        label = "跟踪（渠道未确认）"
    elif channel:
        label = f"跟踪（{channel}）"
    else:
        label = "跟踪"
    pending = _text(upstream.get("pending_channel"))
    if pending:
        label += f"，{pending} 待切换"
    return label


def _configure_output_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def _profile_asset_ids(catalog: Catalog, profile_id: str | None) -> set[str] | None:
    if not profile_id:
        return None
    profile = catalog.profiles.get(profile_id)
    if not profile:
        raise CatalogError(f"找不到配置档: {profile_id}")
    return {entry.id for entry in profile.entries}


def _print_problems(catalog: Catalog) -> None:
    for problem in catalog.problems:
        print(f"ERROR: {problem.display(catalog.root)}", file=sys.stderr)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HarnessOS 受管资产目录")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="校验源数据与目录产物同步状态")
    subparsers.add_parser("render", help="重建 Markdown 与 HTML 目录")
    list_parser = subparsers.add_parser("list", help="查询受管资产")
    list_parser.add_argument("--type")
    list_parser.add_argument("--domain")
    list_parser.add_argument("--status")
    list_parser.add_argument("--profile")
    plan_parser = subparsers.add_parser("plan", help="生成配置档恢复清单（不执行）")
    plan_parser.add_argument("profile")
    plan_parser.add_argument(
        "--satisfied",
        action="append",
        default=[],
        metavar="ASSET_ID",
        help="标记目标环境已满足的资产；可重复使用，不写回配置档",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    _configure_output_encoding()
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    catalog = Catalog(args.root).load()
    if catalog.problems:
        _print_problems(catalog)
        return 1
    output_path = catalog.root / CATALOG_NAME
    html_output_path = catalog.root / CATALOG_HTML_NAME
    if args.command == "render":
        try:
            markdown = catalog.render_text()
            html = catalog.render_html()
        except CatalogError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        output_path.write_text(markdown, encoding="utf-8", newline="\n")
        html_output_path.write_text(html, encoding="utf-8", newline="\n")
        print(f"已生成 {output_path} 与 {html_output_path}")
        return 0
    if args.command == "check":
        try:
            outputs = (
                (CATALOG_NAME, output_path, catalog.render_text()),
                (CATALOG_HTML_NAME, html_output_path, catalog.render_html()),
            )
        except CatalogError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        for name, path, expected in outputs:
            try:
                actual = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                print(f"ERROR: 缺少 {name}，请运行 catalog.py render", file=sys.stderr)
                return 1
            if actual.replace("\r\n", "\n") != expected:
                print(f"ERROR: {name} 与源数据不同步，请运行 catalog.py render", file=sys.stderr)
                return 1
        print(f"资产目录检查通过：{len(catalog.assets)} 项资产，{len(catalog.profiles)} 个配置档")
        return 0
    if args.command == "list":
        try:
            profile_ids = _profile_asset_ids(catalog, args.profile)
        except CatalogError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        assets = [
            asset for asset in catalog.assets.values()
            if (not args.type or asset.type == args.type)
            and (not args.domain or asset.domain == args.domain)
            and (not args.status or asset.status == args.status)
            and (profile_ids is None or asset.id in profile_ids)
        ]
        for asset in sorted(assets, key=lambda item: item.id):
            freshness = "stale" if asset.stale else "incomplete" if asset.incomplete else "current"
            print(
                f"{asset.id}\t{asset.status}\t{freshness}\t{_provenance_label(asset)}\t{_upstream_label(asset)}\t{asset.name}"
            )
        return 0
    if args.command == "plan":
        try:
            print(catalog.plan_text(args.profile, args.satisfied), end="")
        except CatalogError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
