import json
import random

## 生成井筒的数据

def generate_wellbore_data_2m(file_name="wellbore_data_2m.json"):
    data = []
    
    # 设定起始和结束值
    start_md, end_md = 0.4, 2400.0
    start_tvd, end_tvd = 0.4, 1600.0
    
    # 属性范围
    perm_min, perm_max = 1.0, 8.7
    poro_min, poro_max = 10.0, 50.0
    
    # 射孔区间 MD: 900 - 920
    perf_start, perf_end = 900.0, 920.0
    
    # 步长设为 2 米
    step = 2.0
    
    # 计算总点数
    # 使用 round 确保浮点数计算不会因精度问题少生一个点
    current_md = start_md
    while current_md <= end_md:
        # 计算当前的 TVD (线性插值：TVD = start_tvd + (current_md - start_md) * TVD总跨度 / MD总跨度)
        md_progress = (current_md - start_md) / (end_md - start_md)
        current_tvd = start_tvd + md_progress * (end_tvd - start_tvd)
        
        # 随机生成地质属性
        # 为了让图表看起来更有规律，渗透率可以使用简单的平滑随机
        lithology = random.choice(["Dolomite", "Limestone"])
        permeability = round(random.uniform(perm_min, perm_max), 2)
        porosity = round(random.uniform(poro_min, poro_max), 1)
        
        # 射孔逻辑判断
        is_perforated = perf_start <= current_md <= perf_end
        
        data.append({
            "TVD": round(current_tvd, 2),
            "MD": round(current_md, 2),
            "lithology": lithology,
            "permeability": permeability,
            "porosity": porosity,
            "isPerforated": is_perforated
        })
        
        current_md = round(current_md + step, 2)

    # 导出 JSON
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    
    print(f"完成！生成了 {len(data)} 条数据，步长 2m，已存至 {file_name}")

if __name__ == "__main__":
    generate_wellbore_data_2m()