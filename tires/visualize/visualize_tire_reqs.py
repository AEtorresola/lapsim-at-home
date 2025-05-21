

import graphviz
import os

# Ensure the output directory exists
output_dir = "diagrams"
os.makedirs(output_dir, exist_ok=True)

# --- Common Attributes & Colors ---
graph_attrs = {'rankdir': 'TB', 'splines': 'spline', 'nodesep': '0.8', 'ranksep': '1.2'} # Use spline for smoother curves
node_attrs = {'shape': 'box', 'style': 'rounded,filled', 'fontname': 'Helvetica', 'fontsize': '10'}
edge_attrs = {'arrowhead': 'vee', 'arrowsize': '0.7'}
router_attrs = {'style': 'invis', 'width': '0', 'height': '0', 'label': ''}

level_colors = {
    6: 'lightgrey', 5: '#E0F2F7', 4: '#E8F5E9',
    3: '#FFF9C4', 2: '#FFE0B2', 1: '#FFCDD2'
}

# Function to create node labels (avoids repetition)
def create_label(text, eq_num, latex_eq, approx=False):
    prefix = f"{text}{' (Approx)' if approx else ''}"
    return f"{prefix}\nEq {eq_num}: \\( {latex_eq} \\)"

# ==================================================
# --- Fx Combined Calculation Flow ---
# ==================================================
dot_fx = graphviz.Digraph(
    'Pacejka_Fx_Calculation_Flow_Routed',
    comment='Pacejka 2002 Fx Combined Calculation Flow - Leveled and Routed',
    graph_attr=graph_attrs
)
dot_fx.attr('node', **node_attrs)
dot_fx.attr('edge', **edge_attrs)

# --- Define Invisible Routers ---
# Place them conceptually at the top/bottom but allow edges to connect anywhere
dot_fx.node('RouterL_Top', **router_attrs)
dot_fx.node('RouterR_Top', **router_attrs)
dot_fx.node('RouterL_Bot', **router_attrs)
dot_fx.node('RouterR_Bot', **router_attrs)
# Try to keep routers horizontally aligned if needed (might not be necessary)
# dot_fx.rank(same='min', 'RouterL_Top', 'RouterR_Top')
# dot_fx.rank(same='max', 'RouterL_Bot', 'RouterR_Bot')


# --- Fx Nodes by Level (using subgraphs mainly for visual grouping/color) ---

# Level 6: Base Inputs
with dot_fx.subgraph(name='cluster_fx_6') as c:
    c.attr(label='Level 6: Base Inputs', style='filled', color=level_colors[6], rank='same') # Enforce rank
    c.node('Fz', '\\(F_z\\)', shape='ellipse', fillcolor='white')
    c.node('alpha', '\\(\\alpha\\)', shape='ellipse', fillcolor='white')
    c.node('kappa', '\\(\\kappa\\)', shape='ellipse', fillcolor='white')
    c.node('gamma', '\\(\\gamma\\)', shape='ellipse', fillcolor='white')
    c.node('Fz_nom', '\\(F_{{z,nom}}\\)', shape='ellipse', style='dashed,filled', fillcolor='white')

# Level 5: Lowest Level Components
with dot_fx.subgraph(name='cluster_fx_5') as c:
    c.attr(label='Level 5: Base Components', style='filled', color=level_colors[5], rank='same') # Enforce rank
    c.node('dfz', label=create_label('dfz', 29, r'df_z = \frac{{ F_z - F_{{z,nom}} }}{{ F_{{z,nom}} }}'), fillcolor=level_colors[5])
    c.node('mu_x', label=create_label('μ_x', 25, r'\mu_x = (p_{{dx1}} + ...) ', approx=True), fillcolor=level_colors[5])
    c.node('K_x_kappa', label=create_label('K_xκ', 26, r'K_{{x\kappa}} = p_{{kx1}} F_{{z,nom}} \sin[...]', approx=True), fillcolor=level_colors[5])

# Level 4: Shifts and Fx MF Params
with dot_fx.subgraph(name='cluster_fx_4') as c:
    c.attr(label='Level 4: Shifts & Fx MF Params', style='filled', color=level_colors[4], rank='same') # Enforce rank
    c.node('S_Hx', label=create_label('S_Hx', 18, r'S_{{Hx}} = p_{{hx1}} + p_{{hx2}} df_z', approx=True), fillcolor=level_colors[4])
    c.node('S_Vx', label=create_label('S_Vx', 17, r'S_{{Vx}} = F_z (p_{{vx1}} + ...)', approx=True), fillcolor=level_colors[4])
    c.node('D_x', label=create_label('D_x', 13, r'D_x = \mu_x F_z', approx=True), fillcolor=level_colors[4])
    c.node('C_x', label=create_label('C_x', 14, r'C_x = p_{{cx1}}', approx=True), fillcolor=level_colors[4])
    c.node('B_x', label=create_label('B_x', 15, r'B_x = K_{{x\kappa}} / (C_x D_x)', approx=True), fillcolor=level_colors[4])
    c.node('E_x', label=create_label('E_x', 16, r'E_x = p_{{ex1}} + p_{{ex2}} df_z', approx=True), fillcolor=level_colors[4])

