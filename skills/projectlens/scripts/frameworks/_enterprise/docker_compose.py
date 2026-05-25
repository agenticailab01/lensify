"""Docker Compose adapter — surfaces services + their networking surface.

Triggers on the presence of `docker-compose.yml/yaml` or `compose.yml/yaml`
files in the project (file-presence detection).

Extracts per service:
    - image: or build:
    - exposed ports
    - mounted volumes (count + first few)
    - depends_on links (the dependency graph)
    - environment file references

Uses an indent-aware YAML walker — no PyYAML dependency. The walker only
recognises top-level structure (services / volumes / networks) and treats
each service block as a flat key/value bag, which is plenty for an
overview-grade summary.

Output: ## DOCKER-COMPOSE capsule section.
"""
from __future__ import annotations

import re
from pathlib import Path

try:
    from ..base import (
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_MEDIUM, cap_entries,
    )
    from .._util import truncate, safe_read
except ImportError:
    from base import (  # type: ignore[no-redef]
        FrameworkAdapter, FrameworkInfo, FrameworkEntry,
        PRIORITY_MEDIUM, cap_entries,
    )
    from _util import truncate, safe_read  # type: ignore[no-redef]


_COMPOSE_NAMES = (
    "docker-compose.yml", "docker-compose.yaml",
    "compose.yml", "compose.yaml",
)


def _parse_services(text: str) -> dict:
    """Very small indent-aware parser. Returns {service_name: {key: raw_value}}."""
    services: dict[str, dict] = {}
    current_service: str | None = None
    current_block_indent = 0
    in_services = False
    services_indent = 0

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.lstrip()

        if not in_services:
            if re.match(r"""^services\s*:""", stripped) and indent == 0:
                in_services = True
                services_indent = -1  # will be set by first service entry
            continue

        # Exit services block if dedent past services_indent
        if services_indent != -1 and indent < services_indent and stripped.endswith(":"):
            in_services = False
            continue

        # New service definition: indent slightly past services key, ends with :
        if stripped.endswith(":") and (services_indent == -1 or indent == services_indent):
            services_indent = indent
            current_service = stripped[:-1].strip()
            services[current_service] = {"_raw": []}
            current_block_indent = indent + 2  # typical
            continue

        if current_service and indent >= current_block_indent:
            services[current_service]["_raw"].append(stripped)

    return services


def _summarise_service(raw_lines: list[str]) -> dict:
    """Pull image, ports, volumes, depends_on from a service's raw lines."""
    out = {
        "image": None, "build": None, "ports": [],
        "volumes_count": 0, "depends_on": [], "env_file": [],
    }
    in_ports = False
    in_volumes = False
    in_depends = False
    for raw in raw_lines:
        if re.match(r"""^image\s*:\s*""", raw):
            out["image"] = re.sub(r"""^image\s*:\s*['"]?""", "", raw).rstrip("'\"")
            in_ports = in_volumes = in_depends = False
            continue
        if re.match(r"""^build\s*:""", raw):
            out["build"] = raw.split(":", 1)[1].strip().strip("'\"") or "(context)"
            in_ports = in_volumes = in_depends = False
            continue
        if re.match(r"""^ports\s*:""", raw):
            in_ports, in_volumes, in_depends = True, False, False
            continue
        if re.match(r"""^volumes\s*:""", raw):
            in_volumes, in_ports, in_depends = True, False, False
            continue
        if re.match(r"""^depends_on\s*:""", raw):
            in_depends, in_ports, in_volumes = True, False, False
            continue
        if re.match(r"""^env_file\s*:""", raw):
            # Single value form: env_file: .env
            value = raw.split(":", 1)[1].strip()
            if value:
                out["env_file"].append(value.strip("'\""))
            continue
        if re.match(r"""^environment\s*:""", raw):
            in_ports = in_volumes = in_depends = False
            continue

        if raw.startswith("- "):
            value = raw[2:].strip().strip("'\"")
            if in_ports:
                out["ports"].append(value)
            elif in_volumes:
                out["volumes_count"] += 1
            elif in_depends:
                out["depends_on"].append(value)
        else:
            # Non-list line ends the current sub-block
            in_ports = in_volumes = in_depends = False
    return out


class DockerComposeAdapter(FrameworkAdapter):
    name = "docker_compose"
    detect_signatures = ("docker-compose",)
    priority = PRIORITY_MEDIUM
    max_entries = 20

    @classmethod
    def detect(cls, walk_result, parsed_files) -> bool:
        for rec in walk_result.files:
            if Path(rec.path).name in _COMPOSE_NAMES:
                return True
        return False

    def extract(self, walk_result, parsed_files) -> FrameworkInfo:
        info = FrameworkInfo(name=self.name)
        info.detected_signatures = ["docker-compose.yml"]

        entries: list[FrameworkEntry] = []
        for rec in walk_result.files:
            if Path(rec.path).name not in _COMPOSE_NAMES:
                continue
            text = safe_read(rec.abs_path)
            if text is None:
                continue
            services = _parse_services(text)
            for name, blk in services.items():
                summary = _summarise_service(blk["_raw"])
                entries.append(FrameworkEntry(
                    kind="service",
                    name=name,
                    signature=summary.get("image") or summary.get("build") or "(local)",
                    path=rec.path, line=1,
                    confidence="EXTRACTED",
                    meta={
                        "image": summary["image"],
                        "build": summary["build"],
                        "ports": summary["ports"],
                        "volumes_count": summary["volumes_count"],
                        "depends_on": summary["depends_on"],
                        "env_file": summary["env_file"],
                        "compose_file": rec.path,
                    },
                ))

        entries.sort(key=lambda e: (e.path, e.name))
        info.entries = cap_entries(entries, self.max_entries)
        return info

    def capsule_section(self, info: FrameworkInfo, budget_tokens: int) -> str | None:
        if not info.entries:
            return None
        lines = ["## DOCKER-COMPOSE"]
        for e in info.entries:
            m = e.meta
            img_or_build = m.get("image") or (f"build {m['build']}" if m.get("build") else "(none)")
            lines.append(f"- service `{e.name}` — {img_or_build}  ({e.path})")
            if m.get("ports"):
                lines.append(f"  - ports: {', '.join(m['ports'][:4])}")
            if m.get("depends_on"):
                lines.append(f"  - depends_on: {', '.join(m['depends_on'][:4])}")
            if m.get("volumes_count"):
                lines.append(f"  - volumes: {m['volumes_count']}")
        return truncate("\n".join(lines), budget_tokens)
