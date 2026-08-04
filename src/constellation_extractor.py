"""Scratch script prototyping constellation lookup from sky coordinates
for the planned Constellations dataset (not yet wired into the pipeline).
"""

import astropy.units as u
from astropy.coordinates import SkyCoord, get_constellation

coord = SkyCoord(ra=172.56 * u.degree, dec=7.59 * u.degree)
constellation = get_constellation(coord)  # 'Leo'
