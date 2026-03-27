"""
Reis Log — LeitorRota (Python/Flask)
Servidor otimizado com OCR rápido e base de CEPs em memória
"""

import json
import re
import base64
import os
import io
import time
from flask import Flask, jsonify, request, send_from_directory
from PIL import Image
import pytesseract
import cv2
import numpy as np

# ==================================================
# CONFIGURAÇÃO
# ==================================================
MASTER_PASS = "rota202601"
PORT = 5000
HOST = "0.0.0.0"

# ==================================================
# BANCO DE CEPs (carrega em memória - resposta em milissegundos)
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
# OTIMIZAÇÃO: Cache de CEPs para busca instantânea
# ==================================================
# Cache com lookup sem formatação para busca mais rápida
CEP_CACHE = {}
for cep, rota in CEP_DB.items():
    clean_cep = cep.replace("-", "")
    CEP_CACHE[clean_cep] = {"cep": cep, "rota": rota}
    CEP_CACHE[cep] = {"cep": cep, "rota": rota}

def lookup_cep_instant(raw: str) -> dict | None:
    """Busca CEP no cache - resposta instantânea O(1)"""
    clean = re.sub(r"\D", "", raw)
    if len(clean) < 8:
        return None
    result = CEP_CACHE.get(clean)
    if result:
        return result
    # Tenta com hífen
    formatted = f"{clean[:5]}-{clean[5:8]}"
    result = CEP_CACHE.get(formatted)
    return result

# ==================================================
# OCR OTIMIZADO PARA LEITURA RÁPIDA
# ==================================================

