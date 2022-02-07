# visualizer (v1.0.0)

Right now the app is in alpha testing, so:
* No docs
* No warranties
* No proper UI
* Strange debug output all over the place
* Anything can change at any moment without notice, so pls don't use this in life-critical applications

# Instalation:
```
sudo apt install llvm
sudo apt install libclang-11-dev
```

# General usage:

```shell
python3 visualizer.py cpp --target examples/segment_tree --scale 0.5
```

```
Loops are Red,
Code lines are Blue,
Sugar is Sweet,
And so are you.
```
Btw, Functions are Grey, Ifs are green with a black line separating main statement and else.
All other black lines are function calls.

# Examples:

## [Segment tree](https://github.com/codereptile/visualizer/blob/main/examples/segment_tree/code.cpp):

![screenshot](https://github.com/codereptile/visualizer/blob/main/examples/segment_tree/image.webp)

# FAQ:


What are you using for parsing C++?
 
&mdash; Clang


Why not use `<insert your favorite C++ parser>`? 

&mdash;Because parsing C++ propely requires almost compiling it, 
so only by using a compiler can we get a 100% correct output.
Easiest example is `operator <<` which in most parsers is registered as a `binary expression`, when in reality it is a `function call`. 

# Known bugs // missing features:
* Function calls inside Loop and If conditions aer not registered
* No way to see actual code from visualizer
* Function arguments not registered
* Python support is yet to come
* No way to see how many times a function is called from a single line
* No support for outside-of-function code
* No way to resize/move in editor
* Cross-file function scan is not implemented yet
* No class support
* No struct support
* 5000 tonnes of useless debug output with no way to shut it off
* It's hard to tell code structure if there are many If statements
* Class constructors are not registered as function calls
* If a function is defined in .h, it's not detected