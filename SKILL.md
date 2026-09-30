---
name: github-release
description: 把本地项目/仓库发布到 GitHub —— 默认中文 README 当主语言、多语言 README 配图与主语言严格配对、README 行文风格固化为「效果→问题→怎么用」(zarazhangrui 风格)、网络被墙时自动改走 REST API 推送。触发词：发布到 github、推到 github、github 发布、建仓库、推到远程、开源发布、publish to github、新建 repo、readme 重建、多语言 readme、README 配图。触发词还包含：上 github、push 上去、发个 repo、release。
---

# GitHub 发布

把本地项目发布到 GitHub。**本 skill 只负责"发布"这一段**，不负责造图（造图交给 `svg-infographic`）。

四件事按顺序做：

1. **定语言策略** —— 谁是主语言，文件怎么命名
2. **校验图片配对** —— 每个语言的 README 配它自己语言的图
3. **重建 README** —— 按固化风格：效果 → 问题 → 怎么用
4. **推送** —— git 不通时自动走 REST API

---

## 一、语言策略（★ 核心规则）

### 默认：中文是主语言

```
README.md         ← 中文（主语言，GitHub 打开即见）
README.en.md      ← 英文
```

**为什么默认中文**：用户的地盘是中文，主语言该让中文用户零点击。

> 只有用户明确说"主语言用英文"时才反转（那就 `README.md` 英文 + `README.zh-CN.md` 中文）。
> 拿不准就问一句，别自己改。

### 图片命名：跟随主语言

**★ 铁律：每个语言的 README，配它自己语言的图。中文 README 里不许出现英文图。**

```
无后缀 = 主语言版本；-en = 英文版本
```

| 主语言 | README.md 引用 | README.en.md 引用 |
|---|---|---|
| **中文（默认）** | `hero.svg`、`flow.svg` | `hero-en.svg`、`flow-en.svg` |
| 英文 | `hero-en.svg` | `hero.svg` |

一句话记法：**主语言吃"素名"，英文吃 `-en`。**

### 新增语言

第三语言（如日文）扩展：`README.ja.md` + `hero-ja.svg`。
规则不变 —— 谁的语言，配谁的图。

---

## 二、图片配对校验（推送前必做）

**别靠肉眼。** 每个语言 README 引用的每张图，都得确认它存在、且语言对得上。

```bash
# 中文 README 里不该出现 -en 图
grep -o 'assets/[a-z0-9_-]*\.svg' README.md | sort -u
# 应输出：assets/hero.svg …（不含 -en）

# 英文 README 里每张图都该是 -en
grep -o 'assets/[a-z0-9_-]*\.svg' README.en.md | sort -u
# 应输出：assets/hero-en.svg …

# 引用的文件都真实存在
grep -o 'assets/[a-z0-9_-]*\.svg' README*.md | sed 's/.*://' | sort -u | while read f; do
  [ -f "$f" ] || echo "  ✗ 缺文件: $f"
done
```

**自动校验脚本**见 `scripts/check_readme_assets.py`，一次跑完全部语言：

```bash
python3 scripts/check_readme_assets.py .        # 在仓库根目录跑
```

它会报四种错：
- 中文 README 引用了 `-en` 图（语言错配）
- 英文 README 引用了无后缀图（语言错配）
- 引用了不存在的文件（断图）
- **SVG 里用了 HTML 实体（会让 Chrome 渲染成粉色错块）**

最后一条尤其重要：**SVG 是 XML，不是 HTML**。`&rarr;` `&mdash;` `&nbsp;` 在 XML 里未定义，
Chrome 解析失败后会画一块粉色 `#FFDDDD` —— 而文本溢出检测**完全抓不到**。
XML 只认 `&amp;` `&lt;` `&gt;` `&quot;` `&apos;`。要用 `→` 就直接写 `→`。

**任何一条不过，不许推送。**

---

## 三、README 行文风格（★ 固化，不许自由发挥）

