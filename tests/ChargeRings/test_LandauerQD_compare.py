import numpy as np
from LandauerQD_py import LandauerQDs as LandauerQDs_py
import sys
sys.path.append("../../")
sys.path.append("/home/prokop/git/ppafm")
from pyProbeParticle import LandauerQD as lqd

# ===== Test Parameters =====
TOLERANCE = 1e-8

# System parameters (single point test)
nsite = 3
R = 5.0
Q_tip = 0.6
z_tip = 6.0
K = 0.01    # Coulomb interaction between QDs
tS = 0.1    # QD-substrate coupling
tA = 0.1    # Tip coupling strength
decay = 0.7
Gamma_tip = 1.0  # Tip state broadening
Gamma_sub = 1.0  # Substrate state broadening
E_sub = 0.0
E_tip = 0.0
eta = 0.01

# Energy of states on the sites
E0QDs = np.array([-1.0, -1.0, -1.0])

# Single test point for tip position
tip_pos = np.array([0.0, 0.0, z_tip])

def print_comparison(name, py_val, cpp_val, tol=1e-8, ignore_imag=False, relative=False):
    """Print comparison between Python and C++ values."""
    print(f"\n=== {name} ===")
    print("Python implementation:")
    print(py_val)
    print("\nC++ implementation:")
    print(cpp_val)
    
    # Calculate differences
    diff = np.abs(py_val - cpp_val)
    real_diff = np.abs(np.real(py_val) - np.real(cpp_val))
    imag_diff = np.abs(np.imag(py_val) - np.imag(cpp_val))
    
    max_diff = np.max(diff)
    max_real_diff = np.max(real_diff)
    max_imag_diff = np.max(imag_diff)
    
    if relative:
        # Use relative difference for transmission values
        max_diff = max_diff / (np.abs(py_val).mean() + 1e-10)
        max_real_diff = max_real_diff / (np.abs(np.real(py_val)).mean() + 1e-10)
        if not ignore_imag:
            max_imag_diff = max_imag_diff / (np.abs(np.imag(py_val)).mean() + 1e-10)
    
    print(f"\nMax difference: {max_diff}")
    print(f"Max real difference: {max_real_diff}")
    if not ignore_imag:
        print(f"Max imag difference: {max_imag_diff}")
    
    # For full Hamiltonian test, ignore imaginary part differences
    if ignore_imag:
        return max_real_diff < tol
    else:
        return max_diff < tol

def compare_matrix_files(py_file, cpp_file, tol=1e-8):
    """Compare matrices saved in two files."""
    def read_matrix(filename):
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                # Skip title and dimension lines
                data_lines = [line.strip() for line in lines[3:] if line.strip()]
                matrix = []
                for line in data_lines:
                    row = []
                    elements = line.split()
                    for elem in elements:
                        try:
                            # Remove parentheses and split real/imag parts
                            elem = elem.strip('()')
                            if not elem:  # Skip empty elements
                                continue
                            real, imag = map(float, elem.split(','))
                            row.append(complex(real, imag))
                        except (ValueError, IndexError) as e:
                            print(f"Warning: Could not parse element '{elem}' in {filename}")
                            continue
                    if row:  # Only add non-empty rows
                        matrix.append(row)
                return np.array(matrix) if matrix else None
        except FileNotFoundError:
            print(f"Warning: File {filename} not found")
            return None
        except Exception as e:
            print(f"Error reading {filename}: {str(e)}")
            return None
    
    py_matrix = read_matrix(py_file)
    cpp_matrix = read_matrix(cpp_file)
    
    if py_matrix is None or cpp_matrix is None:
        print(f"Could not compare matrices - one or both files invalid")
        return False
    
    if py_matrix.shape != cpp_matrix.shape:
        print(f"Matrix shapes differ: {py_matrix.shape} vs {cpp_matrix.shape}")
        return False
    
    diff = np.abs(py_matrix - cpp_matrix)
    max_diff = np.max(diff)
    avg_diff = np.mean(diff)
    
    print(f"\nComparing {py_file} vs {cpp_file}:")
    print(f"Maximum difference: {max_diff:.2e}")
    print(f"Average difference: {avg_diff:.2e}")
    print(f"Matrices {'match' if max_diff < tol else 'differ significantly'}")
    
    return max_diff < tol

