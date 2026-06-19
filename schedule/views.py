"""课表 CRUD + 批量导入 + 文件导出"""
import json
import os
import codecs
from django.http import HttpResponse
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import time as dt_time
import uuid
import re

from schedule.models import UserSchedule
from schedule.serializers import ScheduleSerializer, ScheduleImportSerializer


class ScheduleViewSet(viewsets.ModelViewSet):
    """课表管理 ViewSet"""
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = UserSchedule.objects.filter(user_id=self.request.user.username)
        semester = self.request.query_params.get("semester")
        if semester:
            qs = qs.filter(semester=semester)
        weekday = self.request.query_params.get("weekday")
        if weekday is not None:
            qs = qs.filter(weekday=int(weekday))
        return qs

    def perform_create(self, serializer):
        course_id = f"C{uuid.uuid4().hex[:8].upper()}"
        serializer.save(user_id=self.request.user.username, course_id=course_id)

    def create(self, request, *args, **kwargs):
        # 时间冲突校验
        weekday = request.data.get("weekday")
        start = request.data.get("start_time")
        end = request.data.get("end_time")
        if weekday is not None and start and end:
            try:
                new_start = dt_time.fromisoformat(start)
                new_end = dt_time.fromisoformat(end)
                conflicts = UserSchedule.objects.filter(
                    user_id=request.user.username, weekday=int(weekday)
                )
                for s in conflicts:
                    if new_start < s.end_time and new_end > s.start_time:
                        return Response({
                            "code": 409, "msg": f"时间冲突：与「{s.course_name}」({s.start_time}-{s.end_time})冲突",
                            "data": None,
                        }, status=status.HTTP_409_CONFLICT)
            except (ValueError, TypeError):
                pass
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"code": 0, "msg": "更新成功", "data": serializer.data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"code": 0, "msg": "删除成功", "data": None})

    
    @action(detail=False, methods=["post"])
    def batch_import(self, request):
        """批量导入课表（优化版：bulk_create 单次入库）"""
        ser = ScheduleImportSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        courses = ser.validated_data["courses"]
        semester = ser.validated_data.get("semester", "2025-2026-2")

        # 预计算起始 ID，只查一次
        base_count = UserSchedule.objects.count()
        instances = []
        errors = []

        for i, c in enumerate(courses):
            try:
                instances.append(UserSchedule(
                    user_id=request.user.username,
                    course_id=f"C{uuid.uuid4().hex[:8].upper()}",
                    course_name=c.get("course_name", ""),
                    teacher=c.get("teacher", "待定"),
                    weekday=int(c.get("weekday", 0)),
                    start_time=c.get("start_time", "08:00"),
                    end_time=c.get("end_time", "09:30"),
                    location=c.get("location", "待定"),
                    week_range=c.get("week_range", "1-16"),
                    semester=semester,
                ))
            except Exception as e:
                errors.append({"index": i, "error": str(e)})

        if instances:
            UserSchedule.objects.bulk_create(instances, batch_size=500)

        # 返回详细结果
        created = len(instances)
        result = {
            "code": 0,
            "msg": f"成功导入 {created} 条课程" if created else "未识别到有效课程数据，请检查文件格式",
            "data": {
                "created": created,
                "errors": errors[:5],
                "total_lines": len(raw.strip().split("\n")),
                "hint": "格式：课程名称,教师,星期,开始时间,结束时间,地点,周次",
            },
        }
        return Response(result)
    @action(detail=False, methods=["post"])
    def upload_file(self, request):
        """上传课表文件（PDF/Word/CSV/TXT），解析并导入课表"""
        f = request.FILES.get("file")
        if not f:
            return Response({"code": 400, "msg": "请上传文件", "data": None})
        
        semester = request.data.get("semester", "2025-2026-2")
        fname = f.name.lower()
        raw = ""
        courses_data = []
        errors = []

        # Step 1: Extract text based on file type
        if fname.endswith('.pdf'):
            try:
                import fitz as pymupdf
                f.seek(0)
                pdf_bytes = f.read()
                doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
                
                TIME_MAP = {
                    (1, 2): ("08:00", "09:30"),
                    (3, 4): ("10:00", "11:30"),
                    (5, 6): ("14:00", "15:30"),
                    (7, 8): ("16:00", "17:30"),
                }
                
                COL_BOUNDS = [
                    (63, 140, 0), (140, 190, 1), (190, 320, 2),
                    (320, 440, 3), (440, 560, 4), (560, 640, 5), (640, 999, 6),
                ]
                
                def get_weekday(x_pos):
                    for x0, x1, wd in COL_BOUNDS:
                        if x0 <= x_pos < x1:
                            return wd
                    return 0
                
                all_spans = []
                for page_idx in range(len(doc)):
                    page = doc[page_idx]
                    blocks = page.get_text('dict')['blocks']
                    for b in blocks:
                        if 'lines' in b:
                            for l in b['lines']:
                                for s in l['spans']:
                                    t = s['text'].strip()
                                    if t:
                                        all_spans.append({
                                            'p': page_idx,
                                            'x': s['bbox'][0],
                                            'y': s['bbox'][1],
                                            'text': t
                                        })
                
                full_text = doc[0].get_text()
                text_lines = full_text.split('\n')
                MARKERS = ['▲', '●', '○', '△']
                
                for i, line in enumerate(text_lines):
                    anchor_m = re.match(r'\((\d+)-(\d+)节\)\s*([\d\-,]+周?)', line.strip())
                    if not anchor_m:
                        continue
                    
                    start_p = int(anchor_m.group(1))
                    end_p = int(anchor_m.group(2))
                    weeks = anchor_m.group(3)
                    
                    name_parts = []
                    for j in range(i - 1, max(i - 5, -1), -1):
                        prev = text_lines[j].strip()
                        if not prev:
                            continue
                        if re.match(r'^\d+$', prev):
                            break
                        if prev in ['上午', '下午', '晚上']:
                            break
                        if re.match(r'^\(', prev):
                            break
                        
                        is_marker_only = all(c in MARKERS for c in prev)
                        if is_marker_only:
                            continue
                        
                        has_marker = any(prev.endswith(m) for m in MARKERS)
                        
                        if re.match(r'^[\u4e00-\u9fff\w]', prev):
                            name_parts.insert(0, prev)
                            if has_marker and len(name_parts) >= 1:
                                break
                            if len(name_parts) >= 2:
                                break
                        else:
                            break
                    
                    if not name_parts:
                        continue
                    
                    course_name = ''.join(name_parts)
                    for m in MARKERS:
                        course_name = course_name.replace(m, '')
                    course_name = course_name.strip()
                    course_name = re.sub(r'^\d+\s*', '', course_name).strip()
                    
                    if len(course_name) < 3:
                        continue
                    
                    detail_flat = ''.join(text_lines[i:min(i + 8, len(text_lines))])
                    loc_m = re.search(r'场地\s*[:：]\s*(.+?)\s*/\s*教师', detail_flat)
                    teacher_m = re.search(r'教师\s*[:：]\s*(.+?)\s*/\s*教学班', detail_flat)
                    
                    location = loc_m.group(1).strip() if loc_m else '待定'
                    teacher = teacher_m.group(1).strip() if teacher_m else '待定'
                    
                    x_pos = 81
                    name_start = course_name[:4]
                    for s in all_spans:
                        if s['p'] == 0 and name_start in s['text']:
                            x_pos = s['x']
                            break
                    
                    wd = get_weekday(x_pos)
                    time_slot = TIME_MAP.get((start_p, end_p), ("08:00", "09:30"))
                    
                    courses_data.append({
                        'course_name': course_name,
                        'teacher': teacher,
                        'weekday': wd,
                        'start_time': time_slot[0],
                        'end_time': time_slot[1],
                        'location': location,
                        'week_range': weeks,
                    })
                
                doc.close()
                
            except ImportError:
                try:
                    f.seek(0)
                    from PyPDF2 import PdfReader
                    reader = PdfReader(f)
                    raw = '\n'.join(p.extract_text() or '' for p in reader.pages)
                except Exception as e:
                    return Response({"code": 400, "msg": f"PDF解析失败: {e}", "data": None})
            except Exception as e:
                return Response({"code": 400, "msg": f"PDF解析失败: {e}", "data": None})
        
        elif fname.endswith('.docx'):
            try:
                from docx import Document
                f.seek(0)
                doc_obj = Document(f)
                raw = '\n'.join(p.text for p in doc_obj.paragraphs if p.text.strip())
            except Exception as e:
                return Response({"code": 400, "msg": f"Word解析失败: {e}", "data": None})
        
        else:
            try:
                f.seek(0)
                raw = f.read().decode("utf-8-sig")
            except UnicodeDecodeError:
                try:
                    f.seek(0)
                    raw = f.read().decode("gbk")
                except Exception as e:
                    return Response({"code": 400, "msg": f"文件编码错误: {e}", "data": None})
        
        # Step 2: Parse CSV/TXT/DOCX lines
        if raw and not courses_data:
            weekday_map = {
                "周一": 0, "周二": 1, "周三": 2, "周四": 3,
                "周五": 4, "周六": 5, "周日": 6,
                "星期一": 0, "星期二": 1, "星期三": 2,
                "星期四": 3, "星期五": 4, "星期六": 5, "星期日": 6,
            }
            
            csv_lines = raw.strip().replace('\r', '').split('\n')
            for line_no, line in enumerate(csv_lines, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line_no == 1 and any(kw in line for kw in ["课程", "名称", "教师", "星期", "时间"]):
                    continue
                if len(line) < 8:
                    continue
                
                sep = '，' if '，' in line and ',' not in line else ','
                parts = [p.strip() for p in line.split(sep)]
                if len(parts) < 6:
                    continue
                
                try:
                    course_name = parts[0]
                    teacher = parts[1]
                    weekday_str = parts[2]
                    start_time = parts[3]
                    end_time = parts[4]
                    location = parts[5] if len(parts) > 5 else "待定"
                    week_range = parts[6] if len(parts) > 6 else "1-16"
                    
                    weekday = weekday_map.get(weekday_str)
                    if weekday is None:
                        try:
                            weekday = int(weekday_str)
                        except ValueError:
                            continue
                    
                    courses_data.append({
                        'course_name': course_name,
                        'teacher': teacher,
                        'weekday': weekday,
                        'start_time': start_time,
                        'end_time': end_time,
                        'location': location,
                        'week_range': week_range,
                    })
                except Exception as e:
                    errors.append({"line": line_no, "error": str(e)})
        
        # Step 3: Clear old courses and bulk create new ones
        if not courses_data:
            return Response({
                "code": 400,
                "msg": "未识别到有效课程数据，请检查文件格式",
                "data": {"hint": "支持教务系统PDF、CSV(课程名称,教师,星期,开始时间,结束时间,地点,周次)、Word文档"},
            })
        
        UserSchedule.objects.filter(user_id=request.user.username).delete()
        
        instances = []
        for c in courses_data:
            try:
                instances.append(UserSchedule(
                    user_id=request.user.username,
                    course_id="C" + uuid.uuid4().hex[:8].upper(),
                    course_name=c['course_name'],
                    teacher=c['teacher'],
                    weekday=int(c['weekday']),
                    start_time=c['start_time'],
                    end_time=c['end_time'],
                    location=c['location'],
                    week_range=c['week_range'],
                    semester=semester,
                ))
            except Exception as e:
                errors.append({'course': c.get('course_name', '?'), 'error': str(e)})
        
        if instances:
            UserSchedule.objects.bulk_create(instances, batch_size=500)
        
        return Response({
            "code": 0,
            "msg": "成功导入 {} 条课程".format(len(instances)),
            "data": {
                "created": len(instances),
                "errors": errors[:5],
                "hint": "已覆盖旧课表，新导入 {} 门课程".format(len(instances)),
            },
        })

    def auto_import(self, request):
        """自动导入：从教务系统抓取课表"""
        url = request.data.get("url", "")
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        if not url or not username or not password:
            return Response({"code": 400, "msg": "请填写教务系统网址、账号和密码", "data": None})

        created = 0
        errors = []
        try:
            # 尝试使用 requests + BeautifulSoup 抓取
            import requests as rq
            session = rq.Session()
            session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

            # Step 1: 尝试常见教务系统登录路径
            login_url = url.rstrip("/") + "/login"
            resp = session.get(login_url, timeout=10, allow_redirects=True)
            if resp.status_code != 200:
                # 尝试备用路径
                for alt in ["/auth/login", "/signin", "/index/login", "/cas/login"]:
                    try:
                        resp = session.get(url.rstrip("/") + alt, timeout=10)
                        if resp.status_code == 200:
                            login_url = url.rstrip("/") + alt
                            break
                    except:
                        continue

            # Step 2: 解析登录表单
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            form = soup.find("form")
            if not form:
                return Response({"code": 400, "msg": "无法识别登录表单，请确认教务系统网址", "data": None})

            # 收集表单字段
            form_data = {}
            for inp in form.find_all("input"):
                name = inp.get("name")
                if name:
                    form_data[name] = inp.get("value", "")
            # 尝试常见用户名/密码字段名
            for uname_key in ["username", "uname", "user", "account", "j_username", "yhzh", "xh", "学号"]:
                if uname_key in form_data:
                    form_data[uname_key] = username
                    break
            for pwd_key in ["password", "pwd", "passwd", "j_password", "yhmm", "mm", "密码"]:
                if pwd_key in form_data:
                    form_data[pwd_key] = password
                    break

            action = form.get("action", "")
            if action and not action.startswith("http"):
                action = login_url.rsplit("/", 1)[0] + "/" + action.lstrip("/")
            post_url = action or login_url

            # Step 3: 提交登录
            login_resp = session.post(post_url, data=form_data, timeout=15, allow_redirects=True)
            if "密码错误" in login_resp.text or "用户名" in login_resp.text or login_resp.status_code == 401:
                return Response({"code": 400, "msg": "登录失败，请检查账号密码", "data": None})

            # Step 4: 跳转到课表页面
            schedule_urls = ["/schedule", "/course/schedule", "/student/schedule", "/xsgrkbcx", "/kbcx", "/student/course", "/courseTable"]
            schedule_html = ""
            for s_url in schedule_urls:
                try:
                    r = session.get(url.rstrip("/") + s_url, timeout=15)
                    if r.status_code == 200 and len(r.text) > 500:
                        schedule_html = r.text
                        break
                except:
                    continue

            if not schedule_html:
                return Response({"code": 400, "msg": "未找到课表页面，请手动上传或添加", "data": None})

            # Step 5: 解析课表表格
            soup2 = BeautifulSoup(schedule_html, "html.parser")
            table = soup2.find("table")
            if not table:
                return Response({"code": 400, "msg": "未识别到课表表格", "data": None})

            rows = table.find_all("tr")
            weekday_map_cn = {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6}

            # 解析每个单元格
            base_count = UserSchedule.objects.filter(user_id=request.user.username).count()
            instances = []
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) < 6:
                    continue
                for col_idx, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    if not text or len(text) < 6 or col_idx == 0:
                        continue
                    # 按换行符拆分（一个格子可能有多个课程）
                    courses_in_cell = [c.strip() for c in text.replace("\r", "\n").split("\n") if len(c.strip()) > 6]
                    for course_text in courses_in_cell:
                        try:
                            parts = [p.strip() for p in course_text.split(",") if p.strip()]
                            if len(parts) < 2:
                                continue
                            course_name = parts[0]
                            teacher = parts[1] if len(parts) > 1 else "待定"
                            location = parts[2] if len(parts) > 2 else "待定"
                            week_range = parts[3] if len(parts) > 3 else "1-16"

                            instances.append(UserSchedule(
                                user_id=request.user.username,
                                course_id=f"C{uuid.uuid4().hex[:8].upper()}",
                                course_name=course_name,
                                teacher=teacher,
                                weekday=col_idx - 1 if col_idx > 0 else 0,
                                start_time="08:00",
                                end_time="09:30",
                                location=location,
                                week_range=week_range,
                                semester=request.data.get("semester", "2025-2026-2"),
                            ))
                            created += 1
                        except Exception as e:
                            errors.append({"text": course_text[:50], "error": str(e)})

            if instances:
                UserSchedule.objects.bulk_create(instances, batch_size=50)

        except ImportError:
            return Response({"code": 400, "msg": "缺少依赖库(requests/bs4)，请手动导入", "data": None})
        except Exception as e:
            return Response({"code": 500, "msg": f"抓取失败: {e}", "data": None})

        return Response({
            "code": 0,
            "msg": f"成功导入 {created} 条课程",
            "data": {"created": created, "errors": errors[:5]},
        })





    @action(detail=False, methods=["get"])
    def export(self, request):
        """导出课表为 CSV（可扩展 Excel/ICS）"""
        fmt = request.query_params.get("format", "csv")
        qs = self.get_queryset()
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        if fmt == "csv":
            rows = ["课程名称,教师,星期,时间,地点,周次"]
            for s in qs:
                rows.append(
                    f"{s.course_name},{s.teacher},{weekdays[s.weekday]},"
                    f"{s.start_time}-{s.end_time},{s.location},{s.week_range}"
                )
            content = "\n".join(rows)
            response = HttpResponse(content, content_type="text/csv; charset=utf-8-sig")
            response["Content-Disposition"] = "attachment; filename=schedule.csv"
            return response
        return Response({"code": 400, "msg": f"不支持的格式: {fmt}", "data": None})
