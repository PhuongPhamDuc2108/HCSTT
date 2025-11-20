def forward_inference_detailed_rasff(initial_facts, rules):
    # Chuyển input của user thành Dict
    fact_dict = {}
    for f in initial_facts:
        if '=' in f:
            k, v = f.split('=', 1)
            fact_dict[k.strip()] = v.strip()

    matched_rules = []
    
    for rule in rules:
        ve_phai = rule.get('vePhai')
        note = rule.get('Note')
        rule_id = rule.get('id')
        filter_data = rule.get('filter_data', {})
        
        # Lấy thông tin Risk và Dist đã xử lý ở app.py
        risk = rule.get('risk', '0%')
        distribution = rule.get('distribution', 'N/A')

        is_match = True
        matched_conds = []
        
        # So sánh Input User vs Rule Data
        for key, val in fact_dict.items():
            if filter_data.get(key) != val:
                is_match = False
                break
            matched_conds.append(f"{key}={val}")
        
        if is_match and ve_phai:
            matched_rules.append({
                'rule_id': rule_id,
                'premises': matched_conds,
                'conclusion': ve_phai,
                'risk': risk,                 # Trả về FE
                'distribution': distribution, # Trả về FE
                'note': note
            })

    success = len(matched_rules) > 0
    status = f"Tìm thấy {len(matched_rules)} kết quả." if success else "Không tìm thấy luật phù hợp."

    return {
        'success': success,
        'results': matched_rules,
        'status': status
    }