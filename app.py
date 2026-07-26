#للمزيد من الادوات والتطبيقات المكسوره انضم إلى قناة @editortrue
#dev محمود عادل الغريب
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

COOKIES = {
    'PREF': '&hl=ar',
    'VISITOR_INFO1_LIVE': 'ezamH7kpeoQ',
    'YSC': '8xuNjsQmLT4',
    '__Secure-YNID': '20.YT=OHkLyfMnmPp1Em5kp9ArTCpimmHGvswYqK7Le0N6GjkodzP6BJrTEiNViLcnr5YLGJmDiCwk5275kbpumF2cfiaLv3Or8bU3t8Nr9UxnHFOQOlo1yEYQir1iqOaJN6HQUOQTz-ItJPzD7l-1VRYMCU3VKwFQrpyOW1ci8Phg22Pu6djib5WBnW54anD12j966PjAvyJwzq53TwzOW8tIuG33L76BbdzjHERoWszuHIUHv4zCEd8ZMnLgEvMbfgj2JZ4aS7eqL0CaMd36XIQ291wqaxUwBX_sfgeKX8Wegydtn4PpfMybAQpo0k9u1LQCv1BYtZ6xHmh4ZBRvvC-q3Q',
    'VISITOR_PRIVACY_METADATA': 'CgJFRxIEGgAgLQ%3D%3D',
    '__Secure-ROLLOUT_TOKEN': 'COzr983K-Ze-rAEQ-uv49qHalQMYh5vJ96HalQM%3D',
    'GPS': '1',
}

HEADERS = {
    'host': 'www.youtube.com',
    'x-youtube-client-name': '1',
    'x-youtube-client-version': '2.20260715.04.00',
    'x-youtube-page-cl': '948412686',
    'x-youtube-page-label': 'youtube.desktop.web_20260715_04_RC00',
    'accept-language': 'ar',
    'x-goog-visitor-id': 'CgtlemFtSDdrcGVvUSi41OnSBjIKCgJFRxIEGgAgLWLfAgrcAjIwLllUPU9Ia0x5Zk1ubVBwMUVtNWtwOUFyVENwaW1tSEd2c3dZcUs3TGUwTjZHamtvZHpQNkJKclRFaU5WaUxjbnI1WUxHSm1EaUN3azUyNzVrYnB1bUYyY2ZpYUx2M09yOGJVM3Q4TnI5VXhuSEZPUU9sbzF5RVlRaXIxaXFPYUpONkhRVU9RVHotSXRKUHpEN2wtMVZSWU1DVTNWS3dGUXJweU9XMWNpOFBoZzIyUHU2ZGppYjVXQm5XNTRhbkQxMmo5NjZQakF2eUp3enE1M1R3ek9XOHRJdUczM0w3NkJiZHpqSEVSb1dzenVISVVIdjR6Q0VkOFpNbkxnRXZNYmZnajJKWjRhUzdlcUwwQ2FNZDM2WElRMjkxd3FheFV3Qlhfc2ZnZUtYOFdlZ3lkdG40UHBmTXliQVFwbzBrOXUxTFFDdjFCWXRaNnhIbWg0WkJSdnZDLXEzUQ%3D%3D',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36',
}


def get_streaming_data(video_id):
    params = {'v': video_id, 'pbj': '1'}
    r = requests.get('https://www.youtube.com/watch', params=params,
                      cookies=COOKIES, headers=HEADERS, timeout=15)
    data = r.json()
    player_response = data.get('playerResponse', {})
    return player_response, player_response.get('streamingData', {})


def pick_best_url(streaming_data, kind):
    base_url = streaming_data.get('serverAbrStreamingUrl') or streaming_data.get('dashManifestUrl') or ''
    if not base_url:
        return None
    candidates = [f for f in streaming_data.get('adaptiveFormats', [])
                  if f'{kind}/' in f.get('mimeType', '')]
    if not candidates:
        return None
    key = 'height' if kind == 'video' else 'bitrate'
    candidates.sort(key=lambda x: x.get(key, 0), reverse=True)
    itag = candidates[0].get('itag')
    return f"{base_url}&itag={itag}"


@app.route('/download', methods=['POST'])
def download():
    body = request.get_json(force=True, silent=True) or {}
    video_id = body.get('videoId')
    fmt = body.get('format', 'mp4')

    if not video_id:
        return jsonify(success=False, error='videoId مطلوب'), 400

    try:
        player_response, streaming_data = get_streaming_data(video_id)
        if not streaming_data:
            return jsonify(success=False, error='تعذر جلب بيانات البث (ربما انتهت صلاحية الكوكيز)')

        kind = 'video' if fmt == 'mp4' else 'audio'
        url = pick_best_url(streaming_data, kind)
        if not url:
            return jsonify(success=False, error='لا يوجد رابط مناسب لهذه الصيغة')

        title = player_response.get('videoDetails', {}).get('title', video_id)
        ext = 'mp4' if fmt == 'mp4' else 'm4a'
        return jsonify(success=True, downloadUrl=url, filename=f"{title}.{ext}")

    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.route('/', methods=['GET'])
def health():
    return jsonify(status='ok')


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
