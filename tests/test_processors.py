import pytest
from qe2boltz.models import QEData, CrystalStructure, BandStructure
from qe2boltz.processors import process_qe_data

# ==========================================
# 1. Fixtures for Processed Data Testing
# ==========================================
@pytest.fixture
def mock_qe_data_nspin1():
    """Mock QEData for a non-magnetic system (nspin=1)."""
    return QEData(
        prefix="test_nm",
        crystal=CrystalStructure(
            alat=10.0,
            lattice_vectors=[[10,0,0], [0,10,0], [0,0,10]],
            reciprocal_vectors=[[0.1,0,0], [0,0.1,0], [0,0,0.1]],
            symmetry_ops=[[[1,0,0],[0,1,0],[0,0,1]]]
        ),
        bands=BandStructure(
            fermi_energy=0.5,
            nelec=4.0,
            nspin=1,
            nbnd=4,
            kpoints=[[0.0, 0.0, 0.0], [0.5, 0.0, 0.0]],
            eigenvalues=[
                [-1.0, -0.5, 0.1, 0.6], # k-point 1
                [-0.9, -0.4, 0.2, 0.7]  # k-point 2
            ]
        )
    )

@pytest.fixture
def mock_qe_data_nspin2():
    """Mock QEData for a magnetic system (nspin=2)."""
    return QEData(
        prefix="test_mag",
        crystal=CrystalStructure(
            alat=10.0,
            lattice_vectors=[[10,0,0], [0,10,0], [0,0,10]],
            reciprocal_vectors=[[0.1,0,0], [0,0.1,0], [0,0,0.1]],
            symmetry_ops=[[[1,0,0],[0,1,0],[0,0,1]]]
        ),
        bands=BandStructure(
            fermi_energy=0.5,
            nelec=4.0, # Total nelec
            nspin=2,
            nbnd=4,
            # 2 k-points * 2 spins = 4 entries in kpoints and eigenvalues
            kpoints=[
                [0.0, 0.0, 0.0], # k1, spin up
                [0.5, 0.0, 0.0], # k2, spin up
                [0.0, 0.0, 0.0], # k1, spin down
                [0.5, 0.0, 0.0]  # k2, spin down
            ],
            eigenvalues=[
                [-1.0, -0.5, 0.1, 0.6], # k1, up
                [-0.9, -0.4, 0.2, 0.7], # k2, up
                [-1.1, -0.6, 0.0, 0.5], # k1, down
                [-1.0, -0.5, 0.1, 0.6]  # k2, down
            ]
        )
    )

# ==========================================
# 2. Processor Tests
# ==========================================
def test_process_nspin1(mock_qe_data_nspin1):
    """Test band exclusion and nelec adjustment for nspin=1."""
    nbnd_exclude = 1
    processed = process_qe_data(mock_qe_data_nspin1, nbnd_exclude)

    assert processed.nspin == 1
    assert processed.nbnd_effective == 3 # 4 - 1
    assert processed.nelec_adjusted == 2.0 # 4.0 - (2 * 1)
    assert len(processed.kpoints) == 2

    # Check if the first band (-1.0 and -0.9) is excluded
    assert processed.eigenvalues_up[0] == [-0.5, 0.1, 0.6]
    assert processed.eigenvalues_up[1] == [-0.4, 0.2, 0.7]
    assert processed.eigenvalues_dn is None

def test_process_nspin2(mock_qe_data_nspin2):
    """Test band exclusion, nelec adjustment, and spin separation for nspin=2."""
    nbnd_exclude = 1
    processed = process_qe_data(mock_qe_data_nspin2, nbnd_exclude)

    assert processed.nspin == 2
    assert processed.nbnd_effective == 3 # 4 - 1
    assert processed.nelec_adjusted == 3.0 # 4.0 - 1 (Matching original script logic)
    assert len(processed.kpoints) == 2 # Should be unique k-points only

    # Check spin-up slicing
    assert processed.eigenvalues_up[0] == [-0.5, 0.1, 0.6]
    assert processed.eigenvalues_up[1] == [-0.4, 0.2, 0.7]

    # Check spin-down slicing (indices 2 and 3 in original list)
    assert processed.eigenvalues_dn[0] == [-0.6, 0.0, 0.5]
    assert processed.eigenvalues_dn[1] == [-0.5, 0.1, 0.6]

def test_invalid_nbnd_exclude(mock_qe_data_nspin1):
    """Test that excluding more bands than available raises an error."""
    with pytest.raises(ValueError, match="nbnd_exclude cannot be >= total bands"):
        process_qe_data(mock_qe_data_nspin1, nbnd_exclude=5)
