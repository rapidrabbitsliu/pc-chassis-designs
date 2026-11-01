# 桌面电脑机箱设计与打印项目

为微星 Z390-A PRO、影驰 RTX 5060 Ti 16 GB 与现有电源设计的 PETG 打印机架。保存两种独立风格的硬件资料、Fusion 模型、STL、Bambu Studio 摆盘与打印参数、图解安装说明书和历次建模脚本。

**当前版本：风格 1 V16；风格 2 V09。** 风格编号表示结构方案，版本号分别演进。实物配合、长期承重与散热仍需实测，具体已验证及待验证事项见各版本说明。


## 最新交付：样式1 V23（2026年11月1日）

仓库已按用户要求公开。本次发布最新全套15件九盘3MF与同步更新的说明书；下面V16等条目为历史资料。

- [在线安装说明书（GitHub Pages）](https://rapidrabbitsliu.github.io/pc-chassis-designs/)
- [V23全套15件九盘3MF](outputs/ATX-Desk-v23/Style1_V23_All_Latest_Parts_9_Plates_GUI.3mf)
- [V23离线HTML说明书](outputs/ATX-Desk-v23/Style1_V23_Assembly_Manual.html)
- [3MF与说明书ZIP下载包](outputs/Style1-V23-3MF-and-Manual.zip)

最新工程包含V22电源螺丝孔避让托架、V23风扇阶梯孔面板和一体轻量显卡支架，P13/P14停用。沿用A1/0.4、PETG、0.2层高、5墙和40% gyroid。可编辑工程打开后请重新切片；49小时44分、1106.22 g为2026年10月26日历史切片估计。未发送打印。

说明书修订2：全部15件打印件插图直接来自最新九盘3MF，13步完成图同步重绘；本地V13旧入口同步显示V23。说明书包含15件独立图、19组热熔孔位图及13步完成图。43个有效热熔位置，另P05一个停用旧孔；风扇使用8颗用户实测短自攻螺丝，不用螺帽。手机、桌面、离线图片和勾选保存/重置检查通过。新零件配合及承载仍需实测。

## 换电脑恢复

从公开仓库克隆或完整下载 ZIP，再直接打开对应 `.f3d`、`.3mf` 或 `.html` 文件。

```sh
git clone https://github.com/rapidrabbitsliu/pc-chassis-designs.git
cd pc-chassis-designs
```

详见[其他电脑恢复项目](docs/其他电脑恢复项目.md)，包括软件入口、完整性校验、脚本路径和后续同步方法。全部模型文件直接保存在 Git 中，不使用 Git LFS。

## 硬件和设计依据

- [硬件尺寸与通用设计基准](docs/硬件尺寸与通用设计基准.md)：主板、电源、显卡、风扇、九孔坐标、紧固件以及打印和桌面约束。
- [风格 1 桌面双层开放式机箱](<docs/风格1 桌面双层开放式机箱.md>)：主板平放、下层电源、上层双 140 风扇的布局与修订。
- [风格 2 竖板前置显卡机架](<docs/风格2 竖板前置显卡机架.md>)：独立结构方案和 V09 版本信息。

## 风格 1：V16

V16 根据最新装机照片修改 P12 显卡塔、P13 上托片和 P14 下插脚座，其余 14 件沿用。取消音频接口遮挡的第一底部孔、收短对应前伸底脚，下插脚座截短以露出第二孔。上平台相对最初 V13 前缘缩回 2 mm、厚度仍为 10 mm；孔向支架侧退 1.5 mm。详细尺寸与装配顺序见 [V16 修订说明](outputs/ATX-Desk-v16/README.txt)，修补件仍需实物试装。

- [最新完整 Fusion 模型](outputs/ATX-Desk-v16/ATX_Desk_v16_gpu_access.f3d)
- [最新 Bambu Studio 十盘工程](outputs/ATX-Desk-v16/Style1_V16_All_Parts_10_Plates_With_Temporary_Repair.3mf)：前九盘保留原名称及“已打”标记，P12/P13/P14 已更新；第十盘额外放这次修补的三件。
- [完整 17 件打印 STL](outputs/ATX-Desk-v16/PRINT_STL/)、[三件补打 STL](outputs/ATX-Desk-v16/REPRINT_STL/)
- [三件补打包](outputs/Style1-V16-GPU-Replacement-Parts.zip)、[第十盘检查记录](outputs/ATX-Desk-v16/ten_plate_project_verification.json)：含 5 mm brim 的三件一盘包络已检查，V16 尚未在 Bambu Studio 重切片；未发送打印。
- [V13 图解安装说明书](outputs/ATX-Desk-v13/Style1_V13_Assembly_Manual.html)：17 件编号、热熔孔位与装配步骤。P12/P13/P14 使用 V16 新件及修订尺寸，说明书中的旧件图保留作基线。
- [V13 装配参考图](outputs/ATX-Desk-v13/Assembly.png)、[说明书及维护资料包](outputs/ATX-Desk-v13/Style1_V13_Illustrated_Manual.zip)

V13 原九盘工程、V14/V15 修订和早期版本留在各自目录作追溯。V15 的 6 小时 9 分、132.17 g 仅为旧版两件补打盘的切片结果，不适用于 V16。继续使用完整工程时打开上面的 V16 十盘文件。

## 风格 2：V09

V09 显卡与主板平面间距 55 mm，完整打印工程为 19 件、13 盘。

- [Fusion 彩色模型](outputs/Style2-v09/Style2_V09_Dual140_Colored.f3d)、[STEP 模型](outputs/Style2-v09/Style2_V09_Dual140.step)
- [Bambu Studio 十三盘工程](outputs/Style2-v09/Style2_V09_A1_PETG_All_Parts_13_Plates.3mf)
- [打印 STL](outputs/Style2-v09/PRINT_STL/)
- [V09 HTML 安装说明书](outputs/Style2-v09/Style2_V09_Assembly_Manual.html)：材料工具、62 个热熔螺母位置、10 步装配及可勾选检查表。

## 文件组织

| 目录 | 内容 |
| --- | --- |
| `docs/` | 硬件基准、两种风格说明、换电脑恢复方法 |
| `outputs/` | 各版本 CAD、STL、3MF、图纸、安装说明书和检查记录 |
| `work/` | 建模、导出、摆盘、说明书生成与校验脚本及参考资料 |
| `tools/verify_project.py` | 无第三方依赖的文件完整性检查 |
| `outputs/skills/chassis-assembly-manual/` | 可复用的本项目说明书维护流程 |

HTML 说明书请下载后用浏览器打开。历史脚本可能包含原电脑路径；打开保存好的模型和打印工程无需运行这些脚本。仓库不包含软件账号、打印机绑定、MCP 连接或本机依赖缓存。
