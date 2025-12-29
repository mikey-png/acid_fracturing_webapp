import cv2
import numpy as np
import json
import os

# --- 参数配置 ---
MD_RANGE = (900.0, 920.0)
RAD_RANGE = (0.0, 6.9)
STEP = 0.01  # 0.01m 精度，生成 2001x691 的矩阵

# 交互窗口显示大小
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
            # 矩形填充保证从中心(左侧)向外的连续性
            cv2.rectangle(mask, (0, y - 3), (x, y + 3), 255, -1)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False


def generate_concentration_json():
    print(f"正在生成 Sediment Concentration 数据 (步长: {STEP}m)...")

    # 1. 定义轴
    md_axis = np.around(np.arange(MD_RANGE[0], MD_RANGE[1] + STEP, STEP), 2)
    rad_axis = np.around(np.arange(RAD_RANGE[0], RAD_RANGE[1] + STEP, STEP), 2)

    # 2. 对图像进行重采样
    target_shape = (len(rad_axis), len(md_axis))
    resized_mask = cv2.resize(mask, target_shape, interpolation=cv2.INTER_LINEAR)

    grid = []

    # 设定量程
    EMPTY_VAL = 0.0  # 未绘制区域填充 0
    MAX_VAL = 100.0  # 井筒处最大值

    print(f"网格尺寸: {len(md_axis)} x {len(rad_axis)}")

    for i in range(len(md_axis)):
        row = []
        row_pixels = resized_mask[i, :]

        # 找到该行最右侧的扩散边界索引
        if np.any(row_pixels > 0):
            max_r_idx = np.where(row_pixels > 0)[0][-1]
        else:
            max_r_idx = 0

        # 层间噪音 (地层非均质性)
        layer_noise = np.random.normal(1.0, 0.03)

        for j in range(len(rad_axis)):
            # --- 核心判断：未绘制/涂抹到的区域填 0 ---
            if j > max_r_idx or resized_mask[i, j] == 0:
                val = EMPTY_VAL
            else:
                if max_r_idx == 0:
                    val = MAX_VAL if resized_mask[i, j] > 0 else 0.0
                else:
                    # 线性/幂函数衰减映射：从井筒(j=0)的 100 到 边缘(max_r_idx)的 0
                    ratio = j / max_r_idx
                    # 使用 0.8 指数让衰减曲线更符合物理扩散特征
                    base_val = MAX_VAL * (1 - ratio ** 0.8)

                    # 加入水平径向噪音
                    local_rand = np.random.uniform(0.95, 1.05)
                    radial_wave = 1.0 + (np.sin(j * 0.4) * 0.02)

                    val = base_val * local_rand * radial_wave * layer_noise

            # 最终数值限制在 0 - 100
            val = min(MAX_VAL, max(0.0, val))
            row.append(round(float(val), 2))

        grid.append(row)
        if i % 500 == 0: print(f"进度: {i}/{len(md_axis)}")

    # 3. 封装 JSON
    output = {
        "metadata": {
            "title": "Perforation Zone Sediment Concentration",
            "md_range": list(MD_RANGE),
            "radius_range": list(RAD_RANGE),
            "value_range": [0.0, 100.0],
            "points_count": {"md": len(md_axis), "radius": len(rad_axis)}
        },
        "axes": {
            "md": md_axis.tolist(),
            "radius": rad_axis.tolist()
        },
        "grid": grid
    }

    file_name = 'sediment_concentration_perf.json'
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4)

    print(f"\n成功! JSON 已生成: {file_name}")


# --- 交互界面 ---
window_name = 'Concentration Editor (S: Save, R: Reset, ESC: Exit)'
cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, draw_mask)

print("=" * 40)
print("Sediment Concentration 生成器说明:")
print("1. 鼠标左键涂抹: 画出沉淀物分布区域 (左侧为井筒)")
print("2. 涂抹区域: 值从 100 (井筒) 衰减到 0 (边缘)")
print("3. 未涂抹区域: 自动填充为 0")
print("4. 按 'S' 键: 保存并导出 JSON")
print("=" * 40)

while True:
    display = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    # 使用品红色/紫色调预览沉淀物浓度
    display[:, :, 2] = cv2.addWeighted(display[:, :, 2], 1, mask, 0.5, 0)  # R通道
    display[:, :, 0] = cv2.addWeighted(display[:, :, 0], 1, mask, 0.5, 0)  # B通道

    cv2.line(display, (0, 0), (0, CANVAS_H), (255, 255, 255), 2)
    cv2.putText(display, "900m", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(display, "920m", (10, CANVAS_H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow(window_name, display)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        generate_concentration_json()
        break
    elif key == ord('r'):
        mask[:] = 0
    elif key == 27:
        break

cv2.destroyAllWindows()