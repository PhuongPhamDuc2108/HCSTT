# backward_inference.py
# Backward chaining với VET đầy đủ và VET tối ưu

from typing import List, Dict, Tuple, Set

SEPARATORS = ['∧', '^', '&', 'AND', 'and', '&&', ' AND ', ' and ', ';', '|']

EDGE_VARS = ['a', 'b', 'c', 'ma', 'mb', 'mc', 'ha', 'hb', 'hc', 'r', 'R', 'p', 'P', 'S']
ANGLE_VARS = ['A', 'B', 'C']

def _is_edge_variable(var: str) -> bool:
    return var in EDGE_VARS or var.islower()

def _is_angle_variable(var: str) -> bool:
    return var in ANGLE_VARS or (len(var) == 1 and var.isupper())

def _normalize_left(left_expr: str) -> List[str]:
    expr = str(left_expr)
    for sep in SEPARATORS:
        expr = expr.replace(sep, ',')
    parts = [p.strip() for p in expr.split(',') if p.strip()]
    return parts

def _parse_rules(rules_list: List[Dict]) -> Dict[str, Dict]:
    rules_dict: Dict[str, Dict] = {}
    for item in rules_list:
        rule_id = str(item.get('id', '')).strip()
        left_raw = str(item.get('veTrai', item.get('Ve Trai', ''))).strip()
        right_raw = str(item.get('vePhai', item.get('Ve Phai', ''))).strip()
        note = str(item.get('note', item.get('Note', ''))).strip()
        
        if not rule_id or not right_raw:
            continue
        
        premise = _normalize_left(left_raw)
        conclusion = right_raw.strip()
        
        if not premise or not conclusion:
            continue
        
        conclusion_type = 'angle' if _is_angle_variable(conclusion) else 'edge'
        
        rules_dict[rule_id] = {
            'premise': premise,
            'conclusion': conclusion,
            'conclusion_type': conclusion_type,
            'note': note if note else f'Tinh {conclusion} tu {", ".join(premise)}'
        }
    
    return rules_dict

def _find_optimal_vet(full_vet: List[str], rules_dict: Dict[str, Dict], 
                     initial_facts: Set[str], goals: Set[str]) -> Tuple[List[str], Dict]:
    """
    Tìm VET tối ưu từ VET đầy đủ
    
    Thuật toán:
    1. Đảo ngược full_vet để có thứ tự forward (GT → KL)
    2. Simulate lại quá trình suy diễn, chỉ giữ các luật thực sự cần thiết
    3. Một luật được coi là cần thiết nếu:
       - Conclusion của nó được dùng để chứng minh goal hoặc
       - Conclusion của nó được dùng làm premise cho luật khác trong vết tối ưu
    
    Returns:
        optimal_vet: List các rule_id tối ưu
        usage_info: Dict chứa thông tin sử dụng của mỗi luật
    """
    # Đảo ngược để có forward order
    forward_vet = full_vet.copy()
    forward_vet.reverse()
    
    # Track các fact cần thiết
    needed_facts = goals.copy()
    optimal_vet = []
    usage_info = {}
    
    # Duyệt ngược từ cuối VET về đầu
    for rule_id in reversed(forward_vet):
        rule = rules_dict[rule_id]
        conclusion = rule['conclusion']
        
        # Kiểm tra conclusion có cần thiết không
        if conclusion in needed_facts:
            optimal_vet.insert(0, rule_id)
            needed_facts.remove(conclusion)
            
            # Thêm premise vào needed_facts
            for p in rule['premise']:
                if p not in initial_facts:
                    needed_facts.add(p)
            
            usage_info[rule_id] = {
                'needed_for': conclusion,
                'premise': rule['premise'],
                'note': rule['note']
            }
    
    return optimal_vet, usage_info

