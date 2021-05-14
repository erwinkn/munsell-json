# Munsell JSON
This repository contains the Munsell renotation data from 1943, as provided by the [Rochester Institute of Technology](https://www.rit.edu/cos/colorscience/rc_munsell_renotation.php), converted into JSON format. 

The provided JSON file `munsell.json`, contains all the colors from the 1943 renotation data, including Munsell and xyY coordinates, as well as the corresponding sRGB colors in hex format. The original colors that could not be directly expressed in the sRGB space, they were mapped to the closest color.


The Python script that operates the conversion also converts from the Munsell color system to sRGB colors in hex format. It provides a few options to get exactly what you need, see [Usage](#usage).

Since the script originated from a [fun personal project](https://erwinkn.com/#playground), it's designed to provide the data in a format geared towards rendering. As an example, the repository also includes a visualisation of the data using [Zdog](https://zzz.dog/).

## Usage
Generates a JSON file from Munsell renotation data, processed for rendering.
By default, it includes only colors that can be represented in the sRGB gamut. The `hidx` is included by default instead of the original `h` notation, as it allows for an easy translation into the coordinates you need for your visualisation.

```python munsell.py [-h] [-f] [-k {rgb,all,nonrgb}] [-o OUTPUT] [--indent]```

With default options, the data contains:
- hidx: hue index, from 0 to 39, corresponding to 2.5R-10RP
- V: Munsell value 
- C: chroma
- hex: the RGB hex code for this color (sRGB space)

Optional arguments:
- `-f`, `--full`: also include the original hue notation h and the original xyY color data
- `-k {rgb,all,nonrgb}`: choose the colors you keep. Default is `rgb`, which keeps all the colors that can be directly converted to the sRGB space, including the neutrals. `nonrgb` only includes the colors that cannot be directly converted to the sRGB space, mapped to the closest color for their hex code. `all` includes both.
- `-o OUTPUT`: specify a filename for output (default: `munsell_real.json`)
- `--indent`: add indentation to make the resulting JSON human-readable
- `-h`, `--help`: show the help message and exit
