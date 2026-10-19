import os
import sys
import time
import random
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Append current directory to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from flask import Flask, jsonify, request, make_response
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Ignore SSL certificate warnings
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# Try importing protobuf modules for backward compatibility
try:
    from protobuf import my_pb2, output_pb2
except Exception:
    my_pb2 = None
    output_pb2 = None

# Import 55+ authentic real Android devices database
try:
    from devices import (
        REAL_ANDROID_DEVICES,
        get_device_for_identifier,
        get_random_device,
        get_device_by_model,
        get_devices_by_brand,
        generate_random_ip,
    )
except ImportError:
    REAL_ANDROID_DEVICES = [
        {
            "model": "realme RMX2189",
            "brand": "Realme",
            "marketing_name": "Realme C15",
            "system_software": "Android OS 10 / API-29 (QP1A.190711.020/1617006012)",
            "screen_width": 1600,
            "screen_height": 720,
            "screen_dpi": "320",
            "processor_details": "ARM64 FP ASIMD AES | 2301 | 8",
            "memory": 2799,
            "gpu_renderer": "PowerVR Rogue GE8320",
            "opengl": "OpenGL ES 3.2 build 1.11@5425693",
            "carrier": "Vi India",
            "network": "WIFI",
        }
    ]
    def generate_random_ip():
        return f"{random.randint(1,223)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    def get_device_by_model(m):
        return REAL_ANDROID_DEVICES[0]
    def get_devices_by_brand(b):
        return REAL_ANDROID_DEVICES
    def get_random_device(b=None):
        return REAL_ANDROID_DEVICES[0]
    def get_device_for_identifier(identifier=None, model_preference=None, brand_preference=None, random_select=True):
        return REAL_ANDROID_DEVICES[0]

# Import MajorLogin components directly from Sell.py
try:
    from Sell import (
        AES_KEY,
        AES_IV,
        MAJOR_LOGIN_URL,
        CLIENT_SECRET,
        send_major_login,
        MajorLoginResult,
        assemble_proto,
        parse_proto,
        aes_encrypt,
        aes_decrypt,
        write_varint,
        write_varint_field,
        write_string_field,
        write_bytes_field,
        read_varint,
    )
