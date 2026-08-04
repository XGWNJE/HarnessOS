# HarnessOS

[![Stars](https://img.shields.io/github/stars/XGWNJE/HarnessOS?style=flat-square&label=Stars)](https://github.com/XGWNJE/HarnessOS)
[![Top Language](https://img.shields.io/github/languages/top/XGWNJE/HarnessOS?style=flat-square&label=Top%20Language)](https://github.com/XGWNJE/HarnessOS)
[![Last Commit](https://img.shields.io/github/last-commit/XGWNJE/HarnessOS?style=flat-square&label=Last%20Commit)](https://github.com/XGWNJE/HarnessOS)
[![Skills](https://img.shields.io/badge/Skills-13%20active-4caf50?style=flat-square)](https://github.com/XGWNJE/HarnessOS/tree/master/skills)

Agent 长期约束的备份分发引擎。白话版：把 AI 编程助手要守的规矩和会干的活，沉淀成规则与技能文件，统一在本仓库加工，再自动同步到各 AI 工具——让每个 AI 都按你定的标准干活。本仓库是唯一真相源，改动只动这里，别处都是自动生成的副本。

## 项目干什么

- **抓**：harness-observer 静默观察各项目里的纠正、偏好与踩坑，随手抓进原料区，不打断任务。
- **喂**：你直接声明的规则（偏好、习惯、验收标准），权威性最高。
- **拿**：vendor/ 整盘引入第三方成品 skill，原样不改，来源登记在案。

三条收料通道，互补不重叠。原料是粗糙笔记，不能直接用：先查与已有规则有无冲突，经你验收拍板后才固化；固化时按「防止它做错事 → 写成约束规则 / 教会它做事 → 写成技能」分流。流程单向流动：原料 → 本仓库 → 发布到各工具。

## 怎么开始

- **迁移/装机**：新环境克隆本仓库后跑一条装机命令，环境配置、发布、体检一次性完成（命令与细节见 AGENTS.md）。
- **发布**：改完规则跑一条发布命令，自动打包并同步到各 AI 工具（命令与细节见 AGENTS.md）。
- **提交体检**：内置提交前检查——发现发布状态漂移或文档越界会直接拦截提交，按提示修复即可（保底流程是运行 doc-structure skill）。
- **文档结构**：文档职责与模板由 doc-structure skill 维护，多项目共用同一套风格与自动验收标准。

## 文档地图

- `README.md`：本文件，面向人——项目干什么、怎么开始。
- `AGENTS.md`：面向 Agent 的完整操作规则（铁律、命令、验证矩阵、工作规则）——所有操作细节都在这里。
- `CHANGELOG.md`：规则加工历史（新增/修订/废止/框架）。
- `vendor/SOURCES.md`：第三方 skill 来源登记。
- `notes/`：原料区（observer 静默写入，加工完毕即销毁）。
- `reviews/`：评审摘要（owner 主动质检时生成）。
