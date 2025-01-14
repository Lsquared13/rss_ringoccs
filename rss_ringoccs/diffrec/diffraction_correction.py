"""
    Purpose:
        Provide the DiffractionCorrection class for
        performing the necessary mathematics to correct
        for the diffraction effects that are obtained
        during occultation observations of planetary
        rings using radio waves.
    Dependencies:
        #. numpy
        #. scipy
        #. rss_ringoccs
"""
# Import dependencies for the diffcorr module
import numpy as np
from scipy.special import lambertw, iv
from rss_ringoccs.tools.history import write_history_dict
from rss_ringoccs.tools.write_output_files import write_output_files

# Declare constant for the speed of light (km/s)
SPEED_OF_LIGHT_KM = 299792.4580

# Declare constants for multiples of pi.
HALF_PI = 1.570796326794896619231322
TWO_PI = 6.283185307179586476925287
ONE_PI = 3.141592653589793238462643

# Declare constants for the reciprocal of e and the square root of 2.
RCPR_E = 0.3678794411714423215955238
SQRT_2 = 1.414213562373095048801689

# Declare constants for various Bessel function inputs (I_0(x)).
IV0_20 = 87.10850209627940
IV0_25 = 373.02058499037486
IV0_35 = 7257.7994923041760

# Dictionary containing regions of interest within the Saturnian Rings.
region_dict = {
    'all':             [1.0, 400000.0],
    'besselbarnard':   [120210.0, 120330.0],
    'bessel-barnard':  [120210.0, 120330.0],
    'cringripples':    [77690.0, 77760.0],
    'encke':           [132900.0, 134200.0],
    'enckegap':        [132900.0, 134200.0],
    'herschel':        [118100.0, 118380.0],
    'herschelgap':     [118100.0, 118380.0],
    'huygens':         [117650.0, 117950.0],
    'huygensringlet':  [117650.0, 117950.0],
    'janusepimetheus': [96200.0, 96800.0],
    'jeffreys':        [118900.0, 119000.0],
    'jeffreysgap':     [118900.0, 119000.0],
    'kuiper':          [119300.0, 119500.0],
    'kuipergap':       [119300.0, 119500.0],
    'maxwell':         [87410.0, 87610.0],
    'maxwellringlet':  [87410.0, 87610.0],
    'russell':         [118550.0, 118660.0],
    'russellgap':      [118550.0, 118660.0],
    'titan':           [77870.0, 77930.0],
    'titanringlet':    [77870.0, 77930.0]
}


