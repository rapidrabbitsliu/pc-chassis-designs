# 桌面电脑机箱设计与打印项目

为微星 Z390-A PRO、影驰 RTX 5060 Ti 16 GB 与现有电源设计的 PETG 打印机架。保存两种独立风格的硬件资料、Fusion 模型、STL、Bambu Studio 摆盘与打印参数、图解安装说明书和历次建模脚本。

**当前版本：风格 1 V15；风格 2 V09。** 风格编号表示结构方案，版本号分别演进。实物配合、长期承重与散热仍需实测，具体已验证及待验证事项见各版本说明。

## 换电脑恢复

从私有仓库克隆或完整下载 ZIP，再直接打开对应 `.f3d`、`.3mf` 或 `.html` 文件。

```sh
git clone https://github.com/rapidrabbitsliu/pc-chassis-designs.git
cd pc-chassis-designs
```

详见[其他电脑恢复项目](docs/其他电脑恢复项目.md)，包括软件入口、完整性校验、脚本路径和后续同步方法。全部模型文件直接保存在 Git 中，不使用 Git LFS。

## 硬件和设计依据

- [硬件尺寸与通用设计基准](docs/硬件尺寸与通用设计基准.md)：主板、电源、显卡、风扇、九孔坐标、紧固件以及打印和桌面约束。
- [风格 1 桌面双层开放式机箱](<docs/风格1 桌面双层开放式机箱.md>)：主板平放、下层电源、上层双 140 风扇的布局与修订。
- [风格 2 竖板前置显卡机架](<docs/风格2 竖板前置显卡机架.md>)：独立结构方案和 V09 版本信息。

## 风格 1：V15

V15 以 V13 的 17 件结构为基础，仅更新 P12 显卡塔和 P13 上托片。显卡塔的螺丝头通道 CAD 宽 8.2 mm，下槽贯穿加强筋；上托片平台相对 V13 延长 2 mm，两个螺母孔向显卡侧移动 3 mm。配合尺寸以 [V15 修订说明](outputs/ATX-Desk-v15/README.txt)为准，修补件仍需实物试装。

- [最新完整 Fusion 模型](outputs/ATX-Desk-v15/ATX_Desk_v15_gpu_fit.f3d)
- [最新 Bambu Studio 十盘工程](outputs/ATX-Desk-v15/Style1_V15_All_Parts_10_Plates_With_Temporary_Repair.3mf)：前九盘保留原名称及“已打”标记，P12/P13 已更新；第十盘额外放这次修补的两件。
- [完整 17 件打印 STL](outputs/ATX-Desk-v15/PRINT_STL/)、[两件补打 STL](outputs/ATX-Desk-v15/REPRINT_STL/)
- [第十盘检查记录](outputs/ATX-Desk-v15/ten_plate_project_verification.json)：已在 Bambu Studio 切片通过，预计 6 小时 9 分、132.17 g PETG；重新打开工程后可重新切片，未发送打印。
- [V13 图解安装说明书](outputs/ATX-Desk-v13/Style1_V13_Assembly_Manual.html)：17 件编号、热熔孔位与装配步骤。P12/P13 使用 V15 新件及修订尺寸，说明书中的旧件图保留作基线。
- [V13 装配参考图](outputs/ATX-Desk-v13/Assembly.png)、[说明书及维护资料包](outputs/ATX-Desk-v13/Style1_V13_Illustrated_Manual.zip)

V13 原九盘工程与 V14、早期版本留在各自目录作追溯。`Style1-V15-GPU-Replacement-Parts.zip` 内为先前单独打包的一盘未切片工程；继续使用完整工程时优先打开上面的 V15 十盘文件。

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
