"""agent_core 通用工具函数"""
from typing import List, Tuple, Optional
from datetime import datetime, time, timedelta


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """将文本按指定大小分块，支持重叠"""
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += (chunk_size - chunk_overlap)
        if start >= len(text):
            break
    return chunks


def parse_date_range(date_str: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """解析日期范围字符串，支持多种格式"""
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
    ]
    parts = [p.strip() for p in date_str.split("~") if p.strip()]
    if not parts:
        return None, None
    start, end = None, None
    for fmt in formats:
        try:
            start = datetime.strptime(parts[0], fmt)
            break
        except ValueError:
            continue
    if len(parts) > 1:
        for fmt in formats:
            try:
                end = datetime.strptime(parts[1], fmt)
                break
            except ValueError:
                continue
    return start, end


def detect_conflict(
    periods: List[Tuple[time, time]],
    new_start: time,
    new_end: time,
) -> bool:
    """检测时间段是否与已有时间段冲突"""
    for start, end in periods:
        if new_start < end and new_end > start:
            return True
    return False


def weekday_str_to_int(weekday: str) -> int:
    """星期字符串转数字 0=周一"""
    week = weekday.strip()
    mapping = {
        "一": 0, "周一": 0, "星期一": 0,
        "二": 1, "周二": 1, "星期二": 1,
        "三": 2, "周三": 2, "星期三": 2,
        "四": 3, "周四": 3, "星期四": 3,
        "五": 4, "周五": 4, "星期五": 4,
        "六": 5, "周六": 5, "星期六": 5,
        "日": 6, "周日": 6, "星期天": 6, "天": 6,
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    return mapping.get(week.lower(), -1)
