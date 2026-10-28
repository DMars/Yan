# YanUE — UE5.8 C++ 项目与 ChatGPT 材质任务桥

这是初版源码工程，不包含 Unreal Engine 引擎源码或已编译二进制。
C++ 提供游戏模块及 Editor 插件模块；材质图操作由插件内 UE Python 执行。
使用当前 ChatGPT 的 GitHub 连接发任务，不调用 OpenAI API。

## 首次安装（Windows）

1. 安装 UE5.8、Visual Studio 2022 的 C++ 游戏开发工作负载及 UE 所需 Windows SDK。
2. `git clone https://github.com/DMars/Yan.git`，右键 `YanUE.uproject`，生成 Visual Studio 工程文件。
   如果引擎关联未识别，右键选择 Switch Unreal Engine version 并选择本机 5.8。
3. 打开生成的解决方案，选择 `Development Editor / Win64`，编译 `YanUE`，再打开 `YanUE.uproject`。
4. 确认 Python Editor Script Plugin、Editor Scripting Utilities、Yan Material Bridge 已启用。
   Output Log 应显示 `YanBridge ready`。若未显示，在 Python 控制台运行：
   `import yan_worker; yan_worker.start()`。
5. 安装独立 Python 3.10+ 和 GitHub CLI，在 PowerShell 执行 `gh auth login`。
   使用有 DMars/Yan 内容写权限的账号；凭据只由本机 gh 管理，不写入仓库。
6. 在仓库目录运行 `py tools/bridge.py`，保持它与 UE 编辑器同时打开。

## 首次本地验收

无需 GitHub 桥也可先测试。在仓库目录的 PowerShell 中运行：

```powershell
New-Item -ItemType Directory -Force Saved/YanBridge/inbox
Copy-Item examples/blue_material.json Saved/YanBridge/inbox/blue-001.json
```

UE 应创建 `/Game/ChatGPT/M_Blue_001`，并生成
`Saved/YanBridge/reports/blue-001.json`。打开该材质检查蓝色与粗糙度连线和编译错误。
重复执行必须更换任务 id 和 asset_path；已有资产不会被覆盖。

## ChatGPT 控制流程

首次启动后对 ChatGPT 说：
“向 DMars/Yan 的 master 分支 tasks/blue-002.json 写入一个版本 1 的
create_material 任务，参考 examples/blue_material.json，id 为 blue-002，
asset_path 为 /Game/ChatGPT/M_Blue_002；然后检查 reports/blue-002.json。”

ChatGPT GitHub connector -> tasks/*.json -> 本地 bridge.py（每 15 秒）
-> Saved/YanBridge/inbox -> UE 编辑器主线程 -> 本地报告 -> reports/*.json。
报告可能需要后续一次读取才出现；聊天会话不会自动常驻轮询。
初始 examples 不会自动远程执行。仅 master/tasks 中 JSON 被桥接。
GitHub CLI 需要能访问 GitHub；可用 `py tools/bridge.py --once` 排查错误。

## 协议及范围

参考 `examples/blue_material.json` 和 `yan_ir.py`。
支持 Constant、Constant3Vector、ScalarParameter、VectorParameter、TextureCoordinate、
Time、Add、Multiply、Lerp、Sine、OneMinus、Clamp。
输出支持 BaseColor、Roughness、Metallic、EmissiveColor（默认 Surface / Opaque / Default Lit）。
任务只能新建 `/Game/ChatGPT/` 内材质，不能执行任意 Python、Shell、删除已有资产。
错误连线会失败；失败时尝试清理本次新建资产。贴图加载、图片识别和旧版执行器迁移尚未实现。
截图或效果图需要先由 ChatGPT 转换为上述 JSON，效果反推仅为近似。

`status: saved` 表示连线 API 成功、已请求重编译并保存；
**不等于已验证 shader 编译成功**。报告明确返回 `shader_validation: not_verified`。
当前环境未安装 UE 或 Windows 编译工具链，因此尚未完成 UE5.8 编译和编辑器端到端验证。
本机磁盘资产不会随报告上传；Binaries、Saved、Intermediate 被忽略。
当前仓库公开，任务和报告会公开；请勿提交密钥、私有贴图或敏感工程路径。
一个项目仅启动一个 bridge 进程与一个编辑器实例。任务不可原地修改；修改请用新 id。
保留 Saved/YanBridge/reports 可避免同机重复消费；清空 Saved 后旧任务会再次被发现，
但已有资产保护会拒绝覆盖。报告上传冲突会显式报错，请人工检查，不自动覆盖。

## 验证

```powershell
py -m unittest discover -s tests -v
```

UE Python 使用标准库验证，不依赖 jsonschema，避免此前缺依赖问题。
官方 API 参考：
https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialEditingLibrary
https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python
