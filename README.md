# HarnessOS

个人 AI 编程 Harness 的单一真相源（Single Source of Truth）。实战产生原料，这里加工成规则，打包成 Skill 发布到各 AI 编程工具中运行。

## 三层流水线

```
notes/（原料区）  →  本仓库（加工厂）  →  skills/（生产线）
 随手记，2分钟一条      筛选、提炼、版本管理      当前生效的规则，打包发布
```

- **notes/**：原始输入。踩坑记录、判断、实验结论。不追求格式，允许粗糙和矛盾，事后证明错了也没关系。唯一标准：2 分钟内能记完。
- **skills/**：加工完成品。只放当前生效的规则，按场景拆分成单一职责的小 skill，靠 description 精准触发。
- **加工是单向的**：永远改仓库里的源文件，绝不直接改已发布的 .skill 产物。

## 目录结构

```
├── notes/               # 原料区：踩坑笔记、观察记录
├── skills/              # 生产线：Skill 源文件
│   ├── ai-stack-harness/    # 自有：AI 编程技术栈选型 Harness
│   ├── keel/                # 引入：架构治理协议（来源 lencx/skills）
│   └── coding-protocol/     # 引入：风险分级编码执行协议（来源 lencx/skills）
└── CHANGELOG.md         # 规则加工历史
```

## 运转节奏

1. **每次踩坑后**：往 notes/ 记一条「坑 + 当时判断 + 实际结果」。
2. **每月 / 每项目收尾**：翻笔记，重复出现 2 次以上的坑提炼成规则，合入对应 skill，版本号 +1，记入 CHANGELOG。
3. **每次大模型换代**：过一遍所有 skill，删除过时规则（模型变强后旧约束可能失效，留着反而拖累）。
4. **发布**：skill 源文件改动后重新打包为 .skill，导入 Kimi Code / Codex / Claude Code 更新。

## 引入 Skill 来源

- keel、coding-protocol 来自 https://github.com/lencx/skills ，原样引入未做修改，感谢作者 lencx。
