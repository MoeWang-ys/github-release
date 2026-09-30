#!/usr/bin/env python3
"""github.com 被墙时，用 GitHub REST API 推送文件（绕开 git 传输协议）。

适用症状：`github.com:443` 超时（curl 返回 000），但 `api.github.com` 正常（200）。

用法:
    export GITHUB_TOKEN=ghp_xxx
    python3 push_via_api.py <owner>/<repo> <file> [file ...] --message "commit msg"

    # 常用选项
    --branch main          目标分支（默认 main）

脚本流程：取 HEAD → 建 blob → 建 tree → 建 commit → 更新 ref。

⚠ 副作用：本地与远端 commit SHA 会不同（时间戳不同），但内容字节级一致。
   git status 会显示 ahead N，是假象。网络恢复后：
   git fetch && git reset --hard origin/main
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"


def gh(token, method, path, body=None):
    req = urllib.request.Request(
        API + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
    )
    req.add_header("Authorization", "token " + token)
    req.add_header("Accept", "application/vnd.github+json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:500]
        print(f"  ✗ HTTP {e.code} on {method} {path}\n    {detail}")
        raise SystemExit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", help="owner/repo")
    ap.add_argument("files", nargs="*", help="要推送的文件（相对路径）")
    ap.add_argument("--message", "-m", default="update via API")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--delete", "-d", nargs="*", default=[],
                    help="要从仓库删除的路径（可与 files 同时用）")
    args = ap.parse_args()

    if not args.files and not args.delete:
        print("  ✗ 没指定要推送或删除的文件")
        return 2

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("  ✗ 没设 GITHUB_TOKEN")
        print("    export GITHUB_TOKEN=ghp_xxx")
        return 2

    repo = args.repo
    for f in args.files:
        if not os.path.isfile(f):
            print(f"  ✗ 文件不存在: {f}")
            return 2
    # 1. 取当前 HEAD
    try:
        ref = gh(token, "GET", f"/repos/{repo}/git/ref/heads/{args.branch}")
        base_sha = ref["object"]["sha"]
        base = gh(token, "GET", f"/repos/{repo}/git/commits/{base_sha}")
    except SystemExit:
        print(f"    分支 {args.branch} 不存在？首次推送请用别的流程建仓库。")
        return 1

    print(f"  base: {base_sha[:7]}  ({args.branch})")

    # 2. 建 blob
    tree = []
    for f in args.files:
        content = open(f, "rb").read()
        blob = gh(token, "POST", f"/repos/{repo}/git/blobs", {
            "content": base64.b64encode(content).decode(),
            "encoding": "base64",
        })
        tree.append({"path": f, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print(f"  add  {f:<40} {len(content):>7}B  {blob['sha'][:7]}")

    # 2b. 删除：tree entry 的 sha 传 None 即代表删除
    for f in args.delete:
        tree.append({"path": f, "mode": "100644", "type": "blob", "sha": None})
        print(f"  del  {f}")

    # 3. 建 tree
    new_tree = gh(token, "POST", f"/repos/{repo}/git/trees",
                  {"base_tree": base["tree"]["sha"], "tree": tree})
    print(f"  tree: {new_tree['sha'][:7]}")

    # 4. 建 commit
    commit = gh(token, "POST", f"/repos/{repo}/git/commits", {
        "message": args.message,
        "tree": new_tree["sha"],
        "parents": [base_sha],
    })
    print(f"  commit: {commit['sha'][:7]}")

    # 5. 更新 ref
    gh(token, "PATCH", f"/repos/{repo}/git/refs/heads/{args.branch}",
       {"sha": commit["sha"], "force": False})
    print(f"\n  ✓ 推送完成 -> https://github.com/{repo}/commit/{commit['sha']}")
    print(f"    本地 SHA 会与线上不同（内容一致），网络恢复后：")
    print(f"    git fetch && git reset --hard origin/{args.branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
