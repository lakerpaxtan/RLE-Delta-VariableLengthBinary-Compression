import sys
from Compression import Compression

def main():
    if len(sys.argv) != 6:
        print("invalid number of arguments")
        return

    compress = False
    if sys.argv[1] == "compress":
        compress = True
    elif sys.argv[1] != "read":
        print("invalid arguments")
        return


    input = sys.argv[3]
    output = sys.argv[5]

    if compress:
        Compression.compressAndWrite(input, output)
    else:
        Compression.decompressAndWrite(input, output)


if __name__ == "__main__":
    main()