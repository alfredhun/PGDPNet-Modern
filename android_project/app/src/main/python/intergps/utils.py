import math
import sys
from math import sqrt, sin, pi

def isNumber(number):
    try:
        float(number)
        return True
    except:
        return False

def hasNumber(lst):
    for number in lst:
        try:
            float(number)
            return True
        except:
            pass
    return False

def heron_triangle_formula(a, b, c):
    s = (a + b + c) / 2
    return sqrt(s * (s - a) * (s - b) * (s - c))

def angle_area_formula(a, b, angle):
    return 0.5 * a * b * sin(pi / 180.0 * angle)
