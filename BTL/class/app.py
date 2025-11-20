from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import os
from inference import forward_inference_detailed_rasff

app = Flask(__name__)
CORS(app)

# === CẤU HÌNH QUAN TRỌNG ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# [SỬA TÊN FILE Ở ĐÂY] - Cập nhật đúng tên file bạn vừa gửi
EXCEL_FILE = 'RASFF_Rules_Inference_500_DETAILED_RISKANALYSIS.xlsx'
FILE_PATH = os.path.join(BASE_DIR, EXCEL_FILE)

# Thứ tự bộ lọc (Không bao gồm DISTRIBUTION_STAT)
CASCADING_FIELDS = ['NOT_COUNTRY', 'TYPE', 'PROD_CAT', 'PRODUCT', 'HAZARDS_CAT', 'HAZARDS']

global_rules = []
global_initial_values = {}

def parse_ve_trai(ve_trai_str):
    """Tách chuỗi VE_TRAI thành Dict."""
    data = {}
    if not isinstance(ve_trai_str, str) or not ve_trai_str:
        return data
        
    parts = ve_trai_str.split(',')
    for part in parts:
        if '=' in part:
            key, val = part.split('=', 1)
            key = key.strip().upper()
            val = val.strip()
            if key and val:
                data[key] = val
    return data

def load_data_startup():
    global global_rules, global_initial_values
    print(f"\n⏳ [STARTUP] Đang đọc file: {EXCEL_FILE}...")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ LỖI: Không tìm thấy file '{EXCEL_FILE}'. Hãy chắc chắn file Excel nằm cùng thư mục với app.py")
        # Thử tìm file csv nếu không thấy xlsx (phòng trường hợp bạn dùng csv)
        if os.path.exists(FILE_PATH.replace('.xlsx', '.csv')):
            print("⚠️ Tìm thấy file CSV, hãy đổi tên config hoặc convert sang Excel.")
        return

    try:
        # 1. Đọc file Excel
        df = pd.read_excel(FILE_PATH, engine='openpyxl')
        
        # --- XỬ LÝ TÊN CỘT ---
        # Chuẩn hóa hết về chữ in hoa để tránh lỗi (Risk_Percentage -> RISK_PERCENTAGE)
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.fillna('')
        
        print(f"✅ Các cột tìm thấy trong file: {df.columns.tolist()}")
        
        # Kiểm tra xem cột RISK có tồn tại không
        if 'RISK_PERCENTAGE' not in df.columns:
            print("⚠️ CẢNH BÁO: Không tìm thấy cột 'RISK_PERCENTAGE'. Kiểm tra lại file Excel!")

        unique_values = {k: set() for k in CASCADING_FIELDS}
        count = 0

        # 2. Duyệt từng dòng
        for idx, row in df.iterrows():
            ve_phai = str(row.get('VE_PHAI') or row.get('THEN') or '').strip()
            note = str(row.get('NOTE') or 'N/A').strip()
            
            # --- [SỬA LỖI] ĐỌC CỘT RISK ---
            # Thử đọc các biến thể tên cột có thể xảy ra
            risk_val = str(row.get('RISK_PERCENTAGE') or row.get('RISK PERCENTAGE') or row.get('RISK') or '0%').strip()

            if not ve_phai: continue

            # --- Xử lý VE_TRAI ---
            raw_ve_trai = str(row.get('VE_TRAI', '')).strip()
            combined_data = parse_ve_trai(raw_ve_trai)

            # --- Tách DISTRIBUTION_STAT (Key trong Vế Trái) ---
            dist_stat = combined_data.pop('DISTRIBUTION_STAT', 'Chưa có thông tin phân phối')

            # --- Ghi đè dữ liệu cột phụ ---
            product_col = str(row.get('PRODUCT', '')).strip()
            if product_col and product_col.lower() != 'nan':
                combined_data['PRODUCT'] = product_col

            country_col = str(row.get('NOT_COUNTRY', '')).strip()
            if country_col and country_col.lower() != 'nan':
                combined_data['NOT_COUNTRY'] = country_col
            
            # --- Tạo Filter Data ---
            filter_data = {}
            conditions_display = []
            has_valid_data = False

            for field in CASCADING_FIELDS:
                val = combined_data.get(field)
                if val:
                    filter_data[field] = val
                    unique_values[field].add(val)
                    conditions_display.append(f"{field}={val}")
                    has_valid_data = True
            
            if has_valid_data:
                global_rules.append({
                    'id': row.get('ID', idx + 1),
                    'veTrai': ", ".join(conditions_display),
                    'vePhai': ve_phai,
                    'Note': note,
                    'risk': risk_val,          # Giá trị đọc từ cột RISK_PERCENTAGE
                    'distribution': dist_stat, # Giá trị tách từ key DISTRIBUTION_STAT
                    'filter_data': filter_data
                })
                count += 1

        global_initial_values = {k: sorted(list(v)) for k, v in unique_values.items()}
        
        print(f"✅ LOAD THÀNH CÔNG: {count} luật.")
        if count > 0:
            print(f"   🔍 Kiểm tra dòng 1: Risk='{global_rules[0]['risk']}', Dist='{global_rules[0]['distribution']}'")

    except Exception as e:
        print(f"❌ LỖI NGHIÊM TRỌNG KHI ĐỌC FILE: {e}")
        import traceback
        traceback.print_exc()

load_data_startup()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_initial_data', methods=['GET'])
def get_initial_data():
    return jsonify({'success': True, 'values_by_key': global_initial_values})

@app.route('/get_all_filtered_values', methods=['POST'])
def get_all_filtered_values():
    try:
        data = request.get_json()
        selected_values = data.get('selectedValues', {})
        available = {field: set() for field in CASCADING_FIELDS}
        
        for rule in global_rules:
            is_match = True
            for key, val in selected_values.items():
                if rule['filter_data'].get(key) != val:
                    is_match = False
                    break
            
            if is_match:
                for field in CASCADING_FIELDS:
                    val = rule['filter_data'].get(field)
                    if val: available[field].add(val)
        
        final = {k: sorted(list(v)) for k, v in available.items()}
        return jsonify({'success': True, 'availableValuesByField': final})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/forward_inference_rasff', methods=['POST'])
def forward_inference_rasff():
    try:
        data = request.get_json()
        facts = data.get('initial_facts', [])
        result = forward_inference_detailed_rasff(facts, global_rules)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'status': str(e)})

if __name__ == '__main__':
    print("🚀 Server đang chạy tại http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)