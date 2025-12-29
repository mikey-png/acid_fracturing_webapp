import cv2
import numpy as np
import json
import os

# --- 参数配置 ---
MD_RANGE = (900.0, 920.0)
RAD_RANGE = (0.0, 6.9)
STEP = 0.01  # 0.01m 精度

# 交互窗口显示大小
CANVAS_H = 800
CANVAS_W = 400

# 全局变量
drawing = False
mask = np.zeros((CANVAS_H, CANVAS_W), dtype=np.uint8)


def draw_mask(event, x, y, flags, param):
    global drawing, mask
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            cv2.rectangle(mask, (0, y - 3), (x, y + 3), 255, -1)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False


def generate_porosity_json():
    print(f"正在生成 Increased Porosity 数据 (步长: {STEP}m)...")

    md_axis = np.around(np.arange(MD_RANGE[0], MD_RANGE[1] + STEP, STEP), 2)
    rad_axis = np.around(np.arange(RAD_RANGE[0], RAD_RANGE[1] + STEP, STEP), 2)

    target_shape = (len(rad_axis), len(md_axis))
    resized_mask = cv2.resize(mask, target_shape, interpolation=cv2.INTER_LINEAR)

    grid = []

    # 设定量程
    BASE_VAL = 1.0  # 空余区域/背景值
    ZONE_MIN = 1.5  # 扩散边缘值
    ZONE_MAX = 1.83  # 井筒处最大值

    print(f"网格尺寸: {len(md_axis)} x {len(rad_axis)}")

    for i in range(len(md_axis)):
        row = []
        row_pixels = resized_mask[i, :]

        if np.any(row_pixels > 0):
            max_r_idx = np.where(row_pixels > 0)[0][-1]
        else:
            max_r_idx = 0

        # 层间扰动 (影响溶解强度)
        layer_noise = np.random.normal(1.0, 0.01)

        for j in range(len(rad_axis)):
            # 如果在涂抹区域外，值为 1.0
            if j > max_r_idx or resized_mask[i, j] == 0:
                val = BASE_VAL
            else:
                if max_r_idx == 0:
                    val = ZONE_MAX
                else:
                    # 线性映射：从井筒(j=0)的 1.83 到 边缘(max_r_idx)的 1.5
                    ratio = j / max_r_idx
                    # 计算基础增量：在 1.5 到 1.83 之间波动
                    base_increment = ZONE_MAX - (ZONE_MAX - ZONE_MIN) * (ratio ** 0.7)

                    # 加入水平径向噪音
                    local_rand = np.random.uniform(0.98, 1.02)  # 孔隙度噪音通常比浓度小
                    radial_wave = 1.0 + (np.sin(j * 0.3) * 0.01)

                    val = base_increment * local_rand * radial_wave * layer_noise

            # 严格限制在目标范围内
            if val > BASE_VAL:
                val = min(ZONE_MAX, max(ZONE_MIN, val))
            else:
                val = BASE_VAL

            row.append(round(float(val), 3))

        grid.append(row)
        if i % 500 == 0: print(f"进度: {i}/{len(md_axis)}")

    output = {
        "metadata": {
            "title": "Perforation Zone Increased Porosity",
            "md_range": list(MD_RANGE),
            "radius_range": list(RAD_RANGE),
            "value_range": [1.0, 1.83],
            "points_count": {"md": len(md_axis), "radius": len(rad_axis)}
        },
        "axes": {
            "md": md_axis.tolist(),
            "radius": rad_axis.tolist()
        },
        "grid": grid
    }

    file_name = 'increased_porosity_perf.json'
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4)

    print(f"\n成功! JSON 已生成: {file_name}")


# --- 交互界面 ---
window_name = 'Porosity Editor (S: Save, R: Reset, ESC: Exit)'
cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, draw_mask)

while True:
    display = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    # 使用绿色调预览孔隙度
    display[:, :, 1] = cv2.addWeighted(display[:, :, 1], 1, mask, 0.5, 0)

    cv2.line(display, (0, 0), (0, CANVAS_H), (255, 255, 255), 2)
    cv2.putText(display, "900m", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(display, "920m", (10, CANVAS_H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow(window_name, display)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        generate_porosity_json()
        break
    elif key == ord('r'):
        mask[:] = 0
    elif key == 27:
        break

cv2.destroyAllWindows()