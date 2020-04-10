import unittest
import os


class Compression:

    @staticmethod
    def compress_and_write(input, output):
        deltaConvert = DeltaConversion(input)
        deltaConvert.convert_lists()

        rleTime = RunLengthEncoder(deltaConvert.timestampList)
        rleValue = RunLengthEncoder(deltaConvert.valueList)

        rleTime.write_to_file(output)
        f = open(output, "ab")
        # My algo can't have three zeroes in a row --> using to denote separation btwn timestamps and values
        byteArr = bytearray([0, 0, 0])
        f.write(byteArr)
        f.close()
        rleValue.write_to_file(output)

    @staticmethod
    def decompress_and_write(input, output):

        with open(input, "rb") as f:
            byteArr = bytearray(f.read())
            intArr = [int(x) for x in byteArr]

        # Finding the three zero separation denotation
        zeroCount = 0
        splitIndex = None
        for i, num in enumerate(intArr):
            if num == 0:
                zeroCount += 1

            if zeroCount == 3:
                splitIndex = i
                break
        timestampArr = intArr[0:i - 2]
        valueArr = intArr[i + 1:]

        rldTime = RunLengthDecoder(input, timestampArr)
        rldVal = RunLengthDecoder(input, valueArr)
        rldTime.decode_input_to_array()
        rldVal.decode_input_to_array()

        deltaD = DeltaDeconversion(rldTime.decoded, rldVal.decoded)
        deltaD.deconvert_lists()

        with open(output, 'w') as f:
            for i in range(len(deltaD.valueList)):
                f.write("{}, {}\n".format(deltaD.timestampList[i], deltaD.valueList[i]))

    @staticmethod
    def decompress_and_read(input):

        with open(input, "rb") as f:
            byteArr = bytearray(f.read())
            intArr = [int(x) for x in byteArr]

        zeroCount = 0
        splitIndex = None
        for i, num in enumerate(intArr):
            if num == 0:
                zeroCount += 1

            if zeroCount == 3:
                splitIndex = i
                break

        timestampArr = intArr[0:i - 2]
        valueArr = intArr[i + 1:]

        rldTime = RunLengthDecoder(input, timestampArr)
        rldVal = RunLengthDecoder(input, valueArr)
        rldTime.decode_input_to_array()
        rldVal.decode_input_to_array()

        deltaD = DeltaDeconversion(rldTime.decoded, rldVal.decoded)
        deltaD.deconvert_lists()

        for i in range(len(deltaD.valueList)):
            print(deltaD.timestampList[i], deltaD.valueList[i])


# Takes file (init), assumes two-width array, pulls file (create_lists) , sets props to delta arrays (convert lists)
class DeltaConversion:

    def __init__(self, filename):
        self.fileName = filename
        self.timestampList = []
        self.valueList = []

    def create_lists(self):
        with open(self.fileName) as tempFile:
            for line in tempFile:
                tempLine = line.rstrip()  # strip newline from line
                # tempLine = tempLine[:-1]   # remove final char (comma)
                splitList = tempLine.rsplit(", ")  # remove trailing whitespace and split
                self.valueList.append(int(splitList[1]))  # append value
                self.timestampList.append(int(splitList[0]))  # append timestamp

    def convert_lists(self):
        if not self.timestampList or not self.valueList:
            self.create_lists()

        firstTimestamp = self.timestampList.pop(0)
        previousTimestamp = firstTimestamp
        for i, timestamp in enumerate(self.timestampList):
            self.timestampList[i] = timestamp - previousTimestamp
            previousTimestamp = timestamp
        self.timestampList = [firstTimestamp] + self.timestampList

        firstValue = self.valueList.pop(0)
        previousValue = firstValue
        for i, value in enumerate(self.valueList):
            self.valueList[i] = value - previousValue
            previousValue = value
        self.valueList = [firstValue] + self.valueList

        # Getting rid of those pesky negatives (value list only)
        minValue = min(self.valueList)
        if minValue > 0:
            minValue = 0
        self.valueList = [abs(minValue)] + [x - minValue for x in self.valueList]

    def convert(self):
        self.create_lists()
        self.convert_lists()