except ImportError:
    AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    MAJOR_LOGIN_URL = "https://loginbp.ppmainecoonghj.com/MajorLogin"
    CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"

    def write_varint(value: int) -> bytes:
        out = []
        while value > 127:
            out.append((value & 0x7F) | 0x80)
            value >>= 7
        out.append(value)
        return bytes(out)

    def write_varint_field(f, v):
        return write_varint((f << 3) | 0) + write_varint(v)

    def write_string_field(f, v):
        b = v.encode("utf-8") if isinstance(v, str) else v
        return write_varint((f << 3) | 2) + write_varint(len(b)) + b

    def write_bytes_field(f, v):
        return write_varint((f << 3) | 2) + write_varint(len(v)) + v

    def assemble_proto(fields):
        data = bytearray()
        for k, v in fields.items():
            if isinstance(v, int):
                data.extend(write_varint_field(k, v))
            elif isinstance(v, str):
                data.extend(write_string_field(k, v))
            elif isinstance(v, bytes):
                data.extend(write_bytes_field(k, v))
        return bytes(data)

    def read_varint(data, offset):
        r, s = 0, 0
        while True:
            b = data[offset]; offset += 1
            r |= (b & 0x7F) << s
            if not (b & 0x80):
                break
            s += 7
        return r, offset

    def parse_proto(data):
        out = {}
        off = 0
        while off < len(data):
            try:
                tag, off = read_varint(data, off)
            except Exception:
                break
            f = tag >> 3
            w = tag & 0x7
            if f == 0:
                break
            try:
                if w == 0:
                    v, off = read_varint(data, off)
                    out[f] = v
                elif w == 2:
                    ln, off = read_varint(data, off)
                    val = data[off:off + ln]
                    off += ln
                    try:
                        out[f] = val.decode("utf-8")
                    except Exception:
                        out[f] = val
                else:
                    break
            except Exception:
                break
        return out

    def aes_encrypt(plain):
        return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(plain, AES.block_size))

    def aes_decrypt(ciphertext):
        if not ciphertext or len(ciphertext) % 16 != 0:
            return ciphertext
        try:
            try:
                return unpad(AES.new(AES_KEY, AES.MODE_CBC, AES_IV).decrypt(ciphertext),
                             AES.block_size)
            except ValueError:
                return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).decrypt(ciphertext)
        except Exception:
            return ciphertext

    class MajorLoginResult(tuple):
        def __new__(cls, jwt, session_key, session_iv, api="N/A", region="N/A", status="live", account_id=None, device_model="N/A", device_brand="N/A", raw_parsed=None):
            return super().__new__(cls, (jwt, session_key, session_iv))

        def __init__(self, jwt, session_key, session_iv, api="N/A", region="N/A", status="live", account_id=None, device_model="N/A", device_brand="N/A", raw_parsed=None):
            self.jwt = jwt
            self.token = jwt
            self.session_key = session_key
            self.session_iv = session_iv
            self.api = api
            self.region = region
            self.status = status
            self.account_id = account_id
            self.device_model = device_model
            self.device_brand = device_brand
            self.raw_parsed = raw_parsed or {}

        def get(self, key, default=None):
            return getattr(self, key, default)

        def to_dict(self):
            return {
                "token": self.jwt,
                "api": self.api,
                "region": self.region,
                "status": self.status,
                "account_id": self.account_id,
                "device_model": self.device_model,
                "device_brand": self.device_brand,
                "session_key": self.session_key.hex() if isinstance(self.session_key, (bytes, bytearray)) else str(self.session_key),
                "session_iv": self.session_iv.hex() if isinstance(self.session_iv, (bytes, bytearray)) else str(self.session_iv),
                "credit": "RGK TEAM X BT4 TEAM",
            }

    def send_major_login(session, access_token, open_id, platform="4", device=None):
        if device is None:
            device = get_device_for_identifier(open_id, random_select=True)

        model = device.get("model", "realme RMX2189")
        brand = device.get("brand", "Realme")
        os_info = device.get("system_software", "Android OS 10 / API-29 (QP1A.190711.020/1617006012)")
        carrier = device.get("carrier", "Vi India")
        network = device.get("network", "WIFI")
        width = int(device.get("screen_width", 1600))
        height = int(device.get("screen_height", 720))
        dpi = str(device.get("screen_dpi", "320"))
        cpu = device.get("processor_details", "ARM64 FP ASIMD AES | 2301 | 8")
        ram = int(device.get("memory", 2799))
        gpu_renderer = device.get("gpu_renderer", "PowerVR Rogue GE8320")
        opengl = device.get("opengl", "OpenGL ES 3.2 build 1.11@5425693")
        user_id = device.get("unique_device_id") or f"Google|{open_id}"
        client_ip = device.get("client_ip") or generate_random_ip()

        fields = {
            3: time.strftime("%Y-%m-%d %H:%M:%S"),
            4: "free fire", 5: 1, 7: "2.133.9",
            8: os_info,
            9: "Handheld", 10: carrier, 11: network,
            12: width, 13: height, 14: dpi,
            15: cpu, 16: ram,
            17: gpu_renderer,
            18: opengl,
            19: user_id,
            20: client_ip,
            21: "en", 22: open_id, 23: str(platform),
            24: "Handheld", 25: model, 26: "TW",
            29: access_token, 30: 1,
            41: carrier, 42: network,
            57: "1ac4b80ecf0478a44203bf8fac6120f5",
            60: 19799, 61: 2536, 62: 5056, 64: 2768,
            65: 19999, 66: 2536, 67: 19799,
            73: 1,
            74: "/data/app/com.dts.freefiremax-ShI7E0dK8p1IiZ785pvuVQ==/lib/arm64",
            76: 2,
            77: "38f4751a330688ab124c2c804cec90a5|/data/app/com.dts.freefiremax-ShI7E0dK8p1IiZ785pvuVQ==/base.apk",
            78: 2, 79: 2, 81: "64", 83: "2019118527",
            86: "OpenGLES3", 87: 3071, 88: 4, 92: 67920,
            93: "android_max",
            94: "KqsHT+UrR1HKqb6+1db+Ofei+NtZr2+hbiBo3yKDL8w+8E3S5qF2IgEEe1fFQFyHRzl4iyHjHp+QsfeLbjJ6+DidTiKxm0ak2uYYa6QR4nAUdlZR",
            95: 111107,
            96: '{"cur_rate":null,"support_etc2":true}',
            97: 1, 98: 1, 99: "4", 100: "4", 102: "",
            104: 83812, 105: 1,
            106: "https://dl-bs.ggpolarbear.com/live/ABHotUpdates/|https://core-bs.ggpolarbear.com/live/ABHotUpdates/|a4332cb1c1a84e51dd77441e4856ed5a",
            107: "1.9393e7b8e53e8aeb",
        }
        encrypted = aes_encrypt(assemble_proto(fields))
        headers = {
            "Host": "loginbp.ppmainecoonghj.com",
            "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept": "*/*",
            "Accept-Encoding": "deflate, gzip",
            "X-GA-SV": str(int(time.time())),
            "Authorization": "Bearer",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB55",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2018.4.12f1",
            "Content-Length": str(len(encrypted)),
        }
        r = session.post(MAJOR_LOGIN_URL, data=encrypted, headers=headers,
                         timeout=30, verify=False)
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}")

        raw = r.content
        for buf in (aes_decrypt(raw), raw[64:] if len(raw) > 64 else b"", raw):
            if not buf:
                continue
            try:
                parsed = parse_proto(buf)
            except Exception:
                continue
            jwt = parsed.get(8)
            if isinstance(jwt, bytes):
                try:
                    jwt = jwt.decode("utf-8", "ignore")
                except Exception:
                    jwt = ""
            if isinstance(jwt, str) and jwt.startswith("eyJ") and jwt.count(".") == 2:
                sixteen = []
                for fnum in sorted(parsed.keys()):
                    v = parsed[fnum]
                    vals = v if isinstance(v, list) else [v]
                    for val in vals:
                        if isinstance(val, (bytes, bytearray)) and len(val) == 16:
                            sixteen.append(bytes(val))
                        elif isinstance(val, str) and len(val) == 32:
                            try:
                                sixteen.append(bytes.fromhex(val))
                            except Exception:
                                pass
                k = sixteen[-2] if len(sixteen) >= 2 else AES_KEY
                i_ = sixteen[-1] if len(sixteen) >= 2 else AES_IV

                api = parsed.get(10, "N/A")
                if isinstance(api, bytes):
                    try: api = api.decode("utf-8", "ignore")
                    except Exception: api = "N/A"
                region = parsed.get(2, "N/A")
                if isinstance(region, bytes):
                    try: region = region.decode("utf-8", "ignore")
                    except Exception: region = "N/A"
                status = parsed.get(5, "live")
                if isinstance(status, bytes):
                    try: status = status.decode("utf-8", "ignore")
                    except Exception: status = "live"
                account_id = parsed.get(1)

                return MajorLoginResult(
                    jwt, k, i_,
                    api=str(api) if api else "N/A",
                    region=str(region) if region else "N/A",
                    status=str(status) if status else "live",
                    account_id=account_id,
                    device_model=model,
                    device_brand=brand,
                    raw_parsed=parsed
                )
        raise RuntimeError("no JWT")

