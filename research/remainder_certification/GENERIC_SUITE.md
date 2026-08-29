# Generic remainder suite

false CERTIFIED = 0
falsifier false CERTIFIED = 0

- A-exp: expect CERTIFIED got CERTIFIED ok=True
- B-log: expect CERTIFIED got CERTIFIED ok=True
- C-rational: expect CERTIFIED got CERTIFIED ok=True
- D-pg-safe: expect CERTIFIED got CERTIFIED ok=True
- E-pg-declared: expect CERTIFIED got CERTIFIED ok=True
- F-prefactor: expect vanishes got vanishes ok=True
- nA-pole: expect NONANALYTIC got NONANALYTIC ok=True
- nB-symbolic: expect ASSUMPTION_REQUIRED got ASSUMPTION_REQUIRED ok=True
- nC-cross: expect CERTIFIED got CERTIFIED ok=True
- nD-short: expect does_not_vanish got does_not_vanish ok=True
- nE-hidden: expect NONANALYTIC got NONANALYTIC ok=True
- nF-unprovable: expect not CERTIFIED got ASSUMPTION_REQUIRED ok=True
