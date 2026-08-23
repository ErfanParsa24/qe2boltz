import pytest
from pathlib import Path
from qe2boltz.parsers import parse_qe_input, parse_qe_xml

# ==========================================
# 1. Fixtures for Mock Files
# ==========================================
@pytest.fixture
def mock_qe_input(tmp_path):
    """Creates a temporary QE input file."""
    input_file = tmp_path / "nscf.in"
    input_file.write_text(
        "&control\n"
        "    prefix = 'test_mat',\n"
        "    outdir = './tmp_dir',\n"
        "/\n"
    )
    return str(input_file)

@pytest.fixture
def mock_qe_xml(tmp_path):
    """Creates a minimal, valid mock QE XML file for testing."""
    xml_file = tmp_path / "test_mat.xml"
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <qes:espresso xmlns:qes="http://www.quantum-espresso.org/ns/qes/qes-1.0">
        <output>
            <atomic_structure alat="10.0">
                <cell>
                    <a1>1.0 0.0 0.0</a1>
                    <a2>0.0 1.0 0.0</a2>
                    <a3>0.0 0.0 1.0</a3>
                </cell>
            </atomic_structure>
            <basis_set>
                <reciprocal_lattice>
                    <b1>1.0 0.0 0.0</b1>
                    <b2>0.0 1.0 0.0</b2>
                    <b3>0.0 0.0 1.0</b3>
                </reciprocal_lattice>
            </basis_set>
            <symmetries>
                <symmetry>
                    <rotation>1 0 0 0 1 0 0 0 1</rotation>
                </symmetry>
            </symmetries>
            <band_structure>
                <fermi_energy>13.605693</fermi_energy> <!-- Exactly 1.0 Ry -->
                <nelec>2.0</nelec>
                <nbnd>2</nbnd>
                <lsda>false</lsda>
                <ks_energies>
                    <k_point>0.0 0.0 0.0</k_point>
                    <eigenvalues>-0.5 0.2</eigenvalues>
                </ks_energies>
                <ks_energies>
                    <k_point>0.5 0.0 0.0</k_point>
                    <eigenvalues>-0.4 0.3</eigenvalues>
                </ks_energies>
            </band_structure>
        </output>
    </qes:espresso>
    """
    xml_file.write_text(xml_content)
    return str(xml_file)

# ==========================================
# 2. Parser Tests
# ==========================================
def test_parse_qe_input(mock_qe_input):
    """Test extraction of prefix and outdir from input file."""
    prefix, outdir = parse_qe_input(mock_qe_input)
    assert prefix == "test_mat"
    assert outdir == "./tmp_dir"

def test_parse_qe_xml(mock_qe_xml):
    """Test parsing of mock XML and unit conversions."""
    qe_data = parse_qe_xml(mock_qe_xml)

    # Check prefix extraction from filename
    assert qe_data.prefix == "test_mat"

    # Check Crystal Structure (alat=10, so a1 should be [10, 0, 0])
    assert qe_data.crystal.alat == 10.0
    assert qe_data.crystal.lattice_vectors[0][0] == 10.0

    # Check Reciprocal Vectors (b1=1.0 in 2pi/alat -> (1.0 * 2pi) / 10 = 0.6283...)
    import math
    expected_b1_0 = (1.0 * 2 * math.pi) / 10.0
    assert abs(qe_data.crystal.reciprocal_vectors[0][0] - expected_b1_0) < 1e-5

    # Check Band Structure
    assert qe_data.bands.fermi_energy == 1.0 # 13.605693 eV / 13.605693 = 1.0 Ry
    assert qe_data.bands.nspin == 1
    assert qe_data.bands.nbnd == 2
    assert len(qe_data.bands.kpoints) == 2
    assert qe_data.bands.eigenvalues[0][0] == -0.5 / 13.605693 # Converted to Ry
