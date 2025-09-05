#!/usr/bin/env python3
# =============================================================================
# 实例：GitHub LICENSE 文件（MIT 协议）合规性验证脚本
# 功能：验证 "project-x" 仓库 main 分支中 LICENSE 文件是否存在，且内容符合 MIT 协议标准
# 依赖: requests, python-dotenv (安装：pip install requests python-dotenv)
# 使用说明：1. 配置 .mcp_env 文件；2. 安装依赖；3. 直接运行脚本
# =============================================================================

import sys
import os
import requests
import base64
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv


# --------------------------
# 1. 通用工具函数（适配 LICENSE 验证场景）
# --------------------------
def _call_github_api(
    endpoint: str, 
    headers: Dict[str, str], 
    org: str, 
    repo: str = "project-x"  # 目标仓库名（与GitHub上创建的仓库一致）
) -> Tuple[bool, Optional[Dict]]:
    """调用 GitHub API 并返回（请求状态，响应数据）"""
    url = f"https://api.github.com/repos/{org}/{repo}/{endpoint}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True, response.json()
        elif response.status_code == 404:
            print(f"[API 提示] {endpoint} 资源未找到（404），可能是仓库/文件不存在或分支错误", file=sys.stderr)
            return False, None
        else:
            print(f"[API 错误] {endpoint} 状态码：{response.status_code}，可能是令牌权限不足", file=sys.stderr)
            return False, None
    except Exception as e:
        print(f"[API 异常] 调用 {endpoint} 失败：{str(e)}，请检查网络连接", file=sys.stderr)
        return False, None


def _get_license_content(
    headers: Dict[str, str],
    org: str,
    repo: str = "project-x",
    branch: str = "main"  # 与GitHub上LICENSE文件所在分支一致
) -> Optional[str]:
    """获取指定分支下 LICENSE 文件的内容（Base64 解码，UTF-8 编码）"""
    success, result = _call_github_api(
        f"contents/LICENSE?ref={branch}", headers, org, repo
    )
    if not success or not result:
        return None

    try:
        # 解码 Base64 内容，使用 UTF-8 编码（GitHub 文件默认编码）
        return base64.b64decode(result.get("content", "")).decode("utf-8")
    except Exception as e:
        print(f"[文件解码错误] LICENSE：{e}，可能是文件编码非 UTF-8", file=sys.stderr)
        return None


# --------------------------
# 2. 核心验证逻辑（MIT 协议专属校验）
# --------------------------
def verify_license_compliance() -> bool:
    """验证 LICENSE 文件存在性及 MIT 协议内容准确性"""
    # 1. 预期的 MIT 协议标准内容（清洁化后比对，允许空行/空格差异）
    EXPECTED_MIT_CONTENT = """MIT License
Copyright (c) [Year] [Copyright Holder]
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
    
    # 2. 加载本地环境变量（从 .mcp_env 读取配置）
    load_dotenv(".mcp_env")  # 确保 .mcp_env 与脚本同级目录
    github_token = os.environ.get("MCP_GITHUB_TOKEN")
    github_org = os.environ.get("GITHUB_EVAL_ORG")

    # 3. 校验环境变量是否配置正确
    if not github_token:
        print("Error: .mcp_env 文件中未配置 MCP_GITHUB_TOKEN（GitHub 令牌）", file=sys.stderr)
        return False
    if not github_org:
        print("Error: .mcp_env 文件中未配置 GITHUB_EVAL_ORG（GitHub 组织/用户名）", file=sys.stderr)
        return False

    # 4. 构建 GitHub API 请求头（携带令牌认证）
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"  # 使用 GitHub API v3 版本（稳定版）
    }

    # 5. 执行验证流程
    print("=" * 60)
    print("开始执行 GitHub LICENSE 文件（MIT 协议）合规性验证")
    print(f"目标仓库：{github_org}/project-x（main 分支）")
    print("=" * 60)

    # 步骤1：验证 LICENSE 文件是否存在于 main 分支
    print("\n[1/2] 检查 main 分支中 LICENSE 文件是否存在...")
    license_content = _get_license_content(headers, github_org)
    if not license_content:
        print("Error: main 分支中未找到 LICENSE 文件（可能是路径、分支错误或令牌无权限）", file=sys.stderr)
        return False
    print("✓ 成功：LICENSE 文件存在于 main 分支")

    # 步骤2：验证 LICENSE 内容是否符合 MIT 协议标准（清洁化比对，排除空行/空格干扰）
    print("\n[2/2] 验证 LICENSE 内容是否符合 MIT 协议标准...")
    # 清洁化处理：移除空行、首尾空格，统一格式后比对
    def clean_content(content: str) -> str:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        return "\n".join(lines)
    
    cleaned_actual = clean_content(license_content)
    cleaned_expected = clean_content(EXPECTED_MIT_CONTENT)

    if cleaned_actual != cleaned_expected:
        print("Error: LICENSE 内容不符合 MIT 协议标准", file=sys.stderr)
        print("预期核心条款（示例）：Permission is hereby granted, free of charge...", file=sys.stderr)
        print("实际核心条款（示例）：" + cleaned_actual[:60] + "...", file=sys.stderr)
        return False
    print("✓ 成功：LICENSE 内容符合 MIT 协议标准")

    # 验证通过：输出总结
    print("\n" + "=" * 60)
    print("🎉 所有验证步骤通过！LICENSE 文件（MIT 协议）合规性校验成功")
    print("\n验证总结：")
    print(f"  - 目标仓库：{github_org}/project-x")
    print(f"  - 验证文件：LICENSE（main 分支，根目录）")
    print(f"  - 协议类型：MIT 开源协议")
    print(f"  - 版权信息：{[2025]} {[My Team / Your Name]}（与 LICENSE 文件中配置一致）")
    print("=" * 60)
    return True


# --------------------------
# 3. 脚本入口（直接运行）
# --------------------------
if __name__ == "__main__":
    success = verify_license_compliance()
    sys.exit(0 if success else 1)  # 成功返回0，失败返回1（适配CI/CD流程）