app = Flask(__name__)

# Backward-compatible helper functions
def encrypt_message(key, iv, plaintext):
    """
    Encrypt a plaintext message using AES in CBC mode with PKCS#7 padding.
    """
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(plaintext, AES.block_size)
    return cipher.encrypt(padded_message)

def parse_response(response_content):
    """
    Parse a string response that uses key: value pairs separated by newlines.
    """
    response_dict = {}
    lines = str(response_content).split("\n")
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            response_dict[key.strip()] = value.strip().strip('"')
    return response_dict

def get_token(password=None, uid=None, session=None):
    """
    Obtain an OAuth token by posting the provided uid and password to the token endpoint.
    Supports get_token(password, uid), get_token(session, uid, password), or keyword args.
    """
    if isinstance(password, requests.Session):
        s = password
        password = session
    else:
        s = session or requests.Session()
    s.verify = False

    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": "GarenaMSDK/4.0.30",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive"
    }
    data = {
        "uid": str(uid),
        "password": str(password),
        "response_type": "token",
        "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"
    }
    try:
        response = s.post(url, headers=headers, data=data, timeout=30)
        if response.status_code != 200:
            return None
        return response.json()
    except Exception:
        return None

def process_major_login(access_token, open_id, platform="4", session=None,
                        device_model=None, device_brand=None, random_select=True):
    """
    Execute MajorLogin using a randomly selected authentic Android device profile from devices.py.
    """
    if session is None:
        session = requests.Session()
        session.verify = False

    device = get_device_for_identifier(
        identifier=open_id,
        model_preference=device_model,
        brand_preference=device_brand,
        random_select=random_select
    )

    try:
        login_res = send_major_login(session, access_token, open_id, platform=platform, device=device)
        return {
            "token": login_res.jwt,
            "api": login_res.api,
            "region": login_res.region,
            "status": login_res.status,
            "account_id": login_res.account_id,
            "device_model": getattr(login_res, "device_model", device.get("model")),
            "device_brand": getattr(login_res, "device_brand", device.get("brand")),
            "session_key": login_res.session_key.hex() if isinstance(login_res.session_key, (bytes, bytearray)) else str(login_res.session_key),
            "session_iv": login_res.session_iv.hex() if isinstance(login_res.session_iv, (bytes, bytearray)) else str(login_res.session_iv),
        }
    except Exception as e:
        return {"error": f"MajorLogin failed: {e}"}

