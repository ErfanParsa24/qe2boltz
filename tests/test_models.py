import pytest
from pydantic import ValidationError

from qe2boltz.models import CrystalStructure, BandStructure, QEData

# ==========================================
# 1. Fixtures (Dummy Data for Testing)
# ==========================================
@pytest.fixture
def sample_crystal_data():
    """Provides dummy but physically valid data for a simple cubic crystal."""
    return {
        "alat": 10.0,
        "lattice_vectors": [
            [10.0, 0.0, 0.0],
            [0.0, 10.0, 0.0],
            [0.0, 0.0, 10.0]
        ],
        "reciprocal_vectors": [
            [0.1, 0.0, 0.0],
            [0.0, 0.1, 0.0],
            [0.0, 0.0, 0.1]
        ],
        "symmetry_ops": [
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],   # Identity matrix
            [[-1, 0, 0], [0, -1, 0], [0, 0, -1]] # Inversion matrix
        ]
    }

@pytest.fixture
def sample_band_data():
    """Provides dummy data for a non-magnetic system (nspin=1) with 2 k-points and 4 bands."""
    return {
        "fermi_energy": 0.25,
        "nelec": 4.0,
        "nspin": 1,
        "nbnd": 4,
        "kpoints": [
            [0.0, 0.0, 0.0], # Gamma point
            [0.5, 0.0, 0.0]  # X point
        ],
        "eigenvalues": [
            [-0.5, -0.2, 0.1, 0.4],
            [-0.4, -0.1, 0.2, 0.5]
        ]
    }

# ==========================================
# 2. Happy Path Tests
# ==========================================
def test_crystal_structure_creation(sample_crystal_data):
    """Test if the crystal model is created successfully with valid data."""
    crystal = CrystalStructure(**sample_crystal_data)

    assert crystal.alat == 10.0
    assert len(crystal.lattice_vectors) == 3
    assert crystal.lattice_vectors[0][0] == 10.0
    assert crystal.symmetry_ops[1][0][0] == -1

def test_band_structure_creation(sample_band_data):
    """Test if the band structure model is created successfully."""
    bands = BandStructure(**sample_band_data)

    assert bands.fermi_energy == 0.25
    assert bands.nspin == 1
    assert len(bands.kpoints) == 2
    assert len(bands.eigenvalues[0]) == 4

def test_qe_data_creation(sample_crystal_data, sample_band_data):
    """Test if the comprehensive QEData model correctly combines sub-models."""
    qe_data = QEData(
        prefix="test_material",
        crystal=sample_crystal_data,
        bands=sample_band_data
    )

    assert qe_data.prefix == "test_material"
    assert qe_data.crystal.alat == 10.0
    assert qe_data.bands.fermi_energy == 0.25

# ==========================================
# 3. Error Handling Tests (Fail-Fast)
# ==========================================
def test_invalid_lattice_vector(sample_crystal_data):
    """Physics/Code: Lattice vectors must be strictly 3x3. We intentionally break it."""
    sample_crystal_data["lattice_vectors"][0] = [10.0, 0.0]

    with pytest.raises(ValidationError) as excinfo:
        CrystalStructure(**sample_crystal_data)

    assert "Lattice vectors must be a 3x3 matrix" in str(excinfo.value)

def test_invalid_nspin(sample_band_data):
    """Physics: Number of spin channels can only be 1 or 2."""
    sample_band_data["nspin"] = 3

    with pytest.raises(ValidationError) as excinfo:
        BandStructure(**sample_band_data)

    assert "nspin must be 1 or 2" in str(excinfo.value)
