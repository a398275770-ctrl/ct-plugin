# CI — ct-plugin

本地门禁（唯一环境为本机 Arch 虚机，无远端 CI）：
```bash
./scripts/check.sh   # py_compile 语法检查 + pytest 7 场景，全绿才允许 commit
```
commit 纪律：每批次独立 commit（B1..B4 均可单独 revert）；commit 前 check.sh 必须通过。
回滚：`git revert <hash>`（无业务数据迁移，回滚零成本）。
