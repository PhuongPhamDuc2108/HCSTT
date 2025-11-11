"""
🧠 backward_inference.py - Motor Suy Diễn Lùi (Backward Chaining)
Tối ưu cho bộ luật RASFF: IF (nhiều điều kiện) → THEN (1 kết luận)
"""

def backward_inference_rasff(goals, facts, rules):
    """
    Motor suy diễn lùi tối ưu cho RASFF Rules
    
    Đặc điểm bộ luật RASFF:
    - Ve_Phai (THEN): Chỉ 1 kết luận (VD: RISK_DECISION=serious)
    - Ve_Trai (IF): Nhiều điều kiện (5-21 điều kiện)
    - Không có chuỗi luật (luật A → luật B), chỉ facts → conclusion
    
    Args:
        goals: list[str] - Mục tiêu (VD: ['RISK_DECISION=serious'])
        facts: list[str] - Sự kiện đã biết (VD: ['TYPE=food', 'HAZARDS=acetamiprid'])
        rules: list[dict] - Các luật từ Excel
    
    Returns:
        tuple: (success, explanation_steps, proof_tree, status)
    """
    
    print("\n" + "="*80)
    print("⬅️  BACKWARD INFERENCE (SUY DIỄN LÙI) - RASFF OPTIMIZED")
    print("="*80)
    print(f"🎯 Goal (KL): {goals}")
    print(f"📍 Facts (GT): {facts}")
    print(f"📚 Available Rules: {len(rules)}")
    
    fact_set = set(facts)
    explanation_steps = []
    proof_tree = {}
    step_num = 1
    
    # ════════════════════════════════════════════════════════════════════════════════
    # THUẬT TOÁN SUY DIỄN LÙI CHO RASFF
    # ════════════════════════════════════════════════════════════════════════════════
    
    success = False
    matching_rules = []
    
    for goal in goals:
        print(f"\n{'─'*80}")
        print(f"🎯 Chứng minh Goal: {goal}")
        print(f"{'─'*80}")
        
        # BƯỚC 1: Kiểm tra goal có phải là fact không
        if goal in fact_set:
            print(f"  ✅ '{goal}' ∈ GT (Giả Thiết)")
            print(f"     → Goal là FACT ban đầu - CHỨNG MINH ĐƯỢC!")
            
            explanation_steps.append({
                'step': step_num,
                'type': 'FACT',
                'goal': goal,
                'status': 'PROVEN',
                'reason': 'Goal thuộc tập Giả Thiết (GT)',
                'note': None,
                'rule_id': None
            })
            
            proof_tree[goal] = {
                'type': 'fact',
                'proven': True
            }
            
            step_num += 1
            success = True
            continue
        
        # BƯỚC 2: Tìm tất cả luật có THEN = goal
        print(f"\n  🔍 Tìm luật có THEN = '{goal}'...")
        
        candidate_rules = []
        for rule in rules:
            rule_id = rule.get('id', '?')
            ve_phai = str(rule.get('vePhai', '')).strip()
            
            # Kiểm tra Ve_Phai có khớp với goal không
            if ve_phai == goal:
                candidate_rules.append(rule)
        
        if not candidate_rules:
            print(f"  ❌ Không tìm thấy luật nào có THEN = '{goal}'")
            print(f"     → KHÔNG THỂ CHỨNG MINH!")
            
            explanation_steps.append({
                'step': step_num,
                'type': 'FAILED',
                'goal': goal,
                'status': 'FAILED',
                'reason': f'Không có luật nào có THEN = {goal} và không thuộc GT',
                'note': None,
                'rule_id': None
            })
            
            proof_tree[goal] = {
                'type': 'failed',
                'proven': False,
                'reason': 'No matching rule'
            }
            
            step_num += 1
            continue
        
        print(f"  ✓ Tìm thấy {len(candidate_rules)} luật có THEN = '{goal}'")
        
        # BƯỚC 3: Kiểm tra từng luật xem premises có thỏa mãn không
        goal_proven = False
        
        for rule in candidate_rules:
            rule_id = rule.get('id', '?')
            ve_trai = str(rule.get('veTrai', '')).strip()
            ve_phai = str(rule.get('vePhai', '')).strip()
            note = str(rule.get('Note', 'N/A')).strip()
            
            premises = [p.strip() for p in ve_trai.split(',') if p.strip()]
            
            print(f"\n  📋 Kiểm tra Luật #{rule_id}:")
            print(f"     IF:   {ve_trai[:80]}{'...' if len(ve_trai) > 80 else ''}")
            print(f"     THEN: {ve_phai}")
            
            # Kiểm tra TẤT CẢ premises có trong facts không
            missing_premises = []
            satisfied_premises = []
            
            for premise in premises:
                if premise in fact_set:
                    satisfied_premises.append(premise)
                else:
                    missing_premises.append(premise)
            
            print(f"\n     ✓ Thỏa mãn: {len(satisfied_premises)}/{len(premises)} điều kiện")
            
            if missing_premises:
                print(f"     ✗ Thiếu:")
                for mp in missing_premises[:3]:  # Chỉ in 3 điều kiện thiếu đầu tiên
                    print(f"       - {mp}")
                if len(missing_premises) > 3:
                    print(f"       ... và {len(missing_premises)-3} điều kiện khác")
                
                # Lưu vào explanation (không thỏa mãn)
                explanation_steps.append({
                    'step': step_num,
                    'type': 'RULE_CHECKED',
                    'goal': goal,
                    'rule_id': rule_id,
                    'status': 'NOT_SATISFIED',
                    'premises': premises,
                    'satisfied': satisfied_premises,
                    'missing': missing_premises,
                    've_trai': ve_trai,
                    've_phai': ve_phai,
                    'note': note
                })
                step_num += 1
                
            else:
                # TẤT CẢ premises đều thỏa mãn!
                print(f"     ✅ TẤT CẢ điều kiện thỏa mãn!")
                print(f"     → Goal '{goal}' ĐƯỢC CHỨNG MINH bởi Luật #{rule_id}!")
                
                explanation_steps.append({
                    'step': step_num,
                    'type': 'RULE_APPLIED',
                    'goal': goal,
                    'rule_id': rule_id,
                    'status': 'PROVEN',
                    'premises': premises,
                    'satisfied': satisfied_premises,
                    'missing': [],
                    've_trai': ve_trai,
                    've_phai': ve_phai,
                    'note': note
                })
                
                proof_tree[goal] = {
                    'type': 'rule',
                    'rule_id': rule_id,
                    'premises': premises,
                    'note': note,
                    'proven': True
                }
                
                matching_rules.append(rule_id)
                step_num += 1
                goal_proven = True
                success = True
                break  # Đã chứng minh được, không cần kiểm tra luật khác
        
        if not goal_proven:
            print(f"\n  ❌ Không có luật nào thỏa mãn đủ điều kiện")
            print(f"     → Goal '{goal}' KHÔNG THỂ CHỨNG MINH!")
            
            explanation_steps.append({
                'step': step_num,
                'type': 'FAILED',
                'goal': goal,
                'status': 'FAILED',
                'reason': f'Có {len(candidate_rules)} luật nhưng không đủ facts',
                'note': None,
                'rule_id': None
            })
            
            proof_tree[goal] = {
                'type': 'insufficient_facts',
                'proven': False,
                'candidate_rules': len(candidate_rules)
            }
            
            step_num += 1
            success = False
    
    # ════════════════════════════════════════════════════════════════════════════════
    # KẾT LUẬN
    # ════════════════════════════════════════════════════════════════════════════════
    
    print(f"\n{'='*80}")
    print(f"📊 KẾT QUẢ SUY DIỄN LÙI")
    print(f"{'='*80}")
    print(f"  Goals cần chứng minh: {goals}")
    print(f"  Số bước thực hiện: {step_num - 1}")
    
    if success:
        status = f"✅ THÀNH CÔNG - Chứng minh được goals bằng luật {matching_rules}"
        print(f"  Luật đã áp dụng: {matching_rules}")
    else:
        status = "❌ THẤT BẠI - Không đủ facts để chứng minh goals"
    
    print(f"\n  {status}")
    print(f"{'='*80}\n")
    
    return success, explanation_steps, proof_tree, status


