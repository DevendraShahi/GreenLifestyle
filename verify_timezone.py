import os
import django
from django.conf import settings
from django.utils import timezone
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GreenLifestyle.settings')
django.setup()

def verify_timezone():
    print(f"Current Timezone: {settings.TIME_ZONE}")
    
    if settings.TIME_ZONE != 'America/Toronto':
        print("FAIL: Timezone is not America/Toronto")
        return

    now_utc = timezone.now()
    now_local = timezone.localtime(now_utc)
    
    print(f"UTC Time: {now_utc}")
    print(f"Local Time ({settings.TIME_ZONE}): {now_local}")
    
    # Check if local time matches expected offset (approximate check)
    # Toronto is UTC-5 (EST) or UTC-4 (EDT)
    offset = now_local.utcoffset()
    print(f"UTC Offset: {offset}")
    
    if offset in [datetime.timedelta(hours=-5), datetime.timedelta(hours=-4)]:
        print("PASS: Timezone offset seems correct for Toronto")
    else:
        print("FAIL: Unexpected timezone offset")

    print(f"Local Date: {now_local.date()}")

if __name__ == "__main__":
    verify_timezone()
