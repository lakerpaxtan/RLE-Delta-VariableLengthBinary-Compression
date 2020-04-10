import unittest
import os

class Compression:

    @staticmethod
    def compressAndWrite(input, output):
        deltaConvert = DeltaConversion(input)
        deltaConvert.convert_lists()

        rleTime = RunLengthEncoder(deltaConvert.timestampList)
        rleValue = RunLengthEncoder(deltaConvert.valueList)

        rleTime.writeToFile(output)
        f = open(output, "ab")
        byteArr = bytearray([0,0,0]) #  My algo can't have three zeroes in a row --> using to denote change in array
        f.write(byteArr)
        f.close()
        rleValue.writeToFile(output)

    @staticmethod
    def decompressAndWrite(input, output):

        with open(input, "rb") as f:
            byteArr = bytearray(f.read())
            intArr = [int(x) for x in byteArr]

        zeroCount = 0
        splitIndex = None
        for i, num in enumerate(intArr):
            if num == 0:
                zeroCount +=1

            if zeroCount == 3:
                splitIndex = i
                break

        timestampArr = intArr[0:i-2]
        valueArr = intArr[i+1:]

        rldTime = RunLengthDecoder(input, timestampArr)
        rldVal = RunLengthDecoder(input, valueArr)
        rldTime.decodeInputToArray()
        rldVal.decodeInputToArray()

        deltaD = DeltaDeconversion(rldTime.decoded, rldVal.decoded)
        deltaD.deconvert_lists()

        for i in range(len(deltaD.valueListPost)):
            print(deltaD.timestampListPost[i], deltaD.valueListPost[i])













class DeltaConversion:

    def __init__(self, filename):
        self.fileName = filename
        self.timestampList = []
        self.valueList = []
        self.firstTimestamp = None
        self.firstValue = None

    def create_lists(self):
        with open(self.fileName) as tempFile:
            for line in tempFile:
                tempLine = line.rstrip()  # strip newline from line
                tempLine = tempLine[:-1]   # remove final char (comma)
                splitList = tempLine.rsplit(", ")  # remove trailing whitespace and split
                self.valueList.append(int(splitList[1]))  # append value
                self.timestampList.append(int(splitList[0]))  # append timestamp

    def convert_lists(self):
        if not self.timestampList or not self.valueList:
            self.create_lists()

        self.firstTimestamp = self.timestampList.pop(0)
        previousTimestamp = self.firstTimestamp
        for i, timestamp in enumerate(self.timestampList):
            self.timestampList[i] = timestamp - previousTimestamp
            previousTimestamp = timestamp
        self.timestampList = [self.firstTimestamp] + self.timestampList

        self.firstValue = self.valueList.pop(0)
        previousValue = self.firstValue
        for i , value in enumerate(self.valueList):
            self.valueList[i] = value - previousValue
            previousValue = value
        self.valueList = [self.firstValue] + self.valueList

        # Getting rid of those pesky negatives (value list only)
        minValue = min(self.valueList)

        self.valueList = [abs(minValue)] + [x - minValue for x in self.valueList]



    def convert(self):
        self.create_lists()
        self.convert_lists()

#  Deconversion is totally a real word
class DeltaDeconversion:

    def __init__(self, timestampList, valueList):

        self.timestampListPre = timestampList
        self.valueListPre = valueList

        self.timestampListPost = []
        self.valueListPost = []

    def deconvert_lists(self):
        firstTimestamp = self.timestampListPre[0]
        self.timestampListPre.pop(0)
        self.timestampListPost.append(firstTimestamp)

        previousTimestamp = firstTimestamp
        for i, timestamp in enumerate(self.timestampListPre):
            self.timestampListPost.append(previousTimestamp + timestamp)
            previousTimestamp = previousTimestamp + timestamp

        minValue = self.valueListPre.pop(0)

        self.valueListPre = [x - minValue for x in self.valueListPre]

        firstValue = self.valueListPre[0]
        self.valueListPre.pop(0)
        self.valueListPost.append(firstValue)

        previousValue = firstValue
        for i, value in enumerate(self.valueListPre):
            self.valueListPost.append(previousValue + value)
            previousValue = previousValue + value







class RunLengthEncoder:

    def __init__(self, input):
        self.unencoded = input
        self.nonbinaryArray = []

    #  First bit mark number as "need more bits" to allow small numbers to be stored more efficiently
    #  Works recursively
    #  Stored as ints for testing simplicity
    def variableLengthEncoding(number):
        numList = []
        currNum = number
        while currNum > 127:
            first7Bits = currNum & 127
            currNum = currNum >> 7
            numList.append(int(first7Bits | 128))

        numList.append(currNum)
        return numList



    def inputNumber(self, number):

        if number > 127:
            numList = RunLengthEncoder.variableLengthEncoding(number)
            for num in numList:
                self.nonbinaryArray.append(num)

        else:
            self.nonbinaryArray.append(number)

    # Format of encoding is Length , Value
    # Lengths are denoted between the values of 100-127 for single-byte efficiency
    # For 'single run (length = 1) values landing between 100-127, mark as Length = 1, value
    # If run exceeds 27 length, break it
    def encodeInputToArray(self):
        i = 0
        while i < len(self.unencoded):
            runNum = self.unencoded[i]
            currNum = runNum
            runLen = 1
            i+=1
            while i < len(self.unencoded) and runLen < 27:
                currNum = self.unencoded[i]
                if currNum != runNum:
                    break
                i+=1
                runLen+=1

            if runLen == 1 and (runNum < 100 or runNum > 127):
                self.inputNumber(runNum)

            else:
                self.inputNumber(runLen + 100)
                self.inputNumber(runNum)



    def writeToFile(self, name):
        if not self.nonbinaryArray:
            self.encodeInputToArray()

        f = open(name, "ab")
        byteArr = bytearray(self.nonbinaryArray)
        f.write(byteArr)
        f.close()


