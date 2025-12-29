import cv2
import numpy as np
import json
import os

# --- 参数配置 ---
MD_RANGE = (900.0, 920.0)
RAD_RANGE = (0.0, 6.9)
STEP = 0.01  # 0.01m 极高精度

# 交互窗口显示大小 (不影响导出精度)
CANVAS_H = 800
CANVAS_W = 400

# 全局变量
drawing = False
# mask 存储绘图形状
mask = np.zeros((CANVAS_H, CANVAS_W), dtype=np.uint8)


def draw_mask(event, x, y, flags, param):
    global drawing, mask
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            # 模拟画笔：从左侧(井筒)向鼠标位置填充
            # 矩形填充保证了从中心向外的扩散连续性
            cv2.rectangle(mask, (0, y - 3), (x, y + 3), 255, -1)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False


def generate_json_from_mask():
    print(f"正在生成高精度数据 (步长: {STEP}m)...")

    # 1. 定义物理坐标轴
    # np.arange 在 0.01 精度下可能会有浮点数微差，使用 np.around 修正
    md_axis = np.around(np.arange(MD_RANGE[0], MD_RANGE[1] + STEP, STEP), 2)
    rad_axis = np.around(np.arange(RAD_RANGE[0], RAD_RANGE[1] + STEP, STEP), 2)

    # 2. 对绘制的 mask 进行重采样，匹配高精度网格
    # 目标尺寸: (Radius点数, MD点数)
    target_shape = (len(rad_axis), len(md_axis))
    resized_mask = cv2.resize(mask, target_shape, interpolation=cv2.INTER_LINEAR)

    grid = []

    print(f"网格尺寸: {len(md_axis)} x {len(rad_axis)}")

    # 3. 逐行生成带噪音的物理数值
    for i in range(len(md_axis)):
        row = []
        row_pixels = resized_mask[i, :]

        # 找到该行最右侧的扩散边界索引
        if np.any(row_pixels > 0):
            max_r_idx = np.where(row_pixels > 0)[0][-1]
        else:
            max_r_idx = 0

        # 层间噪音基准 (模拟地层非均质性)
        layer_noise = np.random.normal(2.0, 0.05)

        for j in range(len(rad_axis)):
            if j > max_r_idx:
                val = 0.0
            else:
                if max_r_idx == 0:
                    val = 100.0 if resized_mask[i, j] > 0 else 0.0
                else:
                    ratio = j / max_r_idx
                    # 核心线性/幂函数映射
                    base_val = 100.0 * (1 - ratio ** 0.8)

                    # --- 水平径向噪音逻辑 ---
                    # 1. 局部高频噪音 (斑驳感)
                    local_rand = np.random.uniform(0.94, 1.06)
                    # 2. 径向波浪噪音 (模拟流体前缘波动)
                    radial_wave = 1.0 + (np.sin(j * 0.4) * 0.02)

                    val = base_val * local_rand * radial_wave * layer_noise

                    # 基于原始 Mask 亮度的权重修正（处理边缘平滑）
                    weight = resized_mask[i, j] / 255.0
                    val *= weight

            # 最终数值限制
            val = min(100.0, max(0.0, val))
            row.append(round(float(val), 2))

        grid.append(row)
        if i % 500 == 0: print(f"进度: {i}/{len(md_axis)}")

    # 4. 封装导出
    output = {
        "metadata": {
            "title": "High-Res Perforation Lateral Extend",
            "md_range": list(MD_RANGE),
            "radius_range": list(RAD_RANGE),
            "step": STEP,
            "points_count": {"md": len(md_axis), "radius": len(rad_axis)}
        },
        "axes": {
            "md": md_axis.tolist(),
            "radius": rad_axis.tolist()
        },
        "grid": grid
    }

    file_name = 'lateral_extend_perf.json'
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4)

    print(f"\n成功! JSON 已生成: {file_name}")
    print(f"文件大小约为: {os.path.getsize(file_name) / 1024 / 1024:.2f} MB")


# --- 交互界面 ---
window_name = 'Acid Spreading Editor (S: Save, R: Reset, ESC: Exit)'
cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, draw_mask)

print("=" * 40)
print("交互说明:")
print("1. 鼠标左键涂抹: 画出酸液扩散边缘 (左侧为井筒 0m)")
print("2. 按 'S' 键: 执行高精度采样并保存 JSON")
print("3. 按 'R' 键: 清空画布")
print("4. 按 'ESC' 键: 直接退出")
print("=" * 40)

while True:
    # 构造预览画面
    # 蓝色通道显示 Mask 区域
    display = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    display[:, :, 0] = cv2.addWeighted(display[:, :, 0], 1, mask, 0.5, 0)  # 增强蓝色

    # 绘制 UI 引导线
    cv2.line(display, (0, 0), (0, CANVAS_H), (255, 255, 255), 2)  # 井筒线
    cv2.putText(display, f"900m", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(display, f"920m", (10, CANVAS_H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(display, f"Radius: 6.9m", (CANVAS_W - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    cv2.imshow(window_name, display)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        generate_json_from_mask()
        break
    elif key == ord('r'):
        mask[:] = 0
    elif key == 27:
        break

cv2.destroyAllWindows()