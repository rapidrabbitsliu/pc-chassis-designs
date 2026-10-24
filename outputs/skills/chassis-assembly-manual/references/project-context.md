# 项目资料与 V09 基线

项目根目录：`D:/personal-files/docs/ChatGPT/电脑上洞洞板`。从当前工作目录/README 确认路径和版本，不硬套历史数据。

## 维护源

- `docs/风格2 竖板前置显卡机架.md`、`docs/硬件尺寸与通用设计基准.md`。
- `work/build_style2_v09.py`：CAD 来源。
- `work/build_manual_v09.py`：基础说明；`work/illustrate_manual_v09.py`：图解增强。后者非幂等，重建应先生成基础再增强，各一次。
- `outputs/Style2-v09/`：parts.json、print_plate_list.csv、verification.json、manual_part_index.json、Raw_STL、Manual_Refs、Manual_Images。
- HTML：`Style2_V09_Assembly_Manual.html`；打印工程：`Style2_V09_A1_PETG_All_Parts_13_Plates.3mf`。
- NumPy/Pillow Python 曾位于 `C:/Users/liu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`；若不存在用依赖工具重新定位。

## 编号映射

| 编号 | 名称 / 文件名 | 热熔螺母 |
|---|---|---:|
| P01/P02/P03 | 左/中/右立柱：01_UPRIGHT_1/2/3 | 13/9/17 |
| P04/P05/P06 | 左/中/右底脚：02_FOOT_1/2/3 | 4/3/4 |
| P07/P08 | 下/上横撑：03_LOWER/UPPER_CROSSBAR | 0 |
| P09/P10 | 左/右直角框：05_SIDE_RECTANGULAR_FRAME_1/3 | 0 |
| P11 | 显卡承托梁：06_GPU_CARRIER | 8 |
| P12 | 母槽托盘：07_RISER_TRAY_PENDING_MEASUREMENT | 0 |
| P13/P14 | 显卡垫座：08_GPU_PAD_LEFT/RIGHT_FIT_REQUIRED | 0 |
| P15/P16 | 电源前/后托条：09_PSU_SADDLE_FRONT/REAR | 0 |
| P17 | 双风扇立梁：10_FAN_MAST_RIGHT_SIDE | 4 |
| P18/P19 | 下/上风扇框：11_FAN_PANEL_GPU/CPU_RAM_140mm | 0 |

这些编号尚未刻入模型。左右以主板正面、显卡一侧观看为基准；背面图视觉左右翻转，组件身份不变。

V09：62个 M3/H4.5/外径约5mm 热熔螺母，孔径4.7mm；62颗 M3×6（主板9、结构53），建议各备70。H8不能直接替代；螺钉头径≤6.6mm、头高≤3mm。风扇另用8套 M4×40和普通M4螺母、垫片，孔距124.5mm待实测。

包络299.84×280×314mm，显卡/主板基准平面间距55mm；19件13盘。A1/0.4/PETG、0.2层高、5墙、40%gyroid、顶6底5、245/70°C只作历史记录，文档任务不默认重切片。

待实物确认：母槽尺寸和专用安装孔、显卡挡板锁紧和防倾固定、垫座承力位置、散热器/内存/线缆空间、风扇孔距。电源托座仅定位，还需可靠绑带；显卡不可只由母槽或摩擦承重。55mm和无实体干涉均不代表热性能、刚性或PETG长期承载验证；穿透风扇可能朝主板排热。
