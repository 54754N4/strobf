# String Obfuscator

```bash
# Read from stdin
cat .\ReadMe.md | python3 strobf.py -s -t "ps"

# Read from file
python3 strobf.py -f .\ReadMe.md -t "ps"

# Read from input
python3 strobf.py -t "ps" -i "Hello World!"
```