#!/usr/bin/env python3
"""在 GitHub 上发现可用于 KiCad 训练的数据仓库。"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request
import urllib.error
import http.client
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


PERMISSIVE_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "BSD-4-Clause",
    "BSD-0-Clause",
    "ISC",
    "Zlib",
    "CC0-1.0",
    "Unlicense",
    "CERN-OHL-P-2.0",
}

EXCLUDED_REPO_KEYWORDS = {
    "library",
    "footprint",
    "symbol",
    "template",
    "kicadlib",
    "kicad-library",
    "pretty",
    "3d-model",
}


@dataclass
class RepoCandidate:
    full_name: str
    html_url: str
    default_branch: str
    license_spdx: str
    stargazers_count: int
    has_kicad_pcb: bool
    has_kicad_sch: bool
    has_net: bool
    is_library_like: bool
    is_permissive_license: bool
    include: bool
    include_reason: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "full_name": self.full_name,
            "html_url": self.html_url,
            "default_branch": self.default_branch,
            "license_spdx": self.license_spdx,
            "stargazers_count": self.stargazers_count,
            "has_kicad_pcb": self.has_kicad_pcb,
            "has_kicad_sch": self.has_kicad_sch,
            "has_net": self.has_net,
            "is_library_like": self.is_library_like,
            "is_permissive_license": self.is_permissive_license,
            "include": self.include,
            "include_reason": self.include_reason,
        }


def github_get(url: str, token: Optional[str], max_retries: int = 4) -> Dict[str, object]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "aieda-kicad-discovery",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")

    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            transient_status = {429, 500, 502, 503, 504}
            if error.code in transient_status and attempt < max_retries:
                time.sleep(1.5 * (2 ** attempt))
                continue
            raise
        except urllib.error.URLError:
            if attempt < max_retries:
                time.sleep(1.5 * (2 ** attempt))
                continue
            raise
        except (http.client.IncompleteRead, TimeoutError):
            if attempt < max_retries:
                time.sleep(1.5 * (2 ** attempt))
                continue
            raise

    raise RuntimeError("GitHub API 请求失败且超出重试次数")


def search_repositories(query: str, per_page: int, page: int, token: Optional[str]) -> List[Dict[str, object]]:
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page={per_page}&page={page}"
    payload = github_get(url, token)
    items = payload.get("items", [])
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def get_repo_tree(owner: str, repo: str, branch: str, token: Optional[str]) -> List[str]:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    payload = github_get(url, token)
    tree_items = payload.get("tree", [])
    if not isinstance(tree_items, list):
        return []
    paths: List[str] = []
    for item in tree_items:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        if isinstance(path, str):
            paths.append(path)
    return paths


def has_suffix(paths: Iterable[str], suffix: str) -> bool:
    suffix_lower = suffix.lower()
    for path in paths:
        if path.lower().endswith(suffix_lower):
            return True
    return False


def is_permissive_license(spdx: str) -> bool:
    return spdx in PERMISSIVE_LICENSES


def is_library_like_repo(full_name: str, description: str) -> bool:
    text = f"{full_name} {description}".lower()
    return any(keyword in text for keyword in EXCLUDED_REPO_KEYWORDS)


def evaluate_repo(repo: Dict[str, object], token: Optional[str]) -> Optional[RepoCandidate]:
    full_name = str(repo.get("full_name", ""))
    if not full_name or "/" not in full_name:
        return None
    owner, repo_name = full_name.split("/", 1)
    default_branch = str(repo.get("default_branch", "main"))
    html_url = str(repo.get("html_url", ""))
    description = str(repo.get("description", "") or "")
    stargazers_count = int(repo.get("stargazers_count", 0))

    license_payload = repo.get("license")
    license_spdx = "UNKNOWN"
    if isinstance(license_payload, dict):
        license_spdx = str(license_payload.get("spdx_id") or "UNKNOWN")

    paths = get_repo_tree(owner=owner, repo=repo_name, branch=default_branch, token=token)
    has_pcb = has_suffix(paths, ".kicad_pcb")
    has_sch = has_suffix(paths, ".kicad_sch")
    has_net = has_suffix(paths, ".net")
    library_like = is_library_like_repo(full_name, description)
    permissive = is_permissive_license(license_spdx)

    include = has_pcb and permissive and (not library_like)
    if not has_pcb:
        reason = "exclude:no_kicad_pcb"
    elif not permissive:
        reason = f"exclude:license_{license_spdx}"
    elif library_like:
        reason = "exclude:library_or_template_repo"
    else:
        reason = "include:meets_requirements"

    return RepoCandidate(
        full_name=full_name,
        html_url=html_url,
        default_branch=default_branch,
        license_spdx=license_spdx,
        stargazers_count=stargazers_count,
        has_kicad_pcb=has_pcb,
        has_kicad_sch=has_sch,
        has_net=has_net,
        is_library_like=library_like,
        is_permissive_license=permissive,
        include=include,
        include_reason=reason,
    )


def run_discovery(
    output_file: str,
    target_count: int,
    max_pages: int,
    per_page: int,
    token: Optional[str],
    sleep_seconds: float,
) -> Dict[str, object]:
    queries = [
        "kicad pcb in:name,description,readme is:public archived:false",
        "kicad_pcb hardware in:name,description,readme is:public archived:false",
        "open hardware kicad in:name,description,readme is:public archived:false",
    ]

    seen = set()
    candidates: List[RepoCandidate] = []

    for query in queries:
        for page in range(1, max_pages + 1):
            repos = search_repositories(query=query, per_page=per_page, page=page, token=token)
            if not repos:
                break
            for repo in repos:
                full_name = str(repo.get("full_name", ""))
                if not full_name or full_name in seen:
                    continue
                seen.add(full_name)
                try:
                    evaluated = evaluate_repo(repo=repo, token=token)
                except Exception:
                    # 某些仓库 tree 很大或网络抖动时直接跳过，避免整批任务中断。
                    continue
                if evaluated is None:
                    continue
                candidates.append(evaluated)

                included = [item for item in candidates if item.include]
                if len(included) >= target_count:
                    break
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
            if len([item for item in candidates if item.include]) >= target_count:
                break
        if len([item for item in candidates if item.include]) >= target_count:
            break

    included_repos = sorted(
        [candidate for candidate in candidates if candidate.include],
        key=lambda item: item.stargazers_count,
        reverse=True,
    )[:target_count]
    excluded_repos = [candidate for candidate in candidates if not candidate.include]

    payload = {
        "policy": {
            "target_count": target_count,
            "permissive_licenses": sorted(PERMISSIVE_LICENSES),
            "excluded_repo_keywords": sorted(EXCLUDED_REPO_KEYWORDS),
            "queries": queries,
        },
        "stats": {
            "total_examined": len(candidates),
            "included": len(included_repos),
            "excluded": len(excluded_repos),
        },
        "included_repositories": [candidate.to_dict() for candidate in included_repos],
        "excluded_repositories": [candidate.to_dict() for candidate in excluded_repos],
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="发现可用的 GitHub KiCad 训练仓库")
    parser.add_argument("--output-file", required=True, help="输出 whitelist manifest JSON")
    parser.add_argument("--target-count", type=int, default=30, help="目标纳入仓库数量")
    parser.add_argument("--max-pages", type=int, default=3, help="每个查询最大页数")
    parser.add_argument("--per-page", type=int, default=20, help="每页仓库数")
    parser.add_argument("--sleep-seconds", type=float, default=0.2, help="请求节流秒数")
    parser.add_argument(
        "--github-token",
        default=os.getenv("GITHUB_TOKEN", ""),
        help="GitHub token，默认读取 GITHUB_TOKEN",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run_discovery(
        output_file=args.output_file,
        target_count=args.target_count,
        max_pages=args.max_pages,
        per_page=args.per_page,
        token=args.github_token or None,
        sleep_seconds=max(0.0, args.sleep_seconds),
    )
    print(json.dumps(payload["stats"], indent=2, ensure_ascii=False))
    print(f"manifest saved to: {args.output_file}")


if __name__ == "__main__":
    main()
