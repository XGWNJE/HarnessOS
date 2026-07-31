# HarnessOS

[![Stars](https://img.shields.io/github/stars/XGWNJE/HarnessOS?style=flat-square&label=Stars)](https://github.com/XGWNJE/HarnessOS)
[![Top Language](https://img.shields.io/github/languages/top/XGWNJE/HarnessOS?style=flat-square&label=Top%20Language)](https://github.com/XGWNJE/HarnessOS)
[![Last Commit](https://img.shields.io/github/last-commit/XGWNJE/HarnessOS?style=flat-square&label=Last%20Commit)](https://github.com/XGWNJE/HarnessOS)
[![Skills](https://img.shields.io/badge/Skills-7%20active-4caf50?style=flat-square)](https://github.com/XGWNJE/HarnessOS/tree/master/skills)

个人 AI 编程 Harness 的单一真相源（Single Source of Truth）：实战经验在这里被加工成规则和技能，发布到各 AI 编程工具中运行。

## 项目干什么

- **抓**：harness-observer 静默观察各项目里的纠正、偏好与踩坑，随手抓进原料区，不打断任务。
- **喂**：你直接声明的规则（偏好、习惯、验收标准），权威性最高。
- **拿**：vendor/ 整盘引入第三方成品 skill，原样不改，来源登记在案。

三个通道互补不重叠。原料不能直接用——先经冲突检查，再由你验收拍板才能固化；固化后按「会做错事 → 约束规则 / 不会做某事 → 技能」分流。加工单向：原料 → 本仓库 → 发布产物。

## 怎么开始

- **发布**：运行发布脚本一条命令完成打包与发布（命令与细节见 AGENTS.md）。
- **提交体检**：仓库装有 pre-commit 硬卡点，提交前自动体检发布漂移与文档职责边界，违规即拦截——保底流程是运行 doc-structure skill 修复。
- **文档结构**：文档职责与模板由 doc-structure skill 维护，多项目共用同一套风格与自动验收标准。

## 文档地图

- `README.md`：本文件，面向人——项目干什么、怎么开始。
- `AGENTS.md`：面向 Agent 的完整操作规则（铁律、命令、验证矩阵、工作规则）——所有操作细节都在这里。
- `CHANGELOG.md`：规则加工历史（新增/修订/废止/框架）。
- `vendor/SOURCES.md`：第三方 skill 来源登记。
- `notes/`：原料区（observer 静默写入，加工完毕即销毁）。
- `reviews/`：评审摘要（owner 主动质检时生成）。
