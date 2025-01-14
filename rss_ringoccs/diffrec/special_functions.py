import numpy as np
from scipy.special import erf, lambertw
from . import window_functions

# Declare constants for multiples of pi.
TWO_PI = 6.283185307179586476925287
ONE_PI = 3.141592653589793238462643
SQRT_PI_2 = 1.253314137315500251207883
RADS_PER_DEGS = 0.0174532925199432957692369

def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    """
        Purpose:
            To smooth data with a Savitzky-Golay filter.
            This removes high frequency noise while
            maintaining many of the original features of
            the input data.
        Arguments:
            :y (*np.ndarray*):
                The input "Noisy" data.
            :window_size (*int*):
                The length of the window.
                Must be an odd number.
            :order (*int*):
                The order of the polynomial used for filtering.
                Must be less then window_size - 1.
        Keywords:
            :deriv (*int*):
                The order of the derivative what will be computed.
        Output:
            :y_smooth (*np.ndarray*):
                The data smoothed by the Savitzky-Golay filter.
                This returns the nth derivative if the deriv
                keyword has been set.
        Notes:
            The Savitzky-Golay is a type of low-pass filter,
            particularly suited for smoothing noisy data.
            The main idea behind this approach is to make for
            each point a least-square fit with a polynomial of
            high order over a odd-sized window centered at the point.
    """
    try:
        y = np.array(y)
    except:
        raise TypeError(
            "\n\tError Encountered:\n"
            "\trss_ringoccs: Diffrec Subpackage\n"
            "\tspecial_functions.savitzky_golay\n"
            "\tinput variable should be a numpy array."
            "\tSyntax:\n"
            "\t\tysmooth = savitzky_golay(y, Window_Size, Poly_Order)"
        )
    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except (ValueError, TypeError):
        raise ValueError(
            "\n\tError Encountered:\n"
            "\trss_ringoccs: Diffrec Subpackage\n"
            "\tspecial_functions.savitzky_golay:\n"
            "\t\twindow_size must be an odd integer.\n"
        )

    if (window_size % 2 != 1) or (window_size < 1):
        raise ValueError(
            "\n\tError Encountered:\n"
            "\trss_ringoccs: Diffrec Subpackage\n"
            "\tspecial_functions.savitzky_golar:\n"
            "\t\twindow_size must be an odd integer.\n"
        )
    elif (window_size < order + 2):
        raise ValueError(
            "\n\tError Encountered:\n"
            "\trss_ringoccs: Diffrec Subpackage\n"
            "\tspecial_functions.savitzky_golar:\n"
            "\t\twindow_size is too small for the\n"
            "\t\trequested polynomial order.\n"
        )
    else:
        pass

    half_window = (window_size - 1) // 2

    # precompute coefficients
    b = np.zeros((window_size, order+1))
    b[..., 0] = 1
    for k in range(half_window):
        n0 = (half_window) - k
        m = n0
        n = -n0
        for j in range(1, order+1):
            b[k, j] = n
            b[window_size-1-k, j] = m
            n *= -n0
            m *= n0

    b = np.mat(b)

    m = 1
    for i in range(deriv):
        m *= rate*(deriv-i)

    m *= np.linalg.pinv(b).A[deriv]

    # Pad the endpoints with values from the signal.
    firstvals = y[0] - np.abs(y[1:half_window+1][::-1] - y[0])
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))

    return np.convolve(m[::-1], y, mode='valid')

