Prompt: 要求智能体在 name 仅含空白时让 main() 以 SystemExit(2) 退出，不改测试文件。
Change: cli.py 增加 isspace() 检查并 sys.exit(2)。
Verify: pytest tests/test_cli.py 通过，diff 仅含 cli.py 一处修改。
