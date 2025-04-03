import graphviz
import os

# Ensure the output directory exists
output_dir = "diagrams"
os.makedirs(output_dir, exist_ok=True)

# --- Create Graphviz Digraph ---
dot = graphviz.Digraph(
    'Pacejka_Calculation_Flow',
    comment='Pacejka 2002 Combined Slip Model Flow',
    graph_attr={'rankdir': 'TB', 'splines': 'ortho', 'nodesep': '0.6', 'ranksep': '1.0'}
)
dot.attr('node', shape='box', style='rounded', fontname='Helvetica', fontsize='10')
dot.attr('edge', arrowhead='vee', arrowsize='0.7')

# --- Define Nodes ---

# Level 6: Base Inputs
with dot.subgraph(name='cluster_inputs') as c:
    c.attr(label='Base Inputs', style='filled', color='lightgrey')
    c.node('Fz', '\\(F_z\\)', shape='ellipse')
    c.node('alpha', '\\(\\alpha\\)', shape='ellipse')
    c.node('kappa', '\\(\\kappa\\)', shape='ellipse')
    c.node('gamma', '\\(\\gamma\\)', shape='ellipse')
    c.node('Fz_nom', '\\(F_{{z,nom}}\\)', shape='ellipse', style='dashed') # Correct

# Level 5: Lowest Level Components
dot.node('dfz', label=f'dfz\nEq 29: \\( df_z = \\frac{{ F_z - F_{{z,nom}} }}{{ F_{{z,nom}} }} \\)') # Correct
dot.node('mu_y', label=f'μ_y\nEq 27: \\( \\mu_y = (p_{{dy1}} + p_{{dy2}} df_z)(1 + p_{{dy3}} \\gamma^2) \\)') # Correct
dot.node('K_y_alpha', label=f'K_yα\nEq 28: \\( K_{{y\\alpha}} = p_{{ky1}} F_{{z,nom}} \\sin[p_{{ky2}} \\arctan(\\frac{{F_z}}{{F_{{z,nom}}}})] (1 - p_{{ky3}} |\\gamma|) \\)') # Correct
dot.node('mu_x', label=f'μ_x (Approx)\nEq 25: \\( \\mu_x = (p_{{dx1}} + p_{{dx2}} df_z)(1 + p_{{dx3}} \\gamma^2) \\)') # Correct
dot.node('K_x_kappa', label=f'K_xκ (Approx)\nEq 26: \\( K_{{x\\kappa}} = p_{{kx1}} F_{{z,nom}} \\sin[p_{{kx2}} \\arctan(\\frac{{F_z}}{{F_{{z,nom}}}})] (1 - p_{{kx3}} |\\gamma|) \\)') # Correct

# Level 4: Shifts
dot.node('S_Hx', label=f'S_Hx (Approx)\nEq 18: \\( S_{{Hx}} = p_{{hx1}} + p_{{hx2}} df_z \\)') # Correct
dot.node('S_Vx', label=f'S_Vx (Approx)\nEq 17: \\( S_{{Vx}} = F_z (p_{{vx1}} + p_{{vx2}} df_z) \\)') # Correct
dot.node('S_Hy', label=f'S_Hy\nEq 24: \\( S_{{Hy}} = (p_{{hy1}} + p_{{hy2}} df_z) + p_{{hy3}} \\gamma \\)') # Correct
dot.node('S_Vy', label=f'S_Vy\nEq 23: \\( S_{{Vy}} = F_z [(p_{{vy1}} + p_{{vy2}} df_z) + (p_{{vy3}} + p_{{vy4}} df_z) \\gamma] \\)') # Correct

# Level 3: Effective Slips
dot.node('kappa_eff', label=f'κ_eff\nEq 11: \\( \\kappa_{{eff}} = \\kappa + S_{{Hx}} \\)') # Correct
dot.node('alpha_eff', label=f'α_eff\nEq 12: \\( \\alpha_{{eff}} = \\alpha + S_{{Hy}} \\)') # Correct

# Level 4: Magic Formula Parameters (D, C, B, E)
dot.node('D_x', label=f'D_x (Approx)\nEq 13: \\( D_x = \\mu_x F_z \\)')
dot.node('C_x', label=f'C_x (Approx)\nEq 14: \\( C_x = p_{{cx1}} \\)') # Correct
dot.node('B_x', label=f'B_x (Approx)\nEq 15: \\( B_x = K_{{x\\kappa}} / (C_x D_x) \\)') # Correct
dot.node('E_x', label=f'E_x (Approx)\nEq 16 (Simpl.): \\( E_x = p_{{ex1}} + p_{{ex2}} df_z \\)') # Correct
dot.node('D_y', label=f'D_y\nEq 19: \\( D_y = \\mu_y F_z \\)')
dot.node('C_y', label=f'C_y\nEq 20: \\( C_y = p_{{cy1}} \\)') # Correct
dot.node('B_y', label=f'B_y\nEq 21: \\( B_y = K_{{y\\alpha}} / (C_y D_y) \\)') # Correct
dot.node('E_y', label=f'E_y\nEq 22: \\( E_y = (p_{{ey1}} + ...) (1 - (...) \\text{{sign}}(\\alpha_{{eff}})) \\)') # Correct, Abbreviated

# Level 2: Pure Forces
dot.node('Fx_pure', label=f'Fx_pure (Approx)\nEq 5: \\( D_x \\sin[C_x \\arctan(B_x \\kappa_{{eff}} - E_x(...))] + S_{{Vx}} \\)') # Correct, Abbreviated
dot.node('Fy_pure', label=f'Fy_pure\nEq 6: \\( D_y \\sin[C_y \\arctan(B_y \\alpha_{{eff}} - E_y(...))] + S_{{Vy}} \\)') # Correct, Abbreviated

