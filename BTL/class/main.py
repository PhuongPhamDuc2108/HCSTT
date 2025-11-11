from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import os
from werkzeug.utils import secure_filename
from inference import forward_inference_detailed_rasff
from backward_inference import backward_inference_detailed

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

global_rules = []
global_keys = []
global_values_by_key = {}

# ============ THỨ TỰ DROPDOWN CASCADING ============
CASCADING_FIELDS = ['TYPE', 'PRODUCT', 'PROD_CAT', 'HAZARDS', 'HAZARDS_CAT', 'DISTRIBUTION_STAT']

@app.route('/upload_rasff', methods=['POST'])
def upload_rasff():
    global global_rules, global_keys, global_values_by_key
    try:
        print("\n" + "="*80)
        print("📤 UPLOAD REQUEST RECEIVED")
        print("="*80)
        
        if 'file' not in request.files:
            print("❌ No file in request")
            return jsonify({'success': False, 'message': 'Không tìm thấy file'})
        
        file = request.files['file']
        print(f"📄 File received: {file.filename}")
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'File không hợp lệ'})
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'message': 'Chỉ hỗ trợ file Excel (.xlsx, .xls)'})
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"✅ File saved: {filepath}")
        
        try:
            df = pd.read_excel(filepath)
            print(f"✅ Excel file read: {len(df)} rows")
            print(f"Columns: {df.columns.tolist()}")
        except Exception as e:
            print(f"❌ Error reading Excel: {e}")
            return jsonify({'success': False, 'message': f'Lỗi đọc file: {str(e)}'})
        
        global_rules = []
        for idx, row in df.iterrows():
            # ✅ ĐỌC VeTrai TỪ FILE
            veTrai_original = str(row.get('Ve_Trai') or row.get('IF') or '').strip()
            
            # ✅ ĐỌC PRODUCT TỪ CỘT RIÊNG
            product_value = str(row.get('PRODUCT') or '').strip()
            
            # ✅ THÊM PRODUCT VÀO VeTrai (nếu chưa có)
            if product_value and product_value != 'nan':
                # Kiểm tra xem veTrai đã có PRODUCT chưa
                if 'PRODUCT=' not in veTrai_original:
                    veTrai_with_product = f"PRODUCT={product_value},{veTrai_original}"
                else:
                    veTrai_with_product = veTrai_original
            else:
                veTrai_with_product = veTrai_original
            
            rule = {
                'id': row.get('ID') or idx + 1,
                'veTrai': veTrai_with_product,
                'vePhai': str(row.get('Ve_Phai') or row.get('THEN') or '').strip(),
                'Note': str(row.get('Note') or 'N/A').strip(),
                'PRODUCT': product_value  # ✅ Lưu riêng để dễ truy cập
            }
            
            if rule['veTrai'] and rule['vePhai']:
                global_rules.append(rule)
        
        print(f"✅ Parsed {len(global_rules)} rules")
        
        # Extract keys and values từ Ve_Trai (đã có PRODUCT)
        global_keys = []
        global_values_by_key = {}
        
        for rule in global_rules:
            conditions = str(rule['veTrai']).split(',')
            for cond in conditions:
                cond = cond.strip()
                if '=' in cond:
                    parts = cond.split('=', 1)
                    if len(parts) == 2:
                        key, value = parts
                        key = key.strip()
                        value = value.strip()
                        
                        if key and key not in global_keys:
                            global_keys.append(key)
                        
                        if key and key not in global_values_by_key:
                            global_values_by_key[key] = []
                        
                        if key and value and value not in global_values_by_key[key]:
                            global_values_by_key[key].append(value)
        
        # Sắp xếp theo thứ tự CASCADING_FIELDS
        global_keys = [k for k in CASCADING_FIELDS if k in global_values_by_key]
        
        for key in global_values_by_key:
            global_values_by_key[key] = sorted(global_values_by_key[key])
        
        print(f"✅ Extracted {len(global_keys)} keys: {global_keys}")
        print(f"✅ Sample values for PRODUCT: {global_values_by_key.get('PRODUCT', [])[:5]}")
        
        response = {
            'success': True,
            'message': f'Upload thành công! Tìm thấy {len(global_rules)} luật',
            'rules_count': len(global_rules),
            'keys_count': len(global_keys)
        }
        
        return jsonify(response)
    
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'})

@app.route('/get_keys_rasff', methods=['GET'])
def get_keys_rasff():
    """
    📌 API trả về tất cả keys và values ban đầu
    """
    try:
        print("\n📋 GET_KEYS REQUEST")
        print(f"Keys: {global_keys}")
        
        return jsonify({
            'success': True,
            'keys': global_keys,
            'values_by_key': global_values_by_key,
            'cascadingFields': CASCADING_FIELDS
        })
    
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'keys': [],
            'values_by_key': {},
            'cascadingFields': CASCADING_FIELDS,
            'error': str(e)
        })

