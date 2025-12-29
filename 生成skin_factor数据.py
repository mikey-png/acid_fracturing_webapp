import json
import random

def generate_skin_factor_json():
    """生成 Skin Factor 和 Rwh 数据（920-940m，每米一个数据点）"""
    print("正在生成 Skin Factor 数据...")
    
    data = {
        "metadata": {
            "md_range": [920, 940],
            "skin_factor_range": [-3.2, 1],
            "rwh_range": [0, 13.3]
        },
        "data": []
    }
    
    # 生成 920 到 940 的数据，每米一个点
    for md in range(920, 941):  # 920 到 940，共21个点
        # skin_factor: -3.2 到 1
        skin_factor = round(-3.2 + random.random() * (1 - (-3.2)), 2)
        # rwh: 0 到 13.3
        rwh = round(random.random() * 13.3, 2)
        
        data["data"].append({
            "md": md,
            "skin_factor": skin_factor,
            "rwh": rwh
        })
    
    file_name = 'skin_factor_perf.json'
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"成功! JSON 已生成: {file_name}")
    print(f"生成了 {len(data['data'])} 条数据（MD: 920-940m）")
    print(f"Skin factor 范围: {data['metadata']['skin_factor_range']}")
    print(f"Rwh 范围: {data['metadata']['rwh_range']}")

if __name__ == "__main__":
    generate_skin_factor_json()