class DiffractionCorrection(object):
    """
        Purpose:
            Perform diffraction correction for a ring occultation
            on a data set that is a near radially symmetric function
            of the ring radius, or ring intercept point (RIP).
        Arguments:
            :DLP (*object*):
                The data set, usually an instance of the
                DiffractionLimitedProfile class from the rss_ringoccs
                Calibration subpackage. This instance MUST contain
                the following attributes and have the same names.

                |   rho_km_vals:      Ring Radius (km)
                |   phi_rad_vals:     Ring Azimuth Angle (Radians)
                |   p_norm_vals:      Normalized Power
                |   phase_rad_vals:   Phase (Radians)
                |   B_rad_vals:       Elevation Angle (Radians)
                |   D_km_vals:        RIP-Distance (km)
                |   f_sky_hz_vals:    Sky Frequency (Hertz)
                |   rho_dot_kms_vals: RIP-velocity (km/s)
                |   history:          History dictionary

            :res (*float* or *int*):
                The requested resolution for processing (km). This
                must be a positive real number.
        Keywords:
            :rng (*list* or *str*):
                The requested range for diffraction correction.
                Preferred input is rng = [a,b]. Arrays are
                allowed and the range will be set as:

                |    rng = [MIN(array), MAX(array)]

                Finally, certain strings containing a few of the
                regions of interests within the rings of Saturn
                are allowed. Permissable strings are:

                |    'all'             [1.0, 400000.0]
                |    'cringripples'    [77690.0, 77760.0]
                |    'encke'           [132900.0, 134200.0]
                |    'enckegap'        [132900.0, 134200.0]
                |    'janusepimetheus' [96200.0, 96800.0]
                |    'maxwell'         [87410.0, 87610.0]
                |    'maxwellringlet'  [87410.0, 87610.0]
                |    'titan'           [77870.0, 77930.0]
                |    'titanringlet'    [77870.0, 77930.0]
                |    'huygens'         [117650.0, 117950.0]
                |    'huygensringlet'  [117650.0, 117950.0]

                Strings are neither case nor space sensitive.
                For other planets use rng = [a,b]. Default value
                is set to 'all' which processes [1, 400000]
                Values MUST be set in kilometers.
            :wtype (*str):
                The requested tapering function for diffraction
                correction. A string with several allowed inputs:

                |    'rect'      Rectangular Window.
                |    'coss'      Squared Cosine Window.
                |    'kb20'      Kaiser-Bessel 2.0 Window.
                |    'kb25'      Kaiser-Bessel 2.5 Window.
                |    'kb35'      Kaiser-Bessel 3.5 Window.
                |    'kbmd20'    Modified kb20 Window.
                |    'kbmd25'    Modified kb25 Window.

                The variable is neither case nor space sensitive.
                Default window is set to 'kb25'. See window_functions
                submodule for further documentation.
            :fwd (*bool*):
                A Boolean for determining whether or not
                forward modelling will be computed. This is good
                starting point for deciding if the diffraction
                correction is physically significant or valid. If
                the reconstruction is good, the forward model
                should reproduce the p_norm_vals attribute from
                the input DLP instance. Default is set to False.
            :norm (*bool*):
                A Boolean for determining whether or not the
                reconstructed complex transmittance is normalize
                by the window width. This normalization is the
                complex transmittance that is computed by using
                free space divided by the complex transmittance
                that is computed using free space weighted by the
                selected tapering function. Default is True.
            :bfac (*bool*):
                A Boolean for determining whether or not the
                'b' factor in the window width computation is
                used. This is equivalent to setting the Allen
                Deviation for the spacecraft to a positive value
                or to zero. If set to False, the Allen Deviation
                is assumed to be zero. If set to True the Allen
                Deviation is set to 2e-13, or whichever number you
                wish to specify in the sigma keyword (See below).
                Default is True.
            :sigma (*float*):
                The Allen deviation for the spacecraft. If the bfac
                keyword (See above) is set to False, this is ignored.
                If bfac is set to True, and sigma is NOT specified,
                then sigma=2e-13 will be used, which is the Allen
                deviation for Cassini with 1 second integration time.
                For spacecraft other than Cassini, you should provide
                the Allen deviation yourself. Default is sigma=2e-13
            :psitype (*str*):
                A string for determining what approximation to the
                geometrical 'psi' function is used. Several strings
                are allowed:

                |    'full'      No Approximation is applied.
                |    'MTR2'      Second Order Series from MTR86.
                |    'MTR3'      Third Order Series from MTR86.
                |    'MTR4'      Fourth Order Series from MTR86.
                |    'Fresnel'   Standard Fresnel approximation.

                The variable is neither case nor space sensitive.
                Default is set to 'full'.
            :verbose (*bool*):
                A Boolean for determining if various pieces of
                information are printed to the screen or not.
                Default is False.
        Attributes:
            :bfac (*bool*):
                Boolean for bfac (See keywords).
            :dathist (*dict*):
                History from DLP instance.
            :dx_km (*float*):
                Radial spacing for the data points (km).
            :f_sky_hz_vals (*np.ndarray*):
                Recieved frequency from the spacecraft (Hz).
            :finish (*int*):
                Final point that was reconstructed.
            :fwd (*bool*):
                Boolean for fwd (See keywords).
            :history (*dict*):
                History for the DiffractionCorrection class.
                This contains system info and user info, including
                what operating system was used, username, hostname,
                computer name, and the inputs provided.
            :lambda_sky_km_vals (*np.ndarray*):
                Wavelength of recieved signal from spacecraft (km).
            :mu_vals (*np.ndarray*):
                The sine of the ring opening angle (Unitless).
            :n_used (*int*):
                Number of points that were reconstructed.
            :norm (*bool*):
                Boolean for norm (See keywords).
            :norm_eq (*float*):
                Normalized equivalent width computed from window
                that was used during reconstruction. See the
                window_functions submodule for more information.
            :p_norm_fwd_vals (*np.ndarray*):
                Normalized power computer from the forward modelling
                of the reconstructed data. This will be a None type
                variable unless fwd=True is set. If the
                reconstruction went well, this should mimic the raw
                data, p_norm_vals.
            :p_norm_vals (*np.ndarray*):
                Normalized power from the diffracted signal. This is
                the square of the absolute value of the recieved
                complex transmittance.
            :phase_fwd_vals (*np.ndarray*):
                Phase computed from the forward model of the
                reconstructed data. This will be a None type
                variable unless fwd=True is set. If the
                reconstruction went well, this should mimic
                phase_rad_vals. This variable is in radians.
            :phase_rad_vals (*np.ndarray*):
                Phase from the diffracted signal (Radians).
            :phase_vals (*np.ndarray*):
                Reconstructed phase (Radians).
            :phi_rad_vals (*np.ndarray*):
                Ring azimuth angle of the ring intercept (Radians).
            :phi_rl_rad_vals (*np.ndarray*):
                Ring longitude angle. This will be a None type unless
                it was provided in the DLP class. Otherwise,
                this variable is in radians.
            :power_vals (*np.ndarray*):
                Normalized reconstructed power.
            :psitype (*str*):
                String for psitype (See keywords).
            :raw_tau_threshold_vals (*np.ndarray*):
                Threshold optical depth for the diffracted data.
                This will be a None type unless provided for in the
                DLP class.
            :res (*float*):
                Requested resolution (See arguments). In kilometers.
            :rho_corr_pole_km_vals (*np.ndarray*):
                Radial corrections from the Planet's pole. This will
                be a None type variable unless provided in the
                DLP class. Otherwise, this is in kilometers.
            :rho_corr_timing_km_vals (*np.ndarray*):
                Radial corrections from timing offsets. This will be
                a None type variable unless provided in the DLP
                class. Otherwise, this is in kilometers.
            :rho_dot_kms_vals (*np.ndarray*):
                Time derivative of the ring intercept point (km/s).
            :rho_km_vals (*np.ndarray*):
                Ring-intercept-point (RIP) in kilometers.
            :rng (*str*):
                Range that was used for reconstruction, taking into
                the range that was requested by the user. The actual
                range takes into account limits in the available data
                and limits in the required window sizes.
            :rngreq (*str* or *list*):
                Requested range (See keywords).
            :sigma (*float*):
                Requested Allen deviation (See keywords).
            :start (*int*):
                First point that was reconstructed.
            :t_oet_spm_vals (*np.ndarray*):
                Time the signal is measured on Earth. This is a
                None type unless provided for in the DLP class.
            :t_ret_spm_vals (*np.ndarray*):
                Time the signal passes through the diffracting
                medium. This is a None type unless provided for in
                the DLP class.
            :t_set_spm_vals (*np.ndarray*):
                Time the signal is emitted from the spacecraft. This
                is a None type unless provided in the DLP class.
            :tau_threshold_vals (*np.ndarray*):
                Threshold optical depth of the reconstructed data.
            :tau_vals (*np.ndarray*):
                Optical depth of the reconstructed data.
            :verbose (*bool*):
                Boolean for Verbose (See keywords).
            :w_km_vals (*np.ndarray*):
                Window width as a function of radius (km).
            :wtype (*str*):
                String for wtype (See keywords).
    """
    def __init__(self, DLP, res, rng="all", wtype="kbmd20", fwd=False,
                 norm=True, verbose=False, bfac=True, sigma=2.e-13,
                 psitype="fresnel4", write_file=False, res_factor=0.75):

        # Make sure that verbose is a boolean.
        if not isinstance(verbose, bool):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tverbose must be Boolean: True/False\n"
                "\tYour input has type: %s\n"
                "\tInput should have type: bool\n"
                "\tSet verbose=True or verbose=False\n"
                % (type(verbose).__name__)
            )
        elif verbose:
            print("Processing Diffraction Correction:")
            print("\tRunning Error Check on Input Arguments...")
        else:
            pass

        # Check that the input resolution is a positive floating point number.
        if (not isinstance(res, float)):
            try:
                res = float(res)
            except (TypeError, ValueError):
                raise TypeError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\tres must be a positive floating point number\n"
                    "\tYour input has type: %s\n"
                    "\tInput should have type: float\n" % (type(res).__name__)
                )
        else:
            pass

        if (res <= 0.0):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tres must be a positive floating point number\n"
                "\tYour requested resolution (km): %f\n" % (res)
            )
        else:
            pass

        # Check that the requested window type is a legal input.
        if not isinstance(wtype, str):
            erm = ""
            for key in self.__func_dict:
                erm = "%s\t\t'%s'\n" % (erm, key)
            raise TypeError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\twtype must be a string.\n"
                "\tYour input has type: %s\n"
                "\tInput should have type: str\n"
                "\tAllowed string are:\n%s" % (type(wtype).__name__, erm)
            )
        else:
            # Remove spaces and quotes from the wtype variable.
            wtype = wtype.replace(" ", "").replace("'", "").replace('"', "")

            # Set wtype string to lower-case.
            wtype = wtype.lower()
            if not (wtype in self.__func_dict):
                erm = ""
                for key in self.__func_dict:
                    erm = "%s\t\t'%s'\n" % (erm, key)
                raise ValueError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\tIllegal string used for wtype.\n"
                    "\tYour string: '%s'\n"
                    "\tAllowed Strings:\n%s" % (wtype, erm)
                )
            else:
                pass

        # Check that the forward boolean is valid.
        if not isinstance(fwd, bool):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tfwd must be Boolean: True/False\n"
                "\tYour input has type: %s\n"
                "\tInput should have type: bool\n"
                "\tSet fwd=True or fwd=False\n" % (type(fwd).__name__)
            )
        else:
            pass

        # Ensure that the normalize boolean has a legal value.
        if not isinstance(norm, bool):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tnorm must be Boolean: True/False\n"
                "\tYour input has type: %s\n"
                "\tInput should have type: bool\n"
                "\tSet norm=True or norm=False\n" % (type(norm).__name__)
            )
        else:
            pass

        # Make sure that bfac is a boolean.
        if not isinstance(bfac, bool):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tbfac must be Boolean: True/False\n"
                "\tYour input has type: %s\n"
                "\tInput should have type: bool\n"
                "\tSet bfac=True or bfac=False\n" % (type(bfac).__name__)
            )
        else:
            pass

        # Check that write_file boolean is valid.
        if not isinstance(write_file, bool):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\twrite_file must be Boolean: True/False\n"
                "\tYour input has type: %s\n"
                "\tInput should have type: bool\n"
                "\tSet write_file=True or write_file=False\n"
                % (type(write_file).__name__)
            )
        else:
            pass
        
        # Check that res_factor is a floating point number.
        if (not isinstance(res_factor, float)):
            try:
                res_factor = float(res_factor)
            except (TypeError, ValueError):
                raise TypeError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\tres_factor must be a positive floating point number.\n"
                    "\tYour input has type: %s\n" % (type(res_factor).__name__)
                )
        else:
            pass

        if (res_factor <= 0.0):
                raise ValueError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\tres_factor must be a positive floating point number.\n"
                    "\tYour input: %f\n"
                    % (res_factor)
                )
        else:
            pass

        # Cbeck that psitype is a valid string.
        if not isinstance(psitype, str):
            erm = ""
            for key in self.__psi_types:
                erm = "%s\t\t'%s'\n" % (erm, key)
            raise TypeError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tpsitype must be a string.\n"
                "\tYour input has type: %s\n"
                "\tInput should have type: str\n"
                "\tAllowed strings are:\n%s" % (type(psitype).__name__, erm)
            )
        else:
            # Remove spaces, quotes, and apostrophe's from the psitype.
            psitype = psitype.replace(" ", "").replace("'", "")
            psitype = psitype.replace('"', "").lower()

            # Perform error check, print legal inputs if needed.
            if not (psitype in self.__psi_types):
                erm = ""
                for key in self.__psi_types:
                    erm = "%s\t\t'%s'\n" % (erm, key)
                raise TypeError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\tInvalid string for psitype.\n"
                    "\tYour string: '%s'\n"
                    "\tAllowed strings are:\n%s"
                    % (psitype, erm)
                )
            else:
                pass

        # Check that the requested range is a legal input.
        if (not isinstance(rng, str)) and (not isinstance(rng, list)):
            try:
                if (np.size(rng) < 2):
                    erm = ""
                    for key in region_dict:
                        erm = "%s\t\t'%s'\n" % (erm, key)
                    raise TypeError(
                        "\n\tError Encountered:\n"
                        "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                        "\trng must be a list or a valid string.\n"
                        "\tYour input has type: %s\n"
                        "\tSet range=[a,b], where a is the STARTING point\n"
                        "\tand b is the ENDING point of reconstruction, or\n"
                        "\tuse one of the following valid strings:\n%s"
                        % (type(rng).__name__, erm)
                    )
                elif (np.min(rng) < 0):
                    raise ValueError(
                        "\n\tError Encountered:\n"
                        "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                        "\tMinimum requested range must be positive\n"
                        "\tYour minimum requested range: %f\n" % (np.min(rng))
                    )
                else:
                    rng = [np.min(rng), np.max(rng)]
            except TypeError:
                erm = ""
                for key in region_dict:
                    erm = "%s\t\t'%s'\n" % (erm, key)
                raise TypeError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\trng must be a list of floating\n"
                    "\tpoint numbers or a valid string.\n"
                    "\tYour input has type: %s\n"
                    "\tSet range=[a,b], where a is the STARTING point\n"
                    "\tand b is the ENDING point of reconstruction, or\n"
                    "\tuse one of the following valid strings:\n%s"
                    % (type(rng).__name__, erm)
                )
        elif isinstance(rng, list):
            # Try converting all elements to floating point numbers.
            if (not all(isinstance(x, float) for x in rng)):
                try:
                    for i in np.arange(np.size(rng)):
                        rng[i] = float(rng[i])
                except (TypeError, ValueError):
                    erm = ""
                    for key in region_dict:
                        erm = "%s\t\t'%s'\n" % (erm, key)
                    raise TypeError(
                        "\n\tError Encountered:\n"
                        "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                        "\trng must be a list of floating\n"
                        "\tpoint numbers or a valid string.\n"
                        "\tYour input has type: %s\n"
                        "\tSet range=[a,b], where a is the STARTING point\n"
                        "\tand b is the ENDING point of reconstruction, or\n"
                        "\tuse one of the following valid strings:\n%s"
                        % (type(rng).__name__, erm)
                    )
            else:
                pass

            # Check that there are at least two numbers.
            if (np.size(rng) < 2):
                erm = ""
                for key in region_dict:
                    erm = "%s\t\t'%s'\n" % (erm, key)
                raise TypeError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\trng must contain two numbers: rng=[a,b]\n"
                    "\tYou provided less than 2 numbers.\n"
                    "\tSet range=[a,b], where a is the STARTING point\n"
                    "\tand b is the ENDING point of reconstruction, or\n"
                    "\tuse one of the following valid strings:\n%s" % (erm)
                )
            else:
                pass

            # Check that the smallest number is positive.
            if (np.min(rng) < 0.0):
                raise ValueError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\tMinimum requested range must be positive\n"
                    "\tYour minimum requested range: %f\n" % (np.min(rng))
                )
            else:
                pass
        elif isinstance(rng, str):
            rng = rng.replace(" ", "").replace("'", "").replace('"', "")
            rng = rng.lower()
            if not (rng in region_dict):
                erm = ""
                for key in region_dict:
                    erm = "%s\t\t'%s'\n" % (erm, key)
                raise ValueError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\tIllegal string used for rng.\n"
                    "\tYour string: '%s'\n"
                    "\tAllowed Strings:\n%s" % (rng, erm)
                )
        else:
            erm = ""
            for key in region_dict:
                erm = "%s\t\t'%s'\n" % (erm, key)
            raise TypeError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\trng must be a list of floating\n"
                "\tpoint numbers or a valid string.\n"
                "\tYour input has type: %s\n"
                "\tSet range=[a,b], where a is the STARTING point\n"
                "\tand b is the ENDING point of reconstruction, or\n"
                "\tuse one of the following valid strings:\n%s"
                % (type(rng).__name__, erm)
            )

        # Check that the Allen Deviation is a legal value.
        if (not isinstance(sigma, float)):
            try:
                sigma = float(sigma)
            except (TypeError, ValueError):
                raise TypeError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\tsigma must be a positive floating point number.\n"
                    "\tYour input has type: %s\n" % (type(sigma).__name__)
                )
        else:
            pass

        if (np.min(sigma) <= 0.0):
                raise ValueError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\n\tsigma must be a positive floating point number.\n"
                    "\tYour input: %f\n" % (sigma)
                )
        else:
            pass

        if verbose:
            print("\tAssigning inputs as attributes...")

        # Assign variables as attributes.
        self.p_norm_fwd_vals = None
        self.T_hat_fwd_vals = None
        self.phase_fwd_vals = None
        self.input_res = res
        self.verbose = verbose
        self.psitype = psitype
        self.rngreq = rng
        self.wtype = wtype
        self.sigma = sigma
        self.norm = norm
        self.bfac = bfac
        self.res = res*res_factor
        self.fwd = fwd

        # Retrieve variables from the DLP class, setting as attributes.
        if verbose:
            print("\tRetrieving variables from DLP instance...")

        try:
            erm = "rho_km_vals"
            self.rho_km_vals = np.array(DLP.rho_km_vals)
            erm = "p_norm_vals"
            self.p_norm_vals = np.array(DLP.p_norm_vals)
            erm = "phase_rad_vals"
            self.phase_rad_vals = np.array(DLP.phase_rad_vals)
            erm = "B_rad_vals"
            self.B_rad_vals = np.array(DLP.B_rad_vals)
            erm = "D_km_vals"
            self.D_km_vals = np.array(DLP.D_km_vals)
            erm = "phi_rad_vals"
            self.phi_rad_vals = np.array(DLP.phi_rad_vals)
            erm = "f_sky_hz_vals"
            self.f_sky_hz_vals = np.array(DLP.f_sky_hz_vals)
            erm = "rho_dot_kms_vals"
            self.rho_dot_kms_vals = np.array(DLP.rho_dot_kms_vals)
            erm = "t_oet_spm_vals"
            self.t_oet_spm_vals = np.array(DLP.t_oet_spm_vals)
            erm = "t_ret_spm_vals"
            self.t_ret_spm_vals = np.array(DLP.t_ret_spm_vals)
            erm = "t_set_spm_vals"
            self.t_set_spm_vals = np.array(DLP.t_set_spm_vals)
            erm = "rho_corr_pole_km_vals"
            self.rho_corr_pole_km_vals = np.array(DLP.rho_corr_pole_km_vals)
            erm = "rho_corr_timing_km_vals"
            self.rho_corr_timing_km_vals = np.array(DLP.rho_corr_timing_km_vals)
            erm = "phi_rl_rad_vals"
            self.phi_rl_rad_vals = np.array(DLP.phi_rl_rad_vals)
            erm = "raw_tau_threshold_vals"
            self.raw_tau_threshold_vals = np.array(DLP.raw_tau_threshold_vals)
            erm = "history"
            self.dathist = DLP.history
        except (TypeError, ValueError, NameError, AttributeError):
            raise TypeError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\t%s could not be converted into a numpy array.\n"
                "\tCheck your DLP class for errors." % erm
            )

        n_rho = np.size(self.rho_km_vals)

        # Run various error checks on all variables.
        if not (np.all(np.isreal(self.rho_km_vals))):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\trho_km_vals is not an array of real\n"
                "\tvalued floating point numbers. Please\n"
                "\tcheck your DLP class for errors.\n"
            )
        elif (np.size(self.rho_km_vals) < 2):
            raise IndexError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\trho_km_vals has less than 2 points.\n"
                "\tIt is impossible to do reconstruction.\n"
                "\tPlease check your input data.\n"
            )
        elif (np.min(self.rho_km_vals < 0)):
                raise ValueError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\trho_km_vals has negative values.\n"
                    "\tPlease check your DLP class for errors."
                )
        else:
            self.rho_km_vals = self.rho_km_vals.astype(float)

        if (np.size(self.p_norm_vals) != n_rho):
            raise IndexError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tBad DLP: len(power) != len(rho)\n"
                "\tThe number of data points in power is\n"
                "\tnot equal to the number of data points\n"
                "\tin radius. Check the input DLP\n"
                "\tinstance for any errors.\n"
            )
        elif (np.min(self.p_norm_vals) < 0.0):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tThere are negative values in the\n"
                "\tnormalized diffracted power. Check\n"
                "\tthe DLP instance for errors.")
        elif not (np.all(np.isreal(self.p_norm_vals))):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tp_norm_vals is not an array of real\n"
                "\tvalued floating point numbers. Please\n"
                "\tcheck your DLP class for errors.\n"
            )
        else:
            self.p_norm_vals = self.p_norm_vals.astype(float)

        if (np.size(self.phase_rad_vals) != n_rho):
            raise IndexError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tBad DLP: len(phase) != len(rho)\n"
                "\tThe number of data points in phase is\n"
                "\tnot equal to the number of data points\n"
                "\tin radius. Check the input DLP\n"
                "\tinstance for any errors.\n"
            )
        elif not (np.all(np.isreal(self.phase_rad_vals))):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tphase_rad_vals is not an array of real\n"
                "\tvalued floating point numbers. Please\n"
                "\tcheck your DLP class for errors.\n"
            )
        elif (np.max(np.abs(self.phase_rad_vals)) > TWO_PI+1e-8):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tThere are values of phase (radians)\n"
                "\tthat are greater than 2pi. Check the DLP\n"
                "\tinstance for errors. Also check to make sure\n"
                "\tthe values in the DLP intance are in\n"
                "\tradians, and NOT degrees.\n"
            )
        else:
            # Negating phase from mathematical conventions.
            self.phase_rad_vals = -self.phase_rad_vals.astype(float)

        if (np.size(self.B_rad_vals) != n_rho):
            raise IndexError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tBad DLP: len(B) != len(rho)\n"
                "\tThe number of data points in B is\n"
                "\tnot equal to the number of data points\n"
                "\tin radius. Check the input DLP\n"
                "\tinstance for any errors.\n"
            )
        elif (np.max(np.abs(self.B_rad_vals)) > TWO_PI+1e-8):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tThere are values of B (radians)\n"
                "\tthat are greater than 2pi. Check the DLP\n"
                "\tinstance for errors. Also check to make sure\n"
                "\tthe values in the DLP intance are in\n"
                "\tradians, and NOT degrees.\n"
            )
        elif not (np.all(np.isreal(self.B_rad_vals))):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tB_rad_vals is not an array of real\n"
                "\tvalued floating point numbers. Please\n"
                "\tcheck your DLP class for errors.\n"
            )
        else:
            self.B_rad_vals = self.B_rad_vals.astype(float)

        if (np.size(self.D_km_vals) != n_rho):
            raise IndexError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tBad DLP: len(D) != len(rho)\n"
                "\tThe number of data points in D is\n"
                "\tnot equal to the number of data points\n"
                "\tin radius. Check the input DLP\n"
                "\tinstance for any errors.\n"
            )
        elif not (np.all(np.isreal(self.D_km_vals))):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tD_km_vals is not an array of real\n"
                "\tvalued floating point numbers. Please\n"
                "\tcheck your DLP class for errors.\n"
            )
        elif (np.min(self.D_km_vals) < 0.0):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tThere are negative values for the\n"
                "\tspacecraft to RIP distance, D.\n"
                "\tCheck the DLP instance for errors.\n"
            )
        elif (np.min(self.D_km_vals == 0.0)):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tThere are zero-valued elements for the\n"
                "\tSpacecraft to Ring-Intercept-Point distance, D.\n"
                "\Check the DLP instance for errors.\n"
            )
        else:
            self.D_km_vals = self.D_km_vals.astype(float)

        if (np.size(self.phi_rad_vals) != n_rho):
            raise IndexError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tBad DLP: len(phi) != len(rho)\n"
                "\tThe number of data points in angle is\n"
                "\tnot equal to the number of data points\n"
                "\tin radius. Check the input DLP\n"
                "\tinstance for any errors.\n"
            )
        elif not (np.all(np.isreal(self.phi_rad_vals))):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tphi_rad_vals is not an array of real\n"
                "\tvalued floating point numbers. Please\n"
                "\tcheck your DLP class for errors.\n"
            )
        elif (np.max(np.abs(self.phi_rad_vals)) > TWO_PI+1e-6):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tThere are values of phi (in radians)\n"
                "\tthat are greater than 2pi. Check the DLP\n"
                "\tinstance for errors. Also check to make sure\n"
                "\tthe values in the DLP intance are in\n"
                "\tradians, and NOT degrees.\n"
            )
        else:
            self.phi_rad_vals = self.phi_rad_vals.astype(float)

        if (np.size(self.f_sky_hz_vals) != n_rho):
            raise IndexError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tBad DLP: len(frequency) != len(rho)\n"
                "\tThe number of data points in frequency is\n"
                "\tnot equal to the number of data points\n"
                "\tin radius. Check the input DLP\n"
                "\tinstance for any errors.\n"
            )
        elif not (np.all(np.isreal(self.f_sky_hz_vals))):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tf_sky_hz_vals is not an array of real\n"
                "\tvalued floating point numbers. Please\n"
                "\tcheck your DLP class for errors.\n"
            )
        elif (np.min(self.f_sky_hz_vals < 0.0)):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tThere are negative values of the frequency.\n"
                "\tCheck the DLP instance for errors.\n"
            )
        elif (np.min(self.f_sky_hz_vals == 0.0)):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tThere are zero-valued elements for the\n"
                "\tfrequency. Check the DLP instance for errors."
            )
        else:
            self.f_sky_hz_vals = self.f_sky_hz_vals.astype(float)

        if (np.size(self.rho_dot_kms_vals) != n_rho):
            raise IndexError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tBad DLP: len(rho_dot) != len(rho)\n"
                "\tThe number of data points in velocity is\n"
                "\tnot equal to the number of data points\n"
                "\tin radius. Check the input DLP\n"
                "\tinstance for any errors.\n"
            )
        elif not (np.all(np.isreal(self.rho_dot_kms_vals))):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\trho_dot_kms_vals is not an array of real\n"
                "\tvalued floating point numbers. Please\n"
                "\tcheck your DLP class for errors.\n"
            )
        else:
            self.rho_dot_kms_vals = self.rho_dot_kms_vals.astype(float)
            del n_rho, erm

        # Compute sampling distance (km)
        self.dx_km = self.rho_km_vals[1] - self.rho_km_vals[0]

        # Check that the data is well sampled for the requested resolution.
        if (self.dx_km == 0.0):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\trho_km_vals[1]-rho_km_vals[0]=0.0\n"
                "\tThe sample spacing is zero. Please\n"
                "\tcheck the input data for errors."
            )
        elif self.res < 1.999999*self.dx_km:
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tRequested resolution is less than twice the\n"
                "\tsample spacing of the input data. This\n"
                "\tviolates the sampling theorem and will result\n"
                "\tin an inaccurate reconstruction.\n\n"
                "\tRequested Resolution (km): %f\n"
                "\tSample Spacing (km): %f\n\n"
                "\tTO CORRECT THIS:\n"
                "\t\tChoose a resolution GREATER than %f km\n"
                "\n\tPLEASE NOTE:\n"
                "\t\tTo be consistent with PDS results, a scale factor\n"
                "\t\tof 0.75 is applied to your requested resolution.\n"
                "\t\tto ignore this scale factor, please set the\n"
                "\t\tkeyword 'res_factor=1.0' when calling the\n"
                "\t\tDiffractionCorrection class.\n"
                "\t\tres_factor is currently set to: %f"%
                (self.res, self.dx_km, 2.0*self.dx_km/res_factor, res_factor)
            )
        else:
            pass

        if verbose:
            print("\tCheck Variables for Errors...")

        # Check that rho_km_vals is increasing and the rev isn't a chord occ.
        drho = [np.min(self.rho_dot_kms_vals), np.max(self.rho_dot_kms_vals)]

        if (drho[0] < 0) and (drho[1] > 0):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tdrho/dt has positive and negative values.\n"
                "\tYour input file is probably a chord occultation.\n"
                "\tDiffraction Correction can only be performed for\n"
                "\tone event at a time. That is, either an ingress\n"
                "\tor an egress event.\n\n"
                "\tTO CORRECT THIS:\n"
                "\t\tSplit the input into two parts: An egress\n"
                "\t\tportion and an ingress portion, and then run\n"
                "\t\tdiffraction correction on the individual pieces.\n"
            )
        elif ((drho[0] == 0.0) or (drho[1] == 0.0)):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tdrho/dt has elements with value zero.\n"
                "\tYour input file is probably a chord occultation.\n"
                "\tDiffraction Correction can only be performed for\n"
                "\tone event at a time. That is, either an ingress\n"
                "\tor an egress event.\n\n"
                "\tTO CORRECT THIS:\n"
                "\t\tSplit the input into two parts: An egress\n"
                "\t\tportion and an ingress portion, and then run\n"
                "\t\tdiffraction correction on the individual pieces.\n"
                "\t\tIgnore the region where drho/dt is close to zero."
            )
        elif (self.dx_km > 0) and (drho[1] < 0):
            self.rho_dot_kms_vals = np.abs(self.rho_dot_kms_vals)
        elif (self.dx_km < 0) and (drho[0] > 0):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\trho_km_vals is decreasing, yet\n"
                "\trho_dot_kms_vals is positive..\n"
                "\tPlease check your DLP class for errors."
            )
        elif (self.dx_km < 0):
            self.rho_km_vals = self.rho_km_vals[::-1]
            self.phase_rad_vals = self.phase_rad_vals[::-1]
            self.p_norm_vals = self.p_norm_vals[::-1]
            self.phi_rad_vals = self.phi_rad_vals[::-1]
            self.B_rad_vals = self.B_rad_vals[::-1]
            self.f_sky_hz_vals = self.f_sky_hz_vals[::-1]
            self.D_km_vals = self.D_km_vals[::-1]
            self.rho_dot_kms_vals = np.abs(self.rho_dot_kms_vals[::-1])
            self.dx_km *= -1.0
        else:
            del drho

        if verbose:
            print("\tComputing Necessary Variables...")

        # Compute various variables.
        self.lambda_sky_km_vals = SPEED_OF_LIGHT_KM / self.f_sky_hz_vals
        self.mu_vals = np.sin(np.abs(self.B_rad_vals))
        theta = 1j*self.phase_rad_vals
        abs_T = np.sqrt(self.p_norm_vals)
        self.T_hat_vals = abs_T*np.exp(theta)
        del theta, abs_T

        # Compute geometric qunatities and the Fresnel Scale.
        cb = np.cos(self.B_rad_vals)
        sb = np.sin(self.B_rad_vals)
        sp = np.sin(self.phi_rad_vals)
        self.F_km_vals = np.sqrt(0.5 * self.lambda_sky_km_vals *
                                 self.D_km_vals * (1 - cb*cb*sp*sp)/(sb*sb))
        
        del cb, sb, sp

        # Compute the Normalized Equaivalent Width (See MTR86 Equation 20)
        self.norm_eq = self.__func_dict[wtype]["normeq"]

        # Compute the window width. (See MTR86 Equations 19, 32, and 33).
        if bfac:
            omega = TWO_PI * self.f_sky_hz_vals
            alpha = omega*omega * sigma*sigma / (2.0 * self.rho_dot_kms_vals)
            P = self.res / (alpha * (self.F_km_vals*self.F_km_vals))
            self.P = P

            # Create a variable specifying where P>1 occurs.
            Prange = (P > 1.0).nonzero()[0]

            if (np.size(Prange) == 0):
                raise IndexError(
                    "\n\tError Encountered:\n"
                    "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                    "\tThe P parameter in window width computation\n"
                    "\tis less than one for the entirety of the\n"
                    "\tdata set. Either rho_dot_km_vals is too small,\n"
                    "\tor F_km_vals is too large. Request a coarser\n"
                    "\tresolution, or check your data for errors.\n\n"
                    "\tAlternatively, you may set bfac=False as\n"
                    "\ta keyword to skip the use of the P parameter.\n"
                    "\tThis may result in inaccurate window widths."
                )
            else:
                pass

            P = P[Prange]
            alpha = alpha[Prange]
            P1 = P/(1-P)
            P2 = P1*np.exp(P1)

            # LambertW returns nans far values close to zero, so round this.
            P2 = np.around(P2, decimals=16)

            # For values near -1/e, LambertW(x) is roughly -1. 
            crange1 = ((RCPR_E + P2) < 1.0e-16).nonzero()[0]
            crange2 = ((RCPR_E + P2) >= 1.0e-16).nonzero()[0]
            self.w_km_vals = np.zeros(np.size(self.rho_km_vals))

            if (np.size(crange1) > 0):
                self.w_km_vals[Prange[crange1]] = (
                    2.0*self.F_km_vals[Prange[crange1]]*
                    self.F_km_vals[Prange[crange1]]/self.res
                )
            else:
                pass

            if (np.size(crange2) > 0):
                self.w_km_vals[Prange[crange2]] = np.abs(lambertw(P2)-P1)/alpha
            else:
                pass

            del omega, alpha, P, P1, P2, crange1, crange2
        else:
            Prange = np.arange(np.size(self.rho_km_vals))
            self.w_km_vals = 2.0*self.F_km_vals*self.F_km_vals/res
        
        self.w_km_vals *= self.norm_eq

        # From the requested range, extract array of the form [a, b]
        if (isinstance(rng, str)):
            self.rng = np.array(region_dict[rng])
        else:
            self.rng = np.array([np.min(rng), np.max(rng)])

        rho = self.rho_km_vals[Prange]
        w = self.w_km_vals[Prange]

        # Compute the smallest and largest allowed radii for reconstruction.
        rho_min = rho-w/2.0
        rho_max = rho+w/2.0

        wrange = Prange[np.where((rho_min >= np.min(rho)) &
                                 (rho_max <= np.max(rho)))]
        self.wrange = wrange

        # Check that there is enough data for reconstruction.
        if (np.size(wrange) == 0):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tThe window width is too large to reconstruct any\n"
                "\tpoints. Please choose a coarser resolution or\n"
                "\tinspect your input data.\n"
                "\t\tMinimum Available Radius: %f\n"
                "\t\tMaximum Available Radius: %f\n"
                "\t\tMinimum Required Window Width: %f\n"
                "\t\tMaximum Required Window Width: %f\n"
                % (np.min(rho), np.max(rho), np.min(w), np.max(w))
            )
        elif (np.max(rho) < np.min(self.rng)):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tMinimum requested range is greater\n"
                "\tthan the maximum available data point.\n\n"
                "\tYour Requested Minimum (km): %f\n"
                "\tYour Requested Maximum (km): %f\n"
                "\tMaximum Available Data (km): %f\n\n"
                "\tSelect a smaller range for reconstruction\n"
                % (np.min(self.rng), np.max(self.rng), np.max(rho))
            )
        elif (np.min(rho) > np.max(self.rng)):
            raise ValueError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tMaximum requested range is less\n"
                "\tthan the minimum available data point.\n\n"
                "\tYour Requested Minimum (km): %f\n"
                "\tYour Requested Maximum (km): %f\n"
                "\tMinimum Available Data (km): %f\n\n"
                "\tTO CORRECT THIS:\n"
                "\t\tSelect a larger range for reconstruction\n"
                % (np.min(self.rng), np.max(self.rng), np.min(rho))
            )
        else:
            pass

        rho_min = np.min(rho[wrange])
        rho_max = np.max(rho[wrange])

        wrange = wrange[np.where((rho[wrange] >= np.min(self.rng)) &
                                 (rho[wrange] <= np.max(self.rng)))]

        if (np.size(wrange) <= 1):
            raise IndexError(
                "\n\tError Encountered:\n"
                "\t\trss_ringoccs.diffrec.DiffractionCorrection\n\n"
                "\tRequested range does not include any of the\n"
                "\tavailable points for processing. Please choose\n"
                "\tA different range for processing.\n"
                "\t\tMinimum Possible Radius: %f\n"
                "\t\tMaximum Possible Radius: %f\n"
                "\t\tRequested Range Minimum: %f\n"
                "\t\tRequested Range Maximum: %f"
                % (rho_min, rho_max, np.min(self.rng), np.max(self.rng))
            )
        else:
            pass

        self.start = wrange[0]
        self.finish = wrange[-1]
        self.n_used = 1 + (self.finish - self.start)

        # Create input variable and keyword dictionaries for history.
        input_vars = {
            'dlp_inst': DLP.history,
            'res': res
        }

        input_kwds = {
            'rng': rng,
            'wtype': wtype,
            'fwd': fwd,
            'norm': norm,
            'bfac': bfac,
            'sigma': sigma,
            'psitype': psitype,
            'res_factor': res_factor
        }

        # Delete unnecessary variables for clarity.
        del rho, rho_min, rho_max, rng, norm, fwd, bfac, psitype, verbose

        if self.verbose:
            print("\tRunning Fresnel Inversion...")

        self.T_vals = self.__ftrans(fwd=False)

        # Compute power and phase.
        if self.verbose:
            print("\tComputing Power and Phase...")

        self.power_vals = np.abs(self.T_vals*self.T_vals)

        # Return phase to original sign.
        self.phase_vals = -np.arctan2(np.imag(self.T_vals),
                                      np.real(self.T_vals))
        self.phase_rad_vals *= -1

        if self.verbose:
            print("\tInversion Complete.")

        if self.fwd:
            if self.verbose:
                print("\tComputing Forward Transform...")

            self.T_hat_fwd_vals = self.__ftrans(fwd=True)
            self.p_norm_fwd_vals = np.abs(self.T_hat_fwd_vals*
                                          self.T_hat_fwd_vals)
            self.phase_fwd_vals = -np.arctan2(np.imag(self.T_hat_fwd_vals),
                                              np.real(self.T_hat_fwd_vals))
            if self.verbose:
                print("\tForward Transform Complete.")

        # Compute regions of non-zero power.
        crange = (self.power_vals > 0.0).nonzero()

        # Create empty array for normalized optical depth.
        tau = np.zeros(np.size(self.power_vals))

        # Compute the normalized optical depth.
        tau[crange] = -self.mu_vals[crange]*np.log(
            np.abs(self.power_vals[crange]))
        self.tau_vals = tau

        self.tau_threshold_vals = (self.raw_tau_threshold_vals -
                                   self.mu_vals*np.log(self.dx_km/self.res))

        self.__trim_attributes(self.fwd)

        self.history = write_history_dict(input_vars, input_kwds, __file__)

        # Set rev_info attribute from DLP instance.
        self.rev_info = DLP.rev_info
        if write_file:
            write_output_files(self)

        if self.verbose:
            print("\tDiffraction Correction Complete.")

    def __rect(w_in, dx):
        """
            Purpose:
                Compute the rectangular window function.
            Arguments:
                :w_in (*float*):
                    The width of the window function to be computed.
                    This value is in kilometers.
                :dx (*float*):
                    The spacing between points in the window.
                    This is equivalent to the sample spacing.
                    This value is in kilometers.
            Outputs:
                :w_func (*np.ndarray*):
                    Window function of width
                    w_in and with sample spacing dx.
        """
        # Window functions have an odd number of points.
        nw_pts = int(2 * np.floor(w_in / (2.0 * dx)) + 1)

        # Compute window function
        w_func = np.zeros(nw_pts) + 1.0
        return w_func

    def __coss(w_in, dx):
        """
            Purpose:
                Compute the squared cosine window function.
            Arguments:
                :w_in (*float*):
                    The width of the window function to be computed.
                    This value is in kilometers.
                :dx (*float*):
                    The spacing between points in the window.
                    This is equivalent to the sample spacing.
                    This value is in kilometers.
            Outputs:
                :w_func (*np.ndarray*):
                    Window function of width
                    w_in and with sample spacing dx.
        """
        # Window functions have an odd number of points.
        nw_pts = int(2 * np.floor(w_in / (2.0 * dx)) + 1)

        # Compute argument of window function.
        x = ONE_PI*(np.arange(nw_pts) - ((nw_pts - 1) / 2.0)) * dx / w_in

        # Compute window function.
        w_func = np.cos(x)*np.cos(x)
        return w_func

    def __kb20(w_in, dx):
        """
            Purpose:
                Compute the Kaiser-Bessel 2.0 window function.
            Arguments:
                :w_in (*float*):
                    The width of the window function to be computed.
                    This value is in kilometers.
                :dx (*float*):
                    The spacing between points in the window.
                    This is equivalent to the sample spacing.
                    This value is in kilometers.
            Outputs:
                :w_func (*np.ndarray*):
                    Window function of width
                    w_in and with sample spacing dx.
        """
        # Window functions have an odd number of points.
        nw_pts = int(2 * np.floor(w_in / (2.0 * dx)) + 1)

        # Compute argument of window function.
        x = (np.arange(nw_pts) - ((nw_pts - 1) / 2.0)) * dx / w_in

        # Compute window function.
        w_func = iv(0.0, TWO_PI * np.sqrt((1.0 - 4.0*x*x))) / IV0_20
        return w_func

    def __kb25(w_in, dx):
        """
            Purpose:
                Compute the Kaiser-Bessel 2.5 window function.
            Arguments:
                :w_in (*float*):
                    The width of the window function to be computed.
                    This value is in kilometers.
                :dx (*float*):
                    The spacing between points in the window.
                    This is equivalent to the sample spacing.
                    This value is in kilometers.
            Outputs:
                :w_func (*np.ndarray*):
                    Window function of width
                    w_in and with sample spacing dx.
        """
        # Window functions have an odd number of points.
        nw_pts = int(2 * np.floor(w_in / (2.0 * dx)) + 1)

        # Compute argument of window function.
        x = (np.arange(nw_pts) - ((nw_pts - 1) / 2.0)) * dx / w_in

        # Alpha value for kb25 is 2.5.
        alpha = 2.5 * ONE_PI

        # Compute window function.
        w_func = iv(0.0, alpha * np.sqrt((1.0 - 4.0*x*x))) / IV0_25
        return w_func

    def __kb35(w_in, dx):
        """
            Purpose:
                Compute the Kaiser-Bessel 3.5 window function.
            Arguments:
                :w_in (*float*):
                    The width of the window function to be computed.
                    This value is in kilometers.
                :dx (*float*):
                    The spacing between points in the window.
                    This is equivalent to the sample spacing.
                    This value is in kilometers.
            Outputs:
                :w_func (*np.ndarray*):
                    Window function of width
                    w_in and with sample spacing dx.
        """
        # Window functions have an odd number of points.
        nw_pts = int(2 * np.floor(w_in / (2.0 * dx)) + 1)

        # Compute argument of window function.
        x = (np.arange(nw_pts) - ((nw_pts - 1) / 2.0)) * dx / w_in

        # Alpha value for kb35 is 3.5.
        alpha = 3.5 * ONE_PI

        # Compute window function.
        w_func = iv(0.0, alpha * np.sqrt((1.0 - 4.0*x*x))) / IV0_35
        return w_func

    def __kbmd20(w_in, dx):
        """
            Purpose:
                Compute the Modifed Kaiser-Bessel 2.0
                window function.
            Arguments:
                :w_in (*float*):
                    The width of the window function to be computed.
                    This value is in kilometers.
                :dx (*float*):
                    The spacing between points in the window.
                    This is equivalent to the sample spacing.
                    This value is in kilometers.
            Outputs:
                :w_func (*np.ndarray*):
                    Window function of width
                    w_in and with sample spacing dx.
        """
        # Window functions have an odd number of points.
        nw_pts = int(2 * np.floor(w_in / (2.0 * dx)) + 1)

        # Compute argument of window function.
        x = (np.arange(nw_pts) - ((nw_pts - 1) / 2.0)) * dx / w_in

        # Compute window function.
        w_func = (iv(0.0, TWO_PI*np.sqrt(1.0 - 4.0*x*x)) - 1.0)/(IV0_20 - 1.0)
        return w_func

    def __kbmd25(w_in, dx):
        """
            Purpose:
                Compute the Modifed Kaiser-Bessel 2.5
                window function.
            Arguments:
                :w_in (*float*):
                    The width of the window function to be computed.
                    This value is in kilometers.
                :dx (*float*):
                    The spacing between points in the window.
                    This is equivalent to the sample spacing.
                    This value is in kilometers.
            Outputs:
                :w_func (*np.ndarray*):
                    Window function of width
                    w_in and with sample spacing dx.
        """
        # Window functions have an odd number of points.
        nw_pts = int(2 * np.floor(w_in / (2.0 * dx)) + 1)

        # Compute argument of window function.
        x = (np.arange(nw_pts) - ((nw_pts - 1) / 2.0)) * dx / w_in

        # Alpha value for kbmd25 is 2.5.
        alpha = 2.5 * ONE_PI

        # Compute window function.
        w_func = (iv(0.0, alpha*np.sqrt(1.0 - 4.0*x*x)) - 1.0) / (IV0_25 - 1.0)
        return w_func

    # Function dictionary with normalized equivalent widths.
    __func_dict = {
        "rect":   {"func": __rect,     "normeq": 1.00000000},
        "coss":   {"func": __coss,     "normeq": 1.50000000},
        "kb20":   {"func": __kb20,     "normeq": 1.49634231},
        "kb25":   {"func": __kb25,     "normeq": 1.65191895},
        "kb35":   {"func": __kb35,     "normeq": 1.92844639},
        "kbmd20": {"func": __kbmd20,   "normeq": 1.52048174},
        "kbmd25": {"func": __kbmd25,   "normeq": 1.65994218}
        }

    __psi_types = ["fresnel", "fresnel3", "fresnel4",
                   "fresnel6", "fresnel8", "full"]

    def __trim_attributes(self, fwd):
        """
            Purpose:
                Trim the attributes in the DiffractionCorrection
                class so that only reconstructed points will be
                returned to the user. All other unused points are
                discarded.
            Keywords:
                :fwd (*bool*):
                    Boolean for the forward calculation.
                    If set to True, the forward variables
                    will also be trimmed.
        """
        # Get rid of uncomputed values and keep only what was processed.
        start = self.start
        n_used = self.n_used
        crange = np.arange(n_used)+start

        # Ring radius, azimuth angle, diffracted power, and phase.
        self.rho_km_vals = self.rho_km_vals[crange]
        self.p_norm_vals = self.p_norm_vals[crange]
        self.phi_rad_vals = self.phi_rad_vals[crange]
        self.phase_rad_vals = self.phase_rad_vals[crange]

        # Ring opening angle, normalized power, phase, and transmittance.
        self.B_rad_vals = self.B_rad_vals[crange]
        self.power_vals = self.power_vals[crange]
        self.phase_vals = self.phase_vals[crange]
        self.T_hat_vals = self.T_hat_vals[crange]
        self.T_vals = self.T_vals[crange]

        # Fresnel scale, window width, and RIP-Spacecraft distance.
        self.F_km_vals = self.F_km_vals[crange]
        self.w_km_vals = self.w_km_vals[crange]
        self.D_km_vals = self.D_km_vals[crange]

        # Ring radius corrections.
        self.rho_corr_pole_km_vals = self.rho_corr_pole_km_vals[crange]
        self.rho_corr_timing_km_vals = self.rho_corr_timing_km_vals[crange]

        # Various time attributes.
        self.t_oet_spm_vals = self.t_oet_spm_vals[crange]
        self.t_ret_spm_vals = self.t_ret_spm_vals[crange]
        self.t_set_spm_vals = self.t_set_spm_vals[crange]

        # All other attributes.
        self.mu_vals = self.mu_vals[crange]
        self.tau_vals = self.tau_vals[crange]
        self.f_sky_hz_vals = self.f_sky_hz_vals[crange]
        self.phi_rl_rad_vals = self.phi_rl_rad_vals[crange]
        self.rho_dot_kms_vals = self.rho_dot_kms_vals[crange]
        self.lambda_sky_km_vals = self.lambda_sky_km_vals[crange]
        self.raw_tau_threshold_vals = self.raw_tau_threshold_vals[crange]
        self.tau_threshold_vals = self.tau_threshold_vals[crange]

        # If the forward model was run, trim those attributes as well.
        if fwd:
            # Forward power
            self.p_norm_fwd_vals = self.p_norm_fwd_vals[crange]

            # Forward Transmittance and phase.
            self.T_hat_fwd_vals = self.T_hat_fwd_vals[crange]
            self.phase_fwd_vals = self.phase_fwd_vals[crange]

    def __normalize(self, dx, ker, f_scale):
        """
            Purpose:
                Compute the window normalization
            Arguments:
                :ker (*np.ndarray*):
                    The Fresnel Kernel.
                :dx (*float*):
                    The spacing between points in the window.
                    This is equivalent to the sample spacing.
                    This value is in kilometers.
                :f_scale (*np.ndarray*):
                    The Fresnel Scale in kilometers.
            Outputs:
                :norm_fact (*float*):
                    The normalization of the input
                    Fresnel Kernel.
        """
        # Freespace Integral
        T1 = np.abs(np.sum(ker) * dx)

        # Normalization Factor
        norm_fact = SQRT_2 * f_scale / T1
        return norm_fact

    def __psi_func(self, kD, r, r0, phi, phi0, B, D):
        """
            Purpose:
                Compute psi (MTR Equation 4)
            Arguments:
                :kD (*float*):
                    Wavenumber, unitless.
                :r (*float*):
                    Radius of reconstructed point, in kilometers.
                :r0 (*np.ndarray*):
                    Radius of region within window, in kilometers.
                :phi (*np.ndarray*):
                    Root values of dpsi/dphi, radians.
                :phi0 (*np.ndarray*):
                    Ring azimuth angle corresponding to r0, radians.
                :B (*float*):
                    Ring opening angle, in radians.
                :D (*float*):
                    Spacecraft-RIP distance, in kilometers.
            Outputs:
                :psi (*np.ndarray*):
                    Geometric Function from Fresnel Kernel.
        """
        # Compute Xi variable (MTR86 Equation 4b). Signs of xi are swapped.
        xi = (np.cos(B)/D) * (r * np.cos(phi) - r0 * np.cos(phi0))

        # Compute Eta variable (MTR86 Equation 4c).
        eta = (r0*r0 + r*r - 2.0*r*r0*np.cos(phi-phi0)) / (D*D)

        # Sign of xi swapped from MTR86.
        psi_vals = kD * (np.sqrt(1.0+eta-2.0*xi) + xi - 1.0)
        return psi_vals

    def __dpsi(self, kD, r, r0, phi, phi0, B, D):
        """
            Purpose:
                Compute dpsi/dphi
            Arguments:
                :kD (*float*):
                    Wavenumber, unitless.
                :r (*float*):
                    Radius of reconstructed point, in kilometers.
                :r0 (*np.ndarray*):
                    Radius of region within window, in kilometers.
                :phi (*np.ndarray*):
                    Root values of dpsi/dphi, radians.
                :phi0 (*np.ndarray*):
                    Ring azimuth angle corresponding to r0, radians.
                :B (*float*):
                    Ring opening angle, in radians.
                :D (*float*):
                    Spacecraft-RIP distance, in kilometers.
            Outputs:
                :dpsi (*array*):
                    Partial derivative of psi with
                    respect to phi.
        """
        # Compute Xi variable (MTR86 Equation 4b).
        xi = (np.cos(B)/D) * (r * np.cos(phi) - r0 * np.cos(phi0))

        # Compute Eta variable (MTR86 Equation 4c).
        eta = (r0*r0 + r*r - 2.0*r*r0*np.cos(phi-phi0)) / (D*D)

        psi0 = np.sqrt(1.0+eta-2.0*xi)

        # Compute derivatives.
        dxi = -(np.cos(B)/D) * (r*np.sin(phi))
        deta = 2.0*r*r0*np.sin(phi-phi0)/(D*D)

        # Compute the partial derivative.
        psi_d1 = (0.5/psi0)*(deta-2.0*dxi) + dxi
        psi_d1 *= kD

        return psi_d1

    def __d2psi(self, kD, r, r0, phi, phi0, B, D):
        """
            Purpose:
                Compute d^2psi/dphi^2
            Arguments:
                :kD (*float*):
                    Wavenumber, unitless.
                :r (*float*):
                    Radius of reconstructed point, in kilometers.
                :r0 (*np.ndarray*):
                    Radius of region within window, in kilometers.
                :phi (*np.ndarray*):
                    Root values of dpsi/dphi, radians.
                :phi0 (*np.ndarray*):
                    Ring azimuth angle corresponding to r0, radians.
                :B (*float*):
                    Ring opening angle, in radians.
                :D (*float*):
                    Spacecraft-RIP distance, in kilometers.
            Outputs:
                :dpsi (*np.ndarray*):
                    Second partial derivative of psi
                    with respect to phi.
        """
        # Compute Xi variable (MTR86 Equation 4b).
        xi = (np.cos(B)/D) * (r * np.cos(phi) - r0 * np.cos(phi0))

        # Compute Eta variable (MTR86 Equation 4c).
        eta = (r0*r0 + r*r - 2.0*r*r0*np.cos(phi-phi0)) / (D*D)

        psi0 = np.sqrt(1.0+eta-2.0*xi)

        # Compute derivatives.
        dxi = -(np.cos(B)/D) * (r*np.sin(phi))
        dxi2 = -(np.cos(B)/D) * (r*np.cos(phi))

        deta = 2.0*r*r0*np.sin(phi-phi0)/(D*D)
        deta2 = 2.0*r*r0*np.cos(phi-phi0)/(D*D)

        # Compute the second partial derivative.
        psi_d2 = (-0.25/(psi0*psi0*psi0))*(deta-2.0*dxi)*(deta-2.0*dxi)
        psi_d2 += (0.5/psi0)*(deta2-2.0*dxi2)+dxi2
        psi_d2 *= kD

        return psi_d2

    def __ftrans(self, fwd):
        """
            Purpose:
                Compute the Fresnel Inversion.
            Arguments:
                :self:
                    Instance of DiffractionCorrection class.
            Keywords:
                :fwd (*bool*):
                    Boolean for whether or not the forward
                    calculation is being performed.
            Outputs:
                :T_out (*np.ndarray*):
                    Complex transmittance.
        """
        # Compute product of wavenumber and RIP distance.
        kD_vals = TWO_PI * self.D_km_vals / self.lambda_sky_km_vals

        # Define functions.
        fw = self.__func_dict[self.wtype]["func"]
        mes = "\t\tPt: %d  Tot: %d  Width: %d  Psi Iters: %d"

        # If forward transform, adjust starting point by half a window.
        if fwd:
            w_max = np.max(self.w_km_vals[self.start:self.start + self.n_used])
            nw_fwd = int(np.ceil(w_max / (2.0 * self.dx_km)))
            start = int(self.start + nw_fwd)
            n_used = int(self.n_used - 2 * nw_fwd)
            T_in = self.T_vals
        else:
            start = self.start
            n_used = self.n_used
            T_in = self.T_hat_vals
        
        # Create empty array for reconstruction / forward transform.
        T_out = T_in * 0.0

        # Compute first window width and window function.
        w_init = self.w_km_vals[start]
        w_func = fw(w_init, self.dx_km)

        # Compute number of points in window function
        nw = np.size(w_func)

        # Computed range about the first point
        crange = np.arange(int(start-(nw-1)/2), int(1+start+(nw-1)/2))

        # Compute current radius and RIP distance.
        r = self.rho_km_vals[start]
        r0 = self.rho_km_vals[crange]

        if (self.psitype == 'fresnel'):
            crange -= 1
            F2 = (self.F_km_vals*self.F_km_vals).tolist()
            x = r-r0
            x2 = HALF_PI * x * x
            loop = 0
            for i in np.arange(n_used):
                # Current point being computed.
                center = start+i

                # Window width and Frensel scale for current point.
                w = self.w_km_vals[center]
                F = self.F_km_vals[center]

                if (np.abs(w_init - w) >= 2.0 * self.dx_km):
                    # Reset w_init and recompute window function.
                    w_init = w
                    w_func = fw(w, self.dx_km)

                    # Reset number of window points
                    nw = np.size(w_func)

                    # Computed range for current point
                    crange = np.arange(int(center-(nw-1)/2),
                                       int(1+center+(nw-1)/2))

                    # Ajdust ring radius by dx_km.
                    r0 = self.rho_km_vals[crange]
                    r = self.rho_km_vals[center]

                    # Compute psi for with stationary phase value
                    x = r-r0
                    x2 = HALF_PI * x * x
                else:
                    crange += 1
                
                psi_vals = x2 / F2[center]

                # Compute kernel function for Fresnel inverse
                if fwd:
                    ker = w_func*np.exp(1j*psi_vals)
                else:
                    ker = w_func*np.exp(-1j*psi_vals)

                # Range of diffracted data that falls inside the window
                T = T_in[crange]

                # Compute 'approximate' Fresnel Inversion for current point
                T_out[center] = np.sum(ker*T)*self.dx_km*(0.5+0.5j)/F

                # If normalization has been set, normalize the reconstruction
                if self.norm:
                    T_out[center] *= self.__normalize(self.dx_km, ker, F)

                if self.verbose:
                    print(mes % (i, n_used, nw, loop), end="\r")
            if self.verbose:
                print("\n")
        elif (self.psitype == 'fresnel3'):
            crange -= 1
            cosb = np.cos(self.B_rad_vals)
            cosp = np.cos(self.phi_rad_vals)
            sinp = np.sin(self.phi_rad_vals)
            A_2 = 0.5*cosb*cosb*sinp*sinp/(1-cosb*cosb*sinp*sinp)

            # Legendre polynomials
            P_1 = cosb*cosp
            P_1_1 = P_1*P_1
            P_2 = (3.0*P_1_1-1.0)*0.5
            P_1_2 = 2.0*P_1*P_2
            P_3 = (5.0*P_1_1-3.0)*0.5*P_1

            # Second set of polynomials.
            b_0 = (1.0-P_1_1)*0.5
            b_1 = (P_1-P_1*P_2)/3.0
            b_2 = (P_2-P_1*P_3)*0.25

            # Initial radial parameter
            x = r-r0
            x2 = x*x

            # D_km_vals and the square of it.
            d = self.D_km_vals
            d2 = d*d

            loop = 0
            for i in np.arange(n_used):
                # Current point being computed.
                center = start+i

                # Window width and Frensel scale for current point.
                w = self.w_km_vals[center]
                F = self.F_km_vals[center]

                if (np.abs(w_init - w) >= 2.0 * self.dx_km):
                    # Reset w_init and recompute window function.
                    w_init = w
                    w_func = fw(w, self.dx_km)

                    # Reset number of window points
                    nw = np.size(w_func)

                    # Computed range for current point
                    crange = np.arange(int(center-(nw-1)/2),
                                       int(1+center+(nw-1)/2))

                    # Ajdust ring radius by dx_km.
                    r = self.rho_km_vals[center]
                    r0 = self.rho_km_vals[crange]
                    x = r-r0
                    x2 = x*x
                else:
                    crange += 1
                
                z = x/d[center]
                z2 = x2/d2[center]

                psi_vals = z2*(b_0[center]-A_2[center]*P_1_1[center]+
                               (b_1[center]-A_2[center]*P_1_2[center])*z)

                psi_vals *= kD_vals[center]

                # Compute kernel function for Fresnel inverse
                if fwd:
                    ker = w_func*np.exp(1j*psi_vals)
                else:
                    ker = w_func*np.exp(-1j*psi_vals)

                # Range of diffracted data that falls inside the window
                T = T_in[crange]

                # Compute 'approximate' Fresnel Inversion for current point
                T_out[center] = np.sum(ker*T)*self.dx_km*(1.0+1.0j)/(2.0*F)

                # If normalization has been set, normalize the reconstruction
                if self.norm:
                    T_out[center] *= self.__normalize(self.dx_km, ker, F)
                if self.verbose:
                    print(mes % (i, n_used, nw, loop), end="\r")
            if self.verbose:
                print("\n", end="\r")
        elif (self.psitype == 'fresnel4'):
            crange -= 1
            cosb = np.cos(self.B_rad_vals)
            cosp = np.cos(self.phi_rad_vals)
            sinp = np.sin(self.phi_rad_vals)
            A_2 = 0.5*cosb*cosb*sinp*sinp/(1.0-cosb*cosb*sinp*sinp)

            # Legendre polynomials
            P_1 = cosb*cosp
            P12 = P_1*P_1
            P_2 = (3.0*P12-1.0)*0.5
            P_3 = (5.0*P12-3.0)*0.5*P_1

            # Products of Legendre Polynomials used in Expansion
            C_0 = P_1*P_1
            C_1 = 2.0*P_1*P_2
            C_2 = P_2*P_2

            # Second set of polynomials.
            b_0 = (1.0-P12)*0.5
            b_1 = (P_1-P_1*P_2)/3.0
            b_2 = (P_2-P_1*P_3)*0.25

            # Initial radial parameter
            x = (r-r0)
            x2 = x*x

            # D_km_vals and the square of it.
            d = self.D_km_vals
            d2 = d*d

            loop = 0
            for i in np.arange(n_used):
                # Current point being computed.
                center = start+i

                # Window width and Frensel scale for current point.
                w = self.w_km_vals[center]
                F = self.F_km_vals[center]

                if (np.abs(w_init - w) >= 2.0 * self.dx_km):
                    # Reset w_init and recompute window function.
                    w_init = w
                    w_func = fw(w, self.dx_km)

                    # Reset number of window points
                    nw = np.size(w_func)

                    # Computed range for current point
                    crange = np.arange(int(center-(nw-1)/2),
                                       int(1+center+(nw-1)/2))

                    # Ajdust ring radius by dx_km.
                    r = self.rho_km_vals[center]
                    r0 = self.rho_km_vals[crange]
                    x = r-r0
                    x2 = x*x
                else:
                    crange += 1

                z = x/d[center]
                z2 = x2/d2[center]

                psi_vals = b_0[center]-A_2[center]*C_0[center]
                psi_vals += z*(b_1[center]-A_2[center]*C_1[center])
                psi_vals += z2*(b_2[center]-A_2[center]*C_2[center])
                psi_vals *= kD_vals[center]*z2

                # Compute kernel function for Fresnel inverse
                if fwd:
                    ker = w_func*np.exp(1j*psi_vals)
                else:
                    ker = w_func*np.exp(-1j*psi_vals)

                # Range of diffracted data that falls inside the window
                T = T_in[crange]

                # Compute 'approximate' Fresnel Inversion for current point
                T_out[center] = np.sum(ker*T)*self.dx_km*(1.0+1.0j)/(2.0*F)

                # If normalization has been set, normalize the reconstruction
                if self.norm:
                    T_out[center] *= self.__normalize(self.dx_km, ker, F)
                if self.verbose:
                    print(mes % (i, n_used, nw, loop), end="\r")
            if self.verbose:
                print("\n", end="\r")
        elif (self.psitype == 'fresnel6'):
            crange -= 1
            cosb = np.cos(self.B_rad_vals)
            cosp = np.cos(self.phi_rad_vals)
            sinp = np.sin(self.phi_rad_vals)
            A_2 = 0.5*cosb*cosb*sinp*sinp/(1.0-cosb*cosb*sinp*sinp)

            # Legendre polynomials
            P_1 = cosb*cosp
            P12 = P_1*P_1
            P_2 = (3.0*P12-1.0)*0.5
            P_3 = (5.0*P12-3.0)*0.5*P_1
            P_4 = (35.0*P12*P12-30.0*P12+3.0)/8.0
            P_5 = P_1*(63.0*P12*P12-70.0*P12+15.0)/8.0

            # Second set of polynomials.
            b_0 = (1.0-P12)*0.5
            b_1 = (P_1-P_1*P_2)/3.0
            b_2 = (P_2-P_1*P_3)*0.25
            b_3 = (P_3-P_1*P_4)*0.2
            b_4 = (P_4-P_1*P_5)/6.0

            x = r-r0
            x2 = x*x
            x3 = x2*x
            x4 = x3*x

            # Products of Legendre Polynomials used in Expansion
            C_0 = P_1*P_1
            C_1 = 2.0*P_1*P_2
            C_2 = P_2*P_2+2.0*P_1*P_3
            C_3 = 2.0*P_2*P_3
            C_4 = P_3*P_3

            # D_km_vals and various powers.
            d = self.D_km_vals
            d2 = d*d
            d3 = d*d2
            d4 = d*d3

            loop = 0
            for i in np.arange(n_used):
                # Current point being computed.
                center = start+i

                # Window width and Frensel scale for current point.
                w = self.w_km_vals[center]
                F = self.F_km_vals[center]

                if (np.abs(w_init - w) >= 2.0 * self.dx_km):
                    # Reset w_init and recompute window function.
                    w_init = w
                    w_func = fw(w, self.dx_km)

                    # Reset number of window points
                    nw = np.size(w_func)

                    # Computed range for current point
                    crange = np.arange(int(center-(nw-1)/2),
                                       int(1+center+(nw-1)/2))

                    # Ajdust ring radius by dx_km.
                    r = self.rho_km_vals[center]
                    r0 = self.rho_km_vals[crange]
                    x = r-r0
                    x2 = x*x
                    x3 = x2*x
                    x4 = x3*x
                else:
                    crange += 1

                z = x/d[center]
                z2 = x2/d2[center]
                z3 = x3/d3[center]
                z4 = x4/d4[center]

                psi_vals = b_0[center]-A_2[crange]*C_0[center]
                psi_vals += z*(b_1[center]-A_2[crange]*C_1[center])
                psi_vals += z2*(b_2[center]-A_2[crange]*C_2[center])
                psi_vals += z3*(b_3[center]-A_2[crange]*C_3[center])
                psi_vals += z4*(b_4[center]-A_2[crange]*C_4[center])

                psi_vals *= z2*kD_vals[center]

                # Compute kernel function for Fresnel inverse
                if fwd:
                    ker = w_func*np.exp(1j*psi_vals)
                else:
                    ker = w_func*np.exp(-1j*psi_vals)

                # Range of diffracted data that falls inside the window
                T = T_in[crange]

                # Compute 'approximate' Fresnel Inversion for current point
                T_out[center] = np.sum(ker*T)*self.dx_km*(1.0+1.0j)/(2.0*F)

                # If normalization has been set, normalize the reconstruction
                if self.norm:
                    T_out[center] *= self.__normalize(self.dx_km, ker, F)
                if self.verbose:
                    print(mes % (i, n_used, nw, loop), end="\r")
            if self.verbose:
                print("\n", end="\r")
        elif (self.psitype == 'fresnel8'):
            crange -= 1
            cosb = np.cos(self.B_rad_vals)
            cosp = np.cos(self.phi_rad_vals)
            sinp = np.sin(self.phi_rad_vals)
            A_2 = 0.5*cosb*cosb*sinp*sinp/(1.0-cosb*cosb*sinp*sinp)

            # Legendre polynomials
            P_1 = cosb*cosp
            P12 = P_1*P_1
            P_2 = (3.0*P12-1.0)*0.5
            P_3 = P_1*(5.0*P12-3.0)*0.5
            P_4 = (35.0*P12*P12-30.0*P12+3.0)/8.0
            P_5 = P_1*(63.0*P12*P12-70.0*P12+15.0)/8.0
            P_6 = (231.0*P12*P12*P12-315.0*P12*P12+105.0*P12-5.0)/16.0

            # Products of Legendre Polynomials used in Expansion
            C_0 = P_1*P_1
            C_1 = 2.0*P_1*P_2
            C_2 = 2.0*P_1*P_3+P_2*P_2
            C_3 = 2.0*P_1*P_4+2.0*P_2*P_3
            C_4 = 2.0*P_2*P_4+P_3*P_3
            C_5 = 2.0*P_3*P_4
            C_6 = P_4*P_4

            # Second set of polynomials.
            b_0 = (1.0-P12)/2.0
            b_1 = (P_1-P_1*P_2)/3.0
            b_2 = (P_2-P_1*P_3)/4.0
            b_3 = (P_3-P_1*P_4)/5.0
            b_4 = (P_4-P_1*P_5)/6.0
            b_5 = (P_5-P_1*P_4)/7.0
            b_6 = (P_6-P_1*P_5)/8.0

            x = (r-r0)
            x2 = x*x
            x3 = x2*x
            x4 = x3*x
            x5 = x4*x
            x6 = x5*x

            # D_km_vals and various powers.
            d = self.D_km_vals
            d2 = d*d
            d3 = d*d2
            d4 = d*d3
            d5 = d*d4
            d6 = d*d5

            loop = 0
            for i in np.arange(n_used):
                # Current point being computed.
                center = start+i

                # Window width and Frensel scale for current point.
                w = self.w_km_vals[center]
                F = self.F_km_vals[center]

                if (np.abs(w_init - w) >= 2.0 * self.dx_km):
                    # Reset w_init and recompute window function.
                    w_init = w
                    w_func = fw(w, self.dx_km)

                    # Reset number of window points
                    nw = np.size(w_func)

                    # Computed range for current point
                    crange = np.arange(int(center-(nw-1)/2),
                                       int(1+center+(nw-1)/2))

                    # Ajdust ring radius by dx_km.
                    r = self.rho_km_vals[center]
                    r0 = self.rho_km_vals[crange]
                    x = r-r0
                    x2 = x*x
                    x3 = x2*x
                    x4 = x3*x
                    x5 = x4*x
                    x6 = x5*x
                else:
                    crange += 1

                z = x/d[center]
                z2 = x2/d2[center]
                z3 = x3/d3[center]
                z4 = x4/d4[center]
                z5 = x5/d5[center]
                z6 = x6/d6[center]

                psi_vals = b_0[center]-A_2[crange]*C_0[center]
                psi_vals += z*(b_1[center]-A_2[crange]*C_1[center])
                psi_vals += z2*(b_2[center]-A_2[crange]*C_2[center])
                psi_vals += z3*(b_3[center]-A_2[crange]*C_3[center])
                psi_vals += z4*(b_4[center]-A_2[crange]*C_4[center])
                psi_vals += z5*(b_5[center]-A_2[crange]*C_5[center])
                psi_vals += z6*(b_6[center]-A_2[crange]*C_6[center])

                psi_vals *= z2*kD_vals[center]

                # Compute kernel function for Fresnel inverse
                if fwd:
                    ker = w_func*np.exp(1j*psi_vals)
                else:
                    ker = w_func*np.exp(-1j*psi_vals)

                # Range of diffracted data that falls inside the window
                T = T_in[crange]

                # Compute 'approximate' Fresnel Inversion for current point
                T_out[center] = np.sum(ker*T)*self.dx_km*(1.0+1.0j)/(2.0*F)

                # If normalization has been set, normalize the reconstruction
                if self.norm:
                    T_out[center] *= self.__normalize(self.dx_km, ker, F)
                if self.verbose:
                    print(mes % (i, n_used, nw, loop), end="\r")
            if self.verbose:
                print("\n", end="\r")
        else:
            for i in np.arange(n_used):
                # Current point being computed.
                center = start+i

                # Current window width and Fresnel scale.
                w = self.w_km_vals[center]
                F = self.F_km_vals[center]

                if (np.abs(w_init - w) >= 2.0 * self.dx_km):
                    # Reset w_init and recompute window function.
                    w_init = w
                    w_func = fw(w, self.dx_km)

                    # Reset number of window points
                    nw = np.size(w_func)
                else:
                    pass

                # Computed range for current point
                crange = np.arange(int(center-(nw-1)/2),
                                   int(1+center+(nw-1)/2))
                
                # Ajdust ring radius by dx_km.
                r = self.rho_km_vals[center]
                r0 = self.rho_km_vals[crange]
                d = self.D_km_vals[center]
                b = self.B_rad_vals[center]
                phi0 = self.phi_rad_vals[center]
                phi = self.phi_rad_vals[center] + np.zeros(nw)
                kD = kD_vals[crange]

                # Compute Newton-Raphson perturbation
                psi_d1 = self.__dpsi(kD, r, r0, phi, phi0, b, d)
                loop = 0

                while (np.max(np.abs(psi_d1)) > 1.0e-4):
                    psi_d1 = self.__dpsi(kD, r, r0, phi, phi0, b, d)
                    psi_d2 = self.__d2psi(kD, r, r0, phi, phi0, b, d)
                    
                    # Newton-Raphson
                    phi += -(psi_d1 / psi_d2)

                    # Add one to loop variable for each iteration
                    loop += 1
                    if (loop > 5):
                        break

                # Compute Eta variable (MTR86 Equation 4c).
                psi_vals = self.__psi_func(kD, r, r0, phi, phi0, b, d)

                # Compute kernel function for Fresnel inverse
                if fwd:
                    ker = w_func*np.exp(1j*psi_vals)
                else:
                    ker = w_func*np.exp(-1j*psi_vals)

                # Range of diffracted data that falls inside the window
                T = T_in[crange]

                # Compute 'approximate' Fresnel Inversion for current point
                T_out[center] = np.sum(ker*T)*self.dx_km*(1.0+1.0j)/(2.0*F)

                # If normalization has been set, normalize the reconstruction
                if self.norm:
                    T_out[center] *= self.__normalize(self.dx_km, ker, F)
                if self.verbose:
                    print(mes % (i, n_used-1, nw, loop), end="\r")
            if self.verbose:
                print("\n", end="\r")

        return T_out
