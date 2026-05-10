"""iFind 本地取数模板。

用法：
1. 不要上传账号密码到 GitHub。
2. 在本地 Windows/PyCharm 运行。
3. 把超级命令生成的取数代码粘贴到 TODO 函数里。
4. 输出 CSV 到 local_exports/，再运行 build_deploy_data.py。

注意：Streamlit Cloud 不会运行这个文件；它只在你的本地 iFind 环境运行。
"""
from __future__ import annotations

from pathlib import Path
import os
import pandas as pd

# iFind 环境修复成功后通常可以 import iFinDPy；具体以你的版本为准。
# from iFinDPy import *

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "local_exports"
LOCAL.mkdir(exist_ok=True)


def login_ifind() -> None:
    """本地登录。建议把账号密码放环境变量，不要写进代码。"""
    username = os.getenv("IFIND_USERNAME", "YOUR_USERNAME")
    password = os.getenv("IFIND_PASSWORD", "YOUR_PASSWORD")
    if username == "YOUR_USERNAME":
        print("请先设置 IFIND_USERNAME / IFIND_PASSWORD，或在本地临时替换。")
    # TODO: 取消注释并按你的 iFind 版本调整
    # result = THS_iFinDLogin(username, password)
    # print(result)


def ifind_to_dataframe(result) -> pd.DataFrame:
    """把 iFind 返回对象尽量转成 DataFrame。

    不同 iFind 版本返回格式不同；你把 print(result) 发给我后，我会替你改成稳定版。
    """
    if isinstance(result, pd.DataFrame):
        return result
    # 常见情况：result.data 是二维表，result.columns 是列名
    if hasattr(result, "data"):
        data = getattr(result, "data")
        cols = getattr(result, "columns", None)
        try:
            return pd.DataFrame(data, columns=cols)
        except Exception:
            return pd.DataFrame(data)
    # 兜底
    return pd.DataFrame(result)


def fetch_ipo_projects() -> pd.DataFrame:
    """港股 IPO 列表：必须覆盖 A1/临时代码/未上市项目。

    TODO: 在 iFind 超级命令中搜索：
    港股 A1 申请人 临时代码 Application Proof 招股书 保荐人 行业 递表日期

    输出字段建议对应 deploy_data/ipo_projects_template.csv。
    """
    # 示例伪代码，替换成超级命令生成内容：
    # result = THS_xxx("港股IPO申请人", "临时代码;公司名称;递表日期;保荐人;行业;状态", "...")
    # return ifind_to_dataframe(result)
    return pd.DataFrame()


def fetch_ipo_docs() -> pd.DataFrame:
    """招股书、Application Proof、PHIP、配发结果公告文件登记。

    TODO: 在 iFind 超级命令中搜索：
    港股 IPO 招股书 配发结果公告 文件链接 公告日期
    """
    return pd.DataFrame()


def fetch_price_daily_raw(codes: list[str]) -> pd.DataFrame:
    """上市后日行情原始数据，后续由 sampling_180d.py 压缩成 180日采样表。"""
    pieces = []
    for code in codes:
        # 示例伪代码，替换成超级命令生成内容：
        # result = THS_HQ(code, "open;high;low;close;volume;amount;turnover", "", "2024-01-01", "2026-12-31")
        # df = ifind_to_dataframe(result)
        # df["code"] = code
        # pieces.append(df)
        pass
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def main() -> None:
    login_ifind()

    projects = fetch_ipo_projects()
    if not projects.empty:
        projects.to_csv(LOCAL / "ipo_projects.csv", index=False, encoding="utf-8-sig")
        print("Saved local_exports/ipo_projects.csv")
    else:
        print("ipo_projects empty: 先把超级命令代码填入 fetch_ipo_projects()")

    docs = fetch_ipo_docs()
    if not docs.empty:
        docs.to_csv(LOCAL / "ipo_docs.csv", index=False, encoding="utf-8-sig")
        print("Saved local_exports/ipo_docs.csv")
    else:
        print("ipo_docs empty: 先把超级命令代码填入 fetch_ipo_docs()")

    # 等 ipo_projects 有正式代码/上市日期后，再抓行情。
    if not projects.empty and "code" in projects.columns:
        codes = [x for x in projects["code"].dropna().astype(str).tolist() if x]
        prices = fetch_price_daily_raw(codes)
        if not prices.empty:
            prices.to_csv(LOCAL / "price_daily_raw.csv", index=False, encoding="utf-8-sig")
            print("Saved local_exports/price_daily_raw.csv")


if __name__ == "__main__":
    main()