# Level 3: Effective Slips and Combined Components
with dot_fx.subgraph(name='cluster_fx_3') as c:
    c.attr(label='Level 3: Effective Slips & Combined Components', style='filled', color=level_colors[3], rank='same') # Enforce rank
    c.node('kappa_eff', label=create_label('κ_eff', 11, r'\kappa_{{eff}} = \kappa + S_{{Hx}}'), fillcolor=level_colors[3])
    c.node('B_xa', label=create_label('B_xα', 7, r'B_{{x\alpha}} = r_{{bx1}} \cos[...]', approx=True), fillcolor=level_colors[3])
    c.node('C_xa', label=create_label('C_xα', 8, r'C_{{x\alpha}} = r_{{cx1}}', approx=True), fillcolor=level_colors[3])

# Level 2: Pure Force and Weighting Factor
with dot_fx.subgraph(name='cluster_fx_2') as c:
    c.attr(label='Level 2: Pure Force & Weighting Factor', style='filled', color=level_colors[2], rank='same') # Enforce rank
    c.node('Fx_pure', label=create_label('Fx_pure', 5, r'D_x \sin[C_x \arctan(...)] + S_{{Vx}}', approx=True), fillcolor=level_colors[2])
    c.node('G_xa', label=create_label('G_xα', 3, r'G_{{x\alpha}} = \cos[C_{{x\alpha}} \arctan(B_{{x\alpha}} \alpha)]', approx=True), fillcolor=level_colors[2])

# Level 1: Final Combined Force Fx
with dot_fx.subgraph(name='cluster_fx_1') as c:
    c.attr(label='Level 1: Final Output', style='filled', color=level_colors[1], rank='same') # Enforce rank
    c.node('Fx_combined', label=create_label('Fx_combined', 1, r'F_{{x,comb}} = F_{{x,pure}} G_{{x\alpha}}'), shape='doubleoctagon', fillcolor=level_colors[1])

# --- Fx Edges (Routing through invisible nodes) ---
# Edges within the same level or adjacent levels can often go direct
# Edges skipping levels or crossing horizontally are candidates for routing

# Direct Edges (Examples)
dot_fx.edge('Fz', 'dfz')
dot_fx.edge('Fz_nom', 'dfz')
dot_fx.edge('dfz', 'mu_x')
dot_fx.edge('gamma', 'mu_x')
dot_fx.edge('dfz', 'K_x_kappa') # Corrected from mu_x
dot_fx.edge('gamma', 'K_x_kappa')
dot_fx.edge('Fz', 'K_x_kappa')
dot_fx.edge('Fz_nom', 'K_x_kappa')
dot_fx.edge('dfz', 'S_Hx')
dot_fx.edge('Fz', 'S_Vx')
dot_fx.edge('dfz', 'S_Vx')
dot_fx.edge('kappa', 'kappa_eff')
dot_fx.edge('S_Hx', 'kappa_eff')
dot_fx.edge('mu_x', 'D_x')
dot_fx.edge('Fz', 'D_x')
dot_fx.edge('K_x_kappa', 'B_x')
dot_fx.edge('C_x', 'B_x')
dot_fx.edge('D_x', 'B_x')
dot_fx.edge('dfz', 'E_x')
dot_fx.edge('D_x', 'Fx_pure')
dot_fx.edge('C_x', 'Fx_pure')
dot_fx.edge('B_x', 'Fx_pure')
dot_fx.edge('E_x', 'Fx_pure')
dot_fx.edge('kappa_eff', 'Fx_pure')
dot_fx.edge('S_Vx', 'Fx_pure')
dot_fx.edge('kappa', 'B_xa')
dot_fx.edge('C_xa', 'G_xa')
dot_fx.edge('B_xa', 'G_xa')
dot_fx.edge('Fx_pure', 'Fx_combined')
dot_fx.edge('G_xa', 'Fx_combined')

