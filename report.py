#!/usr/bin/python3

import collections
import itertools
import math
from pathlib import Path
import tempfile
import glob

import weasyprint
from PIL import Image
from xstitch import timer, scriptdir

Dimensions = collections.namedtuple("Dimensions", "name, width, height")
class Dimensions:
    def __init__(self, name, width, height):
        self.name = name
        self.width = width
        self.height = height
    def transpose(self):
        return Dimensions(self.name, self.height, self.width)

def page_dimensions(page="A4"):
    """Returns Dimensions(name, width, height) in mm"""
    D = Dimensions
    # paper = {d.name:d for d in
    #          [D("A0", 841, 1189),    D("B0", 1000, 1414),    D("C0", 917, 1297),
    #           D("A1", 594,  841),    D("B1",  707, 1000),    D("C1", 648,  917),
    #           D("A2", 420,  594),    D("B2",  500,  707),    D("C2", 458,  648),
    #           D("A3", 297,  420),    D("B3",  353,  500),    D("C3", 324,  458),
    #           D("A4", 210,  297),    D("B4",  250,  353),    D("C4", 229,  324),
    #           D("A5", 148,  210),    D("B5",  176,  250),    D("C5", 162,  229),
    #           D("A6", 105,  148),    D("B6",  125,  176),    D("C6", 114,  162),
    #           D("A7",  74,  105),    D("B7",   88,  125),    D("C7",  81,  114),
    #           D("A8",  52,   74),    D("B8",   62,   88),    D("C8",  57,   81),
    #           D("A9",  37,   52),    D("B9",   44,   62),    D("C9",  40,   57),
    #           D("A10", 26,   37),    D("B10",  31,   44),    D("C10", 28,   40),
    #           D("A", 216, 279), D("B", 279, 432), D("C", 432, 559), D("D", 559, 864), D("E", 864, 1118),
    #           D("LETTER", 216, 279), D("LEGAL", 216, 356), D("TABLOID", 279, 432), D("LEDGER", 432, 279),
    #           D("Junior", 127, 203), D("Half", 140, 216), D("Memo", 140, 216)]}
    paper = {d.name:d for d in
             [D("A5", 148, 210),
              D("A4", 210, 297),
              D("A3", 297, 420),
              D("B5", 176, 250),
              D("B4", 250, 353),
              D("JIS-B5", 182, 257),
              D("JIS-B4", 257, 364),
              D("LETTER", 216, 279),
              D("LEGAL", 216, 356),
              D("LEDGER", 432, 279)]}
    page = page.upper().replace("ansi", "").strip()
    if page != "A4":
        raise Exception("page not supported")
    return paper[page]

def px(mm):
    return mm*3.78

def create(args, image, colors):
    with tempfile.TemporaryDirectory() as directory:
        timer("report")
        directory = Path("./").absolute()
        preview_file = Path(directory, "out.png")
        html_file = Path(directory, "result.html")
        filename = Path(directory, "result.pdf")

        page = page_dimensions(args.page).transpose()
        grid = math.floor(px(args.grid))
        symbol_size = grid-4
        border = 1 #px

        # if image.width / image.height > page.height / page.width:
        #     preview = image.transpose(Image.ROTATE_270)
        # else:
        #     preview = image
        preview = image
        preview = preview.resize((preview.width*10, preview.height*10))
        preview.save(str(preview_file))

        colors = sorted(colors, key=lambda c: c.hsv())
        symbols = create_symbols(colors)
        pattern = create_pattern(args, image, symbols, page, grid, border, px(args.margin))
        legend = create_legend(colors, symbols)
        icons = "\n".join(load_icons())

        css = css_template.format(size=page.name,
                                  margin=args.margin,
                                  grid=grid,
                                  symbol_size=symbol_size,
                                  border=border)
        html = page_template.format(css=css,
                                    grid=px(args.grid),
                                    preview=str(preview_file),
                                    layout="",
                                    pattern=pattern,
                                    legend=legend,
                                    footer="",
                                    icons=icons,
                                    directory=directory)

        with html_file.open("w") as file:
            file.write(html)
        timer("report")
        timer("render")
        d = weasyprint.HTML(string=html).render()
        print("weasyprint", d.pages[0].width, d.pages[0].height)
        d.write_pdf(str(filename))
        # weasyprint.HTML(string=html).write_pdf(str(filename))
        timer("render")
        # with svgfile.open("w") as file:
            # file.write(pattern)

