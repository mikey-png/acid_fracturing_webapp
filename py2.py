import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import json

def process_well_data_final_fix(input_file, output_json):
    print(f"正在读取文件: {input_file} ...")
    
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        print(f"错误: {e}")
        return

    # --- 1. X 轴转换 (时间轴缩放 0-310) ---
    x_cols = ['x1', 'x2', 'x3', 'x4']
    global_x_max = df[x_cols].max().max()

    def scale_x(val):
        return (val / global_x_max) * 310 if global_x_max != 0 else 0

    # --- 2. Y 轴映射函数 (严格区间映射) ---
    # 逻辑：将 Excel 里的 [Min, Max] 完整映射到 [Target_Min, Target_Max]
    # 这样可以保证结果永远不会超出你设定的范围
    def strict_linear_map(series, target_min, target_max):
        s_min = series.min()
        s_max = series.max()
        
        if s_max == s_min:
            return series.apply(lambda x: target_min)
            
        # 标准线性映射公式：y_target = (y_excel - s_min) / (s_max - s_min) * (target_max - target_min) + target_min
        return (series - s_min) / (s_max - s_min) * (target_max - target_min) + target_min

    # --- 3. 配置四组量程 ---
    processed_series = {
        'surfPressure': {
            'x': df['x1'].apply(scale_x),
            'y': strict_linear_map(df['y1'], 64, 372)  # 严格限制在 [-50, 372]
        },
        'pbhCalc': {
            'x': df['x2'].apply(scale_x),
            'y': strict_linear_map(df['y2'], 126, 452)  # 严格限制在 [-50, 452]
        },
        'designRate': {
            'x': df['x3'].apply(scale_x),
            'y': strict_linear_map(df['y3'], 0.1, 0.5)   # 严格限制在 [0.1, 0.5]
        },
        'skin': {
            'x': df['x4'].apply(scale_x),
            'y': strict_linear_map(df['y4'], -1.8, 1)    # 严格限制在 [-1.8, 1]
        }
    }

    # --- 4. 分钟插值 (0 到 310 min) ---
    target_time = np.arange(10, 311, 1)
    final_output = {"time": target_time.tolist()}

    for key, data in processed_series.items():
        # 准备数据，去除空值
        points = pd.DataFrame({'x': data['x'], 'y': data['y']}).dropna().sort_values('x')
        
        # 线性插值
        # bounds_error=False + fill_value=(y_start, y_end) 确保两端不会出现异常值
        y_points = points['y'].values
        f_interp = interp1d(
            points['x'], 
            y_points, 
            kind='linear', 
            bounds_error=False, 
            fill_value=(y_points[0], y_points[-1]) 
        )
        
        final_output[key] = f_interp(target_time).tolist()

    # --- 5. 导出 JSON ---
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)
    
    print(f"处理完成！Pressure 范围现在是: [{final_output['surfPressure'][0]:.2f}, ...]")
    print(f"结果已保存至: {output_json}")

if __name__ == "__main__":
    process_well_data_final_fix('描点数据.xlsx', 'well_chart_data.json')