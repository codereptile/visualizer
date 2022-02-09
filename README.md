# visualizer (v1.1.3a)

This project aims to make a quick visual representation for a C++ project (though Python support is planned).

Possible use-cases:

* Showing visual representation of different code structures for teaching
* Code dependency analysis
* Per-function code structure analysis.
* (PLANNED) Performance analyzing
* (PLANNED) Unit-test and security analysis

# Instalation:
```
sudo apt install llvm
sudo apt install libclang-11-dev
```

# General usage:

```shell
python3 visualizer.py cpp --target examples/segment_tree --scale 0.5
```

You can also use `--bruteforce 1` to avoid errors.

## Keyboard control:

UP, DOWN, LEFT, RIGHT - move respectively

0 - increase size (zoom in)

9 - decrease size (zoom out)

## About colors:

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

# What's new in v1.1.3?
* OMG, FINALLY RESIZE!!! (literally took 10 min to implement, no idea why didn't do it earlier)
* OMG, FINALLY MOVE AROUND!!! (literally took another 10 min to implement, no idea why didn't do it earlier)

Alpha patch:

* Reduced number of line segments when drawing a curve, improved performance x2, almost not noticeable.
* Various code improvements
* Added FPS meter to verbose mode

# Known bugs // missing features:
* Function calls inside Loop and If conditions are not registered
* No way to see actual code from visualizer
* Function arguments not registered
* Python support is yet to come
* No way to see how many times a function is called from a single line
* No support for outside-of-function code
* No way to resize/move in editor
* It's hard to tell code structure if there are many If statements
* Class / struct constructors are not registered as function calls
* **If an included library is not found, some code may be absent!!! (this can be partually avoided by commenting the problematic include)**
* No way to add libraries that shouldn't be rendered
* No switch case support
* Operator calls are not detected, even if they are user-defined
* On large projects moving/resizing is quite CPU-intensive and takes significant time (projects of around 1500 lines of code are rendered at around 7-8 FPS) 