# Verified Representation Invention v1

New research line. Do not mutate frozen historical artifacts.

Parent freeze: Grounded-Proposer-v1 `3fea222`.

## Question

Can a grounded proposer move from locally correct confluence relations
to a complete, explicit, verifiable change of representation?

\[
\{A_i\} \;\longrightarrow\;
H_{\mathrm{repr}}=(R,\{A_i\},\{\mathcal O_i\},F)
\;\longrightarrow\;
A_i=\mathcal O_i[F]
\;\longrightarrow\;
\mathrm{ZERO}/\mathrm{NONZERO}/\mathrm{UNKNOWN}
\]

Local confluence (P1, 11/11 ZERO on Guo DEV) is the baseline, not the claim.

## Pipeline

`P-D-G-C-V-I` — see `research/LAYERS.md`. Failures are localized to a layer.

## This directory

Contracts are frozen in the first commit. Implementations live in owned
subpackages (see `OWNERS.md`).

Do not put Guo gold names (`Phi_Gamma`, L4–L7, PRB masters, generator
names) in proposer-visible files.