def create_symbols(colors):
    alphabet = """abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZæøåÆØÅ1234567890,.<>`~!@#$%^&*()λπ=+¡ºª¢€ħðþ‘’×¹²³£¥ĦÐÞ“”÷[]{}«»‹›'"|õ/?-_–äÄ"""
    symbols = itertools.cycle(alphabet)
    return {(c.red, c.green, c.blue):l for c,l in zip(colors, symbols)}

def create_pattern(args, image, symbols, page, grid, border, margin):
    result = []

    page_width = math.floor((px(page.width) - margin*2) / (grid + border))
    page_height = math.floor((px(page.height) - margin*2) / (grid + border))
    print("px", page_width, page_height)
    print(px(page.width) - margin*2, px(page.height) - margin*2)

    page = 0
    for pagey in range(0, image.height, page_height):
        for pagex in range(0, image.width, page_width):
            page += 1
            result.append('<p class="pagebreak"></p>')
            result.append("""<table class="pattern">""")
            for y in range(pagey, min(pagey+page_height, image.height)):
                result.append("<tr>")
                for x in range(pagex, min(pagex+page_width, image.width)):
                    pixel = image.getpixel((x, y))[:3]
                    symbol = symbols[pixel]
                    result.append('<td style="background-color:rgb{}; color:{};">'.format(pixel, "#ffffff" if is_dark(pixel) else "#000000"))
                    result.append(symbol)
                    # result.append('<div class="content"></div>')
                    result.append("</td>")
                result.append("</tr>")
            result.append("</table>")
            result.append('<div class="page">{}</div>'.format(page))
    return "\n".join(result)

def is_dark(color):
    return color[0]+color[1]+color[2] < 128 * 3

def create_legend(colors, symbols):
    # redest = min(colors, lambda c: math.sqrt((255-c.red)**2))
    result = []
    result.append('<table class="legend">')
    for color in colors:
        result.append("<tr>")
        row = ("<td>{}</td>".format(x) for x in (symbols[color.rgb()], color.name, color.description))
        result.append("".join(row))
        result.append('<td style="background-color:rgb{}; width:10mm;"></td>'.format(str(color.rgb())))
        result.append("</tr>")
    result.append('</table>')
    return "\n".join(result)

def load_icons():
    p = Path(scriptdir, "icons", "*")
    result = []
    for filename in glob.glob(str(p)):
        with open(filename) as f:
            result.append('<div class="symbol">{}</div>'.format(f.read()))
    return result


page_template = """\
<!DOCTYPE html>
<html>
  <head>
    <style>
    {css}
    </style>
  </head>
  <body>
    <div style="width:100%;background-color:#0000ff">XStitch</div>
    <img src="file://{preview}" class="preview">
    <div style="width:{grid}px; height:{grid}px;background-color: #ff00ff"></div>
    <div style="background-color:#00ff00; height:50px;">
      {icons}
    </div>
    {legend}
    {layout}
    {footer}
    {pattern}
    <p class="pagebreak"></p>
  </body>
</html>
"""

css_template = """\
@page {{
  size: {size} landscape;
  bleed: 0mm;
  margin: {margin}mm;
  border: 0mm;
  padding: 0mm;
}}
body {{
  margin: 0mm;
  border: 0mm;
  padding: 0mm;
}}

.preview {{
  width: 100%;
  qheight: 100%;
  max-width: 8%;
  max-height: 8%;
}}

.legend {{
  border-collapse: collapse;
}}
.legend td {{
  border: {border}px solid black;
}}
.pattern {{
  font-size: 2pt;
  border-collapse: collapse;
}}
.pattern td {{
  qwidth: {grid}mm;
  qheight: {grid}mm;
  width: {grid}px;
  height: {grid}px;
  qwidth: 3mm;
  qheight: 3mm;
  qwidth: 12px;
  qheight: 12px;
  margin: 0mm;
  qborder: 0mm;
  padding: 0.0mm;
  box-sizing: padding-box;
  qbox-sizing: border-box;
  border: {border}px solid black;
}}
.content {{
  width: 2.5mm;
  height: 2.5mm;
  background-color: #ff0000;
}}
.page {{
  position: absolute;
  top: 5px;
  left: -15px;
}}
.pagebreak {{
  page-break-after: always;
}}

.symbol {{
  width: {symbol_size}px;
  height: {symbol_size}px;
}}
"""
