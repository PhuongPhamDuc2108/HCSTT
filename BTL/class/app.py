from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import os
import re  # <--- [MỚI] Import thư viện regex
from collections import Counter
from inference import forward_inference_detailed_rasff

app = Flask(__name__)
CORS(app)

# === CẤU HÌNH ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = 'RASFF_Final_Complete.xlsx'
FILE_PATH = os.path.join(BASE_DIR, EXCEL_FILE)

CASCADING_FIELDS = ['NOT_COUNTRY', 'TYPE', 'PROD_CAT', 'PRODUCT', 'HAZARDS_CAT', 'HAZARDS']

global_rules = []
global_initial_values = {}

VN_TO_EN_COUNTRY_MAP = {
    'Việt Nam': 'Vietnam', 'Trung Quốc': 'China', 'Ấn Độ': 'India', 'Thái Lan': 'Thailand',
    'Thổ Nhĩ Kỳ': 'Turkey', 'Hàn Quốc': 'South Korea', 'Nhật Bản': 'Japan', 'Indonesia': 'Indonesia',
    'Đài Loan': 'Taiwan', 'Iran': 'Iran', 'Pakistan': 'Pakistan', 'Sri Lanka': 'Sri Lanka',
    'Malaysia': 'Malaysia', 'Philippines': 'Philippines', 'Singapore': 'Singapore',
    'Campuchia': 'Cambodia', 'Lào': 'Laos', 'Hồng Kông': 'Hong Kong', 'Israel': 'Israel',
    'Ả Rập Xê Út': 'Saudi Arabia', 'Các Tiểu vương quốc Ả Rập Thống nhất': 'United Arab Emirates',
    'Ba Lan': 'Poland', 'Pháp': 'France', 'Ý': 'Italy', 'Đức': 'Germany', 'Tây Ban Nha': 'Spain',
    'Hà Lan': 'Netherlands', 'Bỉ': 'Belgium', 'Vương Quốc Anh': 'United Kingdom', 'Anh': 'United Kingdom',
    'Thụy Điển': 'Sweden', 'Đan Mạch': 'Denmark', 'Na Uy': 'Norway', 'Ukraina': 'Ukraine',
    'Nga': 'Russia', 'Bulgaria': 'Bulgaria', 'Hungary': 'Hungary', 'Séc': 'Czech Republic',
    'Hy Lạp': 'Greece', 'Bồ Đào Nha': 'Portugal', 'Ireland': 'Ireland',
    'Mỹ': 'United States', 'Hoa Kỳ': 'United States', 'Brazil': 'Brazil', 'Argentina': 'Argentina',
    'Canada': 'Canada', 'Mexico': 'Mexico', 'Chile': 'Chile', 'Ecuador': 'Ecuador',
    'Colombia': 'Colombia', 'Peru': 'Peru',
    'Ai Cập': 'Egypt', 'Maroc': 'Morocco', 'Nigeria': 'Nigeria', 'Nam Phi': 'South Africa',
    'Madagascar': 'Madagascar',
    'Úc': 'Australia', 'New Zealand': 'New Zealand'
}

def parse_ve_trai(ve_trai_str):
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

def find_action_column(columns):
    if 'ACTION_TAKEN' in columns: return 'ACTION_TAKEN'
    if 'ACTION' in columns: return 'ACTION'
    for col in columns:
        c_upper = str(col).upper()
        if "ACTION" in c_upper or "TAKEN" in c_upper or "BIEN_PHAP" in c_upper or "XU_LY" in c_upper:
            return col
    return None

