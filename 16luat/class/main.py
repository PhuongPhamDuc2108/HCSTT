# main.py
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from fpg import FPG
from rpg import RPG
from inference import forward_inference_detailed
from backward_inference import backward_inference_detailed, backward_inference_with_trace

app = Flask(__name__)
CORS(app)

# === CẤU HÌNH DỮ LIỆU ===
DATA_FOLDER = 'data'
DATA_FILE = os.path.join(DATA_FOLDER, 'rules.json')

def ensure_data_exists():
    """Đảm bảo folder data và file rules.json tồn tại"""
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

def load_rules_from_file():
    """Đọc luật từ file JSON"""
    ensure_data_exists()
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_rules_to_file(rules):
    """Lưu luật vào file JSON"""
    ensure_data_exists()
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False, indent=4)

# === API QUẢN LÝ DATA ===

@app.route('/rules', methods=['GET'])
def get_rules():
    """Lấy danh sách luật hiện có"""
    rules = load_rules_from_file()
    return jsonify(rules)

@app.route('/rules/upload', methods=['POST'])
def upload_rules():
    """Nhận danh sách luật từ file Excel (đã parse ở client) và lưu đè"""
    try:
        new_rules = request.json.get('rules', [])
        save_rules_to_file(new_rules)
        return jsonify({'success': True, 'message': f'Đã lưu {len(new_rules)} luật vào hệ thống.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/rules/add', methods=['POST'])
def add_rule():
    """Thêm một luật mới"""
    try:
        rule = request.json.get('rule')
        if not rule:
            return jsonify({'error': 'Thiếu dữ liệu luật'}), 400
        
        rules = load_rules_from_file()
        # Kiểm tra ID trùng
        if any(r['id'] == rule['id'] for r in rules):
             # Nếu trùng ID thì tự tăng ID lên
            try:
                max_id = max([int(r['id']) for r in rules if str(r['id']).isdigit()] or [0])
                rule['id'] = str(max_id + 1)
            except:
                rule['id'] = str(len(rules) + 1)

        rules.append(rule)
        save_rules_to_file(rules)
        return jsonify({'success': True, 'rules': rules})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/rules/update', methods=['POST'])
def update_rule():
    """Cập nhật luật"""
    try:
        updated_rule = request.json.get('rule')
        if not updated_rule:
            return jsonify({'error': 'Thiếu dữ liệu'}), 400
        
        rules = load_rules_from_file()
        found = False
        for i, r in enumerate(rules):
            if r['id'] == updated_rule['id']:
                rules[i] = updated_rule
                found = True
                break
        
        if found:
            save_rules_to_file(rules)
            return jsonify({'success': True, 'rules': rules})
        else:
            return jsonify({'success': False, 'error': 'Không tìm thấy ID luật'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/rules/delete', methods=['POST'])
def delete_rule():
    """Xóa luật"""
    try:
        rule_id = request.json.get('id')
        rules = load_rules_from_file()
        new_rules = [r for r in rules if r['id'] != rule_id]
        
        if len(new_rules) < len(rules):
            save_rules_to_file(new_rules)
            return jsonify({'success': True, 'rules': new_rules})
        else:
            return jsonify({'success': False, 'error': 'Không tìm thấy ID để xóa'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# === CÁC API CŨ (LOGIC SUY DIỄN) GIỮ NGUYÊN ===
# (FPG, RPG, Inference endpoints...)

@app.route('/generate_fpg', methods=['POST'])
def generate_fpg():
    try:
        # Nếu client gửi rules thì dùng, không thì load từ file
        data = request.json.get('rules') or load_rules_from_file()
        initial_facts = request.json.get('initial_facts', [])
        target_goals = request.json.get('target_goals', [])
        layout_method = request.json.get('layout_method', 'kamada_kawai')
        
        if not data:
            return jsonify({'error': 'Không có dữ liệu luật'}), 400
        
        fpg = FPG()
        fpg.load_from_data(data)
        fpg.set_initial_and_target(initial_facts, target_goals)
        fpg.build_graph()
        
        image_base64 = fpg.visualize_to_base64(layout_method=layout_method)
        return jsonify({'success': True, 'image': image_base64})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/generate_rpg', methods=['POST'])
def generate_rpg():
    try:
        data = request.json.get('rules') or load_rules_from_file()
        initial_facts = request.json.get('initial_facts', [])
        target_goals = request.json.get('target_goals', [])
        
        if not data:
            return jsonify({'error': 'Không có dữ liệu luật'}), 400
        
        rpg = RPG()
        rpg.load_from_data(data)
        rpg.set_initial_and_target(initial_facts, target_goals)
        rpg.build_graph()
        
        image_base64 = rpg.visualize_to_base64()
        return jsonify({'success': True, 'image': image_base64})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/forward_inference_advanced', methods=['POST'])
def forward_inference_advanced():
    try:
        data = request.json
        rules = data.get('rules') or load_rules_from_file()
        initial_facts = data.get('initial_facts', [])
        goals = data.get('goals', [])
        
        if not rules: return jsonify({'error': 'Chưa có luật trong hệ thống'}), 400
        
        success, process_table, full_vet, optimal_vet, explanation, conclusion = \
            forward_inference_detailed(initial_facts, goals, rules)
        
        return jsonify({
            'success': success, 'process_table': process_table,
            'full_vet': full_vet, 'optimal_vet': optimal_vet,
            'explanation': explanation, 'conclusion': conclusion,
            'initial_facts': initial_facts, 'goals': goals
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/backward_inference_advanced', methods=['POST'])
def backward_inference_advanced():
    try:
        data = request.json
        rules = data.get('rules') or load_rules_from_file()
        initial_facts = data.get('initial_facts', [])
        goals = data.get('goals', [])
        
        if not rules: return jsonify({'error': 'Chưa có luật trong hệ thống'}), 400
        
        success, process_table, full_vet, optimal_vet, explanation, conclusion = \
            backward_inference_detailed(initial_facts, goals, rules)
        
        return jsonify({
            'success': success, 'process_table': process_table,
            'full_vet': full_vet, 'optimal_vet': optimal_vet,
            'explanation': explanation, 'conclusion': conclusion,
            'initial_facts': initial_facts, 'goals': goals
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/backward_inference_trace', methods=['POST'])
def backward_inference_trace():
    try:
        data = request.json
        rules = data.get('rules') or load_rules_from_file()
        initial_facts = data.get('initial_facts', [])
        goals = data.get('goals', [])
        
        if not rules: return jsonify({'error': 'Chưa có luật'}), 400
        
        success, trace, applied_rules = \
            backward_inference_with_trace(initial_facts, goals, rules)
        
        return jsonify({
            'success': success, 'trace': trace,
            'applied_rules': applied_rules
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'storage': 'enabled (data/rules.json)'})

if __name__ == '__main__':
    ensure_data_exists()
    print("=" * 70)
    print("🚀 Flask Server chạy tại: http://localhost:5000")
    print("📂 Dữ liệu được lưu tại: /data/rules.json")
    print("=" * 70)
    app.run(debug=True, host='0.0.0.0', port=5000)