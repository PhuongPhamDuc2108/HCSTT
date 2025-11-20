from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import os
from collections import Counter
from inference import forward_inference_detailed_rasff

app = Flask(__name__)
CORS(app)

# === CẤU HÌNH ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = 'RASFF_Rules_Inference_500_SCIENTIFIC_vi.xlsx'
FILE_PATH = os.path.join(BASE_DIR, EXCEL_FILE)

CASCADING_FIELDS = ['NOT_COUNTRY', 'TYPE', 'PROD_CAT', 'PRODUCT', 'HAZARDS_CAT', 'HAZARDS']

global_rules = []
global_initial_values = {}

# === TỪ ĐIỂN CHUẨN HÓA (VIETNAMESE -> ENGLISH) ===
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
            df = pd.read_csv(actual_path)
        else:
            df = pd.read_excel(actual_path, engine='openpyxl')
        
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.fillna('')
        
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
                    'Note': str(row.get('NOTE') or 'N/A').strip(),
                    'risk': str(row.get('RISK_PERCENTAGE') or row.get('RISK') or '0%').strip(),
                    'distribution': dist_stat,
                    'filter_data': filter_data
                })
                count += 1

        global_initial_values = {k: sorted(list(v)) for k, v in unique_values.items()}
        print(f"✅ LOAD THÀNH CÔNG: {count} luật.")

    except Exception as e:
        print(f"❌ LỖI ĐỌC FILE: {e}")

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
        result = forward_inference_detailed_rasff(facts, global_rules)
        return jsonify(result)
    except Exception as e:
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
            
        # --- [CHỈNH SỬA CHÍNH] Sắp xếp giảm dần ---
        # Counter.most_common(10) trả về list các tuple đã sắp xếp: [('Item1', 10), ('Item2', 8)...]
        # Ta tách ra 2 list riêng để Frontend vẽ đúng thứ tự
        
        hazard_sorted = Counter(hazards).most_common(10)
        prod_cat_sorted = Counter(prod_cats).most_common(10)
        product_sorted = Counter(products).most_common(10)

        return jsonify({
            'success': True,
            'total_rules': len(global_rules),
            'stats': {
                'country_counts': dict(Counter(countries).most_common()), # Map không cần thứ tự
                
                'hazard_stats': {
                    'labels': [x[0] for x in hazard_sorted],
                    'values': [x[1] for x in hazard_sorted]
                },
                'prod_cat_stats': {
                    'labels': [x[0] for x in prod_cat_sorted],
                    'values': [x[1] for x in prod_cat_sorted]
                },
                'top_products_list': [{'name': x[0], 'count': x[1]} for x in product_sorted]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)