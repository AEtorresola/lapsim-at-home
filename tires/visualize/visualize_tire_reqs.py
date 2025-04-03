
import graphviz
import os

# Ensure the output directory exists
output_dir = "diagrams"
os.makedirs(output_dir, exist_ok=True)

# --- Common Attributes ---
graph_attrs = {'rankdir': 'TB', 'splines': 'ortho', 'nodesep': '0.6', 'ranksep': '1.0'}
node_attrs = {'shape': 'box', 'style': 'rounded', 'fontname': 'Helvetica', 'fontsize': '10'}
edge_attrs = {'arrowhead': 'vee', 'arrowsize': '0.7'}

# ==================================================
# --- Fx Combined Calculation Flow ---
# ==================================================
dot_fx = graphviz.Digraph(
    'Pacejka_Fx_Calculation_Flow',
    comment='Pacejka 2002 Fx Combined Calculation Flow',
    graph_attr=graph_attrs
)
dot_fx.attr('node', **node_attrs)
dot_fx.attr('edge', **edge_attrs)

# --- Fx Nodes ---

# Inputs (Relevant subset + Shared)
with dot_fx.subgraph(name='cluster_inputs_fx') as c:
    c.attr(label='Base Inputs (for Fx)', style='filled', color='lightgrey')
    c.node('Fz', '\\(F_z\\)', shape='ellipse')
    c.node('alpha', '\\(\\alpha\\)', shape='ellipse') # Needed for G_xa
    c.node('kappa', '\\(\\kappa\\)', shape='ellipse')
    c.node('gamma', '\\(\\gamma\\)', shape='ellipse') # Needed for mu_x, K_x_kappa
    c.node('Fz_nom', '\\(F_{{z,nom}}\\)', shape='ellipse', style='dashed')

# Shared Intermediate
dot_fx.node('dfz', label=f'dfz\nEq 29: \\( df_z = \\frac{{ F_z - F_{{z,nom}} }}{{ F_{{z,nom}} }} \\)')

# Fx Specific Path (Levels 5, 4, 3)
dot_fx.node('mu_x', label=f'μ_x (Approx)\nEq 25: \\( \\mu_x = (p_{{dx1}} + ...) \\)') # Abbreviated
dot_fx.node('K_x_kappa', label=f'K_xκ (Approx)\nEq 26: \\( K_{{x\\kappa}} = p_{{kx1}} F_{{z,nom}} \\sin[...] \\)') # Abbreviated
dot_fx.node('S_Hx', label=f'S_Hx (Approx)\nEq 18: \\( S_{{Hx}} = p_{{hx1}} + p_{{hx2}} df_z \\)')
dot_fx.node('S_Vx', label=f'S_Vx (Approx)\nEq 17: \\( S_{{Vx}} = F_z (p_{{vx1}} + ...) \\)') # Abbreviated
dot_fx.node('kappa_eff', label=f'κ_eff\nEq 11: \\( \\kappa_{{eff}} = \\kappa + S_{{Hx}} \\)')
dot_fx.node('D_x', label=f'D_x (Approx)\nEq 13: \\( D_x = \\mu_x F_z \\)')
dot_fx.node('C_x', label=f'C_x (Approx)\nEq 14: \\( C_x = p_{{cx1}} \\)')
dot_fx.node('B_x', label=f'B_x (Approx)\nEq 15: \\( B_x = K_{{x\\kappa}} / (C_x D_x) \\)')
dot_fx.node('E_x', label=f'E_x (Approx)\nEq 16 (Simpl.): \\( E_x = p_{{ex1}} + p_{{ex2}} df_z \\)')

# Fx Pure Force (Level 2)
dot_fx.node('Fx_pure', label=f'Fx_pure (Approx)\nEq 5: \\( D_x \\sin[C_x \\arctan(...)] + S_{{Vx}} \\)') # Abbreviated

# Combined Slip for Fx (Levels 3, 2)
dot_fx.node('B_xa', label=f'B_xα (Approx)\nEq 7: \\( B_{{x\\alpha}} = r_{{bx1}} \\cos[...] \\)') # Abbreviated
dot_fx.node('C_xa', label=f'C_xα (Approx)\nEq 8: \\( C_{{x\\alpha}} = r_{{cx1}} \\)')
dot_fx.node('G_xa', label=f'G_xα (Approx)\nEq 3: \\( G_{{x\\alpha}} = \\cos[C_{{x\\alpha}} \\arctan(B_{{x\\alpha}} \\alpha)] \\)')

# Final Fx (Level 1)
dot_fx.node('Fx_combined', label=f'Fx_combined\nEq 1: \\( F_{{x,comb}} = F_{{x,pure}} G_{{x\\alpha}} \\)', shape='doubleoctagon')

# --- Fx Edges ---
dot_fx.edge('Fz', 'dfz')
dot_fx.edge('Fz_nom', 'dfz')
dot_fx.edge('dfz', 'mu_x')
dot_fx.edge('gamma', 'mu_x')
dot_fx.edge('Fz', 'K_x_kappa')
dot_fx.edge('Fz_nom', 'K_x_kappa')
dot_fx.edge('gamma', 'K_x_kappa')
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
dot_fx.edge('kappa', 'B_xa') # kappa influences B_xa
dot_fx.edge('C_xa', 'G_xa')
dot_fx.edge('B_xa', 'G_xa')
dot_fx.edge('alpha', 'G_xa') # alpha influences G_xa
dot_fx.edge('Fx_pure', 'Fx_combined')
dot_fx.edge('G_xa', 'Fx_combined')


