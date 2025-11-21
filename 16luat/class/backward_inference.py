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

def _find_optimal_vet(
    full_vet: List[str],
    rules_dict: Dict[str, Dict],
    initial_facts: Set[str],
    goals: Set[str]
) -> Tuple[List[str], Dict]:
    forward_vet = full_vet.copy()
    forward_vet.reverse()
    needed_facts = goals.copy()
    optimal_vet: List[str] = []
    usage_info: Dict[str, Dict] = {}
    for rule_id in reversed(forward_vet):
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

# === Hàm đệ quy: lưu lại chuỗi luật duy nhất đúng ===
def _backward_chain_get_vet(
    goals: Set[str], known: Set[str], rules_dict: Dict[str, Dict],
    vet_full: List[str], used_rule_id: Set[str],
    max_depth=50
) -> bool:
    if goals.issubset(known):
        return True
    if max_depth <= 0:
        return False
    # Tìm goal tiếp cần chứng minh
    for g in sorted(goals):
        if g not in known:
            fact_to_prove = g
            break
    else:
        return goals.issubset(known) # redundant but safe
    fact_type = 'angle' if _is_angle_variable(fact_to_prove) else 'edge'
    applicable_rules = []
    for rule_id, rule_data in rules_dict.items():
        if rule_data['conclusion'] == fact_to_prove and rule_id not in used_rule_id:
            if rule_data['conclusion_type'] == fact_type:
                applicable_rules.append((rule_id, len(rule_data['premise']), 0))
            else:
                applicable_rules.append((rule_id, len(rule_data['premise']), 1))
    if not applicable_rules:
        return False
    applicable_rules.sort(
        key=lambda x: (x[2], x[1], int(x[0]) if x[0].isdigit() else x[0])
    )
    for rule_id, _, _ in applicable_rules:
        rule = rules_dict[rule_id]
        premise = rule['premise']
        new_goals = set(goals)
        if fact_to_prove in new_goals:
            new_goals.remove(fact_to_prove)
        for p in premise:
            if p not in known:
                new_goals.add(p)
        vet_full.append(rule_id)
        used_rule_id.add(rule_id)
        if _backward_chain_get_vet(new_goals, known, rules_dict, vet_full, used_rule_id, max_depth-1):
            return True
        vet_full.pop()
        used_rule_id.remove(rule_id)
    return False

def backward_inference_detailed(initial_facts: List[str], goals: List[str], rules_list: List[Dict]
) -> Tuple[bool, List[Dict], List[str], List[str], List[Dict], str]:
    rules_dict = _parse_rules(rules_list)
    if not rules_dict:
        return False, [], [], [], [], "Khong co luat nao trong he thong"
    GT: Set[str] = set([x.strip() for x in initial_facts if str(x).strip()])
    KL: Set[str] = set([x.strip() for x in goals if str(x).strip()])
    process_table: List[Dict] = [{
        'step': 0,
        'rule': '-',
        'current_goals': sorted(KL),
        'GT': sorted(GT),
        'VET': [],
        'explanation': f'Khoi tao: KL = {{{", ".join(sorted(KL))}}}, GT = {{{", ".join(sorted(GT))}}}',
        'note': 'Bat dau qua trinh suy dien lui'
    }]
    VET_FULL: List[str] = []
    used_rule_id = set()
    success = _backward_chain_get_vet(KL.copy(), GT, rules_dict, VET_FULL, used_rule_id)
    if not success:
        conclusion = f"THAT BAI! Khong the chung minh {KL} tu {GT}"
        process_table.append({
            'step': 1,
            'rule': 'FAIL',
            'current_goals': sorted(KL),
            'GT': sorted(GT),
            'VET': [],
            'explanation': conclusion,
            'note': 'Khong tim duoc chuoi luat thoa man'
        })
        return False, process_table, VET_FULL, [], [], conclusion
    # Build clean table (chỉ các bước thật sự theo chuỗi đúng)
    step = 1
    current_goals = KL.copy()
    for rule_id in VET_FULL:
        rule = rules_dict[rule_id]
        premise = rule['premise']
        fact_to_prove = rule['conclusion']
        fact_type = 'angle' if _is_angle_variable(fact_to_prove) else 'edge'
        if fact_to_prove in current_goals:
            current_goals.remove(fact_to_prove)
        for p in premise:
            if p not in GT:
                current_goals.add(p)
        premise_str = ', '.join(premise)
        process_table.append({
            'step': step,
            'rule': f'r{rule_id}',
            'current_goals': sorted(current_goals) if current_goals else ['∅'],
            'GT': sorted(GT),
            'VET': VET_FULL[:step],
            'explanation': f'Ap dung r{rule_id}: {{{premise_str}}} → {fact_to_prove} (loai: {fact_type})',
            'note': rule['note']
        })
        step += 1
    process_table.append({
        'step': step,
        'rule': 'DONE',
        'current_goals': sorted(KL),
        'GT': sorted(GT),
        'VET': VET_FULL.copy(),
        'explanation': f'THANH CONG! Tat ca muc tieu {{{", ".join(sorted(KL))}}} deu co trong GT',
        'note': 'Da chung minh thanh cong!'
    })
    VET_OPTIMAL, usage_info = _find_optimal_vet(VET_FULL, rules_dict, GT, KL)
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
    conclusion = f"""
=== KET LUAN SUY DIEN LUI ===

THANH CONG! Da chung minh duoc {{{', '.join(sorted(KL))}}} tu {{{', '.join(sorted(GT))}}}

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

def backward_inference_with_trace(initial_facts: List[str], goals: List[str], rules_list: List[Dict]) -> Tuple[bool, List[Dict], List[Dict]]:
    # Xây dựng trace chỉ theo chuỗi thành công
    rules_dict = _parse_rules(rules_list)
    if not rules_dict:
        return False, [], []
    GT: Set[str] = set([x.strip() for x in initial_facts if str(x).strip()])
    KL: Set[str] = set([x.strip() for x in goals if str(x).strip()])
    trace: List[Dict] = [{'set': sorted(KL), 'rule': None, 'action': 'START', 'note': ''}]
    applied_rules: List[Dict]=[]
    VET_FULL: List[str] = []
    used_rule_id = set()
    success = _backward_chain_get_vet(KL.copy(), GT, rules_dict, VET_FULL, used_rule_id)
    if not success:
        return False, trace, applied_rules
    current_set = KL.copy()
    for rule_id in VET_FULL:
        rule = rules_dict[rule_id]
        goal = rule['conclusion']
        premise = rule['premise']
        rule_note = rule['note']
        if goal in current_set:
            current_set.remove(goal)
        for p in premise:
            if p not in GT:
                current_set.add(p)
        trace.append({
            'set': sorted(current_set) if current_set else ['∅'],
            'rule': f'r{rule_id}',
            'action': f"Replace {goal} with {premise}",
            'note': rule_note
        })
        applied_rules.append({
            'rule': rule_id,
            'premise': premise,
            'conclusion': goal,
            'note': rule_note
        })
    return True, trace, applied_rules