def compute_norm_eq(w_func, error_check=True):
    """
        Purpose:
            Compute normalized equivalenth width of a given function.
        Arguments:
            :w_func (*np.ndarray*):
                Function with which to compute
                the normalized equivalent width of.
        Outputs:
            :normeq (*float*):
                The normalized equivalent width of w_func.
        Notes:
            The normalized equivalent width is effectively computed
            using Riemann sums to approximate integrals. Therefore
            large dx values (Spacing between points in w_func)
            will result in an inaccurate normeq. One should keep
            this in mind during calculations.
        Examples:
            Compute the Kaiser-Bessel 2.5 window of width 30
            and spacing 0.1, and then use compute_norm_eq
            to compute the normalized equivalent width:
                In [1]: from rss_ringoccs import diffrec as dc
                In [2]: w = dc.window_functions.kb25(30, 0.1)
                In [3]: normeq = dc.special_functions.compute_norm_eq(w)
                In [4]: print(normeq)
                1.6573619266424229
            In contrast, the actual value is 1.6519208.
            Compute the normalized equivalent width for the squared
            cosine window of width 10 and spacing 0.25.
                In [1]: from rss_ringoccs import diffrec as dc
                In [2]: w = dc.window_functions.coss(10, 0.25)
                In [3]: normeq = dc.special_functions.compute_norm_eq(w)
                In [4]: print(normeq)
                1.5375000000000003
            The normalized equivalent width of the squared cosine
            function can be computed exactly using standard methods
            from a calculus course. It's value is exactly 1.5
            If we use a smaller dx when computing w, we get a better
            approximation. Use width 10 and spacing 0.001.
                In [1]: from rss_ringoccs import diffrec as dc
                In [2]: w = dc.window_functions.coss(10, 0.001)
                In [3]: normeq = dc.special_functions.compute_norm_eq(w)
                In [4]: print(normeq)
                1.50015
    """
    if error_check:
        try:
            w_func = np.array(w_func)
        except (ValueError, TypeError):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.compute_norm_eq:\n"
                "\t\tFirst input could not be converted\n"
                "\t\tinto a numpy array.\n"
            )

        if (not np.all(np.isreal(w_func))):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.compute_norm_eq:\n"
                "\t\tFirst input must be an array\n"
                "\t\tof floating point numbers.\n"
            )
        elif (np.min(w_func) < 0.0):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.compute_norm_eq:\n"
                "\t\tFirst input must be an array\n"
                "\t\tof positive numbers.\n"
            )
        else:
            pass
    nw = np.size(w_func)
    tot = np.sum(w_func)
    normeq = nw*(np.sum(w_func*w_func)) / (tot*tot)

    return normeq

def fresnel_scale(Lambda, d, phi, b, deg=False, error_check=True):
    """
        Purpose:
            Compute the Fresnel Scale from lambda, D, Phi, and B.
        Arguments:
            :Lambda (*np.ndarray* or *float*):
                Wavelength of the incoming signal.
            :d (*np.ndarray* or *float*):
                RIP-Spacecraft Distance.
            :phi (*np.ndarray* or *float*):
                Ring azimuth angle.
            :b (*np.ndarray* or *float*):
                Ring opening angle.
        Keywords:
            :deg (*bool*):
                Set True if phi/b are in degrees.
                Default is radians.
        Output:
            :fres (*np.ndarray* or *float*):
                The Fresnel scale.
        Note:
            Lambda and d must be in the same units.
            The output (Fresnel scale) will have the same units
            as lambda and d. In addition, b and phi must also
            have the same units. If b and phi are in degrees,
            make sure to set deg=True. Default is radians.
    """
    if error_check:
        try:
            Lambda = np.array(Lambda)
        except (ValueError, TypeError):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.fresnel_scale:\n"
                "\t\tFirst input could not be converted\n"
                "\t\tinto a numpy array.\n"
            )

        if (not np.all(np.isreal(Lambda))):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.fresnel_scale:\n"
                "\t\tFirst input must be an array\n"
                "\t\tof floating point numbers.\n"
            )
        elif (np.min(Lambda) < 0.0):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.fresnel_scale:\n"
                "\t\tFirst input must be an array\n"
                "\t\tof positive numbers.\n"
            )
        else:
            pass

        try:
            d = np.array(d)
        except (ValueError, TypeError):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.fresnel_scale:\n"
                "\t\tSecond input could not be converted\n"
                "\t\tinto a numpy array.\n"
            )

        if (not np.all(np.isreal(d))):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.fresnel_scale:\n"
                "\t\tSecond input must be an array\n"
                "\t\tof floating point numbers.\n"
            )
        elif (np.min(d) < 0.0):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.fresnel_scale:\n"
                "\t\tSecond input must be an array\n"
                "\t\tof positive numbers.\n"
            )
        else:
            pass

        try:
            phi = np.array(phi)
        except (ValueError, TypeError):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.fresnel_scale:\n"
                "\t\tThird input could not be converted\n"
                "\t\tinto a numpy array.\n"
            )

        if (not np.all(np.isreal(phi))):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.fresnel_scale:\n"
                "\t\tThird input must be an array\n"
                "\t\tof floating point numbers.\n"
            )
        else:
            pass

        try:
            b = np.array(b)
        except (ValueError, TypeError):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.fresnel_scale:\n"
                "\t\tSecond input could not be converted\n"
                "\t\tinto a numpy array.\n"
            )

        if (not np.all(np.isreal(b))):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.fresnel_scale:\n"
                "\t\tSecond input must be an array\n"
                "\t\tof floating point number.\n"
            )
        else:
            pass
    else:
        pass

    if deg:
        cb = np.cos(b * RADS_PER_DEGS)
        sb = np.sin(b * RADS_PER_DEGS)
        sp = np.sin(phi * RADS_PER_DEGS)
    else:
        cb = np.cos(b)
        sb = np.sin(b)
        sp = np.sin(phi)

    fres = np.sqrt(0.5 * Lambda * d * (1 - (cb*cb) * (sp*sp)) / (sb*sb))
    return fres

