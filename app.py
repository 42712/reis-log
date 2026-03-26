"""
Reis Log — LeitorRota (Python/Flask)
Servidor com API JSON e interface PWA
"""

import json
import re
import base64
import os
import requests
from flask import Flask, jsonify, request, send_from_directory

# ==================================================
# CONFIGURAÇÃO
# ==================================================
GEMINI_API_KEY = "AIzaSyAVnKMUIZ6iHmY_Et74GtevTQOCcmmdcPo"
MASTER_PASS = "rota202601"
PORT = 5000
HOST = "0.0.0.0"

# ==================================================
# BANCO DE CEPs (carrega em memória - resposta imediata)
# ==================================================
CEP_DB_PATH = os.path.join(os.path.dirname(__file__), "cep_rota.json")

def load_cep_db():
    with open(CEP_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cep_db(db: dict):
    with open(CEP_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, separators=(",", ":"))

CEP_DB = load_cep_db()
print(f"✅ Base carregada: {len(CEP_DB):,} CEPs")

# ==================================================
# HELPERS CEP
# ==================================================
def normalize_cep(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if len(digits) >= 8:
        return f"{digits[:5]}-{digits[5:8]}"
    return raw.strip()

def lookup_cep(raw: str) -> dict | None:
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 8:
        return None
    cep = f"{digits[:5]}-{digits[5:8]}"
    if cep in CEP_DB:
        return {"cep": cep, "rota": CEP_DB[cep]}
    for k, v in CEP_DB.items():
        if k.replace("-", "") == digits[:8]:
            return {"cep": k, "rota": v}
    return None

def extract_ceps_from_text(text: str) -> list[str]:
    if not text:
        return []
    fixed = (text
        .replace("O", "0").replace("o", "0")
        .replace("l", "1").replace("I", "1").replace("|", "1")
        .replace("S", "5").replace("B", "8")
        .replace("Z", "2").replace("G", "6"))
    candidates = set()
    for m in re.finditer(r"\b(\d{5})[-\s](\d{3})\b", fixed):
        candidates.add(f"{m.group(1)}-{m.group(2)}")
    for m in re.finditer(r"\b(\d{8})\b", fixed):
        d = m.group(1)
        candidates.add(f"{d[:5]}-{d[5:]}")
    for m in re.finditer(r"(\d{5})[^\d\n]{0,2}(\d{3})", fixed):
        candidates.add(f"{m.group(1)}-{m.group(2)}")
    return [c for c in candidates if re.match(r"^\d{5}-\d{3}$", c)]

def is_valid_cep(cep: str) -> bool:
    if not re.match(r"^\d{5}-\d{3}$", cep):
        return False
    digits = cep.replace("-", "")
    if len(set(digits)) == 1:
        return False
    num = int(digits)
    return 1_000_000 <= num <= 99_999_999

# ==================================================
# GEMINI OCR
# ==================================================
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.0-flash-lite:generateContent"
)

def gemini_ocr(image_base64: str) -> str | None:
    if not GEMINI_API_KEY or "COLE_SUA" in GEMINI_API_KEY:
        return None
    try:
        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": (
                            "Leia o CEP brasileiro nesta imagem. "
                            "O CEP tem 8 dígitos (ex: 74080-010 ou 74080010). "
                            "Pode estar impresso, escrito à mão com caneta ou pincel, "
                            "ou em tela de computador. "
                            "Responda SOMENTE com os 8 dígitos no formato NNNNN-NNN. "
                            "Se não houver CEP, responda NONE."
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "maxOutputTokens": 12,
                "temperature": 0
            }
        }
        resp = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=8
        )
        if not resp.ok:
            return None
        data = resp.json()
        text = (data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                    .strip())
        return None if not text or text == "NONE" else text
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

# ==================================================
# FLASK APP
# ==================================================
app = Flask(__name__, static_folder="static")

# ── Rotas para servir os arquivos estáticos ─────────
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

# ==================================================
# API — BUSCA DE CEP
# ==================================================
@app.route("/api/cep/<cep>")
def api_cep(cep: str):
    result = lookup_cep(cep)
    if result:
        return jsonify({"found": True, **result})
    norm = normalize_cep(cep)
    return jsonify({"found": False, "cep": norm, "rota": None}), 404

