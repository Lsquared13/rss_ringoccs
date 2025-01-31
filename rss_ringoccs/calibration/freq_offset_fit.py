"""
Purpose:
        Compute a fit to the frequency offset residual using
        the frequency offset, predicted sky frequency, and
        reconstructed sky
        frequency.
"""

import numpy as np
import warnings
warnings.simplefilter('ignore', np.RankWarning)
import matplotlib.pyplot as plt
from scipy.interpolate import splrep, splev
import sys

from .calc_f_sky_recon import calc_f_sky_recon
from .calc_freq_offset import calc_freq_offset
from ..tools.write_output_files import construct_filepath

import sys
sys.path.append('../../')
import rss_ringoccs as rss
sys.path.remove('../../')


class FreqOffsetFit(object):
    """
    Obtains :math:`f(t)_{offset}` from ``calc_freq_offset``,
    :math:`f(t)_{dr}` from ``calc_f_sky_recon``, and :math:`f(t)_{dp}`
    from ``get_f_sky_pred``. Computes a polynomial fit
    :math:`\hat{f}(t)_{resid}` of order specified by ``poly_order`` to
    sigma-clipped residual difference :math:`f(t)_{resid}` between
    observed and predicted frequency offset where the residual is
    given by

    .. math::
        f(t)_{resid} = f(t)_{offset} - (f(t)_{dr}-f(t)_{dp})

    Final frequency offset :math:`\hat{f}(t)_{offset}` is found using
    the polynomial fit :math:`\hat{f}(t)_{resid}` to the frequency
    offset residuals such that

    .. math::
        \hat{f}(t)_{offset} = \hat{f}(t)_{resid} +
        (f(t)_{dr} - f(t)_{dp})

    Arguments:
        :rsr_inst (*object*): object instance of the RSRReader class
        :geo_inst (*object*): object instance of the Geometry class

    Keyword Arguments:
        :poly_order (*float*): whole number specifying the order of
                        the polynomial fit to the residual frequency
                        offset
        :f_uso_x (*float*): frequency in Hz of the X-band ultra-stable
                        oscilator onboard the Cassini spacecraft.
                        Default is 8427222034.3405 Hz.
        :verbose (*bool*): when True, enables verbose output mode

    Attributes:
        :f_offset_fit (*np.ndarray*): final frequency offset evaluated using 
                        fit to offset residuals 
                        :math:`\hat{f}(t)_{offset} =
                        \hat{f}(t)_{resid} + (f(t)_{dr} - f(t)_{dp})`
        :f_spm (*np.ndarray*): SPM at which the offset frequency was sampled
        :f_sky_pred (*np.ndarray*): predicted sky frequency :math:`f(t)_{dp}`
        :f_sky_resid_fit (*np.ndarray*): fit to the residual frequency offset
                        math:`\hat{f}(t)_{resid}` evaluated at
                        ``f_spm``
        :chi_squared (*float*): sum of the squared residual frequency offset fit
                        normalized by the fit value (Pearson's
                        :math:`\chi^2`) such that
                        :math:`\chi^2 = \\frac{1}{N-m}
                        \sum((\hat{f}(t)_{resid}-f(t)_{resid})
                        /\hat{f}(t)_{resid})^2`
                        for :math:`N` data and :math:`m` free
                        parameters (i.e., the polynomial order plus
                        one).
    """

    def __init__(self, rsr_inst, geo_inst, poly_order=7,
            f_uso_x=8427222034.34050, verbose=False, write_file=False):


        # Check inputs for validity
        if not isinstance(rsr_inst, rss.rsr_reader.RSRReader):
            sys.exit('ERROR (FreqOffsetFit): rsr_inst input must be an '
                + 'instance of the RSRReader class')

        if not isinstance(geo_inst, rss.occgeo.Geometry):
            sys.exit('ERROR (FreqOffsetFIt): geo_inst input must be an '
                + 'instance of the Geometry class')

        if not isinstance(poly_order, int):
            print('WARNING (FreqOffsetFit): poly_order input must be an int. '
                + 'Ignoring current input and setting to order 9')
            poly_order = 9

        if not isinstance(verbose, bool):
            print('WARNING (FreqOffsetFit): verbose input must be boolean. '
                + 'Ignoring current input and setting to False')
            verbose = False

        # Extract necessary information from input instances
        #   NOTE: predicted sky frequency extracted from rsr_inst later
        self.band = rsr_inst.band
        self.year = rsr_inst.year
        self.doy = rsr_inst.doy
        self.dsn = rsr_inst.dsn
        self.raw_spm_vals = rsr_inst.spm_vals
        self.__IQ_m = rsr_inst.IQ_m
        self.rev_info = rsr_inst.rev_info


        spm_geo = geo_inst.t_oet_spm_vals
        rho_geo = geo_inst.rho_km_vals
        kernels = geo_inst.kernels
        self.profdir = geo_inst.get_profile_dir()
        self.rev_info = geo_inst.rev_info
        sc_name = geo_inst.history['Positional Args']['spacecraft']

        # Adjust USO frequency by wavelength
        if self.band == 'X':
            f_uso = f_uso_x
        elif self.band == 'S':
            f_uso = f_uso_x*(3.0/11.0)
        elif self.band == 'K':
            f_uso = f_uso_x*3.8
        else:
            raise ValueError('WARNING (freq_offset_fit.py): Invalid frequency '
                            + 'band!')

        # Compute spline coefficients relating SPM to rho
        rho_geo_spl_coef = splrep(spm_geo, rho_geo)

        # compute max and min SPM values for occultation
        # Evaluate spm-to-rho spline at raw SPM to get raw rho sampling
        #    that matches SPM values
        self.raw_rho = splev(self.raw_spm_vals,rho_geo_spl_coef)

        # Create boolean mask where True is within occultation range and
        #    False is outside the occultation range -- this is generalized
        #    to work for diametric and chord occultations
        inds = [(self.raw_rho>6.25e4)&(self.raw_rho<3e5)]
        occ_inds = [(self.raw_rho>7e4)&(self.raw_rho<1.4e5)]

        # Find the max and min SPM values with True boolean indices
        if len(self.raw_spm_vals[inds]) > 2 :
            spm_min = np.min(self.raw_spm_vals[inds])
            spm_max = np.max(self.raw_spm_vals[inds])
        else:
            print('Error in estimating SPM range for frequency offset!')
            spm_min = self.raw_spm_vals[0]
            spm_max = self.raw_spm_vals[-1]

        # Calculate offset frequency within given SPM limits
        if verbose:
            print('\tCalculating observed frequency offset...')

        foff_inst = calc_freq_offset(rsr_inst,spm_min,spm_max)
        f_spm, f_offset = foff_inst.f_spm, foff_inst.f_offset

        if verbose:
            print('\tCalculating predicted frequency offset...')
        spm0, f_sky_pred = rsr_inst.get_f_sky_pred(f_spm=f_spm)
        f_sky_recon = calc_f_sky_recon(f_spm, rsr_inst, sc_name, f_uso,
                kernels)

        # Interpolate rho to frequency time values
        f_rho = splev(f_spm, rho_geo_spl_coef)

        # Compute residual sky frequency
        f_sky_resid = f_offset - (f_sky_recon - f_sky_pred)

        if verbose:
            print('\tCreating sigma clipping mask array...')
        self.__fsr_mask = self.create_mask(f_spm, f_rho, f_sky_resid)

        # Fit frequency offset residual
        if verbose:
            print('\tCalculating fit to frequency offset residuals...')
        f_sky_resid_fit,chi2 = self.fit_f_sky_resid(f_spm, f_rho, f_sky_resid,
                poly_order=poly_order)

        # Draw and save reference plot
        if write_file:
            self.plotFORFit(f_spm,f_sky_resid,f_sky_resid_fit,self.__fsr_mask,
                            spm_min,spm_max,geo_inst.t_oet_spm_vals[0],
                            geo_inst.t_oet_spm_vals[-1],poly_order)

        # Calculate frequency offset fit
        self.f_offset_fit = f_sky_resid_fit + (f_sky_recon - f_sky_pred)
        self.f_spm = f_spm
        self.f_sky_pred  = f_sky_pred
        self.f_sky_resid_fit = f_sky_resid_fit
        self.chi_squared = chi2
        self.f_sky_resid = f_sky_resid

    def create_mask(self, f_spm, f_rho, f_sky_resid):
        """
        Purpose:
            Creates a Boolean mask array which excludes data based on
            the following critera:
                #. ring or planetary occultation in region prevents
                accurate estimation of the offset frequency
                #. offset frequencies fall more than 5-sigma beyond
                the median offset frequency
                #. adjacent data all excluded by previous requirements
                (excludes noise which by happenstance satisfies the
                above criteria)

        Arguments:
            :f_spm (*np.ndarray*): SPM sampled by ``calc_freq_offset``
                        when calculating the offset frequencies for
                        the occultation
            :f_rho (*np.ndarray*): ring intercept radius of the
                        spacecraft signal resampled to match f_spm
            :f_sky_resid (*np.ndarray*): residual sky frequency

        Returns:
            :fsr_mask (*np.ndarray*): Array of booleons, with True for
                                      reliable residual frequency offset.
        """

        # Create mask array that includes everything
        fsr_mask = np.array([True for i in range(len(f_sky_resid))],dtype=bool)

        # Compute median, standard deviation, and implememt sigma-clipping
        #   for data which fall in acceptable regions
        fsr_median = np.nanmedian(f_sky_resid[fsr_mask])
        fsr_stdev = 3.*np.sqrt(np.nanmedian(np.square(f_sky_resid-fsr_median)))
        if fsr_stdev < 1 or fsr_stdev > 5 :
            fsr_stdev = 1

        # iteratively check to see if each residual value is within 3 sigma
        for i in range(len(f_sky_resid)):
            # exclude nans
            if np.isnan(f_sky_resid[i]):
                fsr_mask[i] = False
            # exclude data outside 3-sigma of median
            if (f_sky_resid[i] < fsr_median - fsr_stdev) or (
                    f_sky_resid[i] > fsr_median + fsr_stdev):
                fsr_mask[i] = False

        # if there are no True values in mask array, then reset 
        #   and hope for the best
        if not np.any(fsr_mask):
            fsr_mask = np.array([True for i in range(len(f_sky_resid))],
                    dtype=bool)
            for i in range(len(f_sky_resid)):
                # exclude nans
                if np.isnan(f_sky_resid[i]):
                    fsr_mask[i] = False

        # Polynomial fit clipping
        # try a 9th order polynomial fit
        pinit = np.polyfit(f_spm[fsr_mask], f_sky_resid[fsr_mask], 9)

        # Compute standard deviation from fit and implememt sigma-clipping
        #   for data which fall in acceptable regions
        fit_stdev = 3.*np.sqrt(np.nanmedian(np.square(f_sky_resid-
            np.polyval(pinit,f_spm))))

        # if the fit can give us a reasonable constraint, use it to 
        #   help sigma clip
        if fit_stdev < 2 :
            # Create new mask array that includes everything
            fsr_mask = np.array([True for i in range(len(f_sky_resid))],
                    dtype=bool)
            # iteratively check to see if each residual value is within 3 sigma
            for i in range(len(f_sky_resid)):
                if (f_sky_resid[i] < np.polyval(pinit,f_spm[i]) - 
                        fit_stdev) or (f_sky_resid[i] > np.polyval(
                            pinit,f_spm[i]) + fit_stdev):
                    fsr_mask[i] = False
        else:
            fit_stdev = 0.1

        # iteratively check adjacent values for false positives
        #   i.e., all four adjacent mask array values are False
        #   first forwards
        for i in range(2,len(fsr_mask)-2):
            if fsr_mask[i]:
                if not fsr_mask[i-2]:
                    if not fsr_mask[i-1]:
                        if not fsr_mask[i+1]:
                            if not fsr_mask[1+2]:
                                fsr_mask[i] = False

        # now check backwards, just in case false positives were supporting
        # each other and preventing removal
        for i in range(len(fsr_mask)-2,2,-1):
            if fsr_mask[i]:
                if not fsr_mask[i-2]:
                    if not fsr_mask[i-1]:
                        if not fsr_mask[i+1]:
                            if not fsr_mask[1+2]:
                                fsr_mask[i] = False

        ## return frequency sky residual mask array
        return fsr_mask

    def fit_f_sky_resid(self, f_spm, f_rho, f_sky_resid, poly_order=None, 
            verbose=False):
        """
        Fit a polynomial to residual frequency.

        Arguments:
            :f_spm (*np.ndarray*): SPM sampled by ``calc_freq_offset``
                        when calculating the offset frequencies for
                        the occultation
            :f_rho (*np.ndarray*): ring intercept radius of the
                        spacecraft signal resampled to match f_spm
            :f_sky_resid (*np.ndarray*): residual sky frequency

        Keyword Arguments:
            :poly_order (*float*): Order of polynomial fit to residual
                        frequency
            :verbose (*bool*): If True, print processing steps
        
        Returns:
            :f_sky_resid_fit (*np.ndarray*): fit to the residual frequency 
                            offset math:`\hat{f}(t)_{resid}` evaluated at
                            ``f_spm``
            :chi2 (*float*): sum of the squared residual frequency offset fit
                            normalized by the fit value (Pearson's
                            :math:`\chi^2`) such that
                            :math:`\chi^2 = \\frac{1}{N-m}
                            \sum((\hat{f}(t)_{resid}-f(t)_{resid})
                            /\hat{f}(t)_{resid})^2`
                            for :math:`N` data and :math:`m` free
                            parameters (i.e., the polynomial order plus
                            one).
        """

        if not isinstance(poly_order, int):
            print('WARNING (FreqOffsetFit): poly_order input must be an int. '
                + 'Ignoring current input and setting to order 9')
            poly_order = 9


        npts = len(f_spm)
        spm_temp = ((f_spm - f_spm[int(npts / 2)])
            / max(f_spm - f_spm[int(npts / 2)]))

        ## fit using polynomial of user-selected order
        coef = np.polyfit(spm_temp[self.__fsr_mask],f_sky_resid[self.__fsr_mask],
                                poly_order)

        '''if verbose:
            print('\tPolynomial sum squared residuals:',stats[0])'''

        f_sky_resid_fit = np.polyval( coef, spm_temp )
        v = float(len(f_sky_resid[self.__fsr_mask])) - (poly_order+1)
        chi2 = np.sum(np.square(f_sky_resid_fit[self.__fsr_mask]-
            f_sky_resid[self.__fsr_mask]) / f_sky_resid_fit[self.__fsr_mask])

        return f_sky_resid_fit,chi2

    # Create and save a plot of the offset residual fit
    def plotFORFit(self,spm,resid,fit,mask,spm_min,spm_max,occ_min,occ_max,
            poly_order):
        """
        Purpose:
            Plot results of the automated frequency offset residual
            fit and save plot to a file. File name will match the
            .LBL and .TAB nomenclature.

        Arguments:
            :spm (*np.ndarray*): SPM sampled by ``calc_freq_offset``
                        when calculating the offset frequencies for
                        the occultation
            :resid (*np.ndarray*): residual sky frequency
            :fit (*np.ndarray*): polynomial fit to the residual sky
                        frequency
            :mask (*np.ndarray*): boolean array used to mask residual
                        sky frequency for the polynomial fitting
            :spm_min (*float*): start of occultation in SPM
            :spm_max (*float*): end of occultation in SPM
            :poly_order (*float*): order of polynomial fit to the
                        residual sky frequency
        """
        #generate plot file names
        filenames,outdirs = construct_filepath(self.rev_info,'FORFIT')
        # set up subplot
        ax = plt.figure().add_subplot(111)
        # residuals used for fit
        plt.plot(spm[mask],resid[mask],'.k')
        # all residuals
        plt.plot(spm,resid,'-',color='0.5',lw=1)
        # indicate limits for ring system
        plt.axvline(occ_min,dashes=[12,4],color='0.2')
        plt.axvline(occ_max,dashes=[12,4],color='0.2')
        # fit to residuals
        plt.plot(spm,fit,'-r')
        # limits to plot
        plt.xlim(spm_min-100,spm_max+100)
        plt.ylim(np.nanmin(resid[mask])-0.1,np.nanmax(resid[mask])+0.1)
        # labels
        plt.xlabel('SPM (sec)')
        plt.ylabel(r'$f_{predict}-f_{observe}$')
        plt.text(0.4,0.95,'PolyOrder: '+str(poly_order),transform = 
                ax.transAxes)
        # output
        for file,dir in zip(filenames,outdirs):
            plt.title(file)
            outfile = dir + file + '.PDF'
            print('\tSaving frequency offset fit plot to: \n\t\t' + '/'.join(outfile.split('/')[0:5]) + '/\n\t\t\t' + '/'.join(outfile.split('/')[5:]))
            plt.savefig(outfile)
        plt.close()
"""
Revisions:
"""
