# 家庭资产管理系统

个人/家庭资产管理的 Web 应用，支持管理银行理财、股票、基金、黄金四类资产。

## 快速启动

使用 conda 虚拟环境 `family-asset`：

```bash
conda run -n family-asset pip install -r requirements.txt
conda run -n family-asset python main.py
```

浏览器打开 http://localhost:8002

首次启动会自动创建 `app/data/` 目录及 CSV 文件。