def save_matrix(matrix, filename, title="Matrix"):
    """Save a complex matrix to a file with proper formatting."""
    with open(filename, 'w') as f:
        f.write(f"{title}\n")
        f.write(f"Dimensions: {matrix.shape}\n")
        f.write("Format: (real,imag)\n")
        if len(matrix.shape) == 1:
            # Handle 1D array (vector)
            for elem in matrix:
                f.write(f"({elem.real:.6e},{elem.imag:.6e}) ")
            f.write("\n")
        else:
            # Handle 2D array (matrix)
            for i in range(matrix.shape[0]):
                for j in range(matrix.shape[1]):
                    elem = matrix[i,j]
                    f.write(f"({elem.real:.6e},{elem.imag:.6e}) ")
                f.write("\n")

def matrices_match(py_matrix, cpp_matrix, tol=1e-6, verbose=False):
    """Check if two matrices match within a tolerance."""
    if py_matrix.shape != cpp_matrix.shape:
        if verbose:
            print("Matrix shapes don't match:", py_matrix.shape, "vs", cpp_matrix.shape)
        return False
    
    diff = np.abs(py_matrix - cpp_matrix)
    max_diff = np.max(diff)
    
    if verbose and max_diff > tol:
        print("Matrices differ by more than {}: max difference = {}".format(tol, max_diff))
        print("\nPython matrix:")
        print(py_matrix)
        print("\nC++ matrix:")
        print(cpp_matrix)
        print("\nDifference matrix:")
        print(diff)
        
        # Find position of maximum difference
        max_pos = np.unravel_index(np.argmax(diff), diff.shape)
        print("\nMaximum difference at position {}:".format(max_pos))
        print("Python value:", py_matrix[max_pos])
        print("C++ value:", cpp_matrix[max_pos])
    
    return max_diff <= tol

def read_matrix_from_file(filename):
    """Read a complex matrix from a file."""
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            # Skip title and dimension lines
            data_lines = [line.strip() for line in lines[3:] if line.strip()]
            matrix = []
            for line in data_lines:
                row = []
                elements = line.split()
                for elem in elements:
                    try:
                        # Remove parentheses and split real/imag parts
                        elem = elem.strip('()')
                        if not elem:  # Skip empty elements
                            continue
                        real, imag = map(float, elem.split(','))
                        row.append(complex(real, imag))
                    except (ValueError, IndexError) as e:
                        print(f"Warning: Could not parse element '{elem}' in {filename}")
                        continue
                if row:  # Only add non-empty rows
                    matrix.append(row)
            return np.array(matrix) if matrix else None
    except FileNotFoundError:
        print(f"Warning: File {filename} not found")
        return None
    except Exception as e:
        print(f"Error reading {filename}: {str(e)}")
        return None