def fresnel_inverse(T_hat, ker, dx, f_scale):
    """
        Purpose:
            Compute the approximation Fresnel
            Inverse (MTR86 Equation 15)
        Arguments:
            :T_hat (*np.ndarray*):
                The complex transmittance of the
                normalized diffraction data.
            :ker (*np.ndarray*):
                he Fresnel Kernel.
            :dx (*float*):
                The spacing between points in the window.
                This is equivalent to the sample spacing.
                This value is in kilometers.
            :f_scale (*np.ndarray*):
                The Fresnel Scale, in kilometers.
        Outputs:
            :T (*complex*):
                The fresnel inversion about the center
                of the Fresnel Kernel.
    """
    T = np.sum(ker * T_hat) * dx * (1.0+1.0j) / (2.0 * f_scale)
    return T

def psi_func(kD, r, r0, phi, phi0, B, D, error_check=True):
    """
        Purpose:
            Calculate psi from geometry variables.
        Arguments:
            :r (*np.ndarray*):
                Ring radius variable, in kilometers.
            :r0 (*float*):
                Ring intercept point, in kilometers.
            :d (*float*):
                RIP-Spacecraft distance in kilometers.
            :b (*float*):
                The ring opening angle, in radians.
            :phi (*np.ndarray*):
                The ring azimuth angle or r, in radians.
            :phi0 (*np.ndarray*):
                The ring azimuth angle for r0, in radians.
        Keywords:
            :verbose (*bool*):
                Boolean for printing out information to
                the command line.
        Outputs:
            :psi (*np.ndarray*):
                Geometric quantity found in the Fresnel kernel.
    """
    if error_check:
        try:
            r = np.array(r)
        except (ValueError, TypeError):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tFirst input could not be converted\n"
                "\t\tinto a numpy array.\n"
            )

        if (not np.all(np.isreal(r))):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tFirst input must be an array\n"
                "\t\tof floating point number.\n"
            )
        elif (np.min(r) < 0.0):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tFirst input must be an array\n"
                "\t\tof positive numbers.\n"
            )
        else:
            pass
        
        try:
            r0 = np.array(r0)
        except (ValueError, TypeError):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tSecond input could not be converted\n"
                "\t\tinto a numpy array.\n"
            )

        if (not np.all(np.isreal(r0))):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tFirst input must be an array\n"
                "\t\tof floating point number.\n"
            )
        elif (np.min(r0) < 0.0):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tFirst input must be an array\n"
                "\t\tof positive numbers.\n"
            )
        else:
            pass
        
        try:
            D = np.array(D)
        except (ValueError, TypeError):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tThird input could not be converted\n"
                "\t\tinto a numpy array.\n"
            )

        if (not np.all(np.isreal(D))):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tThird input must be an array\n"
                "\t\tof floating point number.\n"
            )
        elif (np.min(D) < 0.0):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tThird input must be an array\n"
                "\t\tof positive numbers.\n"
            )
        else:
            pass

        try:
            B = np.array(B)
        except (ValueError, TypeError):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tFourth input could not be converted\n"
                "\t\tinto a numpy array.\n"
            )

        if (not np.all(np.isreal(B))):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tFourth input must be an array\n"
                "\t\tof floating point number.\n"
            )
        else:
            pass

        try:
            phi = np.array(phi)
        except (ValueError, TypeError):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tFifth input could not be converted\n"
                "\t\tinto a numpy array.\n"
            )

        if (not np.all(np.isreal(phi))):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffrec Subpackage\n"
                "\tspecial_functions.psi_d1_phi:\n"
                "\t\tFifth input must be an array\n"
                "\t\tof floating point number.\n"
            )
        else:
            pass

        if (not isinstance(phi0, float)):
            try:
                phi0 = float(phi0)
            except (TypeError, ValueError):
                raise TypeError(
                    "\n\tError Encountered:\n"
                    "\trss_ringoccs: Diffrec Subpackage\n"
                    "\tspecial_functions.psi_d1_phi:\n"
                    "\t\tSecond input must be a positive\n"
                    "\t\tfloating point number.\n"
                )
        else:
            pass
    else:
        pass

    # Compute Xi variable (MTR86 Equation 4b).
    xi = (np.cos(B)/D) * (r * np.cos(phi) - r0 * np.cos(phi0))

    # Compute Eta variable (MTR86 Equation 4c).
    eta = (r0*r0 + r*r - 2.0*r*r0*np.cos(phi-phi0)) / (D*D)
    psi_vals = kD * (np.sqrt(1.0+eta-2.0*xi) - (1.0-xi))
    return psi_vals

