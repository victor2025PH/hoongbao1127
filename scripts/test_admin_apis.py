#!/usr/bin/env python3
"""
测试管理后台所有 API 端点
"""
import requests
import json
import sys
from urllib3.exceptions import InsecureRequestWarning

# 禁用 SSL 警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = "https://admin.usdt2026.cc/api"
USERNAME = "admin"
PASSWORD = "123456"

def get_token():
    """获取登录 token"""
    url = f"{BASE_URL}/v1/admin/auth/login"
    data = {"username": USERNAME, "password": PASSWORD}
    
    try:
        response = requests.post(url, json=data, verify=False)
        if response.status_code == 200:
            result = response.json()
            return result.get("token")
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {str(e)}")
        return None

def test_api(endpoint, method="GET", token=None, data=None, description=""):
    """测试 API 端点"""
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, verify=False)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, verify=False)
        else:
            print(f"❌ 不支持的 HTTP 方法: {method}")
            return False
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {description}")
            if "data" in result:
                data_info = result["data"]
                if isinstance(data_info, dict):
                    # 显示关键统计信息
                    for key in ["total", "users", "redpackets", "transactions"]:
                        if key in data_info:
                            print(f"   {key}: {data_info[key]}")
            return True
        else:
            print(f"❌ {description} - 状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ {description} - 错误: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("  管理后台 API 测试")
    print("=" * 60)
    print()
    
    # 1. 登录获取 token
    print("[1/7] 测试登录...")
    token = get_token()
    if not token:
        print("❌ 无法获取 token，测试终止")
        return
    print(f"✅ 登录成功，Token: {token[:50]}...")
    print()
    
    # 2. 测试仪表盘统计
    print("[2/7] 测试仪表盘统计...")
    test_api("/v1/admin/dashboard/stats", token=token, description="仪表盘统计")
    print()
    
    # 3. 测试用户列表
    print("[3/7] 测试用户管理...")
    test_api("/v1/admin/users/list", token=token, description="用户列表")
    print()
    
    # 4. 测试红包列表
    print("[4/7] 测试红包管理...")
    test_api("/v1/admin/redpackets/list", token=token, description="红包列表")
    print()
    
    # 5. 测试交易列表
    print("[5/7] 测试交易管理...")
    test_api("/v1/admin/transactions/list", token=token, description="交易列表")
    print()
    
    # 6. 测试签到管理
    print("[6/7] 测试签到管理...")
    test_api("/v1/admin/checkin/list", token=token, description="签到记录列表")
    test_api("/v1/admin/checkin/stats", token=token, description="签到统计")
    print()
    
    # 7. 测试邀请管理
    print("[7/7] 测试邀请管理...")
    test_api("/v1/admin/invite/list", token=token, description="邀请记录列表")
    test_api("/v1/admin/invite/stats", token=token, description="邀请统计")
    print()
    
    print("=" * 60)
    print("  测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()