def process_token(uid, password, platform="4", device_model=None, device_brand=None, random_select=True):
    """
    Get OAuth token data and execute MajorLogin with a randomly selected real device.
    """
    session = requests.Session()
    session.verify = False

    token_data = get_token(password=password, uid=uid, session=session)
    if not token_data:
        return {"error": "Failed to retrieve token from OAuth endpoint"}

    access_token = token_data.get('access_token')
    open_id = token_data.get('open_id')

    if not access_token or not open_id:
        return {"error": "OAuth response missing access_token or open_id"}

    return process_major_login(
        access_token,
        open_id,
        platform=platform,
        session=session,
        device_model=device_model,
        device_brand=device_brand,
        random_select=random_select
    )

def _handle_login_request():
    """
    Internal handler for /token and /majorlogin endpoints.
    Accepts parameters from query string, JSON body, or form data.
    Supports:
      - (uid, password) OR (access_token, open_id)
      - Devices randomly selected by default from 56+ pool
      - Optional '?model=Pixel+8+Pro' or '?brand=Samsung' override
    """
    json_data = request.get_json(silent=True) or {}
    
    uid = request.args.get('uid') or json_data.get('uid') or request.form.get('uid')
    password = request.args.get('password') or json_data.get('password') or request.form.get('password')
    access_token = request.args.get('access_token') or json_data.get('access_token') or request.form.get('access_token')
    open_id = request.args.get('open_id') or json_data.get('open_id') or request.form.get('open_id')
    platform = request.args.get('platform') or json_data.get('platform') or request.form.get('platform') or "4"
    
    device_model = (request.args.get('device_model') or request.args.get('model') or request.args.get('device') or 
                    json_data.get('device_model') or json_data.get('model') or json_data.get('device') or 
                    request.form.get('device_model') or request.form.get('model'))
    device_brand = (request.args.get('device_brand') or request.args.get('brand') or 
                    json_data.get('device_brand') or json_data.get('brand') or 
                    request.form.get('device_brand') or request.form.get('brand'))
    
    # Random selection by default
    bind_param = (request.args.get('bind') or json_data.get('bind') or request.form.get('bind') or 
                  request.args.get('deterministic') or json_data.get('deterministic'))
    random_select = not (str(bind_param).lower() in ("true", "1", "yes"))

    if access_token and open_id:
        result = process_major_login(
            access_token,
            open_id,
            platform=platform,
            device_model=device_model,
            device_brand=device_brand,
            random_select=random_select
        )
    elif uid and password:
        result = process_token(
            uid,
            password,
            platform=platform,
            device_model=device_model,
            device_brand=device_brand,
            random_select=random_select
        )
    else:
        return jsonify({
            "error": "Missing parameters: either (uid and password) or (access_token and open_id) are required",
            "example_usage": "/usage"
        }), 400

    if "error" in result:
        return jsonify(result), 500

    # Ensure "token" appears first in the JSON response
    ordered_result = {
        "token": result.get("token"),
        "api": result.get("api", "N/A"),
        "region": result.get("region", "N/A"),
        "status": result.get("status", "live"),
        "credit": "RGK TEAM X BT4 TEAM"
    }

    if result.get("device_model") is not None:
        ordered_result["device_model"] = result.get("device_model")
    if result.get("device_brand") is not None:
        ordered_result["device_brand"] = result.get("device_brand")
    if result.get("account_id") is not None:
        ordered_result["account_id"] = result.get("account_id")
    if result.get("session_key") is not None:
        ordered_result["session_key"] = result.get("session_key")
    if result.get("session_iv") is not None:
        ordered_result["session_iv"] = result.get("session_iv")

    response = make_response(jsonify(ordered_result))
    response.headers["Content-Type"] = "application/json"
    return response

