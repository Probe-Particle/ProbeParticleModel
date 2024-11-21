import numpy as np
from ctypes import c_int, c_double, c_bool, c_void_p
import ctypes
import os
from . import cpp_utils

cpp_name = 'LandauerQD'
cpp_utils.make('landauer')
lib = ctypes.CDLL(cpp_utils.CPP_PATH + "/" + cpp_name + cpp_utils.lib_ext)

array1d = np.ctypeslib.ndpointer(dtype=np.double, ndim=1, flags='CONTIGUOUS')
array2d = np.ctypeslib.ndpointer(dtype=np.double, ndim=2, flags='CONTIGUOUS')
array3d = np.ctypeslib.ndpointer(dtype=np.double, ndim=3, flags='CONTIGUOUS')

# Global variable to store number of quantum dots
_n_qds = None

# Initialize system
lib.initLandauerQDs.argtypes = [c_int, array2d, array1d, 
                               c_double, c_double, c_double,
                               c_double, c_double, c_double,
                               c_double, c_double, c_double]
lib.initLandauerQDs.restype = None

def init(QDpos, Esite, K=0.01, decay=1.0, tS=0.01,  E_sub=0.0, E_tip=0.0, tA=0.1, eta=0.0, Gamma_tip=1.0, Gamma_sub=1.0):
    """Initialize the LandauerQDs system.
    
    Args:
        QDpos: array[n_qds, 3] - Positions of quantum dots
        Esite: array[n_qds] - On-site energies
        K: float - Coulomb interaction between QDs
        decay: float - Decay constant for tip-QD coupling
        tS: float - Coupling strength to substrate
        E_sub: float - Substrate energy level
        E_tip: float - Tip energy level
        tA: float - Tip coupling strength prefactor
        eta: float - Infinitesimal broadening parameter
        Gamma_tip: float - Broadening of tip state
        Gamma_sub: float - Broadening of substrate state
    """
    global _n_qds
    _n_qds = len(QDpos)
    QDpos = np.ascontiguousarray(QDpos, dtype=np.float64)
    Esite = np.ascontiguousarray(Esite, dtype=np.float64)
    lib.initLandauerQDs(_n_qds, QDpos, Esite, K, decay, tS,
                       E_sub, E_tip, tA, eta, Gamma_tip, Gamma_sub)

# Clean up
lib.deleteLandauerQDs.argtypes = []
lib.deleteLandauerQDs.restype = None

def cleanup():
    """Clean up the LandauerQDs system."""
    global _n_qds
    lib.deleteLandauerQDs()
    _n_qds = None

# Calculate transmissions
lib.calculateTransmissions.argtypes = [c_int, array2d, array1d, c_int, array1d, array1d]
lib.calculateTransmissions.restype = None

def calculate_transmissions(ptips, energies, H_QDs=None):
    """Calculate transmission for multiple tip positions and energies.
    
    Args:
        ptips: array[n_pos, 3] - Tip positions
        energies: array[n_E] - Energy values
        H_QDs: array[n_pos, n_qds+1, n_qds+1] - Optional pre-computed Hamiltonians
        
    Returns:
        array[n_pos, n_E] - Transmission values
    """
    if _n_qds is None:
        raise RuntimeError("System not initialized. Call init() first.")
        
    npos = len(ptips)
    nE = len(energies)
    ptips = np.ascontiguousarray(ptips, dtype=np.float64)
    energies = np.ascontiguousarray(energies, dtype=np.float64)
    transmissions = np.zeros(npos * nE, dtype=np.float64)  # 1D for C++
    
    if H_QDs is not None:
        # Flatten H_QDs to 1D for C++
        H_QDs = np.ascontiguousarray(H_QDs, dtype=np.float64).reshape(-1)
    
    lib.calculateTransmissions(npos, ptips, energies, nE, H_QDs, transmissions)
    return transmissions.reshape(npos, nE)  # Reshape back to 2D

# Solve Hamiltonians
lib.solveHamiltonians.argtypes = [c_int, array2d, array1d, array1d, array1d, array1d, array1d, array1d]
lib.solveHamiltonians.restype = None

def solve_hamiltonians(ptips, Qtips, Qsites=None, get_evals=False, get_evecs=False, get_H=True, get_G=False):
    """Solve Hamiltonians for multiple tip positions.
    
    Args:
        ptips: array[n_pos, 3] - Tip positions
        Qtips: array[n_pos] - Tip charges
        Qsites: array[n_pos, n_qds] - Optional site charges
        get_evals: bool - Return eigenvalues
        get_evecs: bool - Return eigenvectors
        get_H: bool - Return Hamiltonians
        get_G: bool - Return Green's functions
        
    Returns:
        tuple of requested arrays
    """
    if _n_qds is None:
        raise RuntimeError("System not initialized. Call init() first.")
        
    npos = len(ptips)
    ptips = np.ascontiguousarray(ptips, dtype=np.float64)
    Qtips = np.ascontiguousarray(Qtips, dtype=np.float64)
    
    if Qsites is not None:
        # Flatten Qsites to 1D for C++
        Qsites = np.ascontiguousarray(Qsites, dtype=np.float64).reshape(-1)
    
    # Always create arrays for C++, even if we don't need them
    evals = np.zeros(npos, dtype=np.float64)
    evecs = np.zeros(npos * _n_qds, dtype=np.float64)
    Hs = np.zeros(npos * (_n_qds+1) * (_n_qds+1), dtype=np.float64)
    Gs = np.zeros(npos * (_n_qds+1) * (_n_qds+1), dtype=np.float64)
    
    lib.solveHamiltonians(npos, ptips, Qtips, Qsites, evals, evecs, Hs, Gs)
    
    results = []
    if get_evals: results.append(evals)
    if get_evecs: results.append(evecs.reshape(npos, _n_qds))  # Reshape back to 2D
    if get_H: results.append(Hs.reshape(npos, _n_qds+1, _n_qds+1))  # Reshape back to 3D
    if get_G: results.append(Gs.reshape(npos, _n_qds+1, _n_qds+1))  # Reshape back to 3D
    
    return tuple(results) if len(results) > 1 else results[0]

# Solve site occupancies
lib.solveSiteOccupancies.argtypes = [c_int, array2d, array1d, array1d]
lib.solveSiteOccupancies.restype = None

def solve_site_occupancies(ptips, Qtips):
    """Solve site occupancies for multiple tip positions.
    
    Args:
        ptips: array[n_pos, 3] - Tip positions
        Qtips: array[n_pos] - Tip charges
        
    Returns:
        array[n_pos, n_qds] - Site occupancies
    """
    if _n_qds is None:
        raise RuntimeError("System not initialized. Call init() first.")
        
    npos = len(ptips)
    ptips = np.ascontiguousarray(ptips, dtype=np.float64)
    Qtips = np.ascontiguousarray(Qtips, dtype=np.float64)
    Qout = np.zeros(npos * _n_qds, dtype=np.float64)  # Make it 1D for C++
    
    lib.solveSiteOccupancies(npos, ptips, Qtips, Qout)
    return Qout.reshape(npos, _n_qds)  # Reshape back to 2D for Python
