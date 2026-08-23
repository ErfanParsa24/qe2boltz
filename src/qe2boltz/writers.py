from pathlib import Path
from .models import ProcessedData

# Physical constants for BoltzTraP2 (which uses Angstrom and eV)
BOHR_TO_ANGSTROM = 0.529177210903
RY_TO_EV = 13.605693

def write_boltztrap2_generic(processed_data: ProcessedData, output_dir: str = "."):
    """
    Writes the processed data in the BoltzTraP2 generic format (.bandsdat).

    Directory structure:
    - If nspin == 1: output_dir/prefix.bandsdat
    - If nspin == 2:
        output_dir/spin_up/prefix.bandsdat
        output_dir/spin_down/prefix.bandsdat

    BoltzTraP2 expects lattice vectors in Angstrom and energies in eV.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Convert lattice vectors from Bohr (used in QE) to Angstrom (used in BoltzTraP2)
    lat_ang = [[v * BOHR_TO_ANGSTROM for v in vec] for vec in processed_data.crystal.lattice_vectors]

    nkpt = len(processed_data.kpoints)
    nbnd = processed_data.nbnd_effective

    def write_single_file(filepath: Path, eigenvalues):
        """Helper function to write a single .bandsdat file."""
        with open(filepath, 'w') as f:
            f.write(f"{processed_data.prefix}\n")
            f.write(f"{nkpt}\n")

            # Write lattice vectors (3 lines)
            for vec in lat_ang:
                f.write(f"{vec[0]:.10f} {vec[1]:.10f} {vec[2]:.10f}\n")

            # Write k-points and eigenvalues
            for ik in range(nkpt):
                kpt = processed_data.kpoints[ik]
                f.write(f"{kpt[0]:.10f} {kpt[1]:.10f} {kpt[2]:.10f} {nbnd}\n")

                # Convert energies from Ry to eV and write them space-separated
                eig_ev = [e * RY_TO_EV for e in eigenvalues[ik]]
                eig_str = " ".join(f"{e:.10f}" for e in eig_ev)
                f.write(f"{eig_str}\n")

    # Generate output files based on spin polarization
    if processed_data.nspin == 1:
        # Non-magnetic: single file in output_dir
        filepath = out_path / f"{processed_data.prefix}.bandsdat"
        write_single_file(filepath, processed_data.eigenvalues_up)
    else:
        # Spin-polarized: separate directories for up and down
        up_dir = out_path / "spin_up"
        dn_dir = out_path / "spin_down"

        up_dir.mkdir(parents=True, exist_ok=True)
        dn_dir.mkdir(parents=True, exist_ok=True)

        filepath_up = up_dir / f"{processed_data.prefix}.bandsdat"
        filepath_dn = dn_dir / f"{processed_data.prefix}.bandsdat"

        write_single_file(filepath_up, processed_data.eigenvalues_up)
        write_single_file(filepath_dn, processed_data.eigenvalues_dn)