def resolution_inverse(x, error_check=True):
    """
        Purpose:
            Compute the inverse of y = x/(exp(-x)+x-1)
        Arguments:
            :x (*np.ndarray* or *float*):
                Independent variable
        Outputs:
            :f (*np.ndarray* or *float*):
                The inverse of x/(exp(-x)+x-1)
        Dependencies:
            #. numpy
            #. scipy.special
        Method:
            The inverse of x/(exp(-x)+x-1) is computed using the
            LambertW function. This function is the inverse of
            y = x * exp(x). This is computed using the scipy.special
            subpackage using their lambertw function.
        Warnings:
            #. The real part of the argument must be greater than 1.
            #. The scipy.special lambertw function is slightly
               inaccurate when it's argument is near -1/e. This
               argument is z = exp(x/(1-x)) * x/(1-x)
        Examples:
            Plot the function on the interval (1,2)
                In [1]: import rss_ringoccs.diffcorr.special_functions as sf
                In [2]: import numpy as np
                In [3]: x = np.array(range(0,1001))*0.001+1.01
                In [4]: y = sf.resolution_inverse(x)
                In [5]: import matplotlib.pyplot as plt
                In [6]: plt.show(plt.plot(x,y))
                (Beautiful plots appear here)
    """
    if error_check:
        y = x
        try:
            x = np.array(x)
            if (not np.all(np.isreal(x))) and (not np.all(np.iscomplex(x))):
                raise TypeError(
                    "\n\tError Encountered:\n"
                    "\trss_ringoccs: Diffcorr Subpackage\n"
                    "\tspecial_function.resolution_inverse:\n"
                    "\t\tInput must be a real or complex valued numpy array.\n"
                    "\t\tThe elements of your array have type: %s"
                    % (x.dtype)
                )
            else:
                del y
        except (TypeError, ValueError) as errmes:
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffcorr Subpackage\n"
                "\tspecial_function.resolution_inverse:\n"
                "\t\tInput must be a real or complex valued numpy array.\n"
                "\t\tYour input has type: %s\n"
                "\tOriginal Error Mesage: %s\n"
                % (type(y).__name__, errmes)
            )
        if (np.min(np.real(x)) <= 1.0):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffcorr Subpackage\n"
                "\tspecial_function.resolution_inverse:\n"
                "\t\tThis function is only defined for inputs\n"
                "\t\twhose real part is greater than 1.\n"
                "\t\tYour input has real minimum: %f\n"
                % (np.min(np.real(x)))
            )
        else:
            pass

    P1 = x/(1.0-x)
    P2 = P1*np.exp(P1)
    f = lambertw(P2)-P1

    if np.all(np.isreal(x)):
        f = np.real(f)

    return f

