"""
Solapi BMS (카카오 친구톡) 발송 모듈
send_weekly_report.py 패턴 그대로 이식
"""
import hashlib, hmac, time, uuid, json, urllib.request
from config import ACADEMY


def _auth():
    key    = ACADEMY['solapi_key']
    secret = ACADEMY['solapi_secret']
    date   = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
    salt   = str(uuid.uuid4())
    sig    = hmac.new(secret.encode(), (date + salt).encode(), hashlib.sha256).hexdigest()
    return f'HMAC-SHA256 apiKey={key}, date={date}, salt={salt}, signature={sig}'


def send_bms(to: str, text: str) -> dict:
    """
    카카오 친구톡(BMS) 발송. 실패 시 LMS 자동 대체.
    반환: {'ok': True} 또는 {'ok': False, 'error': ..., 'detail': ...}
    """
    payload = {
        'messages': [{
            'to':   to,
            'from': ACADEMY['from_number'],
            'text': text,
            'kakaoOptions': {
                'pfId': ACADEMY['kakao_pf_id'],
                'disableSms': False,
                'bms': {
                    'targeting':      'I',
                    'chatBubbleType': 'TEXT',
                    'content':        text,
                }
            }
        }]
    }
    data = json.dumps(payload).encode('utf-8')
    req  = urllib.request.Request(
        'https://api.solapi.com/messages/v4/send-many',
        data=data,
        headers={'Authorization': _auth(), 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            return {'ok': True, 'raw': result}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        return {'ok': False, 'error': e.code, 'detail': detail}


def send_batch(targets, dry_run=False):
    """
    targets: [{'name': ..., 'phone': ..., 'text': ...}, ...]
    dry_run=True: 실제 발송 없이 결과 객체만 반환
    반환: [{'name': ..., 'ok': True/False, ...}, ...]
    """
    results = []
    for t in targets:
        name, phone, text = t['name'], t['phone'], t['text']
        print(f'  📤 {name:10s} → {phone} ... ', end='', flush=True)
        if dry_run:
            print('⬜ DRY-RUN (발송 생략)')
            results.append({'name': name, 'ok': True, 'dry_run': True})
            continue
        result = send_bms(phone, text)
        if result['ok']:
            print('✅ 카톡 접수')
        else:
            print(f'❌ {result.get("detail", "")[:80]}')
        results.append({'name': name, **result})
        time.sleep(0.3)
    return results