def backward_inference_detailed(initial_facts: List[str],
                                goals: List[str],
                                rules_list: List[Dict]) -> Tuple[bool, List[Dict], List[str], List[str], List[Dict], str]:
    """
    Backward chaining với VET đầy đủ và VET tối ưu
    
    Returns:
        success: bool
        process_table: Bảng quá trình
        full_vet: VET đầy đủ (tất cả luật đã dùng)
        optimal_vet: VET tối ưu (chỉ luật cần thiết)
        explanation: Giải thích chi tiết
        conclusion: Kết luận cuối cùng (text)
    """
    rules_dict = _parse_rules(rules_list)
    if not rules_dict:
        return False, [], [], [], [], "Khong co luat nao trong he thong"
    
    GT: Set[str] = set([x.strip() for x in initial_facts if str(x).strip()])
    KL: Set[str] = set([x.strip() for x in goals if str(x).strip()])
    
    current_goals = KL.copy()
    VET_FULL: List[str] = []
    process_table: List[Dict] = []
    
    process_table.append({
        'step': 0,
        'rule': '-',
        'current_goals': sorted(current_goals),
        'GT': sorted(GT),
        'VET': [],
        'explanation': f'Khoi tao: KL = {{{", ".join(sorted(KL))}}}, GT = {{{", ".join(sorted(GT))}}}',
        'note': 'Bat dau qua trinh suy dien lui'
    })
    
    step = 1
    MAX_STEPS = 100
    
    while step <= MAX_STEPS:
        if current_goals.issubset(GT):
            process_table.append({
                'step': step,
                'rule': 'DONE',
                'current_goals': sorted(current_goals),
                'GT': sorted(GT),
                'VET': VET_FULL.copy(),
                'explanation': f'THANH CONG! Tat ca muc tieu {{{", ".join(sorted(current_goals))}}} deu co trong GT',
                'note': 'Da chung minh thanh cong!'
            })
            break
        
        fact_to_prove = None
        for g in sorted(current_goals):
            if g not in GT:
                fact_to_prove = g
                break
        
        if fact_to_prove is None:
            break
        
        fact_type = 'angle' if _is_angle_variable(fact_to_prove) else 'edge'
        
        applicable_rules = []
        for rule_id, rule_data in rules_dict.items():
            if rule_data['conclusion'] == fact_to_prove and rule_id not in VET_FULL:
                if rule_data['conclusion_type'] == fact_type:
                    applicable_rules.append((rule_id, len(rule_data['premise']), 0))
                else:
                    applicable_rules.append((rule_id, len(rule_data['premise']), 1))
        
        if not applicable_rules:
            conclusion = f"THAT BAI! Khong tim thay luat de chung minh '{fact_to_prove}' (loai: {fact_type})"
            process_table.append({
                'step': step,
                'rule': 'FAIL',
                'current_goals': sorted(current_goals),
                'GT': sorted(GT),
                'VET': VET_FULL.copy(),
                'explanation': conclusion,
                'note': f'Khong co luat nao co ve phai = "{fact_to_prove}"'
            })
            return False, process_table, VET_FULL, [], [], conclusion
        
        applicable_rules.sort(key=lambda x: (x[2], x[1], int(x[0]) if x[0].isdigit() else x[0]))
        found_rule = applicable_rules[0][0]
        
        premise = rules_dict[found_rule]['premise']
        rule_note = rules_dict[found_rule]['note']
        
        current_goals.remove(fact_to_prove)
        for p in premise:
            if p not in GT:
                current_goals.add(p)
        
        VET_FULL.append(found_rule)
        
        premise_str = ', '.join(premise)
        process_table.append({
            'step': step,
            'rule': f'r{found_rule}',
            'current_goals': sorted(current_goals),
            'GT': sorted(GT),
            'VET': VET_FULL.copy(),
            'explanation': f'Ap dung r{found_rule}: {{{premise_str}}} → {fact_to_prove} (loai: {fact_type})',
            'note': rule_note
        })
        
        step += 1
    
    success = current_goals.issubset(GT)
    
    if not success:
        conclusion = f"THAT BAI! Khong the chung minh {KL} tu {GT}"
        return False, process_table, VET_FULL, [], [], conclusion
    
    # Tìm VET tối ưu
    VET_OPTIMAL, usage_info = _find_optimal_vet(VET_FULL, rules_dict, GT, KL)
    
    # Tạo explanation cho VET tối ưu
    explanation: List[Dict] = []
    for i, r in enumerate(VET_OPTIMAL, start=1):
        explanation.append({
            'step': i,
            'rule': r,
            'premise': rules_dict[r]['premise'],
            'conclusion': rules_dict[r]['conclusion'],
            'conclusion_type': rules_dict[r]['conclusion_type'],
            'note': rules_dict[r]['note'],
            'needed_for': usage_info.get(r, {}).get('needed_for', '')
        })
    
    # Tạo kết luận cuối cùng
    conclusion = f"""
=== KET LUAN SUY DIEN LUI ===

THANH CONG! Da chung minh duoc {{{', '.join(sorted(KL))}}} tu {{{', '.join(sorted(GT))}}}

VET DAY DU (tat ca luat da dung): {' -> '.join(['r' + r for r in VET_FULL[::-1]])}
So luong luat su dung: {len(VET_FULL)}

VET TOI UU (chi luat can thiet): {' -> '.join(['r' + r for r in VET_OPTIMAL])}
So luong luat toi uu: {len(VET_OPTIMAL)}

CAC BUOC TINH TOAN (theo VET toi uu):
"""
    
    for i, r in enumerate(VET_OPTIMAL, start=1):
        rule = rules_dict[r]
        conclusion += f"\nBuoc {i}: Ap dung luat r{r}\n"
        conclusion += f"  - Tien de: {{{', '.join(rule['premise'])}}}\n"
        conclusion += f"  - Ket luan: {rule['conclusion']}\n"
        conclusion += f"  - Cong thuc: {rule['note']}\n"
    
    if len(VET_FULL) > len(VET_OPTIMAL):
        removed = set(VET_FULL) - set(VET_OPTIMAL)
        conclusion += f"\nCac luat bi loai bo (khong can thiet): {', '.join(['r' + r for r in removed])}"
    
    return success, process_table, VET_FULL, VET_OPTIMAL, explanation, conclusion


