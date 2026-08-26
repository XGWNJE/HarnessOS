# HarnessOS

[![Stars](https://img.shields.io/github/stars/XGWNJE/HarnessOS?style=flat-square&label=Stars)](https://github.com/XGWNJE/HarnessOS)
[![Top Language](https://img.shields.io/github/languages/top/XGWNJE/HarnessOS?style=flat-square&label=Top%20Language)](https://github.com/XGWNJE/HarnessOS)
[![Last Commit](https://img.shields.io/github/last-commit/XGWNJE/HarnessOS?style=flat-square&label=Last%20Commit)](https://github.com/XGWNJE/HarnessOS)
[![Skills](https://img.shields.io/badge/Skills-13%20active-4caf50?style=flat-square)](https://github.com/XGWNJE/HarnessOS)

**HarnessOS · Agent 通用资产中枢（Agent Asset Hub）**。白话版：把跨项目复用的规矩、技能和公共 Hook 放在一个源头加工、发布和核验。本仓库是这些资产的唯一真相源；各业务项目、外部工具和本机环境仍由各自负责。

## 项目干什么

- **收料**：harness-observer 静默观察各项目里的纠正、偏好与踩坑，随手抓进原料区；第三方成品技能原样引入并登记来源。
- **加工**：经你验收后，把可跨项目复用的约束固化为规则，把可复用能力固化为技能；HarnessOS 自有公共 Hook 也在这里维护。
- **发布与核验**：把规则和技能同步到各 Agent，检查发布漂移、HarnessOS 自有 Hook 注册和文档边界。

不负责：业务项目的规则、代码和私有 Hook；MCP 服务、CLI、账号、密钥和本机开发环境的安装或运行维护。它们可以使用这里发布的通用资产，但不由这里接管。

流程单向流动：原料 → 本仓库加工 → 发布到各工具。

## 怎么开始

- **安装**：新环境克隆本仓库后运行安装入口，发布并核验 HarnessOS 自己的资产（命令与细节见 AGENTS.md）。
- **发布与体检**：改完资产运行发布入口；体检覆盖发布漂移、HarnessOS 自有 Hook 注册和文档职责（命令与细节见 AGENTS.md）。
- **提交体检**：内置提交前检查——发现发布状态漂移或文档越界直接拦截提交，按提示修复即可。
- **文档边界**：项目文档的事实归属与漂移纠正由 project-doc-boundary skill 维护。

## 文档地图

- `README.md`：本文件，面向人——项目干什么、怎么开始。
- `AGENTS.md`：面向 Agent 的完整操作规则（铁律、命令、验证矩阵、工作规则）——所有操作细节都在这里。
- `CHANGELOG.md`：规则加工历史（新增/修订/废止/框架）。
- `global/AGENTS.md`：全局通用规则源文件（发布到 5 个 Agent 读取位置：home/Codex/OpenCode/Claude Code/DSH）。
- `global/hooks/`：HarnessOS 自有公共 Hook 源文件与注册清单。
- `vendor/SOURCES.md`：第三方 skill 来源登记。
- `notes/`：原料区（observer 静默写入，加工完毕即销毁）。
- `reviews/`：评审摘要（owner 主动质检时生成）。
