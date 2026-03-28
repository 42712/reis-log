"""
Reis Log — LeitorRota Python/Flask
OCR com Gemini Vision (principal) + Tesseract melhorado (fallback)
"""

import json, re, base64, os, time, requests
from flask import Flask, jsonify, request, send_from_directory

# ==================================================
# ⚙️  CONFIGURAÇÃO — troque a chave se necessário
# ==================================================
GEMINI_API_KEY = "AIzaSyAVnKMUIZ6iHmY_Et74GtevTQOCcmmdcPo"   # ← substitua se revogada
MASTER_PASS    = "rota202601"
PORT           = 5000
HOST           = "0.0.0.0"

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash-lite:generateContent?key=" + GEMINI_API_KEY
)

# ==================================================
# 📦  BANCO DE CEPs — carregado em memória (O(1))
# ==================================================
DB_PATH = os.path.join(os.path.dirname(__file__), "cep_rota.json")

def _load():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, separators=(",", ":"))

CEP_DB = _load()
print(f"✅ Base carregada: {len(CEP_DB):,} CEPs")

# Cache duplo: com hífen e sem hífen
CEP_CACHE: dict = {}
for _cep, _rota in CEP_DB.items():
    _clean = _cep.replace("-", "")
    CEP_CACHE[_clean]  = {"cep": _cep, "rota": _rota}
    CEP_CACHE[_cep]    = {"cep": _cep, "rota": _rota}

def _lookup(raw: str):
    clean = re.sub(r"\D", "", raw)
    if len(clean) < 8:
        return None
    result = CEP_CACHE.get(clean)
    if result:
        return result
    fmt = f"{clean[:5]}-{clean[5:8]}"
    return CEP_CACHE.get(fmt)

def _add_to_cache(cep_fmt: str, rota: str):
    clean = cep_fmt.replace("-", "")
    CEP_CACHE[clean]   = {"cep": cep_fmt, "rota": rota}
    CEP_CACHE[cep_fmt] = {"cep": cep_fmt, "rota": rota}

# ==================================================
# 🔍  OCR — Gemini Vision
# ==================================================
_PROMPT = (
    "Esta imagem contém um CEP brasileiro (formato NNNNN-NNN ou NNNNNNNN). "
    "Pode estar impresso, manuscrito a caneta ou em etiqueta. "
    "Extraia SOMENTE os 8 dígitos do CEP, sem texto extra, sem hífen, sem espaços. "
    "Se não houver CEP visível, responda exatamente: NENHUM"
)

# Correções OCR comuns: letras confundíveis → dígitos
_OCR_FIX = str.maketrans({
    'O': '0', 'o': '0',
    'I': '1', 'l': '1', 'i': '1',
    'Z': '2', 'z': '2',
    'S': '5', 's': '5',
    'G': '6', 'g': '6',
    'B': '8',
    'q': '9',
})

def _fix_digits(text: str) -> str:
    return text.translate(_OCR_FIX)

def _extract_digits(text: str):
    """Extrai 8 dígitos do texto OCR aplicando correções de letras."""
    fixed  = _fix_digits(re.sub(r"[^0-9OoIilZzSsGgBbq]", "", text))
    digits = re.sub(r"\D", "", fixed)
    if len(digits) >= 8:
        return digits[:8]
    # Tenta padrão NNNNN[-]NNN no texto original
    m = re.search(r"(\d{5})[-\s]?(\d{3})", text)
    if m:
        return m.group(1) + m.group(2)
    return None