# === [MỚI] HÀM TÍNH TOÁN RISK TỪ NOTE ===
def calculate_risk_from_note(note_text):
    """
    Phân tích cột Note để tính chỉ số % rủi ro nếu cột RISK bị thiếu.
    """
    if not isinstance(note_text, str):
        return 0 # Mặc định

    # 1. Ưu tiên tìm mẫu "(x/5)" (Ví dụ: (3/5) -> 60%)
    match = re.search(r'\((\d+)/5\)', note_text)
    if match:
        score = int(match.group(1))
        # Quy đổi: (Điểm / 5) * 100
        return int((score / 5) * 100)

    # 2. Nếu không có số sao, tìm theo từ khóa ngữ nghĩa
    text_lower = note_text.lower()
    if 'serious' in text_lower or 'nghiêm trọng' in text_lower or 'cao' in text_lower:
        return 85
    elif 'decision not yet taken' in text_lower or 'chưa quyết định' in text_lower or 'undecided' in text_lower:
        return 50
    elif 'thấp' in text_lower or 'low' in text_lower:
        return 20
    
    return 0 # Không xác định

def load_data_startup():
    global global_rules, global_initial_values
    print(f"\n⏳ [STARTUP] Đang đọc file dữ liệu...")
    
    actual_path = FILE_PATH
    if not os.path.exists(actual_path):
        csv_path = actual_path.replace('.xlsx', '.csv')
        extra_csv_path = actual_path + " - All_Rules.csv"
        if os.path.exists(csv_path): actual_path = csv_path
        elif os.path.exists(extra_csv_path): actual_path = extra_csv_path
        else:
             print(f"❌ LỖI: Không tìm thấy file dữ liệu {EXCEL_FILE}.")
             return

    try:
        if actual_path.endswith('.csv'):
            try:
                df = pd.read_csv(actual_path, encoding='utf-8-sig')
            except:
                df = pd.read_csv(actual_path, encoding='latin-1')
        else:
            df = pd.read_excel(actual_path, engine='openpyxl')
        
        action_col_original = find_action_column(df.columns)
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.fillna('')
        
        action_col_upper = str(action_col_original).strip().upper() if action_col_original else None
        
        if action_col_upper:
            print(f"✅ Đã map cột Action: '{action_col_original}'")
        else:
            print("⚠️ CẢNH BÁO: Không tìm thấy cột Action!")

        unique_values = {k: set() for k in CASCADING_FIELDS}
        count = 0

        for idx, row in df.iterrows():
            ve_phai = str(row.get('VE_PHAI') or row.get('THEN') or '').strip()
            if not ve_phai: continue

            raw_ve_trai = str(row.get('VE_TRAI', '')).strip()
            combined_data = parse_ve_trai(raw_ve_trai)
            dist_stat = combined_data.pop('DISTRIBUTION_STAT', 'Chưa có thông tin phân phối')

            if str(row.get('PRODUCT', '')).strip(): combined_data['PRODUCT'] = str(row.get('PRODUCT')).strip()
            if str(row.get('NOT_COUNTRY', '')).strip(): combined_data['NOT_COUNTRY'] = str(row.get('NOT_COUNTRY')).strip()
            
            action_val = 'Chưa có thông tin'
            if action_col_upper:
                raw_val = row.get(action_col_upper)
                if pd.notna(raw_val) and str(raw_val).strip() != '' and str(raw_val).lower() != 'nan':
                    action_val = str(raw_val).strip()
            
            # === [MỚI] XỬ LÝ RISK PERCENTAGE TỰ ĐỘNG ===
            # Lấy giá trị từ cột có sẵn
            raw_risk = row.get('RISK_PERCENTAGE') or row.get('RISK')
            risk_val = '0%'
            
            # Nếu có cột dữ liệu thì dùng
            if pd.notna(raw_risk) and str(raw_risk).strip() != '' and str(raw_risk).strip() != '0%':
                risk_val = str(raw_risk).strip()
            else:
                # Nếu không có, tự tính từ cột NOTE
                note_content = str(row.get('NOTE') or '').strip()
                calculated_risk = calculate_risk_from_note(note_content)
                if calculated_risk > 0:
                    risk_val = f"{calculated_risk}%"
            # =============================================

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
                rule_id = str(row.get('ID', idx + 1)).strip()
                if rule_id.endswith('.0'): rule_id = rule_id[:-2]

                global_rules.append({
                    'id': rule_id, 
                    'veTrai': ", ".join(conditions_display),
                    'vePhai': ve_phai,
                    'Note': str(row.get('NOTE') or 'N/A').strip(),
                    'risk': risk_val, # Sử dụng giá trị đã xử lý ở trên
                    'action_taken': action_val,
                    'distribution': dist_stat,
                    'filter_data': filter_data
                })
                count += 1

        global_initial_values = {k: sorted(list(v)) for k, v in unique_values.items()}
        print(f"✅ LOAD THÀNH CÔNG: {count} luật.")

    except Exception as e:
        print(f"❌ LỖI ĐỌC FILE: {e}")
        import traceback
        traceback.print_exc()

