from .models import QEData, ProcessedData

def process_qe_data(qe_data: QEData, nbnd_exclude: int) -> ProcessedData:
    """
    Processes raw QE data for BoltzTraP2:
    1. Adjusts the number of electrons based on excluded bands.
    2. Separates spin-up and spin-down eigenvalues if nspin == 2.
    3. Slices the eigenvalues to exclude the lowest 'nbnd_exclude' bands.

    This logic strictly follows the original sample script provided.
    """
    if nbnd_exclude < 0:
        raise ValueError("nbnd_exclude must be >= 0")
    if nbnd_exclude >= qe_data.bands.nbnd:
        raise ValueError("nbnd_exclude cannot be >= total bands (nbnd)")

    # 1. Adjust nelec (Matching original script logic)
    if qe_data.bands.nspin == 2:
        nelec_adjusted = qe_data.bands.nelec - nbnd_exclude
    else:
        nelec_adjusted = qe_data.bands.nelec - (2 * nbnd_exclude)

    nbnd_effective = qe_data.bands.nbnd - nbnd_exclude

    # Calculate actual number of unique k-points
    # (Total kpoints in XML is nkpt * nspin)
    nkpt = len(qe_data.bands.kpoints) // qe_data.bands.nspin

    # K-points are identical for both spin channels, so we take the first 'nkpt' entries
    kpoints = qe_data.bands.kpoints[:nkpt]

    eigenvalues_up = []
    eigenvalues_dn = []

    # 2. Separate and slice eigenvalues
    if qe_data.bands.nspin == 1:
        for ik in range(nkpt):
            # Slice from nbnd_exclude to the end of the band list
            eigenvalues_up.append(qe_data.bands.eigenvalues[ik][nbnd_exclude:])
    else:
        # nspin == 2: First 'nkpt' entries are spin-up, next 'nkpt' are spin-down
        for ik in range(nkpt):
            eigenvalues_up.append(qe_data.bands.eigenvalues[ik][nbnd_exclude:])
            # ik + nkpt targets the corresponding k-point in the spin-down block
            eigenvalues_dn.append(qe_data.bands.eigenvalues[ik + nkpt][nbnd_exclude:])

    return ProcessedData(
        prefix=qe_data.prefix,
        crystal=qe_data.crystal,
        fermi_energy=qe_data.bands.fermi_energy,
        nelec_adjusted=nelec_adjusted,
        nspin=qe_data.bands.nspin,
        nbnd_effective=nbnd_effective,
        kpoints=kpoints,
        eigenvalues_up=eigenvalues_up,
        eigenvalues_dn=eigenvalues_dn if qe_data.bands.nspin == 2 else None
    )
