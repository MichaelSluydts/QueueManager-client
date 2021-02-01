# -*- coding: utf-8 -*-

#!/usr/bin/env python

import matplotlib;
matplotlib.use('agg')
import seaborn;
import numpy as np
import pylab as pl
from scipy.optimize import curve_fit

def BM3(x, a, b, c, d):
    return a+ b*x + c*x**2 + d*x**3

class EquationOfState:
    _e = 1.60217733e-19
    b3 = 0.52917720859**3
    Ry = 13.6056923
    """Fit equation of state for bulk systems.

    The following equation is used::

                          2      3        -2/3
      E(V) = c + c t + c t  + c t ,  t = V
              0   1     2      3

    Use::

       eos = EquationOfState(volumes, energies)
       v0, e0, B, BP = eos.fit()
       eos.plot()

    """
    def __init__(self, volumes, energies):

        self.v = np.array(volumes)
        self.e = np.array(energies)
        self.v0 = None

    def fit2(self):
        """Calculate volume, energy, and bulk modulus.

        Returns the optimal volume, the minumum energy, and the bulk
        modulus.  Notice that the ASE units for the bulk modulus is
        eV/Angstrom^3 - to get the value in GPa, do this::

          v0, e0, B = eos.fit()
          print B * _e * 1.0e21, 'GPa'

        """

        fitdata = np.polyfit(self.v ** -(2.0 / 3.), self.e, 3, full=True)
        ssr = fitdata[1]
        sst = np.sum((self.e - np.average(self.e)) ** 2.)
        self.residuals = float(ssr / sst)
        fit0 = np.poly1d(fitdata[0])
        fit1 = np.polyder(fit0, 1)  # 1st derivative of a polynomial fit0
        fit2 = np.polyder(fit1, 1)
        fit3 = np.polyder(fit2, 1)

        self.v0 = None
        for t in np.roots(fit1):
            if t > 0 and fit2(t) > 0:
                self.v0 = t ** (-3. / 2.)
                break

        if self.v0 is None:
            nv = len(self.v)
            middle = int(np.round(nv / 2))
            minimumv = np.min(self.v)
            self.v0 = minimumv - (self.v - minimumv)
            print('Warning no minimum found, extrapolating.')

        self.e0 = fit0(t)
        der2 = fit2(t)
        der3 = fit3(t)
        der2V = 4. / 9. * t ** 5 * der2
        der3V = -20. / 9. * t ** (13. / 2.) * der2 - 8. / 27. * t ** (15. / 2.) * der3
        self.B = der2V / t ** (3. / 2.)
        self.BP = -1 - t ** (-3. / 2.) * der3V / der2V
        self.fit0 = fit0

        return self.v0, self.e0, self.B, self.BP, self.residuals

    def fit(self):
        """Calculate volume, energy, and bulk modulus.

        Returns the optimal volume, the minumum energy, and the bulk
        modulus.  Notice that the ASE units for the bulk modulus is
        eV/Angstrom^3 - to get the value in GPa, do this::

          v0, e0, B = eos.fit()
          print B * _e * 1.0e21, 'GPa'

        """
        #print(self.v,self.e)
        fitdata = np.polyfit(self.v**-(2.0 / 3.), self.e, 3, full=True)
        ssr = fitdata[1]
        sst = np.sum((self.e - np.average(self.e))**2.)
        self.residuals = float(ssr/sst)
        #print(fitdata[0])
        fit0 = np.poly1d(fitdata[0])
        fit1 = np.polyder(fit0, 1) # 1st derivative of a polynomial fit0
        fit2 = np.polyder(fit1, 1)
        fit3 = np.polyder(fit2, 1)

        self.v0 = None
        for t in np.roots(fit1):
            if t > 0 and fit2(t) > 0:
                self.v0 = t**(-3./2.)
                break

        if self.v0 is None:
            nv = len(self.v)
            middle = int(np.round(nv/2))
            minimumv = np.min(self.v)
            self.v0 = minimumv - (self.v - minimumv)
            print('Warning no minimum found, extrapolating.')

        self.e0 = fit0(t)
        der2 = fit2(t)
        der3 = fit3(t)
        der2V = 4./9. * t**5 * der2
        der3V = -20./9. * t**(13./2.) * der2 - 8./27. * t**(15./2.) * der3
        self.B = der2V / t**(3./2.)
        self.BP = -1 - t**(-3./2.) * der3V / der2V
        self.fit0 = fit0

        return self.v0, self.e0, self.B, self.BP, self.residuals

    def plot(self, filename=None, show=None):
        """Plot fitted energy curve.

        Uses Matplotlib to plot the energy curve.  Use *show=True* to
        show the figure and *filename='abc.png'* or
        *filename='abc.eps'* to save the figure to a file."""

        if self.v0 is None:
            self.fit()

        if filename is None and show is None:
            show = False

#        x = 3.95
#        f = pl.figure(figsize=(x * 2.5**0.5, x))
        f = pl.figure()
        f.subplots_adjust(left=0.12, right=0.9, top=0.9, bottom=0.12)
        pl.plot(self.v, self.e, 'o')
        x = np.linspace(min(self.v), max(self.v), 100)
        pl.plot(x, self.fit0(x**-(2.0 / 3)), '-r')
        pl.xlabel(u'volume [$\AA^3$]')
        pl.ylabel(u'energy [eV]')
        pl.title(u'E: %.3f eV, V: %.3f $\AA^3$, B: %.3f GPa, B$_P$: %.3f' %
                  (self.e0, self.v0, self.B *self._e * 1.0e21, self.BP), y = 1.02)

        if show:
            pl.show()
        if filename is not None:
            f.savefig(filename)

        return f