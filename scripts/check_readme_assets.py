#!/usr/bin/env python3
"""校验多语言 README 的配图是否与各自语言配对。

规则（见 SKILL.md 第一节）：
  无后缀 = 主语言版本；-en = 英文版本
  中文 README 不许引用 -en 图；英文 README 不许引用无后缀图。

用法:
    python3 check_readme_assets.py [repo_root] [--main zh|en]

默认主语言 zh。退出码非 0 表示有问题。
"""
import os
import re
import sys
from typing import Optional

# README 文件名 -> 该文件"应有的语言"
ZH_FILES = ("README.md", "README.zh.md", "README.zh-CN.md")
EN_FILES = ("README.en.md", "README.en-US.md")

ASSET_RE = re.compile(r'(?:src=|!\[[^\]]*\]\()["\']?([^"\')>\s]+\.(?:svg|png|jpg|jpeg|gif|webp))', re.I)

# XML 里非法的 HTML 命名实体（SVG 是 XML，只认 &amp; &lt; &gt; &quot; &apos;）
XML_LEGAL_ENTITIES = {"amp", "lt", "gt", "quot", "apos"}
ENTITY_RE = re.compile(r'&([a-zA-Z][a-zA-Z0-9]*);')


def strip_code_blocks(text):
    """剔除 markdown 代码块与行内代码，避免把示例文字误当成图片引用。"""
    text = re.sub(r'```.*?```', '', text, flags=re.S)      # 围栏代码块
    text = re.sub(r'~~~.*?~~~', '', text, flags=re.S)      # 波浪号代码块
    text = re.sub(r'`[^`\n]*`', '', text)                  # 行内代码
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)     # 注释
    return text


def check_svg_content(path):
    """查 SVG 里有没有会让 Chrome 报解析错的 HTML 实体。返回问题列表。"""
    issues = []
    try:
        text = open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        return [f"无法读取: {e}"]

    for name in set(ENTITY_RE.findall(text)):
        if name not in XML_LEGAL_ENTITIES:
            issues.append(f"HTML 实体 &{name}; 在 XML/SVG 里非法 → 改用真实字符")

    # 未转义的 & （后面不是实体）
    for m in re.finditer(r'&(?![a-zA-Z][a-zA-Z0-9]*;|#\d+;|#x[0-9a-fA-F]+;)', text):
        line = text[:m.start()].count("\n") + 1
        issues.append(f"第 {line} 行有未转义的 & → 用 &amp;")
        break

    return issues


def lang_of(readme, main_lang):
    """这个 README 文件是哪个语言。"""
    if readme in EN_FILES:
        return "en"
    if readme in ZH_FILES:
        if readme == "README.md":
            return main_lang          # README.md 的语言 = 主语言
        return "zh"
    return None


def expected_suffix(lang):
    """该语言的图是否应该带 -en 后缀（仅英文带）。"""
    return lang == "en"


def check(root: str, main_lang: str = "zh") -> int:
    readmes = [f for f in os.listdir(root)
               if f.startswith("README") and f.endswith(".md")]
    if not readmes:
        print("  ✗ 没找到任何 README*.md")
        return 1

    problems = 0
    print(f"主语言: {main_lang}\n")

    for readme in sorted(readmes):
        lang = lang_of(readme, main_lang)
        if lang is None:
            print(f"  ? {readme}: 语言无法判定，跳过")
            continue

        want_en = expected_suffix(lang)
        raw = open(os.path.join(root, readme), encoding="utf-8").read()
        assets = sorted(set(ASSET_RE.findall(strip_code_blocks(raw))))

        tag = "英文" if lang == "en" else "中文"
        print(f"  {readme}  [{tag}]  应引用{' -en 图' if want_en else ' 无后缀图'}")
        if not assets:
            print("     (无图片引用)")
            continue

        for a in assets:
            base = os.path.basename(a)
            is_en = "-en." in base

            # ① 语言配对
            if want_en and not is_en:
                print(f"     ✗ 语言错配: {a}  (英文 README 应引用 -en 图)")
                problems += 1
                continue
            if not want_en and is_en:
                print(f"     ✗ 语言错配: {a}  (中文 README 不该引用 -en 图)")
                problems += 1
                continue

            # ② 文件存在（跳过网络图片）
            if a.startswith(("http://", "https://", "data:")):
                print(f"     · 外链: {a[:60]}")
                continue
            full = os.path.join(root, a)
            if not os.path.isfile(full):
                print(f"     ✗ 断图: {a}  (文件不存在)")
                problems += 1
                continue

            # ③ SVG 内容检查（HTML 实体会让 Chrome 报解析错）
            if a.lower().endswith(".svg"):
                issues = check_svg_content(full)
                if issues:
                    print(f"     ✗ {a} 内容有问题:")
                    for it in issues:
                        print(f"        · {it}")
                    problems += len(issues)
                else:
                    print(f"     ✓ {a}")
            else:
                print(f"     ✓ {a}")

        # ③ 反向检查：有 -en 图，但是否有英文 README 在用
    has_en_readme = any(lang_of(r, main_lang) == "en" for r in readmes)
    for d in (os.path.join(root, "assets"), os.path.join(root, "docs", "assets")):
        if not os.path.isdir(d):
            continue
        en_imgs = sorted(f for f in os.listdir(d) if "-en." in f)
        if en_imgs and not has_en_readme:
            print(f"\n  ⚠ {d} 有 {len(en_imgs)} 张 -en 图，但没有任何英文 README 引用它们")
            print(f"     （README.md 是主语言，不算英文版）→ 要么补 README.en.md，要么删图")
            problems += 1

    print()
    if problems:
        print(f"  ✗ {problems} 个问题，先修完再推送")
        return 1
    print("  ✓ 全部配对正确")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = args[0] if args else "."
    main = "zh"
    if "--main" in sys.argv:
        main = sys.argv[sys.argv.index("--main") + 1]
    if main not in ("zh", "en"):
        print("--main 只能是 zh 或 en")
        sys.exit(2)
    sys.exit(check(root, main))
