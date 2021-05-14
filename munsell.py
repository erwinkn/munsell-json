import json
from itertools import product, compress, islice, chain
import csv
import os
import argparse

parser = argparse.ArgumentParser("""
Generates a JSON file from Munsell renotation data, processed for rendering.
By default, it includes only colors that can be represented in the sRGB gamut.
The data contains:
    - hidx: hue index, from 0 to 39, corresponding to 2.5R-10RP
    - V: Munsell value 
    - C: chroma
    - hex: the RGB hex code for this color (sRGB space)""")
parser.add_argument('-f', '--full', action='store_true', help='also include the original hue notation h and the original xyY color data')
parser.add_argument('-k', action='store', dest='keep', choices=['rgb', 'all', 'nonrgb'], default='rgb',
help='choose what colors you keep: those in the sRGB gamut, those out of the gamut, or both')
parser.add_argument('-o', action='store', dest='output', help="specify a filename for output (default: 'munsell_real.json')")
parser.add_argument('--indent', action='store_true', help='add indentation to make the resulting JSON human-readable')

args = parser.parse_args()
full = args.full
keep = args.keep
do_indent = args.indent

primary = ['R', 'YR', 'Y', 'GY', 'G', 'BG', 'B', 'PB', 'P', 'RP']
increments = ['2.5', '5', '7.5', '10']
# produce all combinations in order
hues = map(lambda x: x[1] + x[0], product(primary, increments))
# provide a quick index lookup for each hue
hues_to_idx = dict([(x, i) for i, x in enumerate(hues)])
def hue_to_idx(hue):
    return hues_to_idx[hue]

# Convert standard illuminant C -> D65
# see http://www.brucelindbloom.com/index.html?Eqn_ChromAdapt.html
def adapt_C_D65_bradford(XYZ_C):
    X, Y, Z = XYZ_C
    return [+0.9904476*X -0.0071683*Y -0.0116156*Z,
            -0.0123712*X +1.0155950*Y -0.0029282*Z,
            -0.0035635*X +0.0067697*Y +0.9181569*Z]

# normalization coeff to ensure that the color of Munsell value = 10 (lightest color) has Y = 100 (max luminance)
reflect_coeff = 0.9749629514078465

# see http://www.brucelindbloom.com/Eqn_xyY_to_XYZ.html for the conversion functions below
def xyY_to_XYZ(xyY):
    x, y, Y = xyY
    return [x*Y/y, Y, (1 - x - y)*Y/y]

def XYZ_to_xyY(XYZ):
    X, Y, Z = XYZ

def gamma(x):
    return 12.92 * x if x <= 0.0031308 else 1.055 * pow(x, 1/2.4) - 0.055 

def XYZ_to_sRGB(XYZ):
    X, Y, Z = XYZ
    return [gamma(+ 0.03241003232976359  *X - 0.015373989694887858*Y - 0.004986158819963629  *Z),
            gamma(- 0.009692242522025166 *X + 0.01875929983695176 *Y + 0.00041554226340084706*Z),
            gamma(+ 0.0005563941985197545*X - 0.0020401120612391  *Y + 0.010571489771875336  *Z)]

def in_sRGB_gamut(XYZ):
    R, G, B = XYZ_to_sRGB(XYZ)
    return 0 <= R <= 1 and 0 <= G <= 1 and 0 <= B <= 1
def out_of_sRGB_gamut(XYZ): return not in_sRGB_gamut(XYZ)

def clamp(v, low, high):
    return min(max(low, v), high)

def sRGB_to_hex(RGB):
    R, G, B = [int(255*v) for v in RGB]
    R, G, B = clamp(R, 0, 255), clamp(G, 0, 255), clamp(B, 0, 255)
    return '#%02x%02x%02x' % (R, G, B)

# see https://observablehq.com/@jrus/munsell-spin for this polynomial
def V_to_Y(V):
    return V * (1.2219 + V * (-0.23111 + V * (0.23951 + V * (-0.021009 + V * (0.0008404)))))

