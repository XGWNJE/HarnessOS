#!/usr/bin/env python3
"""Read-only inventory; never follow directory links or delete resources."""

import argparse
import collections
import datetime
import heapq
import json
import os
import stat
import sys
import time


def native_path(path):
    path = os.path.abspath(path)
    if os.name != "nt" or path.startswith("\\\\?\\"):
        return path
    if path.startswith("\\\\"):
        return "\\\\?\\UNC\\" + path[2:]
    return "\\\\?\\" + path


def inventory(requested_root, depth=3, top=20, dedupe_hardlinks=False):
    root = os.path.realpath(os.path.abspath(requested_root))
    scan_root = native_path(root)
    if not os.path.isdir(scan_root):
        raise ValueError("Root must be an existing directory")
    started = time.monotonic()
    totals = collections.defaultdict(lambda: [0, 0])
    largest = []
    seen = set()
    logical_bytes = unique_bytes = files = errors = links = special_files = 0
    error_samples, link_samples = [], []

    def record_error(relative, error):
        nonlocal errors
        errors += 1
        if len(error_samples) < 20:
            error_samples.append({"path": relative, "error": str(error)})

    stack = [(scan_root, ())]
    while stack:
        directory, parts = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    child_parts = (*parts, entry.name)
                    relative = "/".join(child_parts)
                    try:
                        info = entry.stat(follow_symlinks=False)
                        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                            links += 1
                            if len(link_samples) < 50:
                                link_samples.append(relative)
                            continue
                        if stat.S_ISDIR(info.st_mode):
                            stack.append((entry.path, child_parts))
                            continue
                        if not stat.S_ISREG(info.st_mode):
                            special_files += 1
                            continue
                        # Windows DirEntry.stat can omit inode/link fields.
                        if dedupe_hardlinks:
                            info = os.stat(entry.path, follow_symlinks=False)
                        size = info.st_size
                        files += 1
                        logical_bytes += size
                        if dedupe_hardlinks:
                            if info.st_nlink > 1:
                                if not info.st_ino:
                                    raise ValueError("Filesystem did not supply a hardlink identity")
                                identity = (info.st_dev, info.st_ino)
                                if identity not in seen:
                                    unique_bytes += size
                                    seen.add(identity)
                            else:
                                unique_bytes += size
                        if len(child_parts) == 1:
                            totals[entry.name][0] += size
                            totals[entry.name][1] += 1
                        for length in range(1, min(len(child_parts) - 1, depth) + 1):
                            group = "/".join(child_parts[:length])
                            totals[group][0] += size
                            totals[group][1] += 1
                        item = (size, relative)
                        if len(largest) < top:
                            heapq.heappush(largest, item)
                        elif item > largest[0]:
                            heapq.heapreplace(largest, item)
                    except (OSError, ValueError) as error:
                        record_error(relative, error)
        except OSError as error:
            record_error("/".join(parts) or ".", error)

    groups = [
        {"path": name, "logicalBytes": size, "files": count}
        for name, (size, count) in totals.items()
    ]
    groups.sort(key=lambda row: (-row["logicalBytes"], row["path"]))
    return {
        "format": "agent-workspace-inventory-v1",
        "root": root,
        "scannedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "seconds": round(time.monotonic() - started, 3),
        "complete": errors == 0,
        "logicalBytes": logical_bytes,
        "uniqueFileBytes": unique_bytes if dedupe_hardlinks and not errors else None,
        "files": files,
        "topLevel": [row for row in groups if "/" not in row["path"]],
        "largestGroups": groups[:top],
        "largestFiles": [
            {"path": name, "logicalBytes": size} for size, name in sorted(largest, reverse=True)
        ],
        "linksSkipped": links,
        "linkSamples": link_samples,
        "specialFilesSkipped": special_files,
        "errors": errors,
        "errorSamples": error_samples,
        "measurement": "Logical bytes only; groups overlap. Unique bytes deduplicate hardlinks inside this root only. No allocated-space or reclaimability claim. Links are excluded.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--depth", type=int, default=3, choices=range(1, 9))
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--dedupe-hardlinks", action="store_true")
    parser.add_argument("--output", help="Write JSON here after scanning; otherwise print to stdout")
    args = parser.parse_args()
    if not 1 <= args.top <= 1000:
        parser.error("--top must be between 1 and 1000")
    try:
        result = inventory(args.root, args.depth, args.top, args.dedupe_hardlinks)
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        # Exclusive creation also prevents accidentally replacing a source file.
        with open(native_path(args.output), "x", encoding="utf-8") as output:
            output.write(payload)
    else:
        print(payload, end="")
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