def ocr_gemini(image_b64: str):
    """Gemini Vision: retorna 8 dígitos ou None."""
    if not GEMINI_API_KEY or "COLE_SUA" in GEMINI_API_KEY:
        return None
    try:
        payload = {
            "contents": [{
                "parts": [
                    {"text": _PROMPT},
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}}
                ]
            }],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 32}
        }
        resp = requests.post(GEMINI_URL, json=payload, timeout=8)
        if resp.status_code != 200:
            print(f"  Gemini HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        raw  = resp.json()
        text = raw["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"  Gemini raw: {repr(text)}")
        if "NENHUM" in text.upper():
            return None
        return _extract_digits(text)
    except Exception as e:
        print(f"  Gemini erro: {e}")
        return None

def ocr_tesseract(image_b64: str):
    """Tesseract com vários pré-processamentos como fallback."""
    try:
        import cv2, numpy as np, pytesseract
    except ImportError:
        print("  Tesseract/OpenCV não instalados — pulando fallback")
        return None
    try:
        arr = np.frombuffer(base64.b64decode(image_b64), np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        if w < 900:
            scale = 900 / w
            gray  = cv2.resize(gray, (int(w * scale), int(h * scale)),
                               interpolation=cv2.INTER_CUBIC)

        versions = [
            # CLAHE
            cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray),
            # threshold adaptativo
            cv2.adaptiveThreshold(gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8),
            # Otsu
            cv2.threshold(gray, 0, 255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        ]

        cfgs = [
            r"--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789-",
            r"--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789-",
        ]
        for ver in versions:
            for cfg in cfgs:
                text   = pytesseract.image_to_string(ver, config=cfg, lang="por")
                digits = _extract_digits(text)
                if digits:
                    print(f"  Tesseract achou: {digits}")
                    return digits
        return None
    except Exception as e:
        print(f"  Tesseract erro: {e}")
        return None

def ocr_pipeline(image_b64: str):
    """1. Gemini Vision  2. Tesseract. Retorna 8 dígitos ou None."""
    t0 = time.time()
    d  = ocr_gemini(image_b64)
    if d:
        print(f"OCR Gemini OK {(time.time()-t0)*1000:.0f}ms → {d}")
        return d
    d = ocr_tesseract(image_b64)
    if d:
        print(f"OCR Tesseract OK {(time.time()-t0)*1000:.0f}ms → {d}")
        return d
    print(f"OCR falhou {(time.time()-t0)*1000:.0f}ms")
    return None

# ==================================================
# 🌐  FLASK
# ==================================================
app = Flask(__name__, static_folder="static")

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")

@app.route("/icon.svg")
def icon():
    return send_from_directory("static", "icon.svg")

@app.route("/sw.js")
def sw():
    return send_from_directory(".", "sw.js")

# ── Busca CEP ─────────────────────────────────────
@app.route("/api/cep/<path:cep>")
def api_cep_get(cep: str):
    r = _lookup(cep)
    if r:
        return jsonify({"found": True, **r})
    return jsonify({"found": False, "cep": cep}), 404

@app.route("/api/cep", methods=["POST"])
def api_cep_post():
    r = _lookup((request.get_json(silent=True) or {}).get("cep", ""))
    if r:
        return jsonify({"found": True, **r})
    return jsonify({"found": False}), 404

# ── OCR ───────────────────────────────────────────
@app.route("/api/ocr", methods=["POST"])
def api_ocr():
    data = request.get_json(silent=True) or {}
    b64  = data.get("image", "")
    if not b64:
        return jsonify({"error": "Imagem não enviada"}), 400

    if "," in b64:
        b64 = b64.split(",", 1)[1]

    try:
        digits = ocr_pipeline(b64)
        if not digits:
            return jsonify({"found": False, "cep": None,
                            "message": "CEP não identificado — tente nova foto"}), 404

        cep_fmt = f"{digits[:5]}-{digits[5:8]}"
        r       = _lookup(digits)
        if r:
            return jsonify({"found": True, "cep": r["cep"], "rota": r["rota"]})
        return jsonify({"found": False, "cep": cep_fmt, "rota": None,
                        "message": "CEP lido mas não consta na base"}), 404

    except Exception as e:
        print(f"Erro /api/ocr: {e}")
        return jsonify({"error": str(e)}), 500

# ── Admin ─────────────────────────────────────────
def _auth():
    body = request.get_json(silent=True) or {}
    return (request.headers.get("X-Master-Pass") == MASTER_PASS or
            body.get("password") == MASTER_PASS)

@app.route("/api/admin/stats")
def api_stats():
    if not _auth(): return jsonify({"error": "Não autorizado"}), 401
    return jsonify({
        "total_ceps":  len(CEP_DB),
        "total_rotas": len(set(CEP_DB.values())),
        "rotas":       sorted(set(CEP_DB.values()))
    })

@app.route("/api/admin/add", methods=["POST"])
def api_add():
    if not _auth(): return jsonify({"error": "Não autorizado"}), 401
    data = request.get_json(silent=True) or {}
    d    = re.sub(r"\D", "", data.get("cep", ""))
    rota = str(data.get("rota", "")).strip()
    if len(d) != 8 or not rota:
        return jsonify({"error": "CEP ou rota inválidos"}), 400
    fmt = f"{d[:5]}-{d[5:8]}"
    CEP_DB[fmt] = rota
    _add_to_cache(fmt, rota)
    _save(CEP_DB)
    return jsonify({"ok": True, "cep": fmt, "rota": rota, "total": len(CEP_DB)})

@app.route("/api/admin/import", methods=["POST"])
def api_import():
    if not _auth(): return jsonify({"error": "Não autorizado"}), 401
    records = (request.get_json(silent=True) or {}).get("data", [])
    added = 0
    for rec in records:
        d    = re.sub(r"\D", "", str(rec.get("cep", "")))
        rota = str(rec.get("rota", "")).strip()
        if len(d) == 8 and rota:
            fmt = f"{d[:5]}-{d[5:8]}"
            CEP_DB[fmt] = rota
            _add_to_cache(fmt, rota)
            added += 1
    if added: _save(CEP_DB)
    return jsonify({"ok": True, "added": added, "total": len(CEP_DB)})

@app.route("/api/admin/export")
def api_export():
    if not _auth(): return jsonify({"error": "Não autorizado"}), 401
    return jsonify(CEP_DB)

@app.route("/api/admin/delete", methods=["POST"])
def api_delete():
    if not _auth(): return jsonify({"error": "Não autorizado"}), 401
    d = re.sub(r"\D", "", (request.get_json(silent=True) or {}).get("cep", ""))
    if len(d) != 8: return jsonify({"error": "CEP inválido"}), 400
    fmt = f"{d[:5]}-{d[5:8]}"
    if fmt not in CEP_DB: return jsonify({"error": "CEP não encontrado"}), 404
    del CEP_DB[fmt]
    CEP_CACHE.pop(d,   None)
    CEP_CACHE.pop(fmt, None)
    _save(CEP_DB)
    return jsonify({"ok": True, "deleted": fmt, "total": len(CEP_DB)})

# ==================================================
# 🚀  MAIN
# ==================================================
if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════╗
║  🚚 Reis Log — LeitorRota PRO                        ║
║                                                      ║
║  ✅ {len(CEP_DB):,} CEPs em cache (busca instantânea)       ║
║  ✅ OCR: Gemini Vision + fallback Tesseract          ║
║                                                      ║
║  Interface: http://localhost:{PORT}                  ║
╚══════════════════════════════════════════════════════╝
""")
    app.run(host=HOST, port=PORT, debug=False, threaded=True)
