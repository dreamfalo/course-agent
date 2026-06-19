"""
模拟测试数据生成脚本
运行: python seed_data.py
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_agent_backend.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from config.models import SystemUser, SystemConfig
from schedule.models import UserSchedule
from task.models import UserTask
from datetime import date, time


def seed_users():
    """创建测试用户"""
    users = [
        {"username": "student01", "password": "pass1234", "email": "stu01@test.com", "role": "student", "phone": "13800000001"},
        {"username": "student02", "password": "pass1234", "email": "stu02@test.com", "role": "student", "phone": "13800000002"},
        {"username": "admin01", "password": "admin123", "email": "admin@test.com", "role": "admin", "phone": "13900000001"},
    ]
    for u in users:
        user, created = SystemUser.objects.get_or_create(username=u["username"], defaults=u)
        if created:
            user.set_password(u["password"])
            user.save()
            print(f"  [+] 用户: {u['username']} ({u['role']})")
        else:
            print(f"  [~] 已存在: {u['username']}")


def seed_schedules():
    """创建测试课表数据"""
    uid = "student01"
    courses = [
        ("高等数学", "张教授", 0, "08:00", "09:30", "教学楼A101"),
        ("大学英语", "李老师", 0, "10:00", "11:30", "教学楼B201"),
        ("线性代数", "王教授", 1, "14:00", "15:30", "教学楼A102"),
        ("计算机基础", "赵老师", 2, "08:00", "09:30", "实验楼C301"),
        ("数据结构", "刘教授", 2, "10:00", "11:30", "实验楼C302"),
        ("概率论", "陈教授", 3, "14:00", "15:30", "教学楼A103"),
        ("人工智能导论", "周老师", 4, "08:00", "09:30", "教学楼B301"),
        ("体育", "吴老师", 4, "16:00", "17:30", "体育馆"),
    ]
    for i, (name, teacher, wd, st, et, loc) in enumerate(courses):
        course_id = f"COURSE_{i+1:04d}"
        obj, created = UserSchedule.objects.get_or_create(
            course_id=course_id,
            defaults={
                "user_id": uid, "course_name": name, "teacher": teacher,
                "weekday": wd, "start_time": time.fromisoformat(st),
                "end_time": time.fromisoformat(et), "location": loc,
                "week_range": "1-16", "semester": "2025-2026-2",
            },
        )
        status = "创建" if created else "已存在"
        print(f"  [{status}] {name} ({['周一','周二','周三','周四','周五'][wd]} {st}-{et})")


def seed_tasks():
    """创建测试学习任务"""
    uid = "student01"
    plan_id = "PLAN_DEMO_001"
    tasks = [
        ("高等数学复习", "数学", date(2026, 6, 19), 0, "15:30", "17:00", 90, 30),
        ("英语单词背诵", "英语", date(2026, 6, 19), 0, "19:00", "20:00", 60, 20),
        ("数据结构作业", "专业课", date(2026, 6, 20), 1, "16:00", "17:30", 90, 0),
        ("线性代数习题", "数学", date(2026, 6, 21), 2, "14:00", "16:00", 120, 0),
    ]
    for i, (name, subj, d, wd, st, et, dur, prog) in enumerate(tasks):
        task_id = f"TASK_{i+1:04d}"
        obj, created = UserTask.objects.get_or_create(
            task_id=task_id,
            defaults={
                "user_id": uid, "plan_id": plan_id, "task_name": name,
                "subject": subj, "date": d, "weekday": wd,
                "start_time": time.fromisoformat(st),
                "end_time": time.fromisoformat(et),
                "duration_minutes": dur, "progress": prog, "status": "pending",
            },
        )
        status = "创建" if created else "已存在"
        print(f"  [{status}] {name} ({d} {st}-{et})")


def main():
    print("=" * 50)
    print("种子数据生成器")
    print("=" * 50)
    print("\n[1/3] 创建测试用户...")
    seed_users()
    print("\n[2/3] 创建测试课表...")
    seed_schedules()
    print("\n[3/3] 创建测试任务...")
    seed_tasks()
    print("\n" + "=" * 50)
    print("种子数据生成完成！")
    print("=" * 50)
    print("\n测试账号:")
    print("  学生: student01 / pass1234")
    print("  学生: student02 / pass1234")
    print("  管理员: admin01 / admin123")


if __name__ == "__main__":
    main()
