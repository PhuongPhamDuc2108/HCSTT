import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import io
import base64
from collections import defaultdict
import numpy as np

class RPG:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.rules = []
        self.initial_facts = set()
        self.target_goals = set()
        
    def add_rule(self, rule_id, antecedents, consequent):
        """Them luat vao danh sach"""
        self.rules.append({
            'id': rule_id, 
            'antecedents': antecedents, 
            'consequent': consequent
        })
        
    def load_from_data(self, data):
        """Load du lieu tu JSON"""
        for item in data:
            rule_id = str(item['id'])
            ve_trai = str(item['veTrai'])
            
            # Xu ly cac dang ky hieu AND
            for sep in ['∧', '^', '&', 'AND', 'and', '&&', ' AND ', ' and ']:
                ve_trai = ve_trai.replace(sep, ',')
            
            antecedents = [x.strip() for x in ve_trai.split(',') if x.strip()]
            consequent = str(item['vePhai']).strip()
            
            if antecedents and consequent:
                self.add_rule(rule_id, antecedents, consequent)
    
    def set_initial_and_target(self, initial_facts, target_goals):
        """Set gia tri GT va KL"""
        self.initial_facts = set(initial_facts) if initial_facts else set()
        self.target_goals = set(target_goals) if target_goals else set()
    
    def build_graph(self):
        """
        Xay dung RPG: Nodes la cac LUAT (rules)
        Dinh nghia: Mot luat r_i la lien he truoc cua luat r_j (r_i -> r_j)
        khi va chi khi ton tai su kien f thoa man:
        r_i: left -> f
        r_j: ... f ... -> q
        """
        self.graph.clear()
        
        # Them tat ca cac rules vao graph nhu la nodes
        for rule in self.rules:
            rule_id = rule['id']
            self.graph.add_node(
                rule_id, 
                node_type='rule',
                antecedents=rule['antecedents'],
                consequent=rule['consequent']
            )
        
        # Tao edges dua tren quan he tien de (Precedence)
        for i, rule_i in enumerate(self.rules):
            consequent_i = rule_i['consequent'] # f cua rule i
            rule_id_i = rule_i['id']
            
            for j, rule_j in enumerate(self.rules):
                if i == j:
                    continue
                    
                antecedents_j = rule_j['antecedents'] # left cua rule j
                rule_id_j = rule_j['id']
                
                # Neu f thuoc left cua rule j -> Tao cung (ri, rj)
                if consequent_i in antecedents_j:
                    self.graph.add_edge(rule_id_i, rule_id_j)
    
    def visualize_to_base64(self, figsize=(26, 18)):
        """
        Ve RPG theo ly thuyet:
        - Nodes: Luat
        - R_GT: Tap luat thoa man ngay tu dau (left la tap con cua GT)
        - R_KL: Tap luat thoa man ket luan (right la tap con cua KL)
        """
        fig = plt.figure(figsize=figsize, facecolor='white')
        ax = fig.add_subplot(111)
        
        if self.graph.number_of_nodes() == 0:
            ax.text(0.5, 0.5, 'Chua co du lieu RPG.\nVui long tai file luat.',
                   ha='center', va='center', fontsize=14, color='red')
            ax.axis('off')
            plt.tight_layout()
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=120, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            return image_base64
        
        # SU DUNG KAMADA-KAWAI LAYOUT nhu yeu cau
        pos = self._get_kamada_kawai_layout()
        
        # ========== VE EDGES ==========
        for (source, target) in self.graph.edges():
            x1, y1 = pos[source]
            x2, y2 = pos[target]
            
            dx = x2 - x1
            dy = y2 - y1
            length = np.sqrt(dx**2 + dy**2)
            
            if length > 0.01:
                norm_dx = dx / length
                norm_dy = dy / length
                
                radius = 2.0
                start_x = x1 + norm_dx * radius
                start_y = y1 + norm_dy * radius
                end_x = x2 - norm_dx * (radius + 0.6)
                end_y = y2 - norm_dy * (radius + 0.6)
                
                arrow_dx = end_x - start_x
                arrow_dy = end_y - start_y
                
                ax.arrow(start_x, start_y,
                        arrow_dx, arrow_dy,
                        head_width=0.7,
                        head_length=0.6,
                        fc='black',          
                        ec='black',
                        linewidth=2.0,
                        length_includes_head=True,
                        zorder=2,
                        alpha=0.9)
        
        # ========== VE NODES (XU LY LOGIC MOI) ==========
        for node in self.graph.nodes():
            x, y = pos[node]
            
            node_data = self.graph.nodes[node]
            antecedents = node_data.get('antecedents', [])
            consequent = node_data.get('consequent', '')
            
            # LOGIC MOI: Dinh nghia R_GT theo tap hop
            # R_GT = {r : left -> q | left subset GT}
            # Tat ca cac tien de cua luat phai nam trong GT
            is_R_GT = False
            if antecedents:
                is_R_GT = set(antecedents).issubset(self.initial_facts)
            
            # LOGIC MOI: Dinh nghia R_KL
            # R_KL = {r : left -> q | q subset KL}
            is_R_KL = consequent in self.target_goals
            
            radius = 1.8
            
            # Ve node dua tren phan loai
            if is_R_GT:
                # Rule thuoc R_GT (Gach ngang nhu hinh minh hoa)
                circle = plt.Circle((x, y), radius, facecolor='white',
                                   edgecolor='black', linewidth=3.0, zorder=5)
                ax.add_patch(circle)
                # Pattern gach ngang
                hatch_circle = plt.Circle((x, y), radius, facecolor='none',
                                         edgecolor='black', linewidth=0,
                                         hatch='---', zorder=6, alpha=0.6)
                ax.add_patch(hatch_circle)
                
            elif is_R_KL:
                # Rule thuoc R_KL (Gach cheo/doc nhu hinh minh hoa)
                circle = plt.Circle((x, y), radius, facecolor='white',
                                   edgecolor='black', linewidth=3.0, zorder=5)
                ax.add_patch(circle)
                # Pattern gach doc/cheo
                hatch_circle = plt.Circle((x, y), radius, facecolor='none',
                                         edgecolor='black', linewidth=0,
                                         hatch='|||', zorder=6, alpha=0.6)
                ax.add_patch(hatch_circle)
            else:
                # Rule trung gian (Hinh tron trang)
                circle = plt.Circle((x, y), radius, facecolor='white',
                                   edgecolor='black', linewidth=3.0, zorder=5)
                ax.add_patch(circle)
            
            # Label ID cua rule
            rule_label = f"r{node}"
            ax.text(x, y, rule_label, ha='center', va='center',
                   fontsize=12, fontweight='bold', color='black', zorder=7)
        
        # ========== LEGEND (CAP NHAT THEO LY THUYET) ==========
        #
        legend_elements = [
            mpatches.Circle((0, 0), 0.35, facecolor='white', edgecolor='black',
                           hatch='---', linewidth=2.0, label=r'Luật $r \in R_{GT}$ (left $\subseteq$ GT)'),
            mpatches.Circle((0, 0), 0.35, facecolor='white', edgecolor='black',
                           hatch='|||', linewidth=2.0, label=r'Luật $r \in R_{KL}$ (q $\subseteq$ KL)'),
            mpatches.Circle((0, 0), 0.35, facecolor='white', edgecolor='black',
                           linewidth=2.0, label='Luật trung gian')
        ]
        
        ax.legend(handles=legend_elements, loc='lower right',
                 fontsize=14, framealpha=0.95, edgecolor='black',
                 fancybox=True, title="Chú thích loại luật")
        
        # ========== TITLE ==========
        ax.set_title('Đồ thị liên hệ trước giữa các luật RPG (Rules Precedence Graph)',
                    fontsize=18, fontweight='bold', pad=20)
        ax.axis('off')
        ax.set_aspect('equal')
        
        if pos:
            x_values = [pos[n][0] for n in pos]
            y_values = [pos[n][1] for n in pos]
            margin = 3.0
            ax.set_xlim(min(x_values) - margin, max(x_values) + margin)
            ax.set_ylim(min(y_values) - margin, max(y_values) + margin)
        
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=120, bbox_inches='tight', facecolor='white')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return image_base64
    
    def _get_kamada_kawai_layout(self):
        """GIU NGUYEN LAYOUT CU"""
        try:
            pos = nx.kamada_kawai_layout(
                self.graph,
                scale=40.0
            )
            pos = self._push_to_edges_rpg(pos, push_factor=1.5)
            return pos
        except:
            return self._get_spring_layout_rpg()
    
    def _push_to_edges_rpg(self, pos, push_factor=1.5):
        if not pos: return pos
        pushed_pos = {}
        x_values = [x for x, y in pos.values()]
        y_values = [y for x, y in pos.values()]
        center_x = np.mean(x_values)
        center_y = np.mean(y_values)
        for node, (x, y) in pos.items():
            dx = x - center_x
            dy = y - center_y
            pushed_pos[node] = (center_x + dx * push_factor, center_y + dy * push_factor)
        return pushed_pos
    
    def _get_spring_layout_rpg(self):
        pos = nx.spring_layout(self.graph, k=9.0, iterations=150, scale=40.0, seed=42)
        return pos