# Routed Edges (Example: alpha -> G_xa, skipping levels)
# Route alpha from Level 6 to G_xa in Level 2 via side routers
dot_fx.edge('alpha', 'RouterL_Top', dir='none', constraint='false') # Connect input to router
dot_fx.edge('RouterL_Top', 'RouterL_Bot', arrowhead='none', constraint='false') # Invisible path down side
dot_fx.edge('RouterL_Bot', 'G_xa', constraint='false') # Connect router to target

# --- Render Fx Graph ---
output_path_fx = os.path.join(output_dir, 'pacejka_flow_fx_routed')
try:
    dot_fx.engine = 'dot'
    dot_fx.render(output_path_fx, format='png', view=False, cleanup=True)
    print(f"Graphviz Fx diagram saved to {output_path_fx}.gv and {output_path_fx}.gv.png")
except graphviz.backend.execute.ExecutableNotFound:
    print("Error: Graphviz executable not found.")
    print("Please install Graphviz (https://graphviz.org/download/)")
    print("and ensure its 'bin' directory is in your system's PATH.")
except Exception as e:
    print(f"An error occurred during Fx rendering: {e}")


# ==================================================
# --- Fy Combined Calculation Flow (Similar Structure) ---
# ==================================================
dot_fy = graphviz.Digraph(
    'Pacejka_Fy_Calculation_Flow_Routed',
    comment='Pacejka 2002 Fy Combined Calculation Flow - Leveled and Routed',
    graph_attr=graph_attrs
)
dot_fy.attr('node', **node_attrs)
dot_fy.attr('edge', **edge_attrs)

# --- Define Invisible Routers ---
dot_fy.node('RouterL_Top', **router_attrs)
dot_fy.node('RouterR_Top', **router_attrs)
dot_fy.node('RouterL_Bot', **router_attrs)
dot_fy.node('RouterR_Bot', **router_attrs)

# --- Fy Nodes by Level ---
# Level 6
with dot_fy.subgraph(name='cluster_fy_6') as c:
    c.attr(label='Level 6: Base Inputs', style='filled', color=level_colors[6], rank='same')
    c.node('Fz', '\\(F_z\\)', shape='ellipse', fillcolor='white')
    c.node('alpha', '\\(\\alpha\\)', shape='ellipse', fillcolor='white')
    c.node('kappa', '\\(\\kappa\\)', shape='ellipse', fillcolor='white')
    c.node('gamma', '\\(\\gamma\\)', shape='ellipse', fillcolor='white')
    c.node('Fz_nom', '\\(F_{{z,nom}}\\)', shape='ellipse', style='dashed,filled', fillcolor='white')
# Level 5
with dot_fy.subgraph(name='cluster_fy_5') as c:
    c.attr(label='Level 5: Base Components', style='filled', color=level_colors[5], rank='same')
    c.node('dfz', label=create_label('dfz', 29, r'df_z = \frac{{ F_z - F_{{z,nom}} }}{{ F_{{z,nom}} }}'), fillcolor=level_colors[5])
    c.node('mu_y', label=create_label('μ_y', 27, r'\mu_y = (p_{{dy1}} + ...)'), fillcolor=level_colors[5])
    c.node('K_y_alpha', label=create_label('K_yα', 28, r'K_{{y\alpha}} = p_{{ky1}} F_{{z,nom}} \sin[...]',), fillcolor=level_colors[5])
# Level 4
with dot_fy.subgraph(name='cluster_fy_4') as c:
    c.attr(label='Level 4: Shifts & Fy MF Params', style='filled', color=level_colors[4], rank='same')
    c.node('S_Hy', label=create_label('S_Hy', 24, r'S_{{Hy}} = (p_{{hy1}} + ...)'), fillcolor=level_colors[4])
    c.node('S_Vy', label=create_label('S_Vy', 23, r'S_{{Vy}} = F_z [(p_{{vy1}} + ...) + (...)\gamma]'), fillcolor=level_colors[4])
    c.node('D_y', label=create_label('D_y', 19, r'D_y = \mu_y F_z'), fillcolor=level_colors[4])
    c.node('C_y', label=create_label('C_y', 20, r'C_y = p_{{cy1}}'), fillcolor=level_colors[4])
    c.node('B_y', label=create_label('B_y', 21, r'B_y = K_{{y\alpha}} / (C_y D_y)'), fillcolor=level_colors[4])
    c.node('E_y', label=create_label('E_y', 22, r'E_y = (p_{{ey1}} + ...) (1 - (...) \text{{sign}}(\alpha_{{eff}}))'), fillcolor=level_colors[4])