@app.route("/api/cep", methods=["POST"])
def api_cep_post():
    data = request.get_json(silent=True) or {}
    cep = data.get("cep", "")
    result = lookup_cep(cep)
    if result:
        return jsonify({"found": True, **result})
    return jsonify({"found": False, "cep": normalize_cep(cep), "rota": None}), 404

# ==================================================
# API — OCR VIA CÂMERA
# ==================================================
@app.route("/api/ocr", methods=["POST"])
def api_ocr():
    data = request.get_json(silent=True) or {}
    image_b64 = data.get("image", "")
    if not image_b64:
        return jsonify({"error": "Imagem não enviada"}), 400
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]
    raw_text = gemini_ocr(image_b64)
    candidates = []
    if raw_text:
        candidates = extract_ceps_from_text(raw_text)
        candidates = [c for c in candidates if is_valid_cep(c)]
    in_db = [c for c in candidates if lookup_cep(c)]
    hit = in_db[0] if in_db else (candidates[0] if candidates else None)
    if hit:
        result = lookup_cep(hit)
        if result:
            return jsonify({
                "found": True,
                "cep": result["cep"],
                "rota": result["rota"],
                "raw_text": raw_text,
                "candidates": candidates
            })
    return jsonify({
        "found": False,
        "cep": hit,
        "rota": None,
        "raw_text": raw_text,
        "candidates": candidates
    }), 404 if not hit else 200

# ==================================================
# API — ADMIN
# ==================================================
def check_auth() -> bool:
    return (
        request.headers.get("X-Master-Pass") == MASTER_PASS or
        (request.get_json(silent=True) or {}).get("password") == MASTER_PASS
    )

@app.route("/api/admin/stats")
def api_stats():
    if not check_auth():
        return jsonify({"error": "Não autorizado"}), 401
    rotas = set(CEP_DB.values())
    return jsonify({
        "total_ceps": len(CEP_DB),
        "total_rotas": len(rotas),
        "rotas": sorted(rotas)
    })

@app.route("/api/admin/add", methods=["POST"])
def api_add_cep():
    if not check_auth():
        return jsonify({"error": "Não autorizado"}), 401
    data = request.get_json(silent=True) or {}
    cep = normalize_cep(data.get("cep", ""))
    rota = str(data.get("rota", "")).strip()
    if not re.match(r"^\d{5}-\d{3}$", cep):
        return jsonify({"error": "CEP inválido"}), 400
    if not rota:
        return jsonify({"error": "Rota inválida"}), 400
    CEP_DB[cep] = rota
    save_cep_db(CEP_DB)
    return jsonify({"ok": True, "cep": cep, "rota": rota, "total": len(CEP_DB)})

@app.route("/api/admin/import", methods=["POST"])
def api_import():
    if not check_auth():
        return jsonify({"error": "Não autorizado"}), 401
    data = request.get_json(silent=True) or {}
    records = data.get("data", [])
    added = 0
    for rec in records:
        cep = normalize_cep(str(rec.get("cep", "")))
        rota = str(rec.get("rota", "")).strip()
        if re.match(r"^\d{5}-\d{3}$", cep) and rota:
            CEP_DB[cep] = rota
            added += 1
    if added:
        save_cep_db(CEP_DB)
    return jsonify({"ok": True, "added": added, "total": len(CEP_DB)})

@app.route("/api/admin/export")
def api_export():
    if not check_auth():
        return jsonify({"error": "Não autorizado"}), 401
    return jsonify(CEP_DB)

@app.route("/api/admin/delete", methods=["POST"])
def api_delete_cep():
    if not check_auth():
        return jsonify({"error": "Não autorizado"}), 401
    data = request.get_json(silent=True) or {}
    cep = normalize_cep(data.get("cep", ""))
    if cep not in CEP_DB:
        return jsonify({"error": "CEP não encontrado"}), 404
    del CEP_DB[cep]
    save_cep_db(CEP_DB)
    return jsonify({"ok": True, "deleted": cep, "total": len(CEP_DB)})

# ==================================================
# INICIALIZAÇÃO
# ==================================================
if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════╗
║  🚚 Reis Log — LeitorRota Python     ║
║  Base: {len(CEP_DB):,} CEPs carregados         ║
║  Interface: http://localhost:{PORT}    ║
║  API: http://localhost:{PORT}/api      ║
╚══════════════════════════════════════╝
""")
    app.run(host=HOST, port=PORT, debug=False)