def fresnel_cos(x, error_check=True):
    """
        Purpose:
            Compute the Fresnel cosine function.
        Arguments:
            :x (*np.ndarray* or *float*):
                A real or complex number, or numpy array.
        Outputs:
            :f_cos (*np.ndarray* or *float*):
                The fresnel cosine integral of x.
        Notes:
            [1] The Fresnel Cosine integral is the solution to the
                equation dy/dx = cos(pi/2 * x^2), y(0) = 0. In other
                words, y = integral (t=0 to x) cos(pi/2 * t^2) dt
            [2] The Fresnel Cosine and Sine integrals are computed by
                using the scipy.special Error Function. The Error
                Function, usually denoted Erf(x), is the solution to
                dy/dx = (2/sqrt(pi)) * exp(-x^2), y(0) = 0. That is:
                y = 2/sqrt(pi) * integral (t=0 to x) exp(-t^2)dt.
                Using Euler's Formula for exponentials allows one
                to use this to solve for the Fresnel Cosine integral.
            [3] The Fresnel Cosine integral is used for the solution
                of diffraction through a square well. Because of this
                it is useful for forward modeling problems in 
                radiative transfer and diffraction.
        Examples:
            Compute and plot the Fresnel Cosine integral.
                In [1]: import rss_ringoccs.diffcorr.special_functions as sf
                In [2]: import numpy as np
                In [3]: import matplotlib.pyplot as plt
                In [4]: x = np.array(range(0,10001))*0.01 - 50.0
                In [5]: y = sf.fresnel_cos(x)
                In [6]: plt.show(plt.plot(x,y))
    """
    if error_check:
        y = x
        try:
            x = np.array(x)
            if (not np.all(np.isreal(x))) and (not np.all(np.iscomplex(x))):
                raise TypeError(
                    "\n\tError Encountered:\n"
                    "\trss_ringoccs: Diffcorr Subpackage\n"
                    "\tspecial_functions.fresnel_cos:\n"
                    "\t\tInput must be a real or complex valued numpy array.\n"
                    "\t\tThe elements of your array have type: %s"
                    % (x.dtype)
                )
            else:
                del y
        except (TypeError, ValueError) as errmes:
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffcorr Subpackage\n"
                "\tspecial_function.fresnel_cos:\n"
                "\t\tInput must be a real or complex valued numpy array.\n"
                "\t\tYour input has type: %s\n"
                "\tOriginal Error Mesage: %s\n"
                % (type(y).__name__, errmes)
            )
    else:
        pass

    f_cos = ((0.25-0.25j)*erf((1.0+1.0j)*x*SQRT_PI_2)+
             (0.25+0.25j)*erf((1.0-1.0j)*x*SQRT_PI_2))

    if (np.isreal(x).all()):
        f_cos = np.real(f_cos)

    return f_cos

def fresnel_sin(x, error_check=True):
    """
        Purpose:
            Compute the Fresnel sine function.
        Variables:
            :x (*np.ndarray* or *float*):
                The independent variable.
        Outputs:
            :f_sin (*np.ndarray* or *float*):
                The fresnel sine integral of x.
        Notes:
            [1] The Fresnel sine integral is the solution to the
                equation dy/dx = sin(pi/2 * x^2), y(0) = 0. In other
                words, y = integral (t=0 to x) sin(pi/2 * t^2) dt
            [2] The Fresnel Cossine and Sine integrals are computed
                by using the scipy.special Error Function. The Error
                Function, usually denoted Erf(x), is the solution to
                dy/dx = (2/sqrt(pi)) * exp(-x^2), y(0) = 0. That is:
                y = 2/sqrt(pi) * integral (t=0 to x) exp(-t^2)dt.
                Using Euler's Formula for exponentials allows one
                to use this to solve for the Fresnel Sine integral.
            [3] The Fresnel sine integral is used for the solution
                of diffraction through a square well. Because of this
                is is useful for forward modeling problems in 
                radiative transfer and diffraction.
        Examples:
            Compute and plot the Fresnel Sine integral.
                In [1]: import rss_ringoccs.diffcorr.special_functions as sf
                In [2]: import numpy as np
                In [3]: import matplotlib.pyplot as plt
                In [4]: x = np.array(range(0,10001))*0.01 - 50.0
                In [5]: y = sf.fresnel_sin(x)
                In [6]: plt.show(plt.plot(x,y))
    """
    if error_check:
        y = x
        try:
            x = np.array(x)
            if (not np.all(np.isreal(x))) and (not np.all(np.iscomplex(x))):
                raise TypeError(
                    "\n\tError Encountered:\n"
                    "\trss_ringoccs: Diffcorr Subpackage\n"
                    "\tspecial_function.fresnel_cos:\n"
                    "\t\tInput must be a real or complex valued numpy array.\n"
                    "\t\tThe elements of your array have type: %s"
                    % (x.dtype)
                )
            else:
                del y
        except (TypeError, ValueError) as errmes:
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffcorr Subpackage\n"
                "\tspecial_function.fresnel_cos:\n"
                "\t\tInput must be a real or complex valued numpy array.\n"
                "\t\tYour input has type: %s\n"
                "\tOriginal Error Mesage: %s\n"
                % (type(y).__name__, errmes)
            )
    else:
        pass

    f_sin = ((0.25+0.25j)*erf((1.0+1.0j)*x*SQRT_PI_2)+
             (0.25-0.25j)*erf((1.0-1.0j)*x*SQRT_PI_2))

    if (np.isreal(x).all()):
        f_sin = np.real(f_sin)

    return f_sin

