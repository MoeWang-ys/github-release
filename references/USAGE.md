# 用法

## 1. 校验图片配对

发布前必跑。在仓库根目录：

```bash
python3 ~/.pi/agent/skills/github-release/scripts/check_readme_assets.py .
```

指定主语言：

```bash
python3 .../check_readme_assets.py . --main en    # 主语言是英文时
```

输出示例：

```
主语言: zh

  README.md  [中文]  应引用 无后缀图
     ✓ assets/hero.svg
  README.en.md  [英文]  应引用 -en 图
     ✗ 语言错配: assets/hero.svg  (英文 README 应引用 -en 图)

  ✗ 1 个问题，先修完再推送
```

退出码 `0` = 通过，`1` = 有问题。

---

## 2. 推送

### 正常情况：用 git

```bash
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

### github.com 不通时：用 API

先诊断：

```bash
curl -s -o /dev/null -w "github.com: %{http_code}\n" --max-time 10 https://github.com
curl -s -o /dev/null -w "api: %{http_code}\n" --max-time 10 https://api.github.com
```

`github.com` = `000` 且 `api` = `200` → 走 API：

```bash
export GITHUB_TOKEN=ghp_xxx
python3 ~/.pi/agent/skills/github-release/scripts/push_via_api.py \
  <owner>/<repo> README.md README.en.md assets/hero.svg \
  -m "docs: bilingual README"
```

删文件（比如重命名 `README.zh.md` → `README.md` 后清理旧版）：

```bash
python3 .../push_via_api.py <owner>/<repo> --delete README.zh.md \
  -m "docs: remove README.zh.md"
```

> ⚠ API 推送只增不删，容易忘掉遗留的旧文件。
> 推送前先比对一次本地与线上文件列表，对不上的就是要 `--delete` 的。

**注意**：API 推送要求仓库和分支**已存在**。首次发布要先建仓库：

```bash
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d '{"name":"<repo>","description":"...","private":false}'
```

再手动建首个 commit（API 不能推一个空分支）。或者干脆：先用 git 推一次（能通的话），之后再用 API 增量推。

---

## 3. 完整发布流程

```bash
# ① 造图（交给 svg-infographic skill）
#    产出 assets/hero.svg + assets/hero-en.svg

# ② 写 README（本 skill 第三节的风格）
#    README.md      ← 中文，引用 assets/hero.svg
#    README.en.md   ← 英文，引用 assets/hero-en.svg

# ③ 校验配对
python3 .../check_readme_assets.py .

# ④ 过自检清单（SKILL.md 第五节）

# ⑤ 推送
git push -u origin main    # 或走 API

# ⑥ 清掉 remote URL 里的 token
git remote set-url origin https://github.com/<user>/<repo>.git
```

---

## 4. 常见问题

**Q: 为什么中文 README 不能用 `-en` 图？**
A: 图里的文字是图的一部分。中文读者看到英文标签的图，等于要跨一道语言。图必须跟正文同语言。

**Q: 主语言想用英文怎么办？**
A: `--main en`，并把 `README.md` 写成英文、中文版叫 `README.zh-CN.md`。图片命名规则不变（无后缀=中文图，`-en`=英文图），只是 `README.md` 引用 `-en` 那套。

**Q: API 推送后 `git status` 显示 ahead 3？**
A: 假象。本地和线上内容一致，只是 commit SHA 不同（时间戳）。网络恢复后 `git fetch && git reset --hard origin/main`。

**Q: 推送后 GitHub 网页显示的还是旧内容？**
A: `raw.githubusercontent.com` 的 CDN 缓存，几分钟自动过期。要立刻确认就走 API 读（见 SKILL.md 第四节）。