@app.route('/', methods=['GET'])
@app.route('/usage', methods=['GET'])
@app.route('/example', methods=['GET'])
def api_usage():
    """
    Returns API documentation and comprehensive examples of usage.
    """
    host = request.host_url.rstrip('/')
    brands = sorted(list(set(d["brand"] for d in REAL_ANDROID_DEVICES)))
    
    return jsonify({
        "service": "Free Fire JWT & MajorLogin API",
        "version": "OB55 (2.133.9)",
        "status": "online",
        "devices": {
            "total_available": len(REAL_ANDROID_DEVICES),
            "selection_mode": "Randomly selected on every request across 56+ authentic real Android devices",
            "supported_brands": brands,
        },
        "endpoints": {
            "/token": {
                "methods": ["GET", "POST"],
                "description": "Full flow: requests OAuth token using uid & password, then executes MajorLogin with a randomly selected real device.",
                "parameters": {
                    "uid": "Garena guest account UID (required if access_token not provided)",
                    "password": "Password hash (required if access_token not provided)",
                    "access_token": "Direct OAuth token (optional, skips OAuth request)",
                    "open_id": "Direct OAuth open ID (optional, skips OAuth request)",
                    "model": "Specific device model to force, e.g. 'SM-S928B' or 'Pixel 8 Pro' (optional)",
                    "brand": "Filter random selection to brand, e.g. 'Samsung' or 'OnePlus' (optional)"
                },
                "example_get": f"{host}/token?uid=8305343157&password=A00CBC5E3626F3A7C21B72FB7032C069071CBC6D9E8B2E8CA51381FF5822FB4A",
                "example_post": {
                    "url": f"{host}/token",
                    "headers": {"Content-Type": "application/json"},
                    "json": {
                        "uid": "8305343157",
                        "password": "A00CBC5E3626F3A7C21B72FB7032C069071CBC6D9E8B2E8CA51381FF5822FB4A"
                    }
                }
            },
            "/majorlogin": {
                "methods": ["GET", "POST"],
                "description": "Direct MajorLogin endpoint: takes access_token & open_id and runs MajorLogin with a randomly selected device.",
                "example_get": f"{host}/majorlogin?access_token=YOUR_ACCESS_TOKEN&open_id=YOUR_OPEN_ID",
                "example_with_random_brand": f"{host}/majorlogin?access_token=YOUR_ACCESS_TOKEN&open_id=YOUR_OPEN_ID&brand=OnePlus",
                "example_with_specific_model": f"{host}/majorlogin?access_token=YOUR_ACCESS_TOKEN&open_id=YOUR_OPEN_ID&model=SM-S928B"
            },
            "/devices": {
                "methods": ["GET"],
                "description": "Inspect all 56 authentic real Android device profiles available in the pool.",
                "example_all": f"{host}/devices",
                "example_by_brand": f"{host}/devices?brand=Samsung",
                "example_by_model": f"{host}/devices?model=Pixel+8+Pro"
            }
        },
        "curl_examples": [
            f"curl -s '{host}/token?uid=8305343157&password=A00CBC5E3626F3A7C21B72FB7032C069071CBC6D9E8B2E8CA51381FF5822FB4A'",
            f"curl -s -X POST '{host}/token' -H 'Content-Type: application/json' -d '{{\"uid\":\"8305343157\",\"password\":\"A00CBC5E3626F3A7C21B72FB7032C069071CBC6D9E8B2E8CA51381FF5822FB4A\"}}'",
            f"curl -s '{host}/majorlogin?access_token=AT&open_id=OI'",
            f"curl -s '{host}/majorlogin?access_token=AT&open_id=OI&model=SM-S928B'",
            f"curl -s '{host}/majorlogin?access_token=AT&open_id=OI&brand=Xiaomi'",
            f"curl -s '{host}/devices?brand=Samsung'"
        ],
        "python_requests_example": (
            "import requests\n\n"
            "# 1. Random real device login\n"
            f"res = requests.get('{host}/token', params={{\n"
            "    'uid': '8305343157',\n"
            "    'password': 'A00CBC5E3626F3A7C21B72FB7032C069071CBC6D9E8B2E8CA51381FF5822FB4A'\n"
            "}})\n"
            "data = res.json()\n"
            "print('JWT:', data.get('token'))\n"
            "print('Device Selected:', data.get('device_brand'), data.get('device_model'))\n"
        )
    })