@app.route('/get_all_filtered_values', methods=['POST'])
def get_all_filtered_values():
    """
    📌 API Lọc giá trị cascading cho TẤT CẢ các trường
    """
    try:
        data = request.get_json()
        selected_values = data.get('selectedValues', {})
        
        print(f"\n🔍 GET_ALL_FILTERED_VALUES")
        print(f"Selected values: {selected_values}")
        
        # Kết quả: dictionary chứa available values cho từng field
        available_values_for_all_fields = {}
        
        for field in CASCADING_FIELDS:
            matching_values = set()
            
            # Lọc các luật phù hợp với selected_values
            for rule in global_rules:
                conditions = str(rule['veTrai']).split(',')
                condition_dict = {}
                
                # Parse conditions thành dict
                for cond in conditions:
                    cond = cond.strip()
                    if '=' in cond:
                        parts = cond.split('=', 1)
                        if len(parts) == 2:
                            key, value = parts[0].strip(), parts[1].strip()
                            condition_dict[key] = value
                
                # Kiểm tra xem rule này có match với tất cả selected_values không
                match = True
                for key, value in selected_values.items():
                    if key != field:  # Bỏ qua field hiện tại
                        if condition_dict.get(key) != value:
                            match = False
                            break
                
                # Nếu match, thêm giá trị của field hiện tại
                if match and field in condition_dict:
                    matching_values.add(condition_dict[field])
            
            available_values_for_all_fields[field] = sorted(list(matching_values))
        
        print(f"✅ Filtered values for all fields:")
        for field, values in available_values_for_all_fields.items():
            print(f"  {field}: {len(values)} values")
        
        return jsonify({
            'success': True,
            'availableValuesByField': available_values_for_all_fields
        })
    
    except Exception as e:
        print(f"❌ Error in get_all_filtered_values: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': str(e),
            'availableValuesByField': {}
        })

@app.route('/search_rasff', methods=['POST'])
def search_rasff():
    """
    ✅ Tìm kiếm luật dựa trên facts đã chọn
    """
    try:
        data = request.get_json()
        facts = data.get('facts', [])
        
        print("\n" + "="*80)
        print("🔍 SEARCH REQUEST")
        print(f"Facts: {facts}")
        print("="*80)
        
        if not facts:
            return jsonify({'success': False, 'message': 'Không có facts', 'rules': [], 'count': 0})
        
        fact_set = set(facts)
        matching_rules = []
        
        for rule in global_rules:
            conditions = str(rule['veTrai']).split(',')
            condition_set = set(cond.strip() for cond in conditions if cond.strip())
            
            # Kiểm tra xem TẤT CẢ facts có nằm trong conditions không
            if fact_set.issubset(condition_set):
                matching_rules.append(rule)
                print(f"✅ MATCH: Rule ID={rule['id']}")
        
        print(f"✅ Found {len(matching_rules)} matching rules")
        
        return jsonify({
            'success': True,
            'rules': matching_rules,
            'count': len(matching_rules)
        })
    
    except Exception as e:
        print(f"❌ Error in search: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e),
            'rules': [],
            'count': 0
        })

@app.route('/forward_inference_rasff', methods=['POST'])
def forward_inference_rasff():
    try:
        data = request.get_json()
        goals = data.get('goals', [])
        facts = data.get('initial_facts', [])
        
        print(f"\n➡️ FORWARD INFERENCE: Goals={goals}, Facts={facts}")
        result = forward_inference_detailed_rasff(goals, facts, global_rules)
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'status': f'Lỗi: {str(e)}',
            'explanation': []
        })

@app.route('/backward_inference_rasff', methods=['POST'])
def backward_inference_rasff():
    try:
        data = request.get_json()
        goals = data.get('goals', [])
        facts = data.get('initial_facts', [])
        
        print(f"\n⬅️ BACKWARD INFERENCE: Goals={goals}, Facts={facts}")
        result = backward_inference_detailed(goals, facts, global_rules)
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'status': f'Lỗi: {str(e)}',
            'explanation': []
        })

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 RASFF LOGIC INFERENCE SYSTEM - BACKEND")
    print("="*80)
    print("\n📝 Routes:")
    print("  - POST /upload_rasff")
    print("  - GET  /get_keys_rasff")
    print("  - POST /get_all_filtered_values")
    print("  - POST /search_rasff")
    print("  - POST /forward_inference_rasff")
    print("  - POST /backward_inference_rasff")
    print("\n🌐 URL: http://127.0.0.1:5000\n")
    
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
