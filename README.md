# qe2boltz

A robust Python package for converting Quantum Espresso XML output to BoltzTraP2 input format, with full support for spin-polarized calculations.

## Features

- **Spin-Polarization Support**: Automatically detects and separates spin-up and spin-down channels for magnetic materials
- **Modern Architecture**: Clean, modular design with data validation using Pydantic
- **Unit Conversion**: Automatic conversion from Quantum Espresso units (Bohr, Ry) to BoltzTraP2 units (Angstrom, eV)
- **Band Exclusion**: Option to exclude core bands for faster calculations
- **Comprehensive Testing**: 14 unit tests + 2 integration benchmarks
- **User-Friendly CLI**: Simple command-line interface with helpful error messages

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Install from Source

```bash
git clone https://github.com/YOUR_USERNAME/qe2boltz.git
cd qe2boltz
pip install -e .
```

## Usage

### Basic Command

```bash
qe2boltz <input_file> <nbnd_exclude> [-o output_dir]
```

### Parameters

- `input_file`: Path to Quantum Espresso input file (e.g., `nscf.in`)
- `nbnd_exclude`: Number of lowest energy bands to exclude (integer)
- `-o, --output-dir`: Output directory (default: current directory)

### Examples

**Non-magnetic system:**
```bash
qe2boltz nscf.in 2 -o ./boltztrap_output
```

**Spin-polarized system:**
```bash
qe2boltz pw.ni.nscf.in 2 -o ./boltztrap_output
```

This will create:
```
boltztrap_output/
├── spin_up/
│   └── prefix.bandsdat
└── spin_down/
    └── prefix.bandsdat
```

### Running BoltzTraP2

After conversion, use BoltzTraP2 to calculate transport properties:

```bash
# For spin-polarized systems
cd boltztrap_output/spin_up
btp2 interpolate -f prefix.bandsdat --lpfac 7
btp2 dope -f prefix.interp -t 300 --efermi 0.0

cd ../spin_down
btp2 interpolate -f prefix.bandsdat --lpfac 7
btp2 dope -f prefix.interp -t 300 --efermi 0.0
```

## Project Structure

```
qe2boltz/
├── pyproject.toml          # Package configuration
├── README.md               # This file
├── .gitignore              # Git ignore rules
├── src/
│   └── qe2boltz/
│       ├── __init__.py
│       ├── cli.py          # Command-line interface
│       ├── models.py       # Data models (Pydantic)
│       ├── parsers.py      # XML parsing
│       ├── processors.py   # Data processing (spin separation)
│       └── writers.py      # BoltzTraP2 file generation
└── tests/
    ├── test_models.py      # Model validation tests
    ├── test_parsers.py     # Parser tests
    ├── test_processors.py  # Processing tests
    └── test_writers.py     # Writer tests
```

## Testing

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

## Physics Background

### Unit Conversions

The package handles the following conversions automatically:

| Quantity | Quantum Espresso | BoltzTraP2 |
|----------|------------------|------------|
| Energy | Rydberg (Ry) | Electron-volt (eV) |
| Length | Bohr | Angstrom (Å) |
| Conversion | 1 Ry = 13.605693 eV | 1 Bohr = 0.529177 Å |

### Spin-Polarized Systems

For magnetic materials (nspin=2), the package:
1. Detects spin polarization from XML (`<lsda>true</lsda>`)
2. Separates eigenvalues into spin-up and spin-down channels
3. Adjusts electron count: `nelec_adjusted = nelec - nbnd_exclude`
4. Generates separate `.bandsdat` files for each spin channel

### BoltzTraP2 Generic Format

The output `.bandsdat` file follows this structure:
```
Line 1:       System name (prefix)
Line 2:       Number of k-points (nkpt)
Lines 3-5:    Lattice vectors in Angstrom (3×3 matrix)
Then for each k-point:
  Line A:     kx ky kz nbnd
  Line B:     e1 e2 e3 ... e_nbnd (in eV)
```

## Benchmark Validation

The package has been validated against published results for:
- **Nickel (Ni) FCC**: Spin-resolved Seebeck coefficients showing opposite signs for spin-up and spin-down channels
- **Iron (Fe) BCC**: Similar spin-dependent behavior

Reference: X. Ma et al., "Ab initio calculation of thermoelectric properties in 3d ferromagnets", New Journal of Physics (2023). DOI: [10.1088/1367-2630/accca1](https://doi.org/10.1088/1367-2630/accca1)

## Dependencies

- `pydantic>=2.0.0`: Data validation
- `numpy>=1.20.0`: Numerical computations
- `lxml>=4.9.0`: XML parsing
- `typer>=0.9.0`: CLI framework
- `pytest>=7.0.0`: Testing (development)

## License

MIT License

## Citation

If you use this package in your research, please cite:

```bibtex
@software{qe2boltz,
  author = {YOUR_NAME},
  title = {qe2boltz: Quantum Espresso to BoltzTraP2 converter},
  year = {2024},
  url = {https://github.com/YOUR_USERNAME/qe2boltz}
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
