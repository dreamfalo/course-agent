import os, sys
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'course_agent_backend.settings'
import django; django.setup()
key = os.getenv('DEEPSEEK_API_KEY','')
print('DeepSeek Key:', ('LOADED' if key else 'MISSING'))
