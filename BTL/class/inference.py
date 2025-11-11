"""
🧠 inference.py - Motor Suy Diễn Tiến (Forward Chaining)
Chuỗi suy diễn từ FACTS → GOALS với ghi chú chi tiết
"""

def forward_inference_detailed_rasff(goals, initial_facts, rules):
    """
    Motor suy diễn tiến chi tiết
    
    Args:
        goals: list[str] - Mục tiêu cần đạt (VD: ['RISK_DECISION=serious'])
        initial_facts: list[str] - Sự kiện ban đầu (VD: ['TYPE=food', 'HAZARDS=acetamiprid'])
        rules: list[dict] - Danh sách luật từ Excel
        
    Returns:
        dict: {
            'success': bool,
            'explanation': list[dict] - Các bước suy diễn chi tiết,
            'working_memory': list[str] - Tất cả facts sau suy diễn,
            'applied_rules': list - ID các luật đã áp dụng,
            'status': str,
            'method': str
        }
    """
    
    print("\n" + "="*80)
    print("➡️  FORWARD INFERENCE (SUY DIỄN TIẾN)")
    print("="*80)
    print(f"🎯 Goals: {goals}")
    print(f"📍 Initial Facts: {initial_facts}")
    print(f"📚 Available Rules: {len(rules)}")
    
    # Khởi tạo Working Memory
    working_memory = set(initial_facts)
    applied_rules = []
    explanation_steps = []
    
    iteration = 0
    max_iterations = len(rules) * 2
    step_num = 1
    
    # ════════════════════════════════════════════════════════════════════════════════
    # VÒNG LẶP SUY DIỄN TIẾN
    # ════════════════════════════════════════════════════════════════════════════════
    
    while iteration < max_iterations:
        iteration += 1
        applied_in_iteration = False
        
        print(f"\n[Iteration {iteration}] Working Memory: {working_memory}")
        
        for rule in rules:
            rule_id = rule.get('id', '?')
            ve_trai = str(rule.get('veTrai', '')).strip()
            ve_phai = str(rule.get('vePhai', '')).strip()
            note = str(rule.get('Note', 'N/A')).strip()
            
            # Bỏ qua luật đã áp dụng
            if rule_id in applied_rules:
                continue
            
            # Parse premises từ Ve_Trai
            premises = [p.strip() for p in ve_trai.split(',') if p.strip()]
            
            # Kiểm tra TẤT CẢ premises có trong Working Memory không
            all_matched = all(premise in working_memory for premise in premises)
            
            if all_matched and len(premises) > 0:
                print(f"  ✓ Áp dụng Luật #{rule_id}")
                print(f"    IF:   {ve_trai}")
                print(f"    THEN: {ve_phai}")
                
                # Thêm kết luận vào Working Memory
                conclusions = [c.strip() for c in ve_phai.split(',') if c.strip()]
                for conclusion in conclusions:
                    working_memory.add(conclusion)
                
                applied_rules.append(rule_id)
                applied_in_iteration = True
                
                # ════════════════════════════════════════════════════════════════
                # LƯU BƯỚC SUY DIỄN CHI TIẾT
                # ════════════════════════════════════════════════════════════════
                explanation_steps.append({
                    'step': step_num,
                    'type': 'RULE_APPLICATION',
                    'rule_id': rule_id,
                    'premises': premises,
                    'conclusion': ve_phai,
                    'note': note,
                    'working_memory_after': list(working_memory)
                })
                
                step_num += 1
        
        # Nếu không có luật nào được áp dụng → dừng
        if not applied_in_iteration:
            print("  (Không có luật nào được áp dụng thêm)")
            break
    
    # ════════════════════════════════════════════════════════════════════════════════
    # KIỂM TRA GOALS
    # ════════════════════════════════════════════════════════════════════════════════
    
    success = all(goal in working_memory for goal in goals)
    
    if success:
        status = "✅ THÀNH CÔNG - Đạt được tất cả goals"
    else:
        missing_goals = [g for g in goals if g not in working_memory]
        status = f"❌ THẤT BẠI - Không đạt được: {missing_goals}"
    
    print(f"\n{'='*80}")
    print(f"📊 Kết quả: {status}")
    print(f"📈 Số bước: {len(applied_rules)}")
    print(f"📋 Luật áp dụng: {applied_rules}")
    print(f"{'='*80}\n")
    
    return {
        'success': success,
        'explanation': explanation_steps,
        'working_memory': list(working_memory),
        'applied_rules': applied_rules,
        'status': status,
        'goals': goals,
        'initial_facts': initial_facts,
        'method': 'Forward Chaining'
    }
