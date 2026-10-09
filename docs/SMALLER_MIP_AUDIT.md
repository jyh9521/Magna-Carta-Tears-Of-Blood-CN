# 普通包全部 mip 视觉核查

## Verified static / visual observation

原 FILE.AFS 的 SHA-256 为 `a9f7e2b34bfb5475bab2793821520295d120e2a122ccd363812f2d03c025072b`。复用普通 Texture/P8 parser 和第 67 轮锁定的纹理 manifest，重新核对包、serial、Palette、每级像素 hash 与 lazy-end 坐标。28 个 Texture 的 163 个非首级 mip 全部导出并在 7 张原尺寸 contact sheet 中检查；结合此前 28 个首级，191 个普通 mip 的视觉检查已完成。

163 个小 mip 未观察到新增独立短语候选；Editor.u/export/32 的较小级仍显示既有 `BAD SIZE`。其余图像表现为地形、建筑、天空、植被、测试图案、纯色或图标的缩小版本。小级图像保留原始像素尺寸，未通过插值放大或 OCR 推断文字。tiny mip 的文字不可读不等于其像素中没有文字。

## 尚未验证

BGRA 到 RGB 的显示解释继续沿用普通包核查，alpha 未合成到游戏背景；运行可见性、用途、流式 Texture 和 SFD 图片文字仍未完成。普通 mip 视觉检查完成不等于全游戏文本提取完成。既有正文集合、6334 初稿、原始资源及测试 ISO 未改动。

## 重现

```powershell
work/venv/Scripts/python.exe -X utf8 tools/audit_mip_views.py --archive work/kr/FILE.AFS --manifest work/extraction-coverage-67/texture-audit/textures.json --out work/extraction-coverage-70/mip-audit
```

输出目录必须为空且位于 ignored work/build。manifest 须为前一普通纹理审计的 textures.json；每项与原资源重新比对，错误身份或差异拒绝继续。生成图片及详细 manifest 仅保存在本地 ignored 输出，不提交原游戏纹理。
