import fitz, re, os, json

desktop = os.path.expanduser("~/Desktop")
pdf_path = None
for f in os.listdir(desktop):
    if "课表" in f and f.endswith(".pdf"):
        pdf_path = os.path.join(desktop, f)
        break

doc = fitz.open(pdf_path)

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

# Extract spans
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
lines = full_text.split('\n')

# Debug: show detail text for each anchor
for i, line in enumerate(lines):
    anchor_m = re.match(r'\((\d+)-(\d+)节\)\s*([\d\-,]+周?)', line.strip())
    if not anchor_m:
        continue
    
    # Join next 8 lines for detail extraction
    detail = ''.join(lines[i:min(i+8, len(lines))])
    # Remove newlines within the detail for regex
    detail_flat = detail.replace('\n', '')
    
    print(f"Course near line {i}:")
    print(f"  Detail flat: {detail_flat[:200]}")
    
    loc_m = re.search(r'场地\s*[:：]\s*(.+?)\s*/\s*教师', detail_flat)
    teacher_m = re.search(r'教师\s*[:：]\s*(.+?)\s*/\s*教学班', detail_flat)
    
    loc = loc_m.group(1).strip() if loc_m else "NOT FOUND"
    teacher = teacher_m.group(1).strip() if teacher_m else "NOT FOUND"
    print(f"  Location: {loc}")
    print(f"  Teacher: {teacher}")
    print()

