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
        Edges: Neu ve phai cua rule A xuat hien trong ve trai cua rule B 
        -> ve edge tu A -> B (A la tien de cua B)
        """
        # Them tat ca cac rules vao graph nhu la nodes
        for rule in self.rules:
            rule_id = rule['id']
            self.graph.add_node(
                rule_id, 
                node_type='rule',
                antecedents=rule['antecedents'],
                consequent=rule['consequent']
            )
        
        # Tao edges: Neu consequent cua rule_i xuat hien trong antecedents cua rule_j
        # thi ve edge tu rule_i -> rule_j
        for i, rule_i in enumerate(self.rules):
            consequent_i = rule_i['consequent']
            rule_id_i = rule_i['id']
            
            for j, rule_j in enumerate(self.rules):
                if i == j:
                    continue
                    
                antecedents_j = rule_j['antecedents']
                rule_id_j = rule_j['id']
                
                # Kiem tra neu consequent cua rule_i co trong antecedents cua rule_j
                if consequent_i in antecedents_j:
                    self.graph.add_edge(rule_id_i, rule_id_j)
    
    def visualize_to_base64(self, figsize=(26, 18)):
        """
        Ve RPG: Nodes la cac LUAT, Edges la quan he tien de
        SU DUNG KAMADA-KAWAI LAYOUT VOI MUI TEN RO RANG
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
        
        # SU DUNG KAMADA-KAWAI LAYOUT
        pos = self._get_kamada_kawai_layout()
        
        # ========== VE EDGES VOI MUI TEN RO RANG ==========
        for (source, target) in self.graph.edges():
            x1, y1 = pos[source]
            x2, y2 = pos[target]
            
            # Tinh vector direction
            dx = x2 - x1
            dy = y2 - y1
            length = np.sqrt(dx**2 + dy**2)
            
            if length > 0.01:
                # Normalize direction
                norm_dx = dx / length
                norm_dy = dy / length
                
                # Rut ngan duong de tranh che node
                radius = 2.0
                start_x = x1 + norm_dx * radius
                start_y = y1 + norm_dy * radius
                end_x = x2 - norm_dx * (radius + 0.6)  # Tru them cho mui ten
                end_y = y2 - norm_dy * (radius + 0.6)
                
                # Tinh chieu dai vector
                arrow_dx = end_x - start_x
                arrow_dy = end_y - start_y
                
                # Ve MUI TEN TO VA RO RANG
                ax.arrow(start_x, start_y,
                        arrow_dx, arrow_dy,
                        head_width=0.7,      # MUI TEN TO
                        head_length=0.6,     # MUI TEN DAI
                        fc='black',          
                        ec='black',
                        linewidth=2.5,       # DUONG DAY
                        length_includes_head=True,
                        zorder=2,
                        alpha=0.9)
        
        # ========== VE NODES (CAC LUAT) ==========
        for node in self.graph.nodes():
            x, y = pos[node]
            
            node_data = self.graph.nodes[node]
            consequent = node_data.get('consequent', '')
            
            # Xac dinh loai node: R_GT, R_KL, hoac binh thuong
            is_R_GT = any(ant in self.initial_facts for ant in node_data.get('antecedents', []))
            is_R_KL = consequent in self.target_goals
            
            radius = 1.8  # Vong tron TO
            
            # Ve vong tron voi pattern khac nhau
            if is_R_GT:
                # Rule trong R_GT (gach ngang)
                circle = plt.Circle((x, y), radius, facecolor='white',
                                   edgecolor='black', linewidth=3.5, zorder=5)
                ax.add_patch(circle)
                hatch_circle = plt.Circle((x, y), radius, facecolor='none',
                                         edgecolor='black', linewidth=3.5,
                                         hatch='---', zorder=6)
                ax.add_patch(hatch_circle)
            elif is_R_KL:
                # Rule trong R_KL (gach cheo)
                circle = plt.Circle((x, y), radius, facecolor='white',
                                   edgecolor='black', linewidth=3.5, zorder=5)
                ax.add_patch(circle)
                hatch_circle = plt.Circle((x, y), radius, facecolor='none',
                                         edgecolor='black', linewidth=3.5,
                                         hatch='///', zorder=6)
                ax.add_patch(hatch_circle)
            else:
                # Rule binh thuong
                circle = plt.Circle((x, y), radius, facecolor='white',
                                   edgecolor='black', linewidth=3.5, zorder=5)
                ax.add_patch(circle)
            
            # Label node: hien thi ID cua rule (r1, r2, ...)
            rule_label = f"r{node}"
            ax.text(x, y, rule_label, ha='center', va='center',
                   fontsize=11, fontweight='bold', color='black', zorder=7)
        
        # ========== LEGEND ==========
        legend_elements = [
            mpatches.Circle((0, 0), 0.35, facecolor='white', edgecolor='black',
                           hatch='---', linewidth=2.5, label='Luat r ∈ R_GT'),
            mpatches.Circle((0, 0), 0.35, facecolor='white', edgecolor='black',
                           hatch='///', linewidth=2.5, label='Luat r ∈ R_KL')
        ]
        
        ax.legend(handles=legend_elements, loc='lower right',
                 fontsize=13, framealpha=0.98, edgecolor='black',
                 fancybox=False)
        
        # ========== TITLE & LAYOUT ==========
        ax.set_title('Bieu do RPG (Rules Precedence Graph)\nNodes: Luat, Edges: Quan he tien de',
                    fontsize=17, fontweight='bold', pad=25)
        ax.axis('off')
        ax.set_aspect('equal')
        
        # Set limits
        if pos:
            x_values = [pos[n][0] for n in pos]
            y_values = [pos[n][1] for n in pos]
            margin = 2.5
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
        """
        KAMADA-KAWAI LAYOUT - minimize energy, tot cho graph vua va nho
        """
        try:
            pos = nx.kamada_kawai_layout(
                self.graph,
                scale=40.0  # Scale lon de trai rong
            )
            
            # Day nodes ra xa tam
            pos = self._push_to_edges_rpg(pos, push_factor=1.5)
            
            return pos
        except:
            # Fallback neu kamada_kawai fail (vi du: graph qua lon)
            return self._get_spring_layout_rpg()
    
    def _push_to_edges_rpg(self, pos, push_factor=1.5):
        """Day nodes ra xa tam"""
        if not pos:
            return pos
        
        pushed_pos = {}
        
        x_values = [x for x, y in pos.values()]
        y_values = [y for x, y in pos.values()]
        center_x = np.mean(x_values)
        center_y = np.mean(y_values)
        
        for node, (x, y) in pos.items():
            dx = x - center_x
            dy = y - center_y
            
            new_x = center_x + dx * push_factor
            new_y = center_y + dy * push_factor
            
            pushed_pos[node] = (new_x, new_y)
        
        return pushed_pos
    
    def _get_spring_layout_rpg(self):
        """Spring layout cho RPG (fallback)"""
        pos = nx.spring_layout(
            self.graph,
            k=9.0,
            iterations=150,
            scale=40.0,
            seed=42
        )
        return pos
