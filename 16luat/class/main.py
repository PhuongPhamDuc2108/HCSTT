# main.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from fpg import FPG
from rpg import RPG
from inference import forward_inference_detailed
from backward_inference import backward_inference_detailed, backward_inference_with_trace

app = Flask(__name__)
CORS(app)

@app.route('/generate_fpg', methods=['POST'])
def generate_fpg():
    """Endpoint: Tạo biểu đồ FPG"""
    try:
        data = request.json.get('rules', [])
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
        
        return jsonify({
            'success': True,
            'image': image_base64,
            'node_count': fpg.graph.number_of_nodes(),
            'edge_count': fpg.graph.number_of_edges(),
            'layout_method': layout_method
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/generate_rpg', methods=['POST'])
def generate_rpg():
    """Endpoint: Tạo biểu đồ RPG"""
    try:
        data = request.json.get('rules', [])
        initial_facts = request.json.get('initial_facts', [])
        target_goals = request.json.get('target_goals', [])
        
        if not data:
            return jsonify({'error': 'Không có dữ liệu luật'}), 400
        
        rpg = RPG()
        rpg.load_from_data(data)
        rpg.set_initial_and_target(initial_facts, target_goals)
        rpg.build_graph()
        
        image_base64 = rpg.visualize_to_base64()
        
        return jsonify({
            'success': True,
            'image': image_base64,
            'node_count': rpg.graph.number_of_nodes(),
            'edge_count': rpg.graph.number_of_edges(),
            'layout_method': 'kamada_kawai'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/forward_inference_advanced', methods=['POST'])
def forward_inference_advanced():
    """Endpoint: Suy diễn tiến"""
    try:
        data = request.json
        rules = data.get('rules', [])
        initial_facts = data.get('initial_facts', [])
        goals = data.get('goals', [])
        
        if not rules or not initial_facts or not goals:
            return jsonify({'error': 'Thiếu dữ liệu'}), 400
        
        success, process_table, full_vet, optimal_vet, explanation, conclusion = \
            forward_inference_detailed(initial_facts, goals, rules)
        
        return jsonify({
            'success': success,
            'process_table': process_table,
            'full_vet': full_vet,
            'optimal_vet': optimal_vet,
            'explanation': explanation,
            'conclusion': conclusion,
            'initial_facts': initial_facts,
            'goals': goals
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/backward_inference_advanced', methods=['POST'])
def backward_inference_advanced():
    """Endpoint: Suy diễn lùi"""
    try:
        data = request.json
        rules = data.get('rules', [])
        initial_facts = data.get('initial_facts', [])
        goals = data.get('goals', [])
        
        if not rules or not initial_facts or not goals:
            return jsonify({'error': 'Thiếu dữ liệu'}), 400
        
        success, process_table, full_vet, optimal_vet, explanation, conclusion = \
            backward_inference_detailed(initial_facts, goals, rules)
        
        return jsonify({
            'success': success,
            'process_table': process_table,
            'full_vet': full_vet,
            'optimal_vet': optimal_vet,
            'explanation': explanation,
            'conclusion': conclusion,
            'initial_facts': initial_facts,
            'goals': goals
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/backward_inference_trace', methods=['POST'])
def backward_inference_trace():
    """Endpoint: Suy diễn lùi với trace"""
    try:
        data = request.json
        rules = data.get('rules', [])
        initial_facts = data.get('initial_facts', [])
        goals = data.get('goals', [])
        
        if not rules or not initial_facts or not goals:
            return jsonify({'error': 'Thiếu dữ liệu'}), 400
        
        success, trace, applied_rules = \
            backward_inference_with_trace(initial_facts, goals, rules)
        
        return jsonify({
            'success': success,
            'trace': trace,
            'applied_rules': applied_rules,
            'initial_facts': initial_facts,
            'goals': goals
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint kiểm tra server"""
    return jsonify({
        'status': 'ok',
        'message': 'Server đang chạy',
        'endpoints': {
            'fpg': '/generate_fpg',
            'rpg': '/generate_rpg',
            'forward_inference': '/forward_inference_advanced',
            'backward_inference': '/backward_inference_advanced',
            'backward_trace': '/backward_inference_trace'
        }
    })

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Flask Server khởi động tại: http://localhost:5000")
    print("=" * 70)
    print("📊 Endpoints:")
    print("   - POST /generate_fpg : Tạo biểu đồ FPG")
    print("   - POST /generate_rpg : Tạo biểu đồ RPG")
    print("   - POST /forward_inference_advanced : Suy diễn tiến")
    print("   - POST /backward_inference_advanced : Suy diễn lùi")
    print("   - POST /backward_inference_trace : Trace suy diễn lùi")
    print("   - GET  /health : Kiểm tra server")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
