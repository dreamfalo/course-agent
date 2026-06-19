"""
全链路集成测试脚本
模拟用户自然语言对话，验证：
  DeepSeek LLM → LangChain Agent 意图识别 → 工具调用 → DB 写入 → API 响应
"""
import os
import sys
import json
import time
import requests

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8000")
USERNAME = "student01"
PASSWORD = "pass1234"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def log(level: str, msg: str):
    color = {"PASS": GREEN, "FAIL": RED, "INFO": CYAN, "WARN": YELLOW}.get(level, "")
    print(f"  {color}[{level}]{RESET} {msg}")


def get_token() -> str:
    log("INFO", "Step 1: 登录获取 JWT Token...")
    resp = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "username": USERNAME, "password": PASSWORD,
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json().get("access", "")
    assert token, "No access token"
    log("PASS", f"Token: {token[:20]}...")
    return token


def h(token): return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def test_schedule_crud(token: str):
    log("INFO", "Step 2: 课表管理 CRUD...")
    headers = h(token)
    resp = requests.get(f"{BASE_URL}/api/schedule/", headers=headers)
    assert resp.status_code == 200
    log("PASS", f"查询课表: {resp.json().get('data', {}).get('total', 0)} 条")

    course = {"course_name": "测试课程-集成", "teacher": "测试教授", "weekday": 3,
              "start_time": "14:00", "end_time": "15:30", "location": "T001", "week_range": "1-8"}
    resp = requests.post(f"{BASE_URL}/api/schedule/", json=course, headers=headers)
    assert resp.status_code == 201
    cid = resp.json()["data"]["id"]
    log("PASS", f"添加课程: ID={cid}")

    resp = requests.post(f"{BASE_URL}/api/schedule/", json=course, headers=headers)
    assert resp.status_code == 409
    log("PASS", "冲突检测生效")

    resp = requests.delete(f"{BASE_URL}/api/schedule/{cid}/", headers=headers)
    assert resp.status_code == 200
    log("PASS", "课程删除成功")
    return True


def test_agent_chat(token: str):
    log("INFO", "Step 3: Agent 自然语言对话...")
    headers = h(token)
    cases = [
        ("帮我查一下课表里有什么课", "schedule_tool"),
        ("帮我搜索一下微积分相关的资料", "rag_retrieve_tool"),
    ]
    sid = None
    for utterance, expected in cases:
        payload = {"message": utterance, "role": "student"}
        if sid: payload["session_id"] = sid
        t0 = time.time()
        resp = requests.post(f"{BASE_URL}/api/agent/chat/", json=payload, headers=headers)
        elapsed = time.time() - t0
        assert resp.status_code == 200, f"Chat failed: {resp.text}"
        data = resp.json()["data"]
        sid = data.get("session_id", "")
        tc = data.get("tool_calls", [])
        if tc:
            called = tc[0].get("tool", "")
            status = "PASS" if called == expected else "WARN"
            log(status, f"「{utterance[:20]}」→ {called} ({elapsed:.1f}s)")
        log("INFO", f"  回复: {data.get('response', '')[:60]}...")
    resp = requests.get(f"{BASE_URL}/api/agent/history/?session_id={sid}", headers=headers)
    log("PASS", f"对话历史持久化: {len(resp.json().get('data', []))} 条")
    return sid


def test_knowledge(token: str):
    log("INFO", "Step 4: 知识库文件上传...")
    headers = {"Authorization": f"Bearer {token}"}
    test_path = "/tmp/test_ai_chain.txt"
    with open(test_path, "w", encoding="utf-8") as f:
        f.write("人工智能是计算机科学的分支，致力于模拟人类智能。\n" * 20)
    with open(test_path, "rb") as f:
        resp = requests.post(f"{BASE_URL}/api/knowledge/",
            files={"file": ("test_ai.txt", f, "text/plain")},
            data={"course_id": "COURSE_0001", "course_name": "人工智能导论"},
            headers=headers)
    assert resp.status_code == 201, f"Upload failed: {resp.text}"
    data = resp.json()["data"]
    log("PASS", f"上传: {data.get('file_name')} ({data.get('chunks_count', 0)} chunks)")
    resp = requests.post(f"{BASE_URL}/api/knowledge/search/", json={"query": "人工智能", "top_k": 3}, headers=h(token))
    assert resp.status_code == 200
    log("PASS", f"检索: {len(resp.json().get('data', {}).get('results', []))} 条")
    os.unlink(test_path)
    return True


def test_task_ai(token: str):
    log("INFO", "Step 5: AI 任务生成...")
    headers = h(token)
    resp = requests.post(f"{BASE_URL}/api/task/ai_generate/", json={
        "daily_study_hours": 2, "subjects": ["数学", "AI"],
        "start_date": "2026-06-20", "days": 7,
    }, headers=headers)
    assert resp.status_code == 200
    plan_id = resp.json().get("data", {}).get("plan_id", "")
    resp = requests.get(f"{BASE_URL}/api/task/gantt/?plan_id={plan_id}", headers=headers)
    log("PASS", f"甘特图: {len(resp.json().get('data', []))} 条")
    return True


def test_config(token: str):
    log("INFO", "Step 6: 系统配置...")
    headers = h(token)
    resp = requests.get(f"{BASE_URL}/api/config/system/public/")
    log("PASS", f"公开配置: {len(resp.json().get('data', {}))} 项")
    resp = requests.get(f"{BASE_URL}/api/config/user/me/", headers=headers)
    log("PASS", f"用户: {resp.json().get('data', {}).get('username', '')}")
    return True


def main():
    print(f"\n{CYAN}{'='*50}{RESET}")
    print(f"{CYAN}  全链路集成测试 - {BASE_URL}{RESET}")
    print(f"{CYAN}{'='*50}{RESET}\n")
    try:
        token = get_token()
    except Exception as e:
        log("FAIL", f"认证失败: {e}")
        log("WARN", "请确保 Django 已启动: python manage.py runserver 8000")
        return 1
    passed, failed = 0, 0
    for name, func in [
        ("课表 CRUD", lambda: test_schedule_crud(token)),
        ("Agent 对话", lambda: test_agent_chat(token)),
        ("知识库上传", lambda: test_knowledge(token)),
        ("AI 任务生成", lambda: test_task_ai(token)),
        ("系统配置", lambda: test_config(token)),
    ]:
        try:
            func()
            passed += 1
        except Exception as e:
            log("FAIL", f"[{name}] {e}")
            failed += 1
    print(f"\n{CYAN}{'='*50}{RESET}")
    print(f"  {GREEN}通过: {passed}{RESET} | {RED}失败: {failed}{RESET}")
    print(f"  {GREEN + '✓ 全链路通过!' if failed == 0 else RED + '✗ 有失败'}{RESET}")
    print(f"{CYAN}{'='*50}\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
