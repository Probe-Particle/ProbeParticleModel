#!/usr/bin/python
from pathlib import Path

from .. import common
from ..HighLevel import computeLJ


def main(argv=None):
    parser = common.CLIParser(description="Generate a Lennard-Jones, Morse, or vdW force field. The generated force field is saved to FFLJ_{x,y,z}.[ext].")
    parser.add_arguments(["input", "input_format", "output_format", "ffModel", "energy", "noPBC"])
    args = parser.parse_args(argv)
    parameters = common.PpafmParameters()
    common.loadParams("params.ini", parameters)
    common.apply_options(vars(args), parameters)
    species_file = "atomtypes.ini" if Path("atomtypes.ini").is_file() else None
    computeLJ(
        args.input,
        geometry_format=args.input_format,
        speciesFile=species_file,
        save_format=args.output_format,
        computeVpot=args.energy,
        ffModel=args.ffModel,
        parameters=parameters,
    )


if __name__ == "__main__":
    main()
