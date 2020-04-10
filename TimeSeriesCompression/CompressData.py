import sys
from Compression import Compression


def main():
    # Added Read Functionality at the end for spec's sake
    if len(sys.argv) == 4:
        if sys.argv[1] == "read":
            input = sys.argv[3]
            Compression.decompress_and_read(input)
            return
    # Wrong number of arguments
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
        Compression.compress_and_write(input, output)
    else:
        Compression.decompress_and_write(input, output)


if __name__ == "__main__":
    main()
