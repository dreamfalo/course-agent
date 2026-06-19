import fitz, re

doc = fitz.open(r"C:/Users/Lenovo/Desktop/武文博(2025-2026-2)课表.pdf")

# Get full text from all pages
full_text = ""
for page in doc:
    full_text += page.get_text()

# Parse courses using regex on the full text
# Pattern: course_name followed by (X-Y节) week /场地:loc /教师:teacher
pattern = r'([^\n▲●○△]{2,30})[▲●○△]?\s*\n\s*\((\d+)-(\d+)节\)\s*([\d\-,]+周?)\s*/\s*场地\s*:\s*(.+?)\s*/\s*教师\s*:\s*(.+?)\s*/\s*教学班'

matches = re.findall(pattern, full_text)
print(f"Found {len(matches)} courses:")
for m in matches:
    name, start_p, end_p, weeks, loc, teacher = m
    print(f"  {name.strip()} | 第{start_p}-{end_p}节 | {weeks} | {loc.strip()} | {teacher.strip()}")

# Also try with newlines inside
pattern2 = r'([^\n]{2,30})[▲●○△]?\s*\n\s*\((\d+)-(\d+)节\)\s*([\d\-,]+周?).*?场地\s*[:：]\s*(.+?)\s*/\s*教师\s*[:：]\s*(.+?)\s*/\s*教学班'
matches2 = re.findall(pattern2, full_text, re.DOTALL)
if len(matches2) > len(matches):
    print(f"\nWith DOTALL: {len(matches2)} courses")
    for m in matches2:
        print(f"  {m[0].strip()} | {m[1]}-{m[2]}节 | {m[3]} | {m[4].strip()[:20]} | {m[5].strip()}")