class RunLengthDecoder:

    def __init__(self, input, arr = []):
        self.filename = input
        self.nonbinaryArray = arr
        self.decoded = []


    def getNextNum(self):
        finalNum = 0
        currNum = self.nonbinaryArray.pop(0)

        if currNum < 128:
            return currNum

        currBit = 0
        while (currNum >> 7) == 1:
            last7bits = currNum & 127
            finalNum = (last7bits << currBit) | finalNum
            currBit += 7
            currNum = self.nonbinaryArray.pop(0)

        finalNum = (currNum << currBit) | finalNum
        return finalNum


    def decodeInputToArray(self):
        if not self.nonbinaryArray:
            self.writeToArray()

        while len(self.nonbinaryArray) > 0:
            currNum = self.getNextNum()

            if currNum > 100 and currNum < 128:
                length = currNum - 100
                value = self.getNextNum()
                for _ in range(length):
                    self.decoded.append(value)

            else:
                self.decoded.append(currNum)



    def writeToArray(self):
        with open(self.filename, "rb") as f:
            byteArr = bytearray(f.read())
            self.nonbinaryArray = [int(x) for x in byteArr]



class IntegrationTests(unittest.TestCase):

    def test_write_to_file(self):
        deltaObject = DeltaConversion("C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/easy.txt")
        deltaObject.convert()
        RLE = RunLengthEncoder(deltaObject.timestampList)
        RLE.writeToFile("testFile.dat")
        if os.path.exists("testFile.dat"):
            os.remove("testFile.dat")

    def test_write_and_read(self):
        deltaObject = DeltaConversion("C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/easy.txt")
        deltaObject.convert()
        RLE = RunLengthEncoder(deltaObject.timestampList)
        RLE.writeToFile("testFile.dat")
        RLD = RunLengthDecoder("testFile.dat")
        RLD.writeToArray()
        self.assertEqual(RLE.nonbinaryArray, RLD.nonbinaryArray)
        if os.path.exists("testFile.dat"):
            os.remove("testFile.dat")

    def test_encode_and_decode(self):
        deltaObject = DeltaConversion("C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/easy.txt")
        deltaObject.convert()
        RLE = RunLengthEncoder(deltaObject.timestampList)
        RLE.writeToFile("testFile.dat")
        RLD = RunLengthDecoder("testFile.dat")
        RLD.decodeInputToArray()
        self.assertEqual(RLE.unencoded, RLD.decoded)
        if os.path.exists("testFile.dat"):
            os.remove("testFile.dat")

    def test_compress(self):
        Compression.compressAndWrite("C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/easy.txt", "testFile.dat")
        Compression.decompressAndWrite("testFile.dat", "whocares.txt")
        if os.path.exists("testFile.dat"):
            os.remove("testFile.dat")

    # def test_compress_write(self):
    #     Compression.compressAndWrite("C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/easy.txt", "testFile.dat")
    #
    # 
    # def test_compress_read(self):
    #     Compression.decompressAndWrite("testFile.dat", "whocares.txt")



class TestRunLengthEncoder(unittest.TestCase):

    def test_encode_to_array(self):
        RLE = RunLengthEncoder([3,3,3,3,5,5,110,110,110,120,3,5,9,9,9])
        RLE.encodeInputToArray()
        self.assertEqual([104, 3, 102, 5, 103, 110, 101,120, 3, 5, 103, 9], RLE.nonbinaryArray)



    def test_variable_length_encoder(self):
        self.assertEqual([229, 9], RunLengthEncoder.variableLengthEncoding(1253))
        self.assertEqual([181,181,211,181,9], RunLengthEncoder.variableLengthEncoding(2528434869))




class TestDeltaMethods(unittest.TestCase):

    def test_create_list(self):
        deltaObject = DeltaConversion("C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/unittest.txt")
        deltaObject.create_lists()
        self.assertEqual(deltaObject.timestampList, [1387909800, 1387909822, 1387909844])
        self.assertEqual(deltaObject.valueList, [120,173,93])

    def test_convert(self):
        deltaObject = DeltaConversion("C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/unittest.txt")
        deltaObject.convert()
        self.assertEqual(deltaObject.timestampList, [1387909800, 22, 22])
        self.assertEqual(deltaObject.valueList, [120, 53, -80])

    def test_convert2(self):
        deltaObject = DeltaConversion(
            "C:/Users/Pax/PycharmProjects/RLE-Delta-VariableLengthBinary-Compression/TimeSeriesCompression/Inputs/easy.txt")
        deltaObject.convert()
        self.assertEqual([1387909800, 22, 22, 34, 21, 11, 12, 10, 9868, 22, 22, 34, 21, 11, 12, 10, 9868, 22, 22, 34, 21, 11, 12, 10], deltaObject.timestampList)

    def test_deconvert(self):
        deltaObject = DeltaDeconversion("not needed", [1387909800, 22, 22, 34, 21, 11, 12, 10, 9868, 22, 22, 34, 21, 11, 12, 10, 9868, 22, 22, 34, 21, 11, 12, 10])
        deltaObject.deconvert_lists()
        self.assertEqual( [1387909800,1387909822,1387909844,1387909878,1387909899,1387909910,1387909922,1387909932,
                          1387919800,1387919822,1387919844,1387919878,1387919899,1387919910,1387919922,1387919932,
                          1387929800,1387929822,1387929844,1387929878,1387929899,1387929910,1387929922,1387929932], deltaObject.timestampListPost)




if __name__ == '__main__':
    unittest.main()