def backward_inference_with_trace(initial_facts: List[str],
                                  goals: List[str],
                                  rules_list: List[Dict]) -> Tuple[bool, List[Dict], List[Dict]]:
    """Backward trace với phân biệt cạnh/góc"""
    rules_dict = _parse_rules(rules_list)
    if not rules_dict:
        return False, [], []
    
    GT: Set[str] = set([x.strip() for x in initial_facts if str(x).strip()])
    KL: Set[str] = set([x.strip() for x in goals if str(x).strip()])
    
    trace: List[Dict] = [{'set': sorted(KL), 'rule': None, 'action': 'START', 'note': ''}]
    current_goals = KL.copy()
    applied_rules: List[Dict] = []
    
    MAX_STEPS = 100
    step = 0
    
    while not current_goals.issubset(GT) and step < MAX_STEPS:
        goal_to_prove = None
        for g in sorted(current_goals):
            if g not in GT:
                goal_to_prove = g
                break
        
        if goal_to_prove is None:
            break
        
        fact_type = 'angle' if _is_angle_variable(goal_to_prove) else 'edge'
        
        found_rule = None
        best_priority = 999
        for rule_id, rule_data in rules_dict.items():
            if rule_data['conclusion'] == goal_to_prove:
                priority = 0 if rule_data['conclusion_type'] == fact_type else 1
                if priority < best_priority:
                    best_priority = priority
                    found_rule = rule_id
        
        if found_rule is None:
            return False, trace, applied_rules
        
        premise = rules_dict[found_rule]['premise']
        rule_note = rules_dict[found_rule]['note']
        
        current_goals.remove(goal_to_prove)
        for p in premise:
            if p not in GT:
                current_goals.add(p)
        
        trace.append({
            'set': sorted(current_goals) if current_goals else ['∅'],
            'rule': f'r{found_rule}',
            'action': f'Replace {goal_to_prove} with {premise}',
            'note': rule_note
        })
        
        applied_rules.append({
            'rule': found_rule,
            'premise': premise,
            'conclusion': goal_to_prove,
            'note': rule_note
        })
        
        step += 1
    
    success = current_goals.issubset(GT)
    return success, trace, applied_rules
