"""
    Module Name:
        diffcorr
    Purpose:
        Provide functions and classes that aid in the process of
        Diffraction Correction / Fresnel Inversion. Additional
        functions for the purpose of forward modelling of
        reconstructed data and diffraction modelling are included.
        Several low-level functions that perform error checks for
        the main functions also exist, as well as functions that
        enable running shell scripts in Python.
    
    Window (Taper) Functions:
        rect................Rectangular window.
        coss................Squared cossine window.
        kb20................Kaiser-Bessel 2.0 window.
        kb25................Kaiser-Bessel 2.5 window.
        kb35................Kaiser-Bessel 3.5 window.
        kbmd20..............Modified Kaiser-Bessel 2.0 window.
        kbmd25..............Modified Kaiser-Bessel 2.5 window.

    Error Checks:
        check_boole.........Checks for Boolean input.
        check_ternary.......Checks for Ternary input.
        check_pos_real......Checks for a single positive real input.
        check_real..........Checks if input is real (Number/Array).
        check_complex.......Checks if input is complex.
    
    Special Functions:
        fresnel_sin.........The Fresnel sine integral.
        fresnel_cos.........The Fresnel cosine integral.
        sq_well_solve.......Diffraction pattern through square well.

    Mathematical Functions:
        compute_norm_eq.....Computes the normalized equivalent width.
        get_norm_eq.........Quickly retrieve pre-computed normalized
                            equivalent widths from strings with the
                            name of common window functions.
        resolution_inverse..Computes the inverse of the function
                            y = x/(exp(-x)+x-1)
        power_func..........Compute power from complex transmittance.
        phase_func..........Compute phase from complex transmittance.
        tau_func............Compute normalized optical depth from the
                            complex transmittance.
        wker................Computes a weighted kernel function.
        freq_wav............Convert frequency to wavelength, and
                            vice-versa. Kilometers or Herts only.
        fresnel_scale.......Compute the Fresnel scale.
    
    Miscellaneous Functions:
        get_range_request...Computes an array of the form [a,b] from
                            a given array, list, or from a set of
                            allowed strings.
        get_range_actual....Given an array of numbers (usually the
                            radial range of the data), a range
                            request, and a window width, compute the
                            allowed range of processing.
"""

# Import advanced tools used for optimization and modeling.
try:
    from .advanced_tools import compare_tau,find_optimal_resolution
    from .advanced_tools import delta_impulse_diffraction
except ModuleNotFoundError:pass

# Import miscellaneous tools used for range and normalized equivalent width.
try:
    from .misc_functions import get_range_request,get_norm_eq,get_range_actual
except ModuleNotFoundError:pass

# Import functions that pertain to physics and diffraction theory.
try:
    from .physics_functions import power_func,phase_func,tau_func,wker
    from .physics_functions import freq_wav,fresnel_forward,fresnel_inverse
    from .physics_functions import compute_norm_eq,fresnel_scale,psi_factor
    from .physics_functions import psi_d1_phi,psi_d2_phi,fresnel_transform
    from .physics_functions import fresnel_inverse,fresnel_inverse_fft,psi
except ModuleNotFoundError:pass

# Import special mathematical functions that are used in diffraction theory.
try:
    from .special_functions import resolution_inverse,sq_well_solve
    from .special_functions import fresnel_cos,fresnel_sin
except ModuleNotFoundError:pass

# Import taper/window functions used in reconstruction and modeling.
try:
    from .window_functions import rect,coss,kb20,kb25,kb35,kbmd20,kbmd25
    from .window_functions import kbal,window_width,normalize
except ModuleNotFoundError:pass

# Import the main classes used in diffraction reconstruction.
from .diffraction_correction import diffraction_correction,rec_data