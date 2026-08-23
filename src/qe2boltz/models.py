from pydantic import BaseModel, Field, field_validator
from typing import List
import numpy as np
from typing import Optional

# ==========================================
# 1. Crystal Structure Model
# ==========================================
class CrystalStructure(BaseModel):
    """
    Physics: This class holds the crystal lattice geometry and its symmetries.
    BoltzTraP2 requires reciprocal lattice vectors to calculate energy
    gradients in the k-space (group velocities).
    """
    alat: float = Field(..., description="Lattice parameter in Bohr")
    lattice_vectors: List[List[float]] = Field(..., description="Real space lattice vectors (a1, a2, a3)")
    reciprocal_vectors: List[List[float]] = Field(..., description="Reciprocal space lattice vectors (b1, b2, b3)")
    symmetry_ops: List[List[List[int]]] = Field(..., description="Symmetry rotation matrices in crystal coordinates")

    @field_validator('lattice_vectors', 'reciprocal_vectors')
    @classmethod
    def check_3x3_matrix(cls, v: List[List[float]]) -> List[List[float]]:
        """Ensure lattice vectors are strictly 3x3 matrices."""
        if len(v) != 3 or any(len(row) != 3 for row in v):
            raise ValueError("Lattice vectors must be a 3x3 matrix.")
        return v

# ==========================================
# 2. Electronic Band Structure Model
# ==========================================
class BandStructure(BaseModel):
    """
    Physics: This class stores electronic information in the k-mesh.
    Crucial for magnetic materials: We must track 'nspin' to properly
    separate spin-up and spin-down channels during the processing phase.
    """
    fermi_energy: float = Field(..., description="Fermi energy in Rydberg")
    nelec: float = Field(..., description="Total number of electrons")
    nspin: int = Field(..., description="Number of spin channels (1 for non-magnetic, 2 for spin-polarized)")
    nbnd: int = Field(..., description="Total number of bands per spin channel")

    kpoints: List[List[float]] = Field(..., description="K-points in crystal (fractional) coordinates")
    eigenvalues: List[List[float]] = Field(
        ...,
        description="Eigenvalues in Rydberg. Shape: (nkpt, nbnd) if nspin=1, or (nkpt, nbnd*nspin) if nspin=2"
    )

    @field_validator('nspin')
    @classmethod
    def check_nspin(cls, v: int) -> int:
        """Validate that nspin is physically meaningful (1 or 2)."""
        if v not in [1, 2]:
            raise ValueError(f"nspin must be 1 or 2, got {v}")
        return v

# ==========================================
# 3. Comprehensive QE Data Model
# ==========================================
class QEData(BaseModel):
    """
    This is the final, unified model outputted by the XML parser.
    It contains all raw physical data needed for BoltzTraP2 processing.
    """
    prefix: str = Field(..., description="The prefix used in the Quantum Espresso calculation")
    crystal: CrystalStructure
    bands: BandStructure


# ... (کدهای قبلی CrystalStructure, BandStructure, QEData اینجا هستند) ...

# ==========================================
# 4. Processed Data Model (For BoltzTraP2)
# ==========================================
class ProcessedData(BaseModel):
    """
    This model holds the data after physical processing (band exclusion and spin separation).
    It is the direct input for the writer module.
    """
    prefix: str
    crystal: CrystalStructure
    fermi_energy: float
    nelec_adjusted: float
    nspin: int
    nbnd_effective: int
    kpoints: List[List[float]]
    eigenvalues_up: List[List[float]]
    eigenvalues_dn: Optional[List[List[float]]] = Field(default=None, description="Only populated if nspin == 2")
