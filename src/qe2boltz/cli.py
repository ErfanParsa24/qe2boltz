import typer
from pathlib import Path

from .parsers import parse_qe_input, parse_qe_xml
from .processors import process_qe_data
from .writers import write_boltztrap2_generic

# Initialize the Typer app
app = typer.Typer(
    name="qe2boltz",
    help="A robust converter from Quantum Espresso XML to BoltzTraP2 generic format.",
    add_completion=False
)

@app.command()
def convert(
    input_file: Path = typer.Argument(
        ...,
        help="Path to the Quantum Espresso input file (e.g., nscf.in)."
    ),
    nbnd_exclude: int = typer.Argument(
        ...,
        help="Number of lowest energy bands to exclude from the calculation."
    ),
    output_dir: Path = typer.Option(
        Path("."),
        "--output-dir", "-o",
        help="Directory to save the BoltzTraP2 output files (.bandsdat)."
    )
):
    """
    Converts Quantum Espresso output to BoltzTraP2 format.

    This command reads the QE input file to find the XML output,
    processes the band structure (handling spin-polarization and band exclusion),
    and writes the data in the BoltzTraP2 generic format.
    """
    # 1. Validate input file
    if not input_file.exists():
        typer.echo(f"Error: Input file '{input_file}' does not exist.", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"🔍 Reading QE input file: {input_file}")
    try:
        prefix, outdir = parse_qe_input(str(input_file))
    except Exception as e:
        typer.echo(f"Error parsing input file: {e}", err=True)
        raise typer.Exit(code=1)

    # 2. Locate the XML file (QE usually saves it in outdir/prefix.save/prefix.xml)
    xml_path = Path(outdir) / f"{prefix}.save" / f"{prefix}.xml"
    if not xml_path.exists():
        # Fallback for simpler outdir structures
        xml_path = Path(outdir) / f"{prefix}.xml"
        if not xml_path.exists():
            typer.echo(f"Error: XML file not found at '{xml_path}' or '{Path(outdir) / f'{prefix}.save' / f'{prefix}.xml'}'.", err=True)
            raise typer.Exit(code=1)

    typer.echo(f"📄 Parsing XML data from: {xml_path}")
    try:
        qe_data = parse_qe_xml(str(xml_path))
    except Exception as e:
        typer.echo(f"Error parsing XML file: {e}", err=True)
        raise typer.Exit(code=1)

    # 3. Process the data
    typer.echo(f"⚙️ Processing data (excluding {nbnd_exclude} bands, nspin={qe_data.bands.nspin})...")
    try:
        processed_data = process_qe_data(qe_data, nbnd_exclude)
    except ValueError as e:
        typer.echo(f"Error during processing: {e}", err=True)
        raise typer.Exit(code=1)

    # 4. Write output files
    typer.echo(f"💾 Writing BoltzTraP2 files to: {output_dir}")
    try:
        write_boltztrap2_generic(processed_data, str(output_dir))
    except Exception as e:
        typer.echo(f"Error writing output files: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo("✅ Conversion completed successfully!")

    if processed_data.nspin == 2:
        typer.echo(f"   Generated: {processed_data.prefix}_up.bandsdat and {processed_data.prefix}_dn.bandsdat")
    else:
        typer.echo(f"   Generated: {processed_data.prefix}.bandsdat")

if __name__ == "__main__":
    app()
