# Mathmax

Mathmax is a calculator application for Windows designed specifically for blind users. It supports both basic and advanced mathematical operations.

## Language Support
- German (primary interface)
- English

## Get Started
- Download the latest version:  
  [Releases page](https://github.com/jokyboy129/Mathmax/releases)
- Try the web version:  
  [Here](https://jokyboy129.github.io/Mathmax/ui)

## Features

### Basic Operations
- Addition: `+`
- Subtraction: `-`
- Multiplication: `*`
- Division: `/`
- Full support for parentheses

### Solving Equations
- Syntax:
  `nsolve(equation; min; max)`
- Example:
  `nsolve(3x + 4; -20; 20)`
- `min` and `max` define the interval in which solutions are searched
- Default range: `-20` to `20`

### Derivatives
- Compute derivative function:
  `algs(function; degree)`
- Compute derivative at a point:
  `nderive(function; point; degree)`
- Example:
  `nderive(3x^2 + 2; 1; 1)`

### Statistics
- Minimum: `min(1; 2; 3; ...)`
- Maximum: `max(1; 2; 3; ...)`
- Mean: `mittel(1; 2; 3; ...)`
- Standard deviation: `sd(1; 2; 3; ...)`

### Function Handling
- Define a function:
  `def f(x): equation`
- Show a function:
  `show f(x)`
- Delete a function:
  `deldef f`

### Trigonometry
- `sin()`, `cos()`, `tan()`
- `asin()`, `acos()`, `atan()`

### Additional Math Features
- Built-in constants: `pi`, `e`
- Factorial: `!`
- Powers: `^`
- Square root: `sqrt()`
- General root: `root(number; degree)`

### Combinatorics & Probability
- Binomial coefficient:
  `binco(n; k)`
- Binomial distribution:
  `binom(n; p; k)`
- Cumulative binomial distribution:
  `cbinom(n; p; k)`