@app.route('/token', methods=['GET', 'POST'])
def get_token_response():
    """
    Endpoint to process requests to retrieve a token via MajorLogin.
    Accepts 'uid' and 'password' or direct 'access_token' and 'open_id'.
    Randomly selects from 56+ real devices by default.
    Allows optional device selection via '?model=SM-S928B' or '?brand=Samsung'.
    """
    return _handle_login_request()

@app.route('/majorlogin', methods=['GET', 'POST'])
def major_login_response():
    """
    Direct MajorLogin endpoint.
    Accepts 'access_token' and 'open_id' or 'uid' and 'password'.
    Randomly selects from 56+ real devices by default.
    Allows optional device selection via '?model=Pixel+8+Pro' or '?brand=Xiaomi'.
    """
    return _handle_login_request()

@app.route('/devices', methods=['GET'])
def list_devices():
    """
    Endpoint to inspect the 55+ authentic real Android device profiles.
    Optional query parameters:
      - ?brand=Samsung  (filter by brand)
      - ?model=Pixel    (search by model / marketing name)
    """
    brand = request.args.get('brand')
    model = request.args.get('model')

    if model:
        dev = get_device_by_model(model)
        if dev:
            return jsonify({"total": 1, "device": dev})
        return jsonify({"error": f"Device model '{model}' not found"}), 404

    if brand:
        brand_devs = get_devices_by_brand(brand)
        return jsonify({
            "brand": brand,
            "total": len(brand_devs),
            "devices": brand_devs
        })

    brands = sorted(list(set(d["brand"] for d in REAL_ANDROID_DEVICES)))
    return jsonify({
        "total_devices": len(REAL_ANDROID_DEVICES),
        "brands": brands,
        "devices": REAL_ANDROID_DEVICES
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"\n{'='*60}")
    print(f" Free Fire MajorLogin API (OB55 / 2.133.9)")
    print(f" Loaded {len(REAL_ANDROID_DEVICES)} authentic real devices with random selection")
    print(f" Documentation & Examples: http://0.0.0.0:{port}/usage")
    print(f" Device catalog          : http://0.0.0.0:{port}/devices")
    print(f"{'='*60}\n")
    app.run(host="0.0.0.0", port=port)