参照 [zarazhangrui](https://github.com/zarazhangrui) 的风格。**顺序不能变**：

```
① 一句话：这是什么 + 给谁用        ← 不出现技术栈名
② 效果：直接上图 / 上结果数字        ← 说"你能拿到什么"，不说"我怎么做的"
③ 问题：Who is this for —— 戳中读者  ← 讲你的处境，不讲我的辛苦
④ 怎么用：最短上手路径 + 触发词      ← 3 步以内
⑤ （可选）原理 / 踩坑                ← 放最后，或干脆外链到独立文件
```

### 硬规则

| 禁止 | 改成 |
|---|---|
| 开篇讲技术栈（"基于 X 和 Y 实现"） | 讲**用户拿到什么** |
| 讲作者的辛酸（"调了很久"、"踩了坑"） | 讲**用户的损失**（"错一个字整张图就废"） |
| 原理 / 架构图放前面 | 移到最后一节，或外链 `RULES.md` |
| 大段论证"为什么我这么做" | 删掉，或压成一句话 |
| 纯文字没有图 | 效果段**必须有图** |

### 好 / 坏的对照

**坏**（讲手段）：
> 一个 agent skill，用手写 SVG + Chrome headless 做信息图。

**好**（讲结果）：
> **不用 AI 生图，让编码 agent 直接给你画图。**
> 架构图、流程图、对比图。字全对、矢量清晰、单张约 8 KB。
> 说一声，图就出来了：
> *[紧跟着就是图]*

### 篇幅

**100 行左右**是甜点。超过 150 行就说明把过程写进来了 —— 挪去附属文件。

### 多语言 ≠ 直译

中文版和英文版**各自独立写**，别逐句翻译：
- 语气词本地化（中文"折腾""再见""刚需"；英文 "no more" / "bye-bye"）
- 触发词**各列各的**（中文用户说「画个架构图」，英文用户说 "draw an architecture diagram"）
- 英文比中文宽，**图也要重新排版**（见 svg-infographic 的中英双语章节）

---

## 四、推送（★ 网络被墙时的兜底）

先试 git：

```bash
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

### 如果卡在 github.com:443

国内网络常见：**`github.com:443` 不通，但 `api.github.com` 通**。先诊断，别瞎重试：

```bash
curl -s -o /dev/null -w "github.com: %{http_code}\n" --max-time 10 https://github.com
curl -s -o /dev/null -w "api.github.com: %{http_code}\n" --max-time 10 https://api.github.com
```

`github.com` 返回 `000`（超时）而 `api` 返回 `200` → **走 REST API 推送**：

```bash
python3 scripts/push_via_api.py <user>/<repo> <file1> <file2> ... -m "commit msg"

# 删文件（改名、清理旧版）
python3 scripts/push_via_api.py <user>/<repo> --delete old-file.md -m "remove old-file.md"

# 增删一起
python3 scripts/push_via_api.py <user>/<repo> README.md --delete README.zh.md -m "..."
```

脚本做三件事：建 blob → 建 tree → 建 commit → 更新 ref。
**完全绕开被卡的 git 传输协议。**

### 建仓库也可以走 API

```bash
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d '{"name":"<repo>","description":"...","private":false}'
```

### 走 API 的两个副作用（必须告诉用户）

1. **本地与线上 SHA 不一致** —— 内容字节级相同，但 commit SHA 不同（提交时间戳不同）。
   `git status` 会显示 `ahead N`，**这是假象**。网络恢复后 `git fetch && git reset --hard origin/main` 理顺。
2. **CDN 缓存** —— `raw.githubusercontent.com` 可能仍显示旧内容，几分钟自动过期。
   想立刻确认，用 API 读（绕开缓存）：
   ```bash
   curl -s -H "Authorization: token $GITHUB_TOKEN" \
     "https://api.github.com/repos/<user>/<repo>/contents/README.md?ref=main" \
     | python3 -c "import sys,json,base64;print(base64.b64decode(json.load(sys.stdin)['content']).decode())"
   ```

### 凭证

- **别把 token 写进 remote URL 后不管** —— 推完立刻清掉：
  ```bash
  git remote set-url origin https://github.com/<user>/<repo>.git
  ```
- token 需要 `repo` 权限；**用完提醒用户撤销**。

---

## 五、发布前自检清单

推送前逐条过：

- [ ] `README.md` 是**中文**（除非用户要求英文）
- [ ] 各语言 README 的**配图语言对得上**（跑 `check_readme_assets.py`）
- [ ] 效果段**有图**，且图在标题下不远处
- [ ] 开篇**没出现技术栈名**
- [ ] 全文**没讲作者辛苦**
- [ ] 篇幅 **≤ 150 行**（超了就挪走过程）
- [ ] 触发词**中英各列**
- [ ] `LICENSE` 存在
- [ ] `.gitignore` 排除 `preview.html`、`__pycache__`、`.DS_Store`
- [ ] 推送后 remote URL **不含 token**

---

## 六、与其他 skill 的分工

| 事 | 交给谁 |
|---|---|
| 造图（信息图/架构图/流程图） | `svg-infographic` |
| 中英双语图重排 | `svg-infographic` |
| **语言策略 / 图片配对 / README 风格 / 推送** | **本 skill** |

---

## 附带脚本

```
scripts/check_readme_assets.py   校验各语言 README 的配图：语言配对 + 文件存在 + SVG 内容
scripts/push_via_api.py          github.com 不通时，用 REST API 推送/删除文件
```

用法见 `references/USAGE.md`。