def backward_inference_detailed(goals, facts, rules):
    """Wrapper cho Flask API"""
    success, explanation, proof_tree, status = backward_inference_rasff(goals, facts, rules)
    
    return {
        'success': success,
        'explanation': explanation,
        'proof_tree': proof_tree,
        'status': status,
        'goals': goals,
        'initial_facts': facts,
        'method': 'Backward Chaining (RASFF Optimized)',
        'total_steps': len(explanation)
    }
"""
🧠 backward_inference.py - Motor Suy Diễn Lùi (Backward Chaining)
Tối ưu cho bộ luật RASFF: IF (nhiều điều kiện) → THEN (1 kết luận)
"""

def backward_inference_rasff(goals, facts, rules):
    """
    Motor suy diễn lùi tối ưu cho RASFF Rules
    
    Đặc điểm bộ luật RASFF:
    - Ve_Phai (THEN): Chỉ 1 kết luận (VD: RISK_DECISION=serious)
    - Ve_Trai (IF): Nhiều điều kiện (5-21 điều kiện)
    - Không có chuỗi luật (luật A → luật B), chỉ facts → conclusion
    
    Args:
        goals: list[str] - Mục tiêu (VD: ['RISK_DECISION=serious'])
        facts: list[str] - Sự kiện đã biết (VD: ['TYPE=food', 'HAZARDS=acetamiprid'])
        rules: list[dict] - Các luật từ Excel
    
    Returns:
        tuple: (success, explanation_steps, proof_tree, status)
    """
    
    print("\n" + "="*80)
    print("⬅️  BACKWARD INFERENCE (SUY DIỄN LÙI) - RASFF OPTIMIZED")
    print("="*80)
    print(f"🎯 Goal (KL): {goals}")
    print(f"📍 Facts (GT): {facts}")
    print(f"📚 Available Rules: {len(rules)}")
    
    fact_set = set(facts)
    explanation_steps = []
    proof_tree = {}
    step_num = 1
    
    # ════════════════════════════════════════════════════════════════════════════════
    # THUẬT TOÁN SUY DIỄN LÙI CHO RASFF
    # ════════════════════════════════════════════════════════════════════════════════
    
    success = False
    matching_rules = []
    
    for goal in goals:
        print(f"\n{'─'*80}")
        print(f"🎯 Chứng minh Goal: {goal}")
        print(f"{'─'*80}")
        
        # BƯỚC 1: Kiểm tra goal có phải là fact không
        if goal in fact_set:
            print(f"  ✅ '{goal}' ∈ GT (Giả Thiết)")
            print(f"     → Goal là FACT ban đầu - CHỨNG MINH ĐƯỢC!")
            
            explanation_steps.append({
                'step': step_num,
                'type': 'FACT',
                'goal': goal,
                'status': 'PROVEN',
                'reason': 'Goal thuộc tập Giả Thiết (GT)',
                'note': None,
                'rule_id': None
            })
            
            proof_tree[goal] = {
                'type': 'fact',
                'proven': True
            }
            
            step_num += 1
            success = True
            continue
        
        # BƯỚC 2: Tìm tất cả luật có THEN = goal
        print(f"\n  🔍 Tìm luật có THEN = '{goal}'...")
        
        candidate_rules = []
        for rule in rules:
            rule_id = rule.get('id', '?')
            ve_phai = str(rule.get('vePhai', '')).strip()
            
            # Kiểm tra Ve_Phai có khớp với goal không
            if ve_phai == goal:
                candidate_rules.append(rule)
        
        if not candidate_rules:
            print(f"  ❌ Không tìm thấy luật nào có THEN = '{goal}'")
            print(f"     → KHÔNG THỂ CHỨNG MINH!")
            
            explanation_steps.append({
                'step': step_num,
                'type': 'FAILED',
                'goal': goal,
                'status': 'FAILED',
                'reason': f'Không có luật nào có THEN = {goal} và không thuộc GT',
                'note': None,
                'rule_id': None
            })
            
            proof_tree[goal] = {
                'type': 'failed',
                'proven': False,
                'reason': 'No matching rule'
            }
            
            step_num += 1
            continue
        
        print(f"  ✓ Tìm thấy {len(candidate_rules)} luật có THEN = '{goal}'")
        
        # BƯỚC 3: Kiểm tra từng luật xem premises có thỏa mãn không
        goal_proven = False
        
        for rule in candidate_rules:
            rule_id = rule.get('id', '?')
            ve_trai = str(rule.get('veTrai', '')).strip()
            ve_phai = str(rule.get('vePhai', '')).strip()
            note = str(rule.get('Note', 'N/A')).strip()
            
            premises = [p.strip() for p in ve_trai.split(',') if p.strip()]
            
            print(f"\n  📋 Kiểm tra Luật #{rule_id}:")
            print(f"     IF:   {ve_trai[:80]}{'...' if len(ve_trai) > 80 else ''}")
            print(f"     THEN: {ve_phai}")
            
            # Kiểm tra TẤT CẢ premises có trong facts không
            missing_premises = []
            satisfied_premises = []
            
            for premise in premises:
                if premise in fact_set:
                    satisfied_premises.append(premise)
                else:
                    missing_premises.append(premise)
            
            print(f"\n     ✓ Thỏa mãn: {len(satisfied_premises)}/{len(premises)} điều kiện")
            
            if missing_premises:
                print(f"     ✗ Thiếu:")
                for mp in missing_premises[:3]:  # Chỉ in 3 điều kiện thiếu đầu tiên
                    print(f"       - {mp}")
                if len(missing_premises) > 3:
                    print(f"       ... và {len(missing_premises)-3} điều kiện khác")
                
                # Lưu vào explanation (không thỏa mãn)
                explanation_steps.append({
                    'step': step_num,
                    'type': 'RULE_CHECKED',
                    'goal': goal,
                    'rule_id': rule_id,
                    'status': 'NOT_SATISFIED',
                    'premises': premises,
                    'satisfied': satisfied_premises,
                    'missing': missing_premises,
                    've_trai': ve_trai,
                    've_phai': ve_phai,
                    'note': note
                })
                step_num += 1
                
            else:
                # TẤT CẢ premises đều thỏa mãn!
                print(f"     ✅ TẤT CẢ điều kiện thỏa mãn!")
                print(f"     → Goal '{goal}' ĐƯỢC CHỨNG MINH bởi Luật #{rule_id}!")
                
                explanation_steps.append({
                    'step': step_num,
                    'type': 'RULE_APPLIED',
                    'goal': goal,
                    'rule_id': rule_id,
                    'status': 'PROVEN',
                    'premises': premises,
                    'satisfied': satisfied_premises,
                    'missing': [],
                    've_trai': ve_trai,
                    've_phai': ve_phai,
                    'note': note
                })
                
                proof_tree[goal] = {
                    'type': 'rule',
                    'rule_id': rule_id,
                    'premises': premises,
                    'note': note,
                    'proven': True
                }
                
                matching_rules.append(rule_id)
                step_num += 1
                goal_proven = True
                success = True
                break  # Đã chứng minh được, không cần kiểm tra luật khác
        
        if not goal_proven:
            print(f"\n  ❌ Không có luật nào thỏa mãn đủ điều kiện")
            print(f"     → Goal '{goal}' KHÔNG THỂ CHỨNG MINH!")
            
            explanation_steps.append({
                'step': step_num,
                'type': 'FAILED',
                'goal': goal,
                'status': 'FAILED',
                'reason': f'Có {len(candidate_rules)} luật nhưng không đủ facts',
                'note': None,
                'rule_id': None
            })
            
            proof_tree[goal] = {
                'type': 'insufficient_facts',
                'proven': False,
                'candidate_rules': len(candidate_rules)
            }
            
            step_num += 1
            success = False
    
    # ════════════════════════════════════════════════════════════════════════════════
    # KẾT LUẬN
    # ════════════════════════════════════════════════════════════════════════════════
    
    print(f"\n{'='*80}")
    print(f"📊 KẾT QUẢ SUY DIỄN LÙI")
    print(f"{'='*80}")
    print(f"  Goals cần chứng minh: {goals}")
    print(f"  Số bước thực hiện: {step_num - 1}")
    
    if success:
        status = f"✅ THÀNH CÔNG - Chứng minh được goals bằng luật {matching_rules}"
        print(f"  Luật đã áp dụng: {matching_rules}")
    else:
        status = "❌ THẤT BẠI - Không đủ facts để chứng minh goals"
    
    print(f"\n  {status}")
    print(f"{'='*80}\n")
    
    return success, explanation_steps, proof_tree, status


def backward_inference_detailed(goals, facts, rules):
    """Wrapper cho Flask API"""
    success, explanation, proof_tree, status = backward_inference_rasff(goals, facts, rules)
    
    return {
        'success': success,
        'explanation': explanation,
        'proof_tree': proof_tree,
        'status': status,
        'goals': goals,
        'initial_facts': facts,
        'method': 'Backward Chaining (RASFF Optimized)',
        'total_steps': len(explanation)
    }
