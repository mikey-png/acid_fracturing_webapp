import json
import random

def generate_oil_rate_json():
    """生成 Oil Rate 数据（920-940m，每米一个数据点）"""
    print("正在生成 Oil Rate 数据...")
    
    data = {
        "metadata": {
            "md_range": [920, 940],
            "value_range_before": [0.09, 2],
            "value_range_after": [0.09, 2]
        },
        "data": []
    }
    
    # 生成 920 到 940 的数据，每米一个点
    for md in range(920, 941):  # 920 到 940，共21个点
        # before: 0.09 到 2
        before = round(0.09 + random.random() * (2 - 0.09), 2)
        # after: 0.09 到 2，但通常比 before 大一些
        after = round(max(before, 0.09 + random.random() * (2 - 0.09)), 2)
        
        data["data"].append({
            "md": md,
            "before": before,
            "after": after
        })
    
    file_name = 'oil_rate_perf.json'
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"成功! JSON 已生成: {file_name}")
    print(f"生成了 {len(data['data'])} 条数据（MD: 920-940m）")

if __name__ == "__main__":
    generate_oil_rate_json()