def preprocess_image_for_ocr(image_bytes):
    """Pré-processa a imagem para melhorar a leitura do OCR (manuscrito, impresso)"""
    # Converte bytes para imagem OpenCV
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return None
    
    # Converte para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplica threshold adaptativo para manuscrito
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                    cv2.THRESH_BINARY, 11, 2)
    
    # Aumenta contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Redimensiona para melhorar leitura
    height, width = enhanced.shape
    if width < 800:
        scale = 800 / width
        new_width = int(width * scale)
        new_height = int(height * scale)
        enhanced = cv2.resize(enhanced, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        binary = cv2.resize(binary, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    return enhanced, binary

def ocr_extract_cep(image_bytes):
    """Extrai CEP da imagem usando OCR otimizado"""
    try:
        start_time = time.time()
        
        # Pré-processa a imagem
        enhanced, binary = preprocess_image_for_ocr(image_bytes)
        if enhanced is None:
            return None
        
        # Configuração otimizada do Tesseract
        custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789-'
        
        # Tenta com a imagem melhorada
        text = pytesseract.image_to_string(enhanced, config=custom_config, lang='por')
        
        # Se não achou, tenta com a imagem binarizada
        if not text or len(text.strip()) < 6:
            text = pytesseract.image_to_string(binary, config=custom_config, lang='por')
        
        # Extrai números da string
        digits = re.sub(r'\D', '', text)
        
        # Valida se tem pelo menos 8 dígitos
        if len(digits) >= 8:
            cep = f"{digits[:5]}-{digits[5:8]}"
            # Valida formato
            if re.match(r'^\d{5}-\d{3}$', cep):
                print(f"OCR detectou: {cep} (tempo: {(time.time()-start_time)*1000:.0f}ms)")
                return cep
        
        # Tenta extrair usando regex direto
        cep_pattern = r'\b(\d{5})[-\s]?(\d{3})\b'
        match = re.search(cep_pattern, text)
        if match:
            cep = f"{match.group(1)}-{match.group(2)}"
            print(f"OCR detectou (regex): {cep}")
            return cep
        
        return None
        
    except Exception as e:
        print(f"Erro OCR: {e}")
        return None

# ==================================================
# FLASK APP
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

# ==================================================
# API — BUSCA DE CEP (INSTANTÂNEA)
# ==================================================
@app.route("/api/cep/<cep>")
def api_cep(cep: str):
    """Busca CEP no banco - resposta em milissegundos"""
    result = lookup_cep_instant(cep)
    if result:
        return jsonify({"found": True, **result})
    return jsonify({"found": False, "cep": cep}), 404

@app.route("/api/cep", methods=["POST"])
def api_cep_post():
    data = request.get_json(silent=True) or {}
    cep = data.get("cep", "")
    result = lookup_cep_instant(cep)
    if result:
        return jsonify({"found": True, **result})
    return jsonify({"found": False, "cep": cep}), 404

# ==================================================
# API — OCR COM CÂMERA (OTIMIZADO)
# ==================================================
@app.route("/api/ocr", methods=["POST"])
def api_ocr():
    """
    POST /api/ocr
    Body: { "image": "<base64>" }
    Retorna CEP detectado e rota
    """
    data = request.get_json(silent=True) or {}
    image_b64 = data.get("image", "")
    
    if not image_b64:
        return jsonify({"error": "Imagem não enviada"}), 400
    
    # Remove header se existir
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]
    
    try:
        # Decodifica base64 para bytes
        image_bytes = base64.b64decode(image_b64)
        
        # Extrai CEP usando OCR
        cep = ocr_extract_cep(image_bytes)
        
        if not cep:
            return jsonify({"found": False, "cep": None, "message": "Não foi possível ler o CEP"}), 404
        
        # Busca no banco
        result = lookup_cep_instant(cep)
        
        if result:
            return jsonify({
                "found": True,
                "cep": result["cep"],
                "rota": result["rota"]
            })
        else:
            return jsonify({
                "found": False,
                "cep": cep,
                "rota": None,
                "message": "CEP não encontrado na base"
            }), 404
            
    except Exception as e:
        print(f"Erro no OCR: {e}")
        return jsonify({"error": str(e)}), 500

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
    cep = data.get("cep", "").strip()
    rota = str(data.get("rota", "")).strip()
    
    # Normaliza CEP
    digits = re.sub(r"\D", "", cep)
    if len(digits) != 8:
        return jsonify({"error": "CEP inválido"}), 400
    if not rota:
        return jsonify({"error": "Rota inválida"}), 400
    
    cep_formatado = f"{digits[:5]}-{digits[5:8]}"
    CEP_DB[cep_formatado] = rota
    CEP_CACHE[digits] = {"cep": cep_formatado, "rota": rota}
    CEP_CACHE[cep_formatado] = {"cep": cep_formatado, "rota": rota}
    save_cep_db(CEP_DB)
    return jsonify({"ok": True, "cep": cep_formatado, "rota": rota, "total": len(CEP_DB)})

@app.route("/api/admin/import", methods=["POST"])
def api_import():
    if not check_auth():
        return jsonify({"error": "Não autorizado"}), 401
    data = request.get_json(silent=True) or {}
    records = data.get("data", [])
    added = 0
    for rec in records:
        cep_raw = str(rec.get("cep", ""))
        rota = str(rec.get("rota", "")).strip()
        digits = re.sub(r"\D", "", cep_raw)
        if len(digits) == 8 and rota:
            cep_formatado = f"{digits[:5]}-{digits[5:8]}"
            CEP_DB[cep_formatado] = rota
            CEP_CACHE[digits] = {"cep": cep_formatado, "rota": rota}
            CEP_CACHE[cep_formatado] = {"cep": cep_formatado, "rota": rota}
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
    cep = data.get("cep", "").strip()
    digits = re.sub(r"\D", "", cep)
    if len(digits) != 8:
        return jsonify({"error": "CEP inválido"}), 400
    cep_formatado = f"{digits[:5]}-{digits[5:8]}"
    if cep_formatado not in CEP_DB:
        return jsonify({"error": "CEP não encontrado"}), 404
    del CEP_DB[cep_formatado]
    if digits in CEP_CACHE:
        del CEP_CACHE[digits]
    if cep_formatado in CEP_CACHE:
        del CEP_CACHE[cep_formatado]
    save_cep_db(CEP_DB)
    return jsonify({"ok": True, "deleted": cep_formatado, "total": len(CEP_DB)})

# ==================================================
# INICIALIZAÇÃO
# ==================================================
if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════╗
║  🚚 Reis Log — LeitorRota PRO                        ║
║                                                      ║
║  ✅ Base: {len(CEP_DB):,} CEPs carregados em cache           ║
║  ✅ OCR otimizado para manuscrito e impresso        ║
║  ✅ Resposta em milissegundos                       ║
║                                                      ║
║  Interface: http://localhost:{PORT}                  ║
║  API: http://localhost:{PORT}/api/cep/74080010      ║
╚══════════════════════════════════════════════════════╝
""")
    app.run(host=HOST, port=PORT, debug=False, threaded=True)