def single_slit_diffraction(x, z, a):
    """
        Purpose:
            Compute diffraction through a single slit for the
            variable x with a distance z from the slit and
            slit parameter a. This assume Fraunhofer diffraction.
        Variables:
            :x:
                A real or complex argument, or numpy array.
            :z (*float*):
                Float
                The perpendicular distance from the slit plane to
                the observer.
            :a (*float*):
                The slit parameter. This is a unitless paramter
                defined as the ratio between the slit width and
                the wavelength of the incoming signal.
        Outputs:
            :f:
                Single slit diffraction pattern.
        Dependences:
            [1] numpy
    """
    y = x
    try:
        x = np.array(x)
        if (not np.all(np.isreal(x))) and (not np.all(np.iscomplex(x))):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffcorr Subpackage\n"
                "\tspecial_function.single_slit_diffraction_solve:\n"
                "\t\tInput must be a real or complex valued numpy array.\n"
                "\t\tThe elements of your array have type: %s"
                % (x.dtype)
            )
        else:
            del y
    except (TypeError, ValueError) as errmes:
        raise TypeError(
            "\n\tError Encountered:\n"
            "\trss_ringoccs: Diffcorr Subpackage\n"
            "\tspecial_function.single_slit_diffraction_solve:\n"
            "\t\tFirst input must be a real or complex valued numpy array.\n"
            "\t\tYour input has type: %s\n"
            "\tOriginal Error Mesage: %s\n"
            % (type(y).__name__, errmes)
        )
    if not (isinstance(z, float)):
        try:
            z = float(z)
        except ValueError:
            raise ValueError(
            "\n\tError Encountered:\n"
            "\trss_ringoccs: Diffcorr Subpackage\n"
            "\tspecial_function.single_slit_diffraction_solve:\n"
            "\t\tSecond input must be a floating point number.\n"
            "\t\tYour input has type: %s\n"
            % (type(z).__name__)
            )
    if not (isinstance(a, float)):
        try:
            a = float(a)
        except ValueError:
            raise ValueError(
            "\n\tError Encountered:\n"
            "\trss_ringoccs: Diffcorr Subpackage\n"
            "\tspecial_function.single_slit_diffraction_solve:\n"
            "\t\tThird input must be a floating point number.\n"
            "\t\tYour input has type: %s\n"
            % (type(a).__name__)
            )

    f = np.sinc(a*x/z)*np.sinc(a*x/z)
    return f

