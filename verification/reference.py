"""Independent numerical reference functions for pre-implementation verification.

These routines are intentionally small and dependency-light.  They are NOT the
future production implementation.  Their purpose is to provide an independent
numerical reference against which the eventual Astropy/GalSim/STPSF-based code
can be tested.

Conventions
-----------
* SI units internally.
* Spectral luminosity density L_nu: W Hz^-1.
* Spectral flux density F_nu: W m^-2 Hz^-1.
* Specific intensity I_nu: W m^-2 Hz^-1 sr^-1.
* Wavelength densities are per metre.

References
----------
Hogg, D. W. 1999, arXiv:astro-ph/9905116, Eqs. 18, 20-24.
Hogg et al. 2002, arXiv:astro-ph/0210394.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import quad

C_M_S = 299_792_458.0
H_J_S = 6.626_070_15e-34
MPC_M = 3.085_677_581_491_367e22


@dataclass(frozen=True)
class FlatLCDMReference:
    """Minimal flat-LambdaCDM distance calculator for independent checks.

    Parameters
    ----------
    H0_km_s_Mpc
        Hubble constant in km s^-1 Mpc^-1.
    Om0
        Present matter density parameter.

    Notes
    -----
    This is intentionally not a general cosmology engine.  It exists only as an
    independent check for the future production implementation, which should use
    ``astropy.cosmology``.
    """

    H0_km_s_Mpc: float = 70.0
    Om0: float = 0.3

    @property
    def Ol0(self) -> float:
        return 1.0 - self.Om0

    @property
    def H0_s(self) -> float:
        return self.H0_km_s_Mpc * 1000.0 / MPC_M

    @property
    def hubble_distance_m(self) -> float:
        return C_M_S / self.H0_s

    def E(self, z: float) -> float:
        if z < 0:
            raise ValueError("Redshift must be non-negative.")
        return float(np.sqrt(self.Om0 * (1.0 + z) ** 3 + self.Ol0))

    def comoving_distance_m(self, z: float) -> float:
        if z < 0:
            raise ValueError("Redshift must be non-negative.")
        integral, _ = quad(lambda zp: 1.0 / self.E(zp), 0.0, z, epsabs=0.0, epsrel=2e-13)
        return self.hubble_distance_m * integral

    def angular_diameter_distance_m(self, z: float) -> float:
        return self.comoving_distance_m(z) / (1.0 + z)

    def luminosity_distance_m(self, z: float) -> float:
        return self.comoving_distance_m(z) * (1.0 + z)


def observed_fnu_from_lnu(
    nu_obs_hz: np.ndarray,
    z: float,
    luminosity_distance_m: float,
    lnu_emitted: Callable[[np.ndarray], np.ndarray],
) -> np.ndarray:
    """Observed F_nu from rest-frame L_nu.

    Implements Hogg (1999) Eq. 22 in the compact form

        F_nu(nu_o) = (1+z) L_nu((1+z) nu_o) / (4 pi D_L^2).
    """

    nu_obs_hz = np.asarray(nu_obs_hz, dtype=float)
    if np.any(nu_obs_hz <= 0):
        raise ValueError("Frequencies must be positive.")
    return (1.0 + z) * lnu_emitted((1.0 + z) * nu_obs_hz) / (
        4.0 * np.pi * luminosity_distance_m**2
    )


def observed_flambda_from_llambda(
    lambda_obs_m: np.ndarray,
    z: float,
    luminosity_distance_m: float,
    llambda_emitted: Callable[[np.ndarray], np.ndarray],
) -> np.ndarray:
    """Observed F_lambda from rest-frame L_lambda (per metre).

        F_lambda(lambda_o) = L_lambda(lambda_o/(1+z))
                             / [4 pi D_L^2 (1+z)].
    """

    lambda_obs_m = np.asarray(lambda_obs_m, dtype=float)
    if np.any(lambda_obs_m <= 0):
        raise ValueError("Wavelengths must be positive.")
    return llambda_emitted(lambda_obs_m / (1.0 + z)) / (
        4.0 * np.pi * luminosity_distance_m**2 * (1.0 + z)
    )


def inu_observed_from_emitted(inu_emitted: np.ndarray, z: float) -> np.ndarray:
    """Transform emitted I_nu at corresponding emitted frequency to observed I_nu."""

    return np.asarray(inu_emitted, dtype=float) / (1.0 + z) ** 3


def ilambda_observed_from_emitted(ilambda_emitted: np.ndarray, z: float) -> np.ndarray:
    """Transform emitted I_lambda at corresponding emitted wavelength to observed I_lambda."""

    return np.asarray(ilambda_emitted, dtype=float) / (1.0 + z) ** 5


def fnu_to_flambda(nu_hz: np.ndarray, fnu: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Convert F_nu(nu) to F_lambda(lambda) with F_lambda per metre.

    Returns wavelengths in increasing order.
    """

    nu_hz = np.asarray(nu_hz, dtype=float)
    fnu = np.asarray(fnu, dtype=float)
    lam = C_M_S / nu_hz
    flambda = fnu * C_M_S / lam**2
    order = np.argsort(lam)
    return lam[order], flambda[order]


def flambda_to_fnu(lambda_m: np.ndarray, flambda: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Convert F_lambda(lambda) per metre to F_nu(nu), returning increasing frequency."""

    lambda_m = np.asarray(lambda_m, dtype=float)
    flambda = np.asarray(flambda, dtype=float)
    nu = C_M_S / lambda_m
    fnu = flambda * lambda_m**2 / C_M_S
    order = np.argsort(nu)
    return nu[order], fnu[order]


def photon_rate_from_flambda(
    lambda_m: np.ndarray,
    flambda_w_m2_m: np.ndarray,
    effective_area_m2: np.ndarray | float,
    throughput: np.ndarray | float = 1.0,
) -> float:
    """Photon rate for a photon-counting detector from F_lambda.

    Integrand = F_lambda * A_eff * throughput * lambda / (h c).
    ``A_eff`` and ``throughput`` should not double-count the same efficiency.
    """

    lam = np.asarray(lambda_m, dtype=float)
    f = np.asarray(flambda_w_m2_m, dtype=float)
    a = np.asarray(effective_area_m2, dtype=float)
    t = np.asarray(throughput, dtype=float)
    integrand = f * a * t * lam / (H_J_S * C_M_S)
    return float(np.trapezoid(integrand, lam))


def photon_rate_from_fnu(
    nu_hz: np.ndarray,
    fnu_w_m2_hz: np.ndarray,
    effective_area_m2: np.ndarray | float,
    throughput: np.ndarray | float = 1.0,
) -> float:
    """Photon rate from F_nu using photons of energy h*nu."""

    nu = np.asarray(nu_hz, dtype=float)
    f = np.asarray(fnu_w_m2_hz, dtype=float)
    a = np.asarray(effective_area_m2, dtype=float)
    t = np.asarray(throughput, dtype=float)
    integrand = f * a * t / (H_J_S * nu)
    return float(np.trapezoid(integrand, nu))
