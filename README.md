# RLE-Delta-VariableLengthBinary-Compression

This project compresses and decompresses integer timeseries using Delta, Run-Length, and Variable Bit length encoding. 

---

### USAGE: 
Given an input of timeseries data formatted as....

timestamp1 (int), value1 (int) \n
timestamp2 (int), value2 (int) \n
timestamp3 (int), value3 (int) \n
......
##### To Compress:
python CompressData.py compress --input "inputfile.txt" --output "outputData.dat"
##### To Decompress:
python CompressData.py decompress --input "inputdata.dat" --output "outputtext.txt"
##### To Print:
python CompressData.py read --input "inputdata.dat" 

#### Assumptions:
- Timestamps are positive and increasing 
- Values are positive (though negatives should work --> currently untested) 
- Lists are equal length
- All inputs are ints and not None

-------------------------------------

### Code Flow: 
Generally speaking.....
##### Compress:
Text Data --> Delta Encoder --> RLE Encoder --> Write to .dat (w/ Variable Length Bit Encoding)
##### Decompress:
Binary Data --> Decode Variable Length Bit Encoding --> RLE Decoder --> Delta Decoder --> Print 


-------------------------------------

### Comments: 
- Encoder and Decoder classes are slightly dependent on the problem input (removing negatives from values), but it's still fairly easy to convert to a any-width int list compressor if you wanted

- Tests are located at the bottom of the Compression file for ease of access and testing within pycharm 

- Function/Class specific clarifications commented inline 

-------------------------------------

### Algorithm / Encoder Explanations: 
#### Delta Encoding: 
- First:  **[Rewriting Array to deltas, to expose larger patterns]**
  - Array[i] = Array[i] - Array[i-1] (except for Array[0] which remains the same)
- Second:  **[Need to compensate for lack of negative integer support in Variable Length Bit Encoder]** 
  - Find the minimum in the newly created array (if not negative, set to zero) 
  - Add minimum to each element in the array inline, and append minimum to the front for storage

#### Run Length Encoder: 
- **(Length), (Value) for Run > 1, (Value) for Run = 1**
- **Run Lengths limited to 28 (values 100-127) for byte length efficiency**
  - Any values between 100-127, encode as [<Length> <Value>]
  - Length in storage = Run Length + 100 for ID purposes

#### Variable Length Bit Encoder: 
- **First bit in byte:  1 = Need more bits, 0 = No more bits**
- **Numbers encoded in little endian for simplicity**
- **Encoder built into RLE Class on insertion to RLE Array** 




