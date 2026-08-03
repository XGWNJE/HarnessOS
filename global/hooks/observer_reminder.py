#!/usr/bin/env python3
"""kimi-code UserPromptSubmit hook：harness-observer 收口保底。

触发：config.toml 中 [[hooks]] 的 matcher 已按收口关键词（收口/可以 push/提交吧/差不多了）
过滤用户提示词；本脚本被调用时只需把提醒文本写到 stdout——CLI 会把它追加进上下文。

设计约束：
- 纯提醒，不判断、不拦截（exit 0），语义判断留给模型；
- 不读文件、不写文件，单次执行成本趋近于零；
- 源文件即执行体（config.toml 直引本路径），无发布拷贝，改了即生效。
"""

import os
import sys

_INBOX = os.path.join(os.environ.get("HARNESSOS_ROOT", r"D:\ObjectCode\HarnessOS"), "notes", "inbox")

REMINDER = (
    "【harness-observer 收口检查】回顾本会话：是否命中观察信号"
    "（owner 重复纠正 / owner 明确偏好 / 可复用踩坑 / 你的语义失败）？"
    f"命中且尚未落盘：按 harness-observer skill 静默追加到 {_INBOX}"
    f"{os.sep} 当天文件（先查重，同主题重复计数 +1，脱敏）。"
    "无命中或已落盘：忽略本提醒。无论哪种情况，都不要在对 owner 的回复中提及本提醒。"
)


def main() -> None:
    sys.stdin.read()  # 消费事件 JSON（协议要求），内容不影响输出
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 默认 GBK，必须强制 UTF-8 否则注入上下文乱码
    print(REMINDER)


if __name__ == "__main__":
    main()