# ==================================================
# --- Fy Combined Calculation Flow ---
# ==================================================
dot_fy = graphviz.Digraph(
    'Pacejka_Fy_Calculation_Flow',
    comment='Pacejka 2002 Fy Combined Calculation Flow',
    graph_attr=graph_attrs
)
dot_fy.attr('node', **node_attrs)
dot_fy.attr('edge', **edge_attrs)

# --- Fy Nodes ---

# Inputs (Relevant subset + Shared)
with dot_fy.subgraph(name='cluster_inputs_fy') as c:
    c.attr(label='Base Inputs (for Fy)', style='filled', color='lightgrey')
    c.node('Fz', '\\(F_z\\)', shape='ellipse')
    c.node('alpha', '\\(\\alpha\\)', shape='ellipse')
    c.node('kappa', '\\(\\kappa\\)', shape='ellipse') # Needed for G_yk
    c.node('gamma', '\\(\\gamma\\)', shape='ellipse')
    c.node('Fz_nom', '\\(F_{{z,nom}}\\)', shape='ellipse', style='dashed')

# Shared Intermediate
dot_fy.node('dfz', label=f'dfz\nEq 29: \\( df_z = \\frac{{ F_z - F_{{z,nom}} }}{{ F_{{z,nom}} }} \\)')

# Fy Specific Path (Levels 5, 4, 3)
dot_fy.node('mu_y', label=f'μ_y\nEq 27: \\( \\mu_y = (p_{{dy1}} + ...) \\)') # Abbreviated
dot_fy.node('K_y_alpha', label=f'K_yα\nEq 28: \\( K_{{y\\alpha}} = p_{{ky1}} F_{{z,nom}} \\sin[...] \\)') # Abbreviated
dot_fy.node('S_Hy', label=f'S_Hy\nEq 24: \\( S_{{Hy}} = (p_{{hy1}} + ...) \\)') # Abbreviated
dot_fy.node('S_Vy', label=f'S_Vy\nEq 23: \\( S_{{Vy}} = F_z [(p_{{vy1}} + ...) + (...)\\gamma] \\)') # Abbreviated
dot_fy.node('alpha_eff', label=f'α_eff\nEq 12: \\( \\alpha_{{eff}} = \\alpha + S_{{Hy}} \\)')
dot_fy.node('D_y', label=f'D_y\nEq 19: \\( D_y = \\mu_y F_z \\)')
dot_fy.node('C_y', label=f'C_y\nEq 20: \\( C_y = p_{{cy1}} \\)')
dot_fy.node('B_y', label=f'B_y\nEq 21: \\( B_y = K_{{y\\alpha}} / (C_y D_y) \\)')
dot_fy.node('E_y', label=f'E_y\nEq 22: \\( E_y = (p_{{ey1}} + ...) (1 - (...) \\text{{sign}}(\\alpha_{{eff}})) \\)') # Abbreviated

# Fy Pure Force (Level 2)
dot_fy.node('Fy_pure', label=f'Fy_pure\nEq 6: \\( D_y \\sin[C_y \\arctan(...)] + S_{{Vy}} \\)') # Abbreviated

# Combined Slip for Fy (Levels 3, 2)
dot_fy.node('B_yk', label=f'B_yκ (Approx)\nEq 9: \\( B_{{y\\kappa}} = r_{{by1}} \\cos[...] \\)') # Abbreviated
dot_fy.node('C_yk', label=f'C_yκ (Approx)\nEq 10: \\( C_{{y\\kappa}} = r_{{cy1}} \\)')
dot_fy.node('G_yk', label=f'G_yκ (Approx)\nEq 4: \\( G_{{y\\kappa}} = \\cos[C_{{y\\kappa}} \\arctan(B_{{y\\kappa}} \\kappa)] \\)')

# Final Fy (Level 1)
dot_fy.node('Fy_combined', label=f'Fy_combined\nEq 2: \\( F_{{y,comb}} = F_{{y,pure}} G_{{y\\kappa}} \\)', shape='doubleoctagon')

# --- Fy Edges ---
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
dot_fy.edge('alpha_eff', 'E_y')
dot_fy.edge('D_y', 'Fy_pure')
dot_fy.edge('C_y', 'Fy_pure')
dot_fy.edge('B_y', 'Fy_pure')
dot_fy.edge('E_y', 'Fy_pure')
dot_fy.edge('alpha_eff', 'Fy_pure')
dot_fy.edge('S_Vy', 'Fy_pure')
dot_fy.edge('alpha', 'B_yk') # alpha influences B_yk
dot_fy.edge('C_yk', 'G_yk')
dot_fy.edge('B_yk', 'G_yk')
dot_fy.edge('kappa', 'G_yk') # kappa influences G_yk
dot_fy.edge('Fy_pure', 'Fy_combined')
dot_fy.edge('G_yk', 'Fy_combined')


# --- Render Graphs ---
output_path_fx = os.path.join(output_dir, 'pacejka_flow_fx')
output_path_fy = os.path.join(output_dir, 'pacejka_flow_fy')
try:
    dot_fx.engine = 'dot'
    dot_fx.render(output_path_fx, format='png', view=False, cleanup=True)
    print(f"Graphviz Fx diagram saved to {output_path_fx}.gv and {output_path_fx}.gv.png")

    dot_fy.engine = 'dot'
    dot_fy.render(output_path_fy, format='png', view=False, cleanup=True)
    print(f"Graphviz Fy diagram saved to {output_path_fy}.gv and {output_path_fy}.gv.png")

except graphviz.backend.execute.ExecutableNotFound:
    print("Error: Graphviz executable not found.")
    print("Please install Graphviz (https://graphviz.org/download/)")
    print("and ensure its 'bin' directory is in your system's PATH.")
except Exception as e:
    print(f"An error occurred during rendering: {e}")

