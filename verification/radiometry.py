"""Numerical checks of cosmological radiometry and spectral-density conventions."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .reference import (
    C_M_S,
    FlatLCDMReference,
    fnu_to_flambda,
    observed_flambda_from_llambda,
    observed_fnu_from_lnu,
    photon_rate_from_flambda,
    photon_rate_from_fnu,
)


@dataclass
class RadiometryResult:
    z: float
    grid_points: int
    distance_duality_relative_error: float
    fnu_bolometric_relative_error: float
    flambda_bolometric_relative_error: float
    fnu_flambda_bolometric_agreement: float
    photon_rate_relative_disagreement: float
    tolman_relative_error: float

    def to_dict(self) -> dict:
        return asdict(self)


def _emitted_lnu(nu_hz: np.ndarray) -> np.ndarray:
    nu = np.asarray(nu_hz, dtype=float)
    nu0 = 3.0e14
    x = nu / nu0
    shape = (x**0.7 + 0.35 * x**-0.8) * np.exp(-(x / 5.0) ** 2) * np.exp(-(0.12 / x) ** 4)
    return 2.4e22 * shape


def _emitted_llambda(lambda_m: np.ndarray) -> np.ndarray:
    lam = np.asarray(lambda_m, dtype=float)
    nu = C_M_S / lam
    return _emitted_lnu(nu) * C_M_S / lam**2


def run_radiometry_check(z: float = 2.0, grid_points: int = 20001) -> RadiometryResult:
    cosmo = FlatLCDMReference(H0_km_s_Mpc=70.0, Om0=0.3)
    da = cosmo.angular_diameter_distance_m(z)
    dl = cosmo.luminosity_distance_m(z)
    duality = abs(dl - (1.0 + z) ** 2 * da) / dl

    nu_e = np.geomspace(2.0e13, 3.0e15, grid_points)
    lnu = _emitted_lnu(nu_e)
    lbol = np.trapezoid(lnu, nu_e)

    nu_o = nu_e / (1.0 + z)
    fnu_o = observed_fnu_from_lnu(nu_o, z, dl, _emitted_lnu)
    fbol_nu = np.trapezoid(fnu_o, nu_o)
    expected_bol = lbol / (4.0 * np.pi * dl**2)
    fnu_err = abs(fbol_nu - expected_bol) / expected_bol

    lambda_o = np.sort(C_M_S / nu_o)
    flambda_o = observed_flambda_from_llambda(lambda_o, z, dl, _emitted_llambda)
    fbol_lambda = np.trapezoid(flambda_o, lambda_o)
    flambda_err = abs(fbol_lambda - expected_bol) / expected_bol
    repr_agreement = abs(fbol_lambda - fbol_nu) / expected_bol

    lam_from_nu, flambda_from_fnu = fnu_to_flambda(nu_o, fnu_o)
    center = 1.7e-6
    sigma = 0.38e-6
    throughput_lambda = 0.83 * np.exp(-0.5 * ((lam_from_nu - center) / sigma) ** 2)
    area = 21.5
    rate_lambda = photon_rate_from_flambda(lam_from_nu, flambda_from_fnu, area, throughput_lambda)

    throughput_nu = 0.83 * np.exp(-0.5 * ((C_M_S / nu_o - center) / sigma) ** 2)
    rate_nu = photon_rate_from_fnu(nu_o, fnu_o, area, throughput_nu)
    photon_disagreement = abs(rate_lambda - rate_nu) / (0.5 * (rate_lambda + rate_nu))

    lambda_e = np.geomspace(0.12e-6, 8.0e-6, grid_points)
    ilam_e = 3.1e5 * (lambda_e / 1.0e-6) ** -0.4 * np.exp(-lambda_e / 5.0e-6) * np.exp(-(0.08e-6 / lambda_e) ** 5)
    i_bol_e = np.trapezoid(ilam_e, lambda_e)
    lambda_obs = lambda_e * (1.0 + z)
    ilam_obs = ilam_e / (1.0 + z) ** 5
    i_bol_o = np.trapezoid(ilam_obs, lambda_obs)
    expected_i = i_bol_e / (1.0 + z) ** 4
    tolman_err = abs(i_bol_o - expected_i) / expected_i

    return RadiometryResult(z, grid_points, duality, fnu_err, flambda_err, repr_agreement, photon_disagreement, tolman_err)


def convergence_table(z: float = 2.0) -> list[dict]:
    return [run_radiometry_check(z=z, grid_points=n).to_dict() for n in (201, 501, 1001, 3001, 10001, 30001)]
