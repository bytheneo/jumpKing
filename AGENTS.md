# JumpKing 專案工作流程

## Git 分支策略
- `main` 為主分支，**禁止直接在 main 上修改**
- 所有修改必須先建立新分支：`git checkout -b <branch-name>`
- 分支命名慣例：`feature/描述`、`fix/描述`、`refactor/描述`
- 修改完成後推送分支並建立 PR 到 main
- 由 bytheneo 手動審查合併，Agent 不自行合併

## 流程步驟
1. 從 main 建立新分支
2. 在新分支上進行修改與提交
3. 推送分支到 origin
4. 建立 Pull Request（feature branch → main）
5. 等待 bytheneo 手動合併
