import requests
import json

# 1. 加载你的API格式工作流
with open(r"D:\work\devlope\comfyUI_b\ComfyUI\user\webapp_tasks\debug_prompt_889aacb3-b4af-420f-9fec-e3c241146028.json", "r", encoding="utf-8") as f:
    workflow = json.load(f)

# 2. （可选）动态修改工作流参数，例如修改某个节点的seed
# 假设你想修改ID为"3"的KSampler节点的seed
# workflow["3"]["inputs"]["seed"] = 42

# 3. 构建请求负载
payload = {
    "prompt": workflow
    # 可以添加其他可选字段，如 "number": 1
}

# 4. 发送POST请求
response = requests.post("http://localhost:8188/prompt", json=payload)

# 5. 处理响应
if response.status_code == 200:
    result = response.json()
    print(f"任务提交成功，prompt_id: {result['prompt_id']}")
else:
    print(f"提交失败，状态码: {response.status_code}")
    print(response.text)