def double_slit_diffraction(x, z, a, d):
    """
        Purpose:
            Compute diffraction through a double slit for the
            variable x with a distance z from the slit and
            slit parameter a and a distance d between the slits.
            This assumes Fraunhofer diffraction.
        Variables:
            :x:
                A real or complex argument, or numpy array.
            :z (*float*):
                The perpendicular distance from the slit
                plane to the observer.
            :a (*float*):
                The slit parameter. This is a unitless paramter
                defined as the ratio between the slit width and
                the wavelength of the incoming signal.
            :d (*float*):
                The distance between slits.
        Outputs:
            :f:
                Single slit diffraction pattern.
        Dependences:
            [1] numpy
    """
    y = x
    try:
        x = np.array(x)
        if (not np.all(np.isreal(x))) and (not np.all(np.iscomplex(x))):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: Diffcorr Subpackage\n"
                "\tspecial_function.double_slit_diffraction_solve:\n"
                "\t\tInput must be a real or complex valued numpy array.\n"
                "\t\tThe elements of your array have type: %s"
                % (x.dtype)
            )
        else:
            del y
    except (TypeError, ValueError) as errmes:
        raise TypeError(
            "\n\tError Encountered:\n"
            "\trss_ringoccs: Diffcorr Subpackage\n"
            "\tspecial_function.double_slit_diffraction_solve:\n"
            "\t\tFirst input must be a real or complex valued numpy array.\n"
            "\t\tYour input has type: %s\n"
            "\tOriginal Error Mesage: %s\n"
            % (type(y).__name__, errmes)
        )
    if not (isinstance(z, float)):
        try:
            z = float(z)
        except ValueError:
            raise ValueError(
            "\n\tError Encountered:\n"
            "\trss_ringoccs: Diffcorr Subpackage\n"
            "\tspecial_function.double_slit_diffraction_solve:\n"
            "\t\tSecond input must be a floating point number.\n"
            "\t\tYour input has type: %s\n"
            % (type(z).__name__)
            )
    if not (isinstance(a, float)):
        try:
            a = float(a)
        except ValueError:
            raise ValueError(
            "\n\tError Encountered:\n"
            "\trss_ringoccs: Diffcorr Subpackage\n"
            "\tspecial_function.double_slit_diffraction_solve:\n"
            "\t\tThird input must be a floating point number.\n"
            "\t\tYour input has type: %s\n"
            % (type(a).__name__)
            )
    if not (isinstance(d, float)):
        try:
            d = float(d)
        except ValueError:
            raise ValueError(
            "\n\tError Encountered:\n"
            "\trss_ringoccs: Diffcorr Subpackage\n"
            "\tspecial_function.double_slit_diffraction_solve:\n"
            "\t\tFourth input must be a floating point number.\n"
            "\t\tYour input has type: %s\n"
            % (type(a).__name__)
            )
    f1 = np.sinc(a*x/z)*np.sinc(a*x/z)
    f2 = np.sin(TWO_PI*d*x/z)*np.sin(TWO_PI*d*x/z)
    f3 = 4.0*np.sin(ONE_PI*d*x/z)*np.sin(ONE_PI*d*x/z)
    f = f1*f2/f3

    return f

def sq_well_solve(x, a, b, F, invert=False):
    """
        Function:
            sq_well_solve
        Purpose:
            Computes the solution of diffraction through a square well.
        Variables:
            :x:
                Real numpy array. The independent variable.
            :a (*float*):
                The LEFTMOST endpoint of the square well.
            :b (*float*):
                The RIGHTMOST endpoint of the square well.
            :F (*float*):
                The Fresnel scale.
        Output:
            :H:
                Complex numpy array.
                Diffraction pattern of a square well on
                the interal [a,b].
        History:
            Translated from IDL: RJM - 2018/05/15 8:03 P.M.
            Updated and added error checks: RJM - 2018/09/19 7:19 P.M.
    """
    if (not isinstance(x, np.ndarray)):
        raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: diffrec subpackage\n"
                "\tspecial_functions: sq_well_solve\n"
                "\tFirst variable should be a numpy array.\n"
        )
    elif (not np.isreal(x).all()):
        raise ValueError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: diffrec subpackage\n"
                "\tspecial_functions: sq_well_solve\n"
                "\tFirst variable should be real valued.\n"
        )
    else:
        pass

    if (not isinstance(a,float)):
        try:
            a = float(a)
        except TypeError:
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: diffrec subpackage\n"
                "\tspecial_functions: sq_well_solve\n"
                "\tSecond variable should be a floating point number.\n"
                "\tYour input has type: %s"
                % (type(a).__name__)
            )
    else:
        pass

    if (not isinstance(b,float)):
        try:
            b = float(b)
        except TypeError:
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: diffrec subpackage\n"
                "\tspecial_functions: sq_well_solve\n"
                "\tThird variable should be a floating point number.\n"
                "\tYour input has type: %s"
                % (type(b).__name__)
            )
    else:
        pass

    if (not isinstance(F,float)):
        try:
            F = float(F)
        except TypeError:
            raise TypeError(
                "\n\tError Encountered:\n"
                "\trss_ringoccs: diffrec subpackage\n"
                "\tspecial_functions: sq_well_solve\n"
                "\tFourth variable should be a floating point number.\n"
                "\tYour input has type: %s"
                % (type(b).__name__)
            )
    else:
        pass

    H = (0.5 - 0.5j) * (fresnel_cos((b-x)/F)-fresnel_cos((a-x)/F)+
                        1j*(fresnel_sin((b-x) / F)-fresnel_sin((a-x)/F)))

    if not invert:
        H = 1-H

    return H