# Level 3: Combined Slip Components
dot.node('B_xa', label=f'B_xα (Approx)\nEq 7: \\( B_{{x\\alpha}} = r_{{bx1}} \\cos[\\arctan(r_{{bx2}} \\kappa)] \\)') # Correct
dot.node('C_xa', label=f'C_xα (Approx)\nEq 8: \\( C_{{x\\alpha}} = r_{{cx1}} \\)') # Correct
dot.node('B_yk', label=f'B_yκ (Approx)\nEq 9: \\( B_{{y\\kappa}} = r_{{by1}} \\cos[\\arctan(r_{{by2}} (\\alpha - r_{{by3}}))] \\)') # Correct
dot.node('C_yk', label=f'C_yκ (Approx)\nEq 10: \\( C_{{y\\kappa}} = r_{{cy1}} \\)') # Correct

# Level 2: Weighting Factors
dot.node('G_xa', label=f'G_xα (Approx)\nEq 3: \\( G_{{x\\alpha}} = \\cos[C_{{x\\alpha}} \\arctan(B_{{x\\alpha}} \\alpha)] \\)') # Correct
dot.node('G_yk', label=f'G_yκ (Approx)\nEq 4: \\( G_{{y\\kappa}} = \\cos[C_{{y\\kappa}} \\arctan(B_{{y\\kappa}} \\kappa)] \\)') # Correct

# Level 1: Combined Forces
dot.node('Fx_combined', label=f'Fx_combined\nEq 1: \\( F_{{x,comb}} = F_{{x,pure}} G_{{x\\alpha}} \\)', shape='doubleoctagon') # Correct
dot.node('Fy_combined', label=f'Fy_combined\nEq 2: \\( F_{{y,comb}} = F_{{y,pure}} G_{{y\\kappa}} \\)', shape='doubleoctagon') # Correct


# --- Define Edges (Dependencies - No changes needed here) ---
dot.edge('Fz', 'dfz')
dot.edge('Fz_nom', 'dfz')
dot.edge('dfz', 'mu_y')
dot.edge('gamma', 'mu_y')
dot.edge('Fz', 'K_y_alpha')
dot.edge('Fz_nom', 'K_y_alpha')
dot.edge('gamma', 'K_y_alpha')
dot.edge('dfz', 'mu_x')
dot.edge('gamma', 'mu_x')
dot.edge('Fz', 'K_x_kappa')
dot.edge('Fz_nom', 'K_x_kappa')
dot.edge('gamma', 'K_x_kappa')
dot.edge('dfz', 'S_Hx')
dot.edge('Fz', 'S_Vx')
dot.edge('dfz', 'S_Vx')
dot.edge('dfz', 'S_Hy')
dot.edge('gamma', 'S_Hy')
dot.edge('Fz', 'S_Vy')
dot.edge('dfz', 'S_Vy')
dot.edge('gamma', 'S_Vy')
dot.edge('kappa', 'kappa_eff')
dot.edge('S_Hx', 'kappa_eff')
dot.edge('alpha', 'alpha_eff')
dot.edge('S_Hy', 'alpha_eff')
dot.edge('mu_x', 'D_x')
dot.edge('Fz', 'D_x')
dot.edge('K_x_kappa', 'B_x')
dot.edge('C_x', 'B_x')
dot.edge('D_x', 'B_x')
dot.edge('dfz', 'E_x')
dot.edge('mu_y', 'D_y')
dot.edge('Fz', 'D_y')
dot.edge('K_y_alpha', 'B_y')
dot.edge('C_y', 'B_y')
dot.edge('D_y', 'B_y')
dot.edge('dfz', 'E_y')
dot.edge('gamma', 'E_y')
dot.edge('alpha_eff', 'E_y')
dot.edge('D_x', 'Fx_pure')
dot.edge('C_x', 'Fx_pure')
dot.edge('B_x', 'Fx_pure')
dot.edge('E_x', 'Fx_pure')
dot.edge('kappa_eff', 'Fx_pure')
dot.edge('S_Vx', 'Fx_pure')
dot.edge('D_y', 'Fy_pure')
dot.edge('C_y', 'Fy_pure')
dot.edge('B_y', 'Fy_pure')
dot.edge('E_y', 'Fy_pure')
dot.edge('alpha_eff', 'Fy_pure')
dot.edge('S_Vy', 'Fy_pure')
dot.edge('kappa', 'B_xa')
dot.edge('alpha', 'B_yk')
dot.edge('C_xa', 'G_xa')
dot.edge('B_xa', 'G_xa')
dot.edge('alpha', 'G_xa')
dot.edge('C_yk', 'G_yk')
dot.edge('B_yk', 'G_yk')
dot.edge('kappa', 'G_yk')
dot.edge('Fx_pure', 'Fx_combined')
dot.edge('G_xa', 'Fx_combined')
dot.edge('Fy_pure', 'Fy_combined')
dot.edge('G_yk', 'Fy_combined')


# --- Render Graph ---
output_path = os.path.join(output_dir, 'pacejka_flow')
try:
    # Specify the engine, e.g., 'dot', 'neato', 'fdp', etc. 'dot' is default for hierarchical.
    dot.engine = 'dot'
    dot.render(output_path, format='png', view=False, cleanup=True)
    print(f"Graphviz diagram saved to {output_path}.gv and {output_path}.gv.png")
except graphviz.backend.execute.ExecutableNotFound:
    print("Error: Graphviz executable not found.")
    print("Please install Graphviz (https://graphviz.org/download/)")
    print("and ensure its 'bin' directory is in your system's PATH.")
except Exception as e:
    print(f"An error occurred during rendering: {e}")