#  Takes delta lists as inputs (init), converts lists and sets to class properties (deconvert lists)
class DeltaDeconversion:

    def __init__(self, timestampList, valueList):
        self.timestampList = timestampList
        self.valueList = valueList

    def deconvert_lists(self):
        firstTimestamp = self.timestampList[0]
        previousTimestamp = firstTimestamp
        for i, timestamp in enumerate(self.timestampList[1:]):
            self.timestampList[i + 1] = previousTimestamp + timestamp
            previousTimestamp = previousTimestamp + timestamp

        # Need to remove bias from values set in original conversion
        minValue = self.valueList.pop(0)
        self.valueList = [x - minValue for x in self.valueList]
        firstValue = self.valueList[0]
        previousValue = firstValue
        for i, value in enumerate(self.valueList[1:]):
            self.valueList[i + 1] = previousValue + value
            previousValue = previousValue + value


# Takes array as input (init), encodes to RLE array property (encode input to array)
# Uses input_number and variable_length_encoding to do Variable Bit Length Encoding directly in input to array
class RunLengthEncoder:

    def __init__(self, input):
        self.unencoded = input
        self.outputArray = []

    #  First bit mark number as "need more bits" to allow small numbers to be stored more efficiently
    #  Works recursively
    #  Stored as ints for testing simplicity
    def variable_length_encoding(number):
        numList = []
        currNum = number
        while currNum > 127:
            first7Bits = currNum & 127
            currNum = currNum >> 7
            numList.append(int(first7Bits | 128))

        numList.append(currNum)
        return numList

    def input_number(self, number):
        if number > 127:
            numList = RunLengthEncoder.variable_length_encoding(number)
            for num in numList:
                self.outputArray.append(num)
        else:
            self.outputArray.append(number)

    # Format of encoding is Length , Value
    # Lengths are denoted between the values of 100-127 for single-byte efficiency
    # For 'single run (length = 1) values landing between 100-127, mark as Length = 1, value
    # If run exceeds 27 length, break it
    def encode_input_to_array(self):
        i = 0
        while i < len(self.unencoded):
            runNum = self.unencoded[i]
            currNum = runNum
            runLen = 1
            i += 1
            while i < len(self.unencoded) and runLen < 27:
                currNum = self.unencoded[i]
                if currNum != runNum:
                    break
                i += 1
                runLen += 1

            if runLen == 1 and (runNum < 100 or runNum > 127):
                self.input_number(runNum)

            else:
                self.input_number(runLen + 100)
                self.input_number(runNum)

    # Writes outputArray to File given as input
    def write_to_file(self, name):
        if not self.outputArray:
            self.encode_input_to_array()

        f = open(name, "ab")
        byteArr = bytearray(self.outputArray)
        f.write(byteArr)
        f.close()


# Takes filename of .dat (init), writes byte array (write to array), decodes to property (decode input to array)
class RunLengthDecoder:

    def __init__(self, input, arr=None):
        if arr is None:
            arr = []
        self.filename = input
        self.inputArray = arr
        self.decoded = []

    # Grabs next number from byte array
    def get_next_num(self):
        finalNum = 0
        currNum = self.inputArray.pop(0)
        if currNum < 128:
            return currNum

        currBit = 0
        while (currNum >> 7) == 1:
            last7bits = currNum & 127
            finalNum = (last7bits << currBit) | finalNum
            currBit += 7
            currNum = self.inputArray.pop(0)

        finalNum = (currNum << currBit) | finalNum
        return finalNum

    def decode_input_to_array(self):
        if not self.inputArray:
            self.write_to_array()

        while len(self.inputArray) > 0:
            currNum = self.get_next_num()
            if currNum > 100 and currNum < 128:
                length = currNum - 100
                value = self.get_next_num()
                for _ in range(length):
                    self.decoded.append(value)
            else:
                self.decoded.append(currNum)

    # Takes bytes from input filename
    def write_to_array(self):
        with open(self.filename, "rb") as f:
            byteArr = bytearray(f.read())
            self.inputArray = [int(x) for x in byteArr]


# =================================TESTING==================================================

