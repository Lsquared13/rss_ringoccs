# Release Notes #

## rss_ringoccs V1.1 ##

Release date: 2019 Feb 1

### Changes from V1.0 ###
1. Output file formats for GEO, CAL, DLP, and TAU files modified to be consistent with December 2018 PDS RSS archive submission.

2. Use 1 kHz RSR files by default, since they are now available on the PDS.

3. Modify power normalization and frequency offset components of calibration steps to reduce/eliminate need for GUIs.

4. Major speed-ups of many routines.

5. Include calculation of threshold optical depth.

6. Ability to produce summary plots of elevation vs time of the Cassini spacecraft from each DSN, for each occultation.

7. Ability to produce Earth views of each occultation.

8. Ability to produce summary PDF files for each occultation, in same format as PDF versions.

9. All output files now include full history of commands used to produce them.

10. Readthedocs documentation produced for all rss_ringoccs routines.

11. Describe validation tests in User Guide. 

12. Provide sample scripts for end-to-end runs of representative occultations.

13. Provide additional details of steps in processing pipeline in User Guide.

**Resolved V1.0-1**

10. Redefine our effective resolution to match RSS Science Team Member Essam Marouf's PDS results by scaling our nominal resolution by a factor of 1/0.75. This gives an excellent match to the PDS results, and makes our results consistent with his for any given user-requested resolution.

**Resolved V1.0-2**

11. Eliminated GUI that produced this error.

**Resolved V1.0-3**

12. Eliminated GUI that produced this error.

### Known Issues and Limitations of V1.1 ###

#### V1.1-1 ####
For the extreme nearly edge-on viewing geometry of Rev133E at X-band, rss_ringoccs gives slightly different results from PDS, traceable to a difference of about 10% in the cubic term of the varaiable psi. The origin of this discrepancy is unknown, but it is not important for any other occultation data sets we have reduced so far, and is relatively minor even for Rev133E at X band.

### Lien list for V1.2 ###

1. Runnable scripts to perform push-button diffraction correction, starting either from raw RSS files or from Essam Marouf's (or our) PDS-style geometry, calibration, and diffraction-limited profiles, at any desired resolution (consistent with the sampling theorem and justified by the SNR), for the full set of RSS occultations at S, X, and Ka-band up to the point of USO failure.

2. More extensive documentation to demonstrate the use of the software.

3. Data catalog query - we will work with the PDS to ensure that our recently-submitted RSS ring occultation observation data catalog is compliant with current PDS search capabilities.

4. Improve speed of slowest routines by using tested multiprocessor code.

5. Explore possibility of processing post-USO failure RSR files.

6. Explore feasibility, level of effort, and value of archiving scattered signal data -- perhaps as a PDART proposal.

## rss_ringoccs V1.0 ##

Release date: 2018 September 30

### Known Issues and Limitations of V1.0 ###
#### V1.0-1 ####
rss_ringoccs implements effective radial resolution as defined in Marouf, Tyler, and Rosen 1986 (MTR86, Icarus 68, 120-166) eq. 19, using a Kaiser-Bessel alpha=2.5 window function. In contrast, Marouf et al.'s diffraction-reconstructed profiles on the PDS Ring-Moon Systems Node adopt the shortest resolvable wavelength as the
resolution metric. Its inverse is the
highest spatial frequency preserved in the data. The latter is 1 cycle/km for the 1 km
resolution of Marouf's reconstructed profiles. The value corresponds to ~750 m
processing resolution as defined in MTR86. The bandwidth of the lowpass filter in the final stage of the data processing chain determines such frequency and is selected to achieve the desired resolution.

Workaroud: In order to produce the best match to the RSS diffraction-reconstructed ring profiles on the PDS, specify in rss_ringoccs a desired resolution 0.75 times that given in the PDS files.

#### V1.0-2 ####
Power and frequency calibration GUIs give the following error message under some versions of Python on MacOS systems:

-[NSApplication _setup:]: unrecognized selector sent to instance

*** Terminating app due to uncaught exception 'NSInvalidArgumentException', reason: '-[NSApplication _setup:]: unrecognized selector sent to instance'

Workaround: Use Linux operating system, and post an Issue on the Github page for rss_ringoccs

#### V1.0-3 ####
Power and frequency calibration GUIs may sometimes not close when users click the "OK" button or the red "X" button.

Workaround: Use Linux operating system, and post an Issue on the Github page for rss_ringoccs