def test4_debug_greens_function():
    """Test Green's function calculation step by step"""
    print("\n=== Test 4: Debugging Green's function calculation ===")
    
    # Initialize QD system
    n_qds = 3
    qd_pos = np.array([
        [0.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [4.0, 0.0, 0.0]
    ])
    e_sites = np.array([1.0, 1.0, 1.0])
    
    # Test parameters
    tip_pos = np.array([1.0, 0.0, 1.0])
    energy = 1.0
    eta = 1e-6  # Small imaginary part for Green's function
    
    # Initialize both implementations
    system_py = LandauerQDs_py(qd_pos, e_sites, K=K, decay=decay, tS=tS, E_sub=E_sub, E_tip=E_tip, tA=tA, eta=eta, Gamma_tip=Gamma_tip, Gamma_sub=Gamma_sub)
    lqd.init(qd_pos, e_sites, K=K, decay=decay, tS=tS, E_sub=E_sub, E_tip=E_tip, tA=tA, eta=eta, Gamma_tip=Gamma_tip, Gamma_sub=Gamma_sub)
    
    print("\nStep 1: Get Hamiltonian without tip")
    h_py = system_py.H_QD_no_tip
    h_cpp = lqd.get_H_QD_no_tip()
    print("Max difference in H_QD:", np.max(np.abs(h_py - h_cpp)))
    save_matrix(h_py, "py_H_QD_no_tip.txt", "H_QD_no_tip (Python)")
    save_matrix(h_cpp, "cpp_H_QD_no_tip.txt", "H_QD_no_tip (C++)")
    if not matrices_match(h_py, h_cpp, verbose=True):
        print("ERROR: H_QD matrices don't match!")
        return False
    
    print("\nStep 2: Get full Hamiltonian with tip")
    h_full_py = system_py.make_full_hamiltonian(tip_pos, Q_tip=Q_tip)
    h_full_cpp = lqd.get_full_H(tip_pos)
    print("Max difference in full H:", np.max(np.abs(h_full_py - h_full_cpp)))
    save_matrix(h_full_py, "py_H_full.txt", "H_full (Python)")
    save_matrix(h_full_cpp, "cpp_H_full.txt", "H_full (C++)")
    if not matrices_match(h_full_py, h_full_cpp, verbose=True):
        print("ERROR: Full H matrices don't match!")
        return False

    print("\nStep 3: Construct (EI - H) matrix")
    # Python calculation
    identity = np.eye(n_qds+2, dtype=np.complex128)
    g_matrix_py = (energy + 1j*eta)*identity - h_full_py
    
    # C++ calculation - we'll save the pre-inversion matrix
    g_matrix_cpp = np.zeros((n_qds+2, n_qds+2), dtype=np.complex128)
    lqd.calculate_greens_function(energy, h_full_cpp, g_matrix_cpp)  # This saves pre-inversion matrix to cpp_pre_inversion.txt
    
    # Load the C++ pre-inversion matrix from file
    g_matrix_cpp = read_matrix_from_file("cpp_pre_inversion.txt")
    
    print("\nPython (EI - H) matrix:")
    print(g_matrix_py)
    print("\nC++ (EI - H) matrix:")
    print(g_matrix_cpp)
    print("\nMax difference in (EI - H):", np.max(np.abs(g_matrix_py - g_matrix_cpp)))
    
    if not matrices_match(g_matrix_py, g_matrix_cpp, verbose=True):
        print("ERROR: (EI - H) matrices don't match!")
        return False
    
    print("\nStep 4: Calculate Green's function G = (EI - H)^(-1)")
    # Python calculation
    g_py = np.linalg.inv(g_matrix_py)
    
    # C++ calculation
    g_cpp = np.zeros((n_qds+2, n_qds+2), dtype=np.complex128)
    lqd.calculate_greens_function(energy, h_full_cpp, g_cpp)  # This performs the full calculation including inversion
    
    print("\nPython Green's function G:")
    print(g_py)
    print("\nC++ Green's function G:")
    print(g_cpp)
    print("\nMax difference in G:", np.max(np.abs(g_py - g_cpp)))
    
    save_matrix(g_py, "py_G.txt", "G (Python)")
    save_matrix(g_cpp, "cpp_G.txt", "G (C++)")
    
    if not matrices_match(g_py, g_cpp, verbose=True):
        print("ERROR: Green's functions don't match!")
        return False
    
    # Verify that G is actually the inverse
    print("\nVerification that G is the inverse:")
    verify_py = np.matmul(g_matrix_py, g_py)
    print("Python G verification (should be identity):")
    print(verify_py)
    verify_cpp = np.matmul(g_matrix_cpp, g_cpp)
    print("C++ G verification (should be identity):")
    print(verify_cpp)
    
    if not matrices_match(verify_py, verify_cpp, tol=1e-6, verbose=True):  # Use higher tolerance for verification
        print("ERROR: G verification matrices don't match!")
        return False
        
    return True

def run_all_tests():
    """Run all comparison tests."""
    passed = 0
    total = 0
    
    print("\n=== Running Green's function debug test ===")
    if test4_debug_greens_function():
        print("Green's function test passed!")
        passed += 1
    else:
        print("Green's function test failed!")
    total += 1
    
    # Return early if Green's function test fails
    if passed != total:
        print(f"\nTests completed: {passed}/{total} passed")
        return False
        
    # ===== Setup geometry =====
    # QD positions in triangle
    phis = np.linspace(0, 2*np.pi, nsite, endpoint=False)
    QDpos = np.zeros((nsite, 3))
    QDpos[:,0] = np.cos(phis)*R
    QDpos[:,1] = np.sin(phis)*R

    print("\n=== Test Setup ===")
    print("QD positions:")
    print(QDpos)
    print("\nTip position:")
    print(tip_pos)

    # ===== Initialize both implementations =====
    print("\n=== Initializing Systems ===")
    # Python implementation
    system_py = LandauerQDs_py(QDpos, E0QDs, K=K, decay=decay, tS=tS,  E_sub=E_sub, E_tip=E_tip, tA=tA,  eta=eta, Gamma_tip=Gamma_tip, Gamma_sub=Gamma_sub)

    # C++ implementation
    lqd.init(QDpos, E0QDs, K=K, decay=decay, tS=tS, E_sub=E_sub, E_tip=E_tip, tA=tA, eta=eta, Gamma_tip=Gamma_tip, Gamma_sub=Gamma_sub)

    # ===== Test 1: Initial Hamiltonian without tip =====
    print("\n=== Test 1: Initial Hamiltonian without tip ===")
    H_py  = system_py.H_QD_no_tip
    H_cpp = lqd.get_H_QD_no_tip()
    save_matrix(H_py,  "py_H_QD_no_tip.txt",  "H_QD_no_tip (Python)")
    save_matrix(H_cpp, "cpp_H_QD_no_tip.txt", "H_QD_no_tip (C++)")
    total += 1
    if print_comparison("H_QD_no_tip", H_py, H_cpp):
        passed += 1

    # ===== Test 2: Tip coupling calculation =====
    print("\n=== Test 2: Tip coupling calculation ===")
    tip_coupling_py  = system_py.calculate_tip_coupling(tip_pos)
    tip_coupling_cpp = lqd.get_tip_coupling(tip_pos)
    save_matrix(tip_coupling_py,  "py_tip_coupling.txt",  "Tip coupling (Python)")
    save_matrix(tip_coupling_cpp, "cpp_tip_coupling.txt", "Tip coupling (C++)")
    total += 1
    if print_comparison("Tip coupling", tip_coupling_py, tip_coupling_cpp):
        passed += 1

    # ===== Test 3: Full Hamiltonian assembly =====
    print("\n=== Test 3: Full Hamiltonian assembly ===")
    H_full_py  = system_py.make_full_hamiltonian(tip_pos, Q_tip=Q_tip)  
    H_full_cpp = lqd.get_full_H(tip_pos)
    save_matrix(H_full_py,  "py_H_full.txt",  "Full Hamiltonian (Python)")
    save_matrix(H_full_cpp, "cpp_H_full.txt", "Full Hamiltonian (C++)")
    total += 1
    if print_comparison("Full Hamiltonian", H_full_py, H_full_cpp, ignore_imag=True):
        passed += 1

    # ===== Test 4: Single energy transmission =====
    E_test = 0.0
    print(f"\n=== Test 4: Transmission at E = {E_test} ===\n")
    
    # Calculate Green's function
    G_py = system_py.calculate_greens_function(E_test, H_full_py)
    save_matrix(G_py, "py_G.txt", "G (Python)")
    
    G_dag_py = np.conjugate(G_py.T)
    save_matrix(G_dag_py, "py_G_dag.txt", "G_dag (Python)")
    
    # Get coupling matrices
    Gamma_s_py, Gamma_t_py = system_py._calculate_coupling_matrices()
    save_matrix(Gamma_s_py, "py_Gamma_s.txt", "Gamma_s (Python)")
    save_matrix(Gamma_t_py, "py_Gamma_t.txt", "Gamma_t (Python)")
    
    # Calculate transmission step by step
    temp1 = Gamma_t_py @ G_dag_py
    save_matrix(temp1, "py_Gamma_t_G_dag.txt", "Gamma_t @ G_dag (Python)")
    
    temp2 = G_py @ temp1
    save_matrix(temp2, "py_G_Gamma_t_G_dag.txt", "G @ Gamma_t @ G_dag (Python)")
    
    temp3 = Gamma_s_py @ temp2
    save_matrix(temp3, "py_final.txt", "Gamma_s @ G @ Gamma_t @ G_dag (Python)")
    
    T_py = np.trace(temp3).real
    print(f"\nTransmission (Python): {T_py}")
    
    # C++ implementation
    tip_pos_arr = np.array([tip_pos])
    energies_arr = np.array([E_test])
    H_QDs = np.zeros((1, len(QDpos)+1, len(QDpos)+1), dtype=np.float64)
    trans_cpp = lqd.calculate_transmissions(tip_pos_arr, energies_arr, H_QDs)[0,0]
    
    total += 1
    if print_comparison("Transmission", np.array([T_py]), np.array([trans_cpp]), tol=1e-2, relative=True):
        passed += 1

    # Compare all intermediate matrices
    print("\n=== Comparing All Intermediate Matrices ===")
    matrices_match = True
    for name in ["H_QD_no_tip", "tip_coupling", "H_full", "G", "G_dag", "Gamma_t", 
                "Gamma_t_G_dag", "G_Gamma_t_G_dag", "Gamma_s", "final"]:
        py_file = f"py_{name}.txt"
        cpp_file = f"cpp_{name}.txt"
        print(f"\nComparing {name}:")
        if compare_matrix_files(py_file, cpp_file):
            print(f"{name} matrices match")
        else:
            print(f"{name} matrices differ")
            matrices_match = False
    
    if matrices_match:
        passed += 1
    total += 1

    # Clean up C++ resources
    lqd.cleanup()

    print(f"\n=== Final Results ===")
    print(f"Passed {passed} out of {total} tests")
    return passed == total

if __name__ == "__main__":
    run_all_tests()