class IntegrationTests(unittest.TestCase):

    def test_write_to_file(self):
        deltaObject = DeltaConversion(
            "C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/easy.txt")
        deltaObject.convert()
        RLE = RunLengthEncoder(deltaObject.timestampList)
        RLE.write_to_file("testFile.dat")
        if os.path.exists("testFile.dat"):
            os.remove("testFile.dat")

    def test_write_and_read(self):
        deltaObject = DeltaConversion(
            "C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/easy.txt")
        deltaObject.convert()
        RLE = RunLengthEncoder(deltaObject.timestampList)
        RLE.write_to_file("testFile.dat")
        RLD = RunLengthDecoder("testFile.dat")
        RLD.write_to_array()
        self.assertEqual(RLE.outputArray, RLD.inputArray)
        if os.path.exists("testFile.dat"):
            os.remove("testFile.dat")

    def test_encode_and_decode_RLE(self):
        deltaObject = DeltaConversion(
            "C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/long.txt")
        deltaObject.convert()
        RLE = RunLengthEncoder(deltaObject.valueList)
        RLE.write_to_file("testFile.dat")
        RLD = RunLengthDecoder("testFile.dat")
        RLD.decode_input_to_array()
        self.assertEqual(RLE.unencoded, RLD.decoded)
        if os.path.exists("testFile.dat"):
            os.remove("testFile.dat")

        deltaObject = DeltaConversion(
            "C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/long.txt")
        deltaObject.convert()
        RLE = RunLengthEncoder(deltaObject.timestampList)
        RLE.write_to_file("testFile.dat")
        RLD = RunLengthDecoder("testFile.dat")
        RLD.decode_input_to_array()
        self.assertEqual(RLE.unencoded, RLD.decoded)
        if os.path.exists("testFile.dat"):
            os.remove("testFile.dat")

    def test_compress(self):
        Compression.compress_and_write(
            "C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/easy.txt",
            "testFile.dat")
        Compression.decompress_and_read("testFile.dat")
        if os.path.exists("testFile.dat"):
            os.remove("testFile.dat")


class TestRunLengthEncoder(unittest.TestCase):

    def test_encode_to_array(self):
        RLE = RunLengthEncoder([3, 3, 3, 3, 5, 5, 110, 110, 110, 120, 3, 5, 9, 9, 9])
        RLE.encode_input_to_array()
        self.assertEqual([104, 3, 102, 5, 103, 110, 101, 120, 3, 5, 103, 9], RLE.outputArray)

    def test_variable_length_encoder(self):
        self.assertEqual([229, 9], RunLengthEncoder.variable_length_encoding(1253))
        self.assertEqual([181, 181, 211, 181, 9], RunLengthEncoder.variable_length_encoding(2528434869))


class TestDeltaMethods(unittest.TestCase):

    def test_create_list(self):
        deltaObject = DeltaConversion(
            "C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/unittest.txt")
        deltaObject.create_lists()
        self.assertEqual(deltaObject.timestampList, [1387909800, 1387909822, 1387909844])
        self.assertEqual(deltaObject.valueList, [120, 173, 93])

    def test_convert(self):
        deltaObject = DeltaConversion(
            "C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/unittest.txt")
        deltaObject.convert()
        self.assertEqual(deltaObject.timestampList, [1387909800, 22, 22])
        self.assertEqual(deltaObject.valueList, [80, 200, 133, 0])

    def test_convert2(self):
        deltaObject = DeltaConversion(
            "C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/easy.txt")
        deltaObject.convert()
        self.assertEqual(
            [1387909800, 22, 22, 34, 21, 11, 12, 10, 9868, 22, 22, 34, 21, 11, 12, 10, 9868, 22, 22, 34, 21, 11, 12,
             10], deltaObject.timestampList)

    def test_deconvert(self):
        deltaObject = DeltaDeconversion(
            [1387909800, 22, 22, 34, 21, 11, 12, 10, 9868, 22, 22, 34, 21, 11, 12, 10, 9868, 22, 22, 34, 21, 11, 12,
             10], [0, 0, 1, 1])
        deltaObject.deconvert_lists()
        self.assertEqual(
            [1387909800, 1387909822, 1387909844, 1387909878, 1387909899, 1387909910, 1387909922, 1387909932,
             1387919800, 1387919822, 1387919844, 1387919878, 1387919899, 1387919910, 1387919922, 1387919932,
             1387929800, 1387929822, 1387929844, 1387929878, 1387929899, 1387929910, 1387929922, 1387929932],
            deltaObject.timestampList)


if __name__ == '__main__':
    unittest.main()
