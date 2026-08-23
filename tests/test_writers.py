import pytest
from pathlib import Path
from qe2boltz.models import ProcessedData, CrystalStructure
from qe2boltz.writers import write_boltztrap2_generic, BOHR_TO_ANGSTROM, RY_TO_EV

# ==========================================
# 1. Fixtures for Writer Testing
# ==========================================
@pytest.fixture
def mock_processed_data_nspin1():
    return ProcessedData(
        prefix="test_nm",
        crystal=CrystalStructure(
            alat=10.0,
            lattice_vectors=[[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]],
            reciprocal_vectors=[[0.1, 0.0, 0.0], [0.0, 0.1, 0.0], [0.0, 0.0, 0.1]],
            symmetry_ops=[[[1, 0, 0], [0, 1, 0], [0, 0, 1]]]
        ),
        fermi_energy=0.5,
        nelec_adjusted=2.0,
        nspin=1,
        nbnd_effective=2,
        kpoints=[[0.0, 0.0, 0.0], [0.5, 0.0, 0.0]],
        eigenvalues_up=[[-0.5, 0.1], [-0.4, 0.2]],
        eigenvalues_dn=None
    )

@pytest.fixture
def mock_processed_data_nspin2():
    return ProcessedData(
        prefix="test_mag",
        crystal=CrystalStructure(
            alat=10.0,
            lattice_vectors=[[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]],
            reciprocal_vectors=[[0.1, 0.0, 0.0], [0.0, 0.1, 0.0], [0.0, 0.0, 0.1]],
            symmetry_ops=[[[1, 0, 0], [0, 1, 0], [0, 0, 1]]]
        ),
        fermi_energy=0.5,
        nelec_adjusted=3.0,
        nspin=2,
        nbnd_effective=2,
        kpoints=[[0.0, 0.0, 0.0], [0.5, 0.0, 0.0]],
        eigenvalues_up=[[-0.5, 0.1], [-0.4, 0.2]],
        eigenvalues_dn=[[-0.6, 0.0], [-0.5, 0.1]]
    )

# ==========================================
# 2. Writer Tests
# ==========================================
def test_write_nspin1(tmp_path, mock_processed_data_nspin1):
    """Test file creation in single directory for non-magnetic system."""
    write_boltztrap2_generic(mock_processed_data_nspin1, str(tmp_path))

    # For nspin=1, file should be directly in output_dir
    outfile = tmp_path / "test_nm.bandsdat"
    assert outfile.exists(), "File should exist in output_dir for nspin=1"

    lines = outfile.read_text().splitlines()
    assert lines[0] == "test_nm"
    assert lines[1] == "2" # nkpt

    # Check lattice vectors (10.0 Bohr * 0.529177 = 5.29177 Angstrom)
    expected_lat = 10.0 * BOHR_TO_ANGSTROM
    assert float(lines[2].split()[0]) == pytest.approx(expected_lat, abs=1e-5)

    # Check k-point 1 format
    assert lines[5] == "0.0000000000 0.0000000000 0.0000000000 2"

    # Check energies (Ry to eV)
    expected_e1 = -0.5 * RY_TO_EV
    expected_e2 = 0.1 * RY_TO_EV
    eigs = lines[6].split()
    assert float(eigs[0]) == pytest.approx(expected_e1, abs=1e-5)
    assert float(eigs[1]) == pytest.approx(expected_e2, abs=1e-5)

def test_write_nspin2(tmp_path, mock_processed_data_nspin2):
    """Test generation of separate directories for magnetic system."""
    write_boltztrap2_generic(mock_processed_data_nspin2, str(tmp_path))

    # For nspin=2, files should be in spin_up/ and spin_down/ subdirectories
    outfile_up = tmp_path / "spin_up" / "test_mag.bandsdat"
    outfile_dn = tmp_path / "spin_down" / "test_mag.bandsdat"

    assert outfile_up.exists(), "Spin-up file should exist in spin_up/ directory"
    assert outfile_dn.exists(), "Spin-down file should exist in spin_down/ directory"

    # Check spin-up file content
    lines_up = outfile_up.read_text().splitlines()
    expected_e1_up = -0.5 * RY_TO_EV
    eigs_up = lines_up[6].split()
    assert float(eigs_up[0]) == pytest.approx(expected_e1_up, abs=1e-5)

    # Check spin-down file content
    lines_dn = outfile_dn.read_text().splitlines()
    expected_e1_dn = -0.6 * RY_TO_EV
    eigs_dn = lines_dn[6].split()
    assert float(eigs_dn[0]) == pytest.approx(expected_e1_dn, abs=1e-5)

    # Verify spin channels have different energies
    assert float(eigs_up[0]) != float(eigs_dn[0]), "Spin channels must have different energies"
