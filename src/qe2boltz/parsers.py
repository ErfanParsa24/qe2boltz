import xml.etree.ElementTree as ET
import re
from pathlib import Path
from typing import Tuple

from .models import QEData, CrystalStructure, BandStructure

# Physical constants
RYDBERG_EV = 13.605693
PI = 3.141592653589793

def parse_qe_input(input_file: str) -> Tuple[str, str]:
    """
    Parses the Quantum Espresso input file to extract 'prefix' and 'outdir'.
    Falls back to defaults ('pwscf' and './') if not found.
    """
    prefix = "pwscf"
    outdir = "./"

    with open(input_file, 'r') as f:
        content = f.read()

    # Simple regex to find prefix = '...' or prefix = "..."
    prefix_match = re.search(r"prefix\s*=\s*['\"]([^'\"]+)['\"]", content)
    if prefix_match:
        prefix = prefix_match.group(1)

    outdir_match = re.search(r"outdir\s*=\s*['\"]([^'\"]+)['\"]", content)
    if outdir_match:
        outdir = outdir_match.group(1)

    return prefix, outdir

def parse_qe_xml(xml_file: str) -> QEData:
    """
    Parses the Quantum Espresso XML output file and returns a validated QEData model.
    Handles unit conversions (eV -> Ry, alat -> Bohr) automatically.
    """
    xml_path = Path(xml_file)
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_file}")

    # Read and strip namespace to simplify ElementTree parsing
    with open(xml_path, 'r', encoding='utf-8') as f:
        xml_content = f.read().replace('xmlns="http://www.quantum-espresso.org/ns/qes/qes-1.0"', '')

    root = ET.fromstring(xml_content)

    # 1. Extract Crystal Structure
    atomic_structure = root.find('output/atomic_structure')
    if atomic_structure is None:
        raise ValueError("Could not find 'output/atomic_structure' in XML")

    alat = float(atomic_structure.attrib['alat'])

    lattice_vectors = []
    for i in range(1, 4):
        vec_elem = atomic_structure.find(f'cell/a{i}')
        if vec_elem is None:
            raise ValueError(f"Could not find 'cell/a{i}' in XML")
        vec_str = vec_elem.text
        vec = [float(x) * alat for x in vec_str.split()]
        lattice_vectors.append(vec)

    reciprocal_vectors = []
    basis_set = root.find('output/basis_set')
    if basis_set is None:
        raise ValueError("Could not find 'output/basis_set' in XML")

    for i in range(1, 4):
        vec_elem = basis_set.find(f'reciprocal_lattice/b{i}')
        if vec_elem is None:
            raise ValueError(f"Could not find 'reciprocal_lattice/b{i}' in XML")
        vec_str = vec_elem.text
        vec = [(float(x) * 2 * PI) / alat for x in vec_str.split()]
        reciprocal_vectors.append(vec)

    symmetry_ops = []
    symmetries = root.find('output/symmetries')
    if symmetries is not None:
        for sym in symmetries.findall('symmetry'):
            rot_elem = sym.find('rotation')
            if rot_elem is not None:
                vals = [int(float(x)) for x in rot_elem.text.split()]
                matrix = [vals[0:3], vals[3:6], vals[6:9]]
                symmetry_ops.append(matrix)

    crystal = CrystalStructure(
        alat=alat,
        lattice_vectors=lattice_vectors,
        reciprocal_vectors=reciprocal_vectors,
        symmetry_ops=symmetry_ops
    )

    # 2. Extract Band Structure
    band_structure = root.find('output/band_structure')
    if band_structure is None:
        raise ValueError("Could not find 'output/band_structure' in XML")

    fermi_elem = band_structure.find('fermi_energy')
    if fermi_elem is None:
        raise ValueError("Could not find 'fermi_energy' in XML")
    fermi_energy_ev = float(fermi_elem.text)
    fermi_energy_ry = fermi_energy_ev / RYDBERG_EV

    nelec_elem = band_structure.find('nelec')
    if nelec_elem is None:
        raise ValueError("Could not find 'nelec' in XML")
    nelec = float(nelec_elem.text)

    nbnd_elem = band_structure.find('nbnd')
    if nbnd_elem is not None:
        nbnd = int(nbnd_elem.text)
    else:
        # Fallback: extract nbnd from the first ks_energies block
        first_ks = band_structure.find('ks_energies')
        if first_ks is None:
            raise ValueError("Could not find 'nbnd' or 'ks_energies' in XML")
        eig_elem = first_ks.find('eigenvalues')
        if eig_elem is None:
            raise ValueError("Could not find 'eigenvalues' in first ks_energies")
        nbnd = len(eig_elem.text.split())

    # Detect spin polarization
    lsda_elem = band_structure.find('lsda')
    nspin = 2 if (lsda_elem is not None and lsda_elem.text.strip().lower() == 'true') else 1

    kpoints = []
    eigenvalues = []

    for ks_block in band_structure.findall('ks_energies'):
        kpt_elem = ks_block.find('k_point')
        if kpt_elem is None:
            raise ValueError("Could not find 'k_point' in ks_energies")
        kpt_str = kpt_elem.text
        kpoints.append([float(x) for x in kpt_str.split()])

        eig_elem = ks_block.find('eigenvalues')
        if eig_elem is None:
            raise ValueError("Could not find 'eigenvalues' in ks_energies")
        eig_str = eig_elem.text
        eig_vals = [float(x) / RYDBERG_EV for x in eig_str.split()]
        eigenvalues.append(eig_vals)

    bands = BandStructure(
        fermi_energy=fermi_energy_ry,
        nelec=nelec,
        nspin=nspin,
        nbnd=nbnd,
        kpoints=kpoints,
        eigenvalues=eigenvalues
    )

    # 3. Assemble and return
    prefix = xml_path.stem.replace('.save', '').replace('.xml', '')
    return QEData(prefix=prefix, crystal=crystal, bands=bands)