# standard white for C illuminant (see: https://observablehq.com/@jrus/cam16#standard_whitepoints)
Xw, Yw, Zw = 98.074, 100, 118.232
def munsell_neutral(V):
    Y = V_to_Y(V)
    X = Xw * Y / Yw
    Z = Zw * Y / Yw
    XYZ_n = (X*reflect_coeff, Y*reflect_coeff, Z*reflect_coeff)
    XYZ_D65 = adapt_C_D65_bradford(XYZ_n)    
    sRGB = XYZ_to_sRGB(XYZ_D65)
    hex = sRGB_to_hex(sRGB)
    if full:
        x = X / (X + Y + Z) if V != 0 else 0
        y = Y / (X + Y + Z) if V != 0 else 0
        return x,y,Y,V,hex
    return V, hex


datafile = "real.dat"
jsonfile = args.output if args.output is not None else "munsell_real.json"
if not os.path.isfile(datafile):
    os.system('curl -o ' + datafile + ' http://www.rit-mcsl.org/MunsellRenotation/real.dat')

with open(datafile, 'r', newline='') as file:
    reader = csv.reader(file, delimiter=' ', skipinitialspace=True)
    # ignore header row
    data = islice(reader, 1, None)
    h, V, C, *xyY = zip(*data)

    # convert xyY data to float
    x,y,Y = map(lambda *args: map(float, *args), xyY)
    # for later reuse
    if full:
        x = list(x)
        y = list(y)
        Y = list(Y)

    # adjust reflectance
    Y_n = map(lambda Y: reflect_coeff * Y, Y)
    # convert xyY data from 3 separate lists into a list of triplets
    xyY = zip(x, y, Y_n)
    # convert xyY -> XYZ under the proper standard illuminant
    XYZ_C = map(xyY_to_XYZ, xyY)
    # have to instantiate for reuse
    XYZ = list(map(adapt_C_D65_bradford, XYZ_C))

    # by default, only keep the values that exist in the sRGB gamut
    if keep != "all":
        filterFun = in_sRGB_gamut if keep == "rgb" else out_of_sRGB_gamut
        boolmask = list(map(filterFun, XYZ))
        XYZ = compress(XYZ, boolmask)
        # convert Value and Chroma to integers
        V = map(int, compress(V, boolmask))
        C = map(int, compress(C, boolmask))
        h = list(compress(h, boolmask))

    # convert to sRGB and hex
    RGB = map(XYZ_to_sRGB, XYZ)
    hexes = map(sRGB_to_hex, RGB)

    # convert the Munsell hue notation to its index in the order
    hidx = map(hue_to_idx, h)

    # add neutrals
    neutrals = map(munsell_neutral, range(11))

    # build up the data
    if full:
        colors_data = [{ 'h': h, 'V': V, 'C': C, 'hidx': hidx, 'x': x, 'y': y, 'Y': Y, 'hex': hex } for h, V, C, hidx, x, y, Y, hex in zip(h, V, C, hidx, x, y, Y, hexes)]
        neutrals_data = [{'h': 'N', 'V': V, 'C': 0, 'hidx': 0, 'x': x, 'y': y, 'Y': Y, 'hex': hex } for x, y, Y, V, hex in neutrals ]
    else:
        colors_data = [{ 'hidx': hidx, 'V': V, 'C': C, 'hex': hex } for hidx, V, C, hex,  in zip(hidx, V, C, hexes)]
        neutrals_data = [{'hidx': 0, 'V': V, 'C': 0, 'hex': hex } for V, hex in neutrals ]

    if keep != "nonrgb":
        jsondata = list(chain(colors_data, neutrals_data))
    else:
        jsondata = list(colors_data)
    
    print('Processed', len(jsondata), 'colors')
    print('Output:', jsonfile)

    with open(jsonfile, "w") as writefile:
        indent = 4 if do_indent else None
        json.dump(jsondata, writefile, indent=indent) 
