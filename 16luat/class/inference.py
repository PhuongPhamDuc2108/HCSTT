# inference.py
# Forward chaining với VET đầy đủ và VET tối ưu

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

def _find_optimal_vet_forward(full_vet: List[str], rules_dict: Dict[str, Dict], 
                             initial_facts: Set[str], goals: Set[str]) -> Tuple[List[str], Dict]:
    """
    Tìm VET tối ưu cho forward chaining
    Chỉ giữ các luật cần thiết để đạt được goals
    """
    needed_facts = goals.copy()
    optimal_vet = []
    usage_info = {}
    
    # Duyệt ngược VET
    for rule_id in reversed(full_vet):
        rule = rules_dict[rule_id]
        conclusion = rule['conclusion']
        
        if conclusion in needed_facts:
            optimal_vet.insert(0, rule_id)
            needed_facts.remove(conclusion)
            
            for p in rule['premise']:
                if p not in initial_facts:
                    needed_facts.add(p)
            
            usage_info[rule_id] = {
                'needed_for': conclusion,
                'premise': rule['premise'],
                'note': rule['note']
            }
    
    return optimal_vet, usage_info

def forward_inference_detailed(initial_facts: List[str],
                               goals: List[str],
                               rules_list: List[Dict]) -> Tuple[bool, List[Dict], List[str], List[str], List[Dict], str]:
    """
    Forward chaining với VET đầy đủ và VET tối ưu
    
    Returns:
        success: bool
        process_table: Bảng quá trình
        full_vet: VET đầy đủ
        optimal_vet: VET tối ưu
        explanation: Giải thích
        conclusion: Kết luận cuối cùng
    """
    rules_dict = _parse_rules(rules_list)
    if not rules_dict:
        return False, [], [], [], [], "Khong co luat nao"
    
    THOA: Set[str] = set([x.strip() for x in initial_facts if str(x).strip()])
    TG: Set[str] = set([x.strip() for x in goals if str(x).strip()])
    
    R = set(rules_dict.keys())
    VET_FULL: List[str] = []
    process_table: List[Dict] = []
    
    process_table.append({
        'step': 0,
        'rule': '-',
        'THOA': sorted(THOA),
        'TG': sorted(TG),
        'R': sorted(R),
        'VET': [],
        'note': 'Khoi tao'
    })
    
    step = 1
    MAX_STEPS = 100
    
    while step <= MAX_STEPS:
        if TG.issubset(THOA):
            process_table.append({
                'step': step,
                'rule': 'DONE',
                'THOA': sorted(THOA),
                'TG': sorted(TG),
                'R': sorted(R),
                'VET': VET_FULL.copy(),
                'note': 'THANH CONG!'
            })
            break
        
        applied_rule = None
        for rule_id in sorted(R, key=lambda x: (len(rules_dict[x]['premise']), int(x) if x.isdigit() else x)):
            premise_set = set(rules_dict[rule_id]['premise'])
            if premise_set.issubset(THOA):
                conclusion = rules_dict[rule_id]['conclusion']
                if conclusion not in THOA:
                    applied_rule = rule_id
                    break
        
        if applied_rule is None:
            conclusion = "THAT BAI! Khong tim thay luat ap dung duoc"
            process_table.append({
                'step': step,
                'rule': 'FAIL',
                'THOA': sorted(THOA),
                'TG': sorted(TG),
                'R': sorted(R),
                'VET': VET_FULL.copy(),
                'note': conclusion
            })
            return False, process_table, VET_FULL, [], [], conclusion
        
        conclusion = rules_dict[applied_rule]['conclusion']
        rule_note = rules_dict[applied_rule]['note']
        THOA.add(conclusion)
        R.discard(applied_rule)
        VET_FULL.append(applied_rule)
        
        process_table.append({
            'step': step,
            'rule': f'r{applied_rule}',
            'THOA': sorted(THOA),
            'TG': sorted(TG),
            'R': sorted(R),
            'VET': VET_FULL.copy(),
            'note': rule_note
        })
        
        step += 1
    
    success = TG.issubset(THOA)
    
    if not success:
        conclusion = f"THAT BAI! Khong the dat duoc {TG} tu {initial_facts}"
        return False, process_table, VET_FULL, [], [], conclusion
    
    # Tìm VET tối ưu
    VET_OPTIMAL, usage_info = _find_optimal_vet_forward(VET_FULL, rules_dict, set(initial_facts), TG)
    
    explanation: List[Dict] = []
    for i, r in enumerate(VET_OPTIMAL, start=1):
        explanation.append({
            'step': i,
            'rule': r,
            'premise': rules_dict[r]['premise'],
            'conclusion': rules_dict[r]['conclusion'],
            'conclusion_type': rules_dict[r]['conclusion_type'],
            'note': rules_dict[r]['note']
        })
    
    # Kết luận
    conclusion = f"""
=== KET LUAN SUY DIEN TIEN ===

THANH CONG! Da dat duoc {{{', '.join(sorted(TG))}}} tu {{{', '.join(sorted(initial_facts))}}}

VET DAY DU (tat ca luat da dung): {' -> '.join(['r' + r for r in VET_FULL])}
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
