import struct, zlib, os
from PIL import Image
import time

tiles = []
colorarray = [
    217, 157, 115,
    140, 127, 169,
    235, 238, 245,
    178, 198, 210,
    247, 203, 164,
    39, 39, 39,
    141, 161, 227,
    249, 163, 199,
    119, 119, 119,
    83, 86, 92,
    203,217, 127,
    244,186, 110,
    243, 233, 121,
    116, 87, 206,
    255, 121, 94,
    255, 170, 95
    ]

tuple_array = [tuple(colorarray[t*3:t*3+3]) for t in range(len(colorarray)//3)]
palette = Image.new("P", (16, 16))
palette.putpalette(colorarray*16)
palette.load()

def quantize(img, dither, transparency_treshold):
    
    img = img.convert("RGBA")
    imgq = img.convert("RGB")
    imgq = imgq._new(imgq.im.convert("P", 1 if dither else 0, palette.im))
    
    imgA = Image.new("RGBA", img.size)
    pixels = imgA.load()
    imgq = imgq.convert("RGB")
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if img.getpixel((x, y))[3] > transparency_treshold:
                pixels[x, y] = imgq.getpixel((x, y))
            else:
                pixels[x, y] = (0, 0, 0, 0)

    print("Quantization complete")
    
    return (imgq, imgA)

def imgtomsch(imgfile, name, save_location, dither, transparency_treshold):
    
    img, imgA = quantize(Image.open(imgfile), dither, transparency_treshold)
    
    imgA = imgA.rotate(-90, expand=True)
    img = img.rotate(-90, expand=True)
    
    width, height = img.size
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if imgA.getpixel((x, y))[3] > transparency_treshold:
                tiles.append((x, y, tuple_array.index(img.getpixel((x, y)))))

    print("Converted pixels into an array of tiles")

    class ByteBuffer():
        def __init__(self, data=bytearray()):
            self.data = data
            
        def writeShort(self, int):
            self.data += struct.pack(">H", int)

        def writeUTF(self, str):
            self.writeShort(len(str))
            self.data += bytes(str.encode("UTF"))
            
        def writeByte(self, int):
            self.data += struct.pack("b", int)
            
        def writeInt(self, int):
            self.data += struct.pack(">i", int)
            
    data = ByteBuffer()

    data.writeShort(width)
    data.writeShort(height)

    data.writeByte(1)

    data.writeUTF("name")
    data.writeUTF(name)

    data.writeByte(1)

    data.writeUTF("sorter")
    data.writeInt(len(tiles))

    print("Header written")

    for tile in tiles:
        data.writeByte(0)
        data.writeShort(tile[1])
        data.writeShort(tile[0])
        data.writeInt(tile[2])
        data.writeByte(0)

    print("Tile data written")
    
    filename = str(int(1000 * time.time())) + ".msch"

    os.chdir(os.path.expandvars(save_location))
    file = open(filename, "wb")
    file.write(b"msch\x00"+zlib.compress(data.data))
    file.close()

    print("Successfully saved {0} ".format(filename))
