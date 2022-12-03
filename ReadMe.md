# String Obfuscator

### Usage

```bash
usage: strobj [-h] [-l MIN_OPS] [-u MAX_OPS] [-b MAX_BITS] -t LANG [-i INPUT | -f FILE | -s]                                                                                                           
                                                                                                                                                                                                       
Obfuscates a string using a polymorphic engine into different languages. Generates a decryption/deobfuscation routine in any of the following in the target languages (which can be specified to the -t
or --target parameter): bash, c#, c_sharp, csharp, c, cpp, c++, javascript, js, java, masm64, powershell, ps, python, py                                                                               
                                                                                                                                                                                                       
optional arguments:                                                                                                                                                                                    
  -h, --help            show this help message and exit                                                                                                                                                
  -l MIN_OPS, --min-ops MIN_OPS                                                                                                                                                                        
                        minimum number of transformations                                                                                                                                              
  -u MAX_OPS, --max-ops MAX_OPS                                                                                                                                                                        
                        maximum number of transformations                                                                                                                                              
  -b MAX_BITS, --max-bits MAX_BITS                                                                                                                                                                     
                        number of bits to encode chars into                                                                                                                                            
  -t LANG, --target LANG                                                                                                                                                                               
                        language to encode decryption routine
  -i INPUT, --input INPUT
                        text to encrypt
  -f FILE, --file FILE  read from input file
  -s, --stdin           read from stdin

```

### Examples

```bash
# Read from stdin
cat .\file.txt | python3 strobf.py -s -t "ps"

# Read from file
python3 strobf.py -f .\file.txt -t "ps"

# Read from input
python3 strobf.py -t "ps" -i "Hello World!"
```