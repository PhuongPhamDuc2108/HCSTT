import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import io
import base64
from collections import defaultdict
import numpy as np


class FPG:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.rules = []
        self.facts = set()
        self.conclusions = set()
        self.initial_facts = set()
        self.target_goals = set()
        
    def add_rule(self, rule_id, antecedents, consequent):
        self.rules.append({'id': rule_id, 'antecedents': antecedents, 'consequent': consequent})
        for ant in antecedents:
            self.facts.add(ant)
        self.conclusions.add(consequent)
        
    def load_from_data(self, data):
        for item in data:
            rule_id = str(item['id'])
            ve_trai = str(item['veTrai'])
            for sep in ['∧', '^', '&', 'AND', 'and', '&&', ' AND ', ' and ']:
                ve_trai = ve_trai.replace(sep, ',')
            antecedents = [x.strip() for x in ve_trai.split(',') if x.strip()]
            consequent = str(item['vePhai']).strip()
            if antecedents and consequent:
                self.add_rule(rule_id, antecedents, consequent)

    def set_initial_and_target(self, initial_facts, target_goals):
        self.initial_facts = set(initial_facts) if initial_facts else set()
        self.target_goals = set(target_goals) if target_goals else set()
    
    def build_graph(self):
        """Chi fact/goal nodes, edges truc tiep tu fact -> goal"""
        all_items = self.facts | self.conclusions
        for item in all_items:
            self.graph.add_node(item, node_type='fact', label=item)
        
        # Noi fact -> goal voi rule label
        for rule in self.rules:
            rule_label = f"r{rule['id']}"
            consequent = rule['consequent']
            for ant in rule['antecedents']:
                if ant in self.graph.nodes and consequent in self.graph.nodes:
                    self.graph.add_edge(ant, consequent, rule=rule_label)

    def visualize_to_base64(self, figsize=(26, 18), layout_method='improved_hierarchical'):
        """
        Ve FPG: GIU NGUYEN KICH THUOC ANH, VONG TRON TO, DAY NODES RA CANH
        """
        fig = plt.figure(figsize=figsize, facecolor='white')
        ax = fig.add_subplot(111)
        
        if self.graph.number_of_nodes() == 0:
            ax.text(0.5, 0.5, 'Chua co du lieu FPG.\nVui long tai file luat va nhap GT, KL.',
                   ha='center', va='center', fontsize=14, color='red')
            ax.axis('off')
            plt.tight_layout()
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=120, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            return image_base64

        # CHON LAYOUT METHOD
        if layout_method == 'spring':
            pos = self._get_spring_layout()
        elif layout_method == 'kamada_kawai':
            pos = self._get_kamada_kawai_layout()
        elif layout_method == 'circular':
            pos = self._get_circular_layout()
        elif layout_method == 'shell':
            pos = self._get_shell_layout()
        else:  # improved_hierarchical (mac dinh)
            pos = self._get_improved_hierarchical_layout()
        
        # Nhom edges theo (source, target)
        edge_groups = defaultdict(list)
        for (source, target, data) in self.graph.edges(data=True):
            edge_key = (source, target)
            rule_label = data.get('rule', '')
            edge_groups[edge_key].append(rule_label)
        
        # Ve edges voi OFFSET de tach nhau
        for (source, target), rule_labels in edge_groups.items():
            x1, y1 = pos[source]
            x2, y2 = pos[target]
            
            num_edges = len(rule_labels)
            
            # Tinh vector vuong goc de offset
            dx = x2 - x1
            dy = y2 - y1
            length = np.sqrt(dx**2 + dy**2)
            
            if length > 0.01:
                perp_x = -dy / length
                perp_y = dx / length
            else:
                perp_x, perp_y = 0, 1
            
            # Ve TUNG EDGE voi offset rieng
            for i, rule_label in enumerate(rule_labels):
                # Tinh offset: cac duong tach nhau
                if num_edges == 1:
                    offset = 0
                else:
                    offset = (i - (num_edges - 1) / 2) * 0.4
                
                # Vi tri start va end co offset
                start_x = x1 + perp_x * offset
                start_y = y1 + perp_y * offset
                end_x = x2 + perp_x * offset
                end_y = y2 + perp_y * offset
                
                # ========== VE DUONG THANG ==========
                line = ax.plot([start_x, end_x], [start_y, end_y],
                              color='dimgray', linewidth=2.0, alpha=0.65, 
                              solid_capstyle='round', zorder=1)[0]
                
                # ========== VE MUI TEN (HUONG TU FACT -> GOAL) ==========
                if length > 0.01:
                    dir_x = end_x - start_x
                    dir_y = end_y - start_y
                    dir_length = np.sqrt(dir_x**2 + dir_y**2)
                    
                    if dir_length > 0.01:
                        norm_dx = dir_x / dir_length
                        norm_dy = dir_y / dir_length
                        
                        arrow_start_frac = 0.75
                        arrow_sx = start_x + dir_x * arrow_start_frac
                        arrow_sy = start_y + dir_y * arrow_start_frac
                        
                        ax.arrow(arrow_sx, arrow_sy,
                                norm_dx * 0.35, norm_dy * 0.35,
                                head_width=0.3, head_length=0.25,
                                fc='black', ec='black',
                                linewidth=0,
                                zorder=2, alpha=0.9)
                
                # ========== VE RULE LABEL TREN CANH ==========
                mid_x = (start_x + end_x) / 2
                mid_y = (start_y + end_y) / 2
                
                label_offset = 0.6
                label_x = mid_x + perp_x * label_offset
                label_y = mid_y + perp_y * label_offset
                
                ax.text(label_x, label_y, rule_label,
                       fontsize=10, ha='center', va='center',
                       weight='bold', color='black',
                       bbox=dict(boxstyle='round,pad=0.35',
                                facecolor='gold',
                                edgecolor='darkorange',
                                linewidth=1.8,
                                alpha=0.95),
                       zorder=10)
        
        # ========== VE FACT/GOAL NODES (VONG TRON TO, CHU NHO) ==========
        for node in self.graph.nodes():
            x, y = pos[node]
            
            is_GT = node in self.initial_facts
            is_KL = node in self.target_goals
            
            radius = 1.2  # TANG MANH: 0.5 -> 1.2 (TANG 140%)
            
            if is_GT:
                circle = plt.Circle((x, y), radius, facecolor='white',
                                   edgecolor='black', linewidth=3.5, zorder=5)
                ax.add_patch(circle)
                hatch_circle = plt.Circle((x, y), radius, facecolor='none',
                                         edgecolor='black', linewidth=3.5,
                                         hatch='---', zorder=6)
                ax.add_patch(hatch_circle)
            elif is_KL:
                circle = plt.Circle((x, y), radius, facecolor='white',
                                   edgecolor='black', linewidth=3.5, zorder=5)
                ax.add_patch(circle)
                hatch_circle = plt.Circle((x, y), radius, facecolor='none',
                                         edgecolor='black', linewidth=3.5,
                                         hatch='///', zorder=6)
                ax.add_patch(hatch_circle)
            else:
                circle = plt.Circle((x, y), radius, facecolor='white',
                                   edgecolor='black', linewidth=3.5, zorder=5)
                ax.add_patch(circle)
            
            # Label node (GIU NGUYEN FONT SIZE)
            ax.text(x, y, node, ha='center', va='center',
                   fontsize=14, fontweight='bold', color='black', zorder=7)
        
        # ========== LEGEND ==========
        legend_elements = [
            mpatches.Circle((0, 0), 0.35, facecolor='white', edgecolor='black',
                           hatch='---', linewidth=2.5, label='Fact (f in GT)'),
            mpatches.Circle((0, 0), 0.35, facecolor='white', edgecolor='black',
                           hatch='///', linewidth=2.5, label='Goal (f in KL)')
        ]
        
        ax.legend(handles=legend_elements, loc='lower right',
                 fontsize=13, framealpha=0.98, edgecolor='black',
                 fancybox=False)
        
        # ========== TITLE & LAYOUT ==========
        ax.set_title('Bieu do FPG (Forward Production Graph)\nFact -> Goal voi Rule labels tren canh',
                    fontsize=17, fontweight='bold', pad=25)
        ax.axis('off')
        ax.set_aspect('equal')
        
        # Set limits voi margin RAT NHO de day nodes gan canh
        if pos:
            x_values = [pos[n][0] for n in pos]
            y_values = [pos[n][1] for n in pos]
            margin = 1.5  # GIAM MANH: 4.0 -> 1.5 de day ra canh
            ax.set_xlim(min(x_values) - margin, max(x_values) + margin)
            ax.set_ylim(min(y_values) - margin, max(y_values) + margin)
        
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=120, bbox_inches='tight', facecolor='white')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return image_base64
    
    def _get_improved_hierarchical_layout(self):
        """
        Layout hierarchical DAY MANH NODES RA CANH, TRANH TRUNG TAM
        """
        levels = {}
        
        # Tinh level cho moi node
        pure_facts = self.facts - self.conclusions
        for fact in pure_facts:
            levels[fact] = 0
        
        # Tinh level cho nodes khac (BFS-like)
        for iteration in range(100):
            changed = False
            for rule in self.rules:
                consequent = rule['consequent']
                ant_levels = [levels[ant] for ant in rule['antecedents'] if ant in levels]
                
                if ant_levels:
                    new_level = max(ant_levels) + 1
                    if consequent not in levels or levels[consequent] < new_level:
                        levels[consequent] = new_level
                        changed = True
            
            if not changed:
                break
        
        # Nhom nodes theo level
        level_groups = defaultdict(list)
        for node, level in levels.items():
            level_groups[level].append(node)
        
        max_level = max(levels.values()) if levels else 0
        
        # Tao positions - DAY RA CANH, TANG SCALE
        pos = {}
        
        # TANG SCALE DE TRAI RA
        horizontal_scale = 28.0  # Tang manh
        vertical_scale = 22.0    # Tang manh
        
        for level in sorted(level_groups.keys()):
            nodes = sorted(level_groups[level])
            num_nodes = len(nodes)
            
            # Vi tri X: trai deu theo level (theo chieu ngang)
            x = level * horizontal_scale
            
            # Vi tri Y: DAY MANH RA TREN/DUOI
            if num_nodes == 1:
                y_positions = [0]
            else:
                # TANG SPAN RAT LON de day nodes ra tren/duoi
                y_span = num_nodes * vertical_scale * 1.6  # HE SO CAO
                y_positions = np.linspace(-y_span/2, y_span/2, num_nodes)
            
            for i, node in enumerate(nodes):
                pos[node] = (x, y_positions[i])
        
        # Optimize positions de giam crossing
        pos = self._optimize_crossings(pos, level_groups)
        
        # DAY MANH RA CANH BANG CACH SCALE VA PUSH
        pos = self._push_to_edges(pos, push_factor=1.8)
        
        return pos
    
    def _push_to_edges(self, pos, push_factor=1.8):
        """
        DAY MANH nodes ra xa tam (0,0) de gan canh NHAT
        """
        if not pos:
            return pos
        
        pushed_pos = {}
        
        # Tim tam cua graph
        x_values = [x for x, y in pos.values()]
        y_values = [y for x, y in pos.values()]
        center_x = np.mean(x_values)
        center_y = np.mean(y_values)
        
        # Day moi node ra xa tam VOI HE SO LON
        for node, (x, y) in pos.items():
            # Vector tu tam den node
            dx = x - center_x
            dy = y - center_y
            
            # TANG KHOANG CACH tu tam
            new_x = center_x + dx * push_factor
            new_y = center_y + dy * push_factor
            
            pushed_pos[node] = (new_x, new_y)
        
        return pushed_pos
    
    def _optimize_crossings(self, pos, level_groups):
        """
        Heuristic de giam edge crossings
        """
        for level in sorted(level_groups.keys())[1:]:
            nodes = level_groups[level]
            
            # Tinh barycenter cho moi node
            barycenters = {}
            for node in nodes:
                predecessors = list(self.graph.predecessors(node))
                if predecessors:
                    avg_y = np.mean([pos[pred][1] for pred in predecessors if pred in pos])
                    barycenters[node] = avg_y
                else:
                    barycenters[node] = pos[node][1]
            
            # Sap xep nodes theo barycenter
            sorted_nodes = sorted(nodes, key=lambda n: barycenters[n])
            
            # Cap nhat lai y-positions
            num_nodes = len(sorted_nodes)
            vertical_scale = 22.0
            y_span = num_nodes * vertical_scale * 1.6
            
            if num_nodes == 1:
                y_positions = [0]
            else:
                y_positions = np.linspace(-y_span/2, y_span/2, num_nodes)
            
            for i, node in enumerate(sorted_nodes):
                x_pos = pos[node][0]
                pos[node] = (x_pos, y_positions[i])
        
        return pos
    
    def _get_spring_layout(self):
        """Spring layout DAY RA CANH"""
        pos = nx.spring_layout(
            self.graph,
            k=9.0,
            iterations=150,
            scale=40.0,
            seed=42
        )
        return pos
    
    def _get_kamada_kawai_layout(self):
        """Kamada-Kawai layout DAY RA CANH"""
        try:
            pos = nx.kamada_kawai_layout(
                self.graph,
                scale=40.0
            )
        except:
            pos = self._get_spring_layout()
        return pos
    
    def _get_circular_layout(self):
        """Circular layout DAY RA CANH"""
        pos = nx.circular_layout(
            self.graph,
            scale=40.0
        )
        return pos
    
    def _get_shell_layout(self):
        """Shell layout DAY RA CANH"""
        levels = {}
        pure_facts = self.facts - self.conclusions
        for fact in pure_facts:
            levels[fact] = 0
        
        for iteration in range(100):
            changed = False
            for rule in self.rules:
                consequent = rule['consequent']
                ant_levels = [levels[ant] for ant in rule['antecedents'] if ant in levels]
                
                if ant_levels:
                    new_level = max(ant_levels) + 1
                    if consequent not in levels or levels[consequent] < new_level:
                        levels[consequent] = new_level
                        changed = True
            
            if not changed:
                break
        
        level_groups = defaultdict(list)
        for node, level in levels.items():
            level_groups[level].append(node)
        
        shells = [level_groups[level] for level in sorted(level_groups.keys())]
        
        pos = nx.shell_layout(
            self.graph,
            nlist=shells,
            scale=40.0
        )
        return pos
