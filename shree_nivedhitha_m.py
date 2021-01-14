import numpy as np  # Recommended for vector calculations
#from geopy.geocoders import Nominatim
from geopy.distance import geodesic
#import pandas as pd


# Shree Nivedhitha M
def find_best_school(houses, schools):
    # Inputs: Array of coordinate-tuples (latitude, longitude in degrees) for all houses and all schools.
    # Output: Array of the index of the nearest school for each house.
    # This is a place-holder function that returns a random output. Please modify this function.
    ls=[]
    for i in range(len(houses)):
      mini=12800
      for j in range(len(schools)):
        try:
          dis=geodesic(houses[i], schools[j]).km
          if (dis<mini):
            mini = dis 
            ind=j
        except:
          print("error")
          pass         
      ls.append(ind)
    print(ls)
    return np.array(ls)
 

def basic_test(my_function):
    # Demo input, do not round. Locations are given in (latitude, longitude) pairs (in degrees). It is not the same as cartesian coordinates (x,y)
    houses = [(28.1, 78), (13, 78), (13, 26), (28, 76)]
    schools = [(28, 77), (13, 77), (20, 68)]
    answer = [0, 1, 2, 0]
    output = my_function(houses, schools)
    try:
        print("Basic Score: {:0.2%}".format((np.array(answer) == output).mean()))
    except:
        print("Error: give the index of nearest school for each house in the list")
 
"""
We have some automated tests similar to the basic_test above, that judge speed and accuracy on 1000 houses and 1000 schools.
The best solution is accurate, fast, with low memory use and short, in that order. (Accuracy in finding the nearest school correctly)
It is good to use common libraries like numpy, scipy etc than writing extra lines of code (as long as the speed does not reduce).
Make sure your function can fit inside a single cell of Google Colab Notebook (colab.research.google.com).
"""
 
basic_test(find_best_school)
# Aim for 100% score. #StackBOX
# This document is the intellectual property of StackBOX (stackbox.xyz). Do not publish this question or its solutions online.