load_data_startup()

def chuan_hoa_quoc_gia(name):
    if not name: return None
    name = str(name).strip()
    if name in VN_TO_EN_COUNTRY_MAP: return VN_TO_EN_COUNTRY_MAP[name]
    return VN_TO_EN_COUNTRY_MAP.get(name.title(), name)

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
        
        # 1. Chạy suy diễn
        response_data = forward_inference_detailed_rasff(facts, global_rules)
        
        # 2. TÌM LẠI ID CỦA LUẬT GỐC và ACTION
        if 'results' in response_data:
            for item in response_data['results']:
                conclusion_text = item.get('conclusion')
                
                matched_rule = next((r for r in global_rules if r['vePhai'] == conclusion_text), None)
                
                if matched_rule:
                    found_id = matched_rule['id']
                    found_action = matched_rule['action_taken']
                    
                    # Gán lại ID và Action vào kết quả trả về cho FE
                    item['id'] = found_id
                    item['action_taken'] = found_action
                    
                    # Nếu trong kết quả suy diễn chưa có risk (hoặc risk=0%), lấy lại risk từ global_rules
                    if 'risk' not in item or item['risk'] == '0%':
                         item['risk'] = matched_rule['risk']
                    
                    print(f"✅ Khôi phục ID: {found_id} -> Action: {found_action} -> Risk: {item['risk']}")
                else:
                    item['action_taken'] = "Không tìm thấy thông tin (Lỗi khớp ID)"
                    
        return jsonify(response_data)
    except Exception as e:
        print(f"Lỗi API Inference: {e}")
        return jsonify({'success': False, 'status': str(e)})

@app.route('/get_dashboard_statistics', methods=['GET'])
def get_dashboard_statistics():
    try:
        countries = []
        hazards = []
        prod_cats = []
        products = []
        
        for rule in global_rules:
            fd = rule.get('filter_data', {})
            raw_country = fd.get('NOT_COUNTRY')
            if raw_country:
                english_name = chuan_hoa_quoc_gia(raw_country)
                if english_name: countries.append(english_name)
                
            if fd.get('HAZARDS_CAT'): hazards.append(fd.get('HAZARDS_CAT'))
            if fd.get('PROD_CAT'): prod_cats.append(fd.get('PROD_CAT'))
            if fd.get('PRODUCT'): products.append(fd.get('PRODUCT'))
            
        hazard_sorted = Counter(hazards).most_common(10)
        prod_cat_sorted = Counter(prod_cats).most_common(10)
        product_sorted = Counter(products).most_common(10)

        return jsonify({
            'success': True,
            'total_rules': len(global_rules),
            'stats': {
                'country_counts': dict(Counter(countries).most_common()),
                'hazard_stats': {'labels': [x[0] for x in hazard_sorted], 'values': [x[1] for x in hazard_sorted]},
                'prod_cat_stats': {'labels': [x[0] for x in prod_cat_sorted], 'values': [x[1] for x in prod_cat_sorted]},
                'top_products_list': [{'name': x[0], 'count': x[1]} for x in product_sorted]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)