# Level 3
with dot_fy.subgraph(name='cluster_fy_3') as c:
    c.attr(label='Level 3: Effective Slips & Combined Components', style='filled', color=level_colors[3], rank='same')
    c.node('alpha_eff', label=create_label('α_eff', 12, r'\alpha_{{eff}} = \alpha + S_{{Hy}}'), fillcolor=level_colors[3])
    c.node('B_yk', label=create_label('B_yκ', 9, r'B_{{y\kappa}} = r_{{by1}} \cos[...]', approx=True), fillcolor=level_colors[3])
    c.node('C_yk', label=create_label('C_yκ', 10, r'C_{{y\kappa}} = r_{{cy1}}', approx=True), fillcolor=level_colors[3])
# Level 2
with dot_fy.subgraph(name='cluster_fy_2') as c:
    c.attr(label='Level 2: Pure Force & Weighting Factor', style='filled', color=level_colors[2], rank='same')
    c.node('Fy_pure', label=create_label('Fy_pure', 6, r'D_y \sin[C_y \arctan(...)] + S_{{Vy}}'), fillcolor=level_colors[2])
    c.node('G_yk', label=create_label('G_yκ', 4, r'G_{{y\kappa}} = \cos[C_{{y\kappa}} \arctan(B_{{y\kappa}} \kappa)]', approx=True), fillcolor=level_colors[2])
# Level 1
with dot_fy.subgraph(name='cluster_fy_1') as c:
    c.attr(label='Level 1: Final Output', style='filled', color=level_colors[1], rank='same')
    c.node('Fy_combined', label=create_label('Fy_combined', 2, r'F_{{y,comb}} = F_{{y,pure}} G_{{y\kappa}}'), shape='doubleoctagon', fillcolor=level_colors[1])

# --- Fy Edges (Routing through invisible nodes) ---
# Direct Edges
dot_fy.edge('Fz', 'dfz')
dot_fy.edge('Fz_nom', 'dfz')
dot_fy.edge('dfz', 'mu_y')
dot_fy.edge('gamma', 'mu_y')
dot_fy.edge('Fz', 'K_y_alpha')
dot_fy.edge('Fz_nom', 'K_y_alpha')
dot_fy.edge('gamma', 'K_y_alpha')
dot_fy.edge('dfz', 'S_Hy')
dot_fy.edge('gamma', 'S_Hy')
dot_fy.edge('Fz', 'S_Vy')
dot_fy.edge('dfz', 'S_Vy')
dot_fy.edge('gamma', 'S_Vy')
dot_fy.edge('alpha', 'alpha_eff')
dot_fy.edge('S_Hy', 'alpha_eff')
dot_fy.edge('mu_y', 'D_y')
dot_fy.edge('Fz', 'D_y')
dot_fy.edge('K_y_alpha', 'B_y')
dot_fy.edge('C_y', 'B_y')
dot_fy.edge('D_y', 'B_y')
dot_fy.edge('dfz', 'E_y')
dot_fy.edge('gamma', 'E_y')
dot_fy.edge('alpha_eff', 'E_y') # L3 -> L4
dot_fy.edge('D_y', 'Fy_pure')
dot_fy.edge('C_y', 'Fy_pure')
dot_fy.edge('B_y', 'Fy_pure')
dot_fy.edge('E_y', 'Fy_pure')
dot_fy.edge('alpha_eff', 'Fy_pure')
dot_fy.edge('S_Vy', 'Fy_pure')
dot_fy.edge('alpha', 'B_yk')
dot_fy.edge('C_yk', 'G_yk')
dot_fy.edge('B_yk', 'G_yk')
dot_fy.edge('Fy_pure', 'Fy_combined')
dot_fy.edge('G_yk', 'Fy_combined')

# Routed Edges (Example: kappa -> G_yk)
dot_fy.edge('kappa', 'RouterR_Top', dir='none', constraint='false')
dot_fy.edge('RouterR_Top', 'RouterR_Bot', arrowhead='none', constraint='false')
dot_fy.edge('RouterR_Bot', 'G_yk', constraint='false')


# --- Render Fy Graph ---
output_path_fy = os.path.join(output_dir, 'pacejka_flow_fy_routed')
try:
    dot_fy.engine = 'dot'
    dot_fy.render(output_path_fy, format='png', view=False, cleanup=True)
    print(f"Graphviz Fy diagram saved to {output_path_fy}.gv and {output_path_fy}.gv.png")
except graphviz.backend.execute.ExecutableNotFound:
    print("Error: Graphviz executable not found.")
    print("Please install Graphviz (https://graphviz.org/download/)")
    print("and ensure its 'bin' directory is in your system's PATH.")
except Exception as e:
    print(f"An error occurred during Fy rendering: {e}")


