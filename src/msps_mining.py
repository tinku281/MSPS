#!/usr/bin/python

'''
Created on Feb 12, 2013

@author: Saurabh Dingolia
'''

import sys
import os
import re
import math


def begin_msps():
  if (  sequences == None or len(sequences) == 0 or
        mis_values == None or len(mis_values) == 0  ):
    print 'Invalid data sequence or minimum support values'
    return;
  
  # Total no. of data sequences
  sequence_count = len(sequences)
  
  # Import statements
  import itertools
  from collections import Counter

  # Get the item support for each item i.e. sup(i)
  global item_supports
  flattened_sequences = [ list(set(itertools.chain(*sequence))) for sequence in sequences ]
  support_counts = dict(Counter(item for flattened_sequence in flattened_sequences for item in flattened_sequence)) 
  item_supports = {item:support_counts.get(item)/float(sequence_count) for item in support_counts.keys()}
  
  # Get the sorted list of frequent items i.e items with sup(i) >= MIS(i)
  frequent_items = sorted([item for item in item_supports.keys() if item_supports.get(item) >= mis_values.get(item)],key=mis_values.get)
  
#  print flattened_sequences 
#  print frequent_items
#  print support_counts
  
  # Get the minimum item support count for each item
#  mis_counts = {item:int(math.ceil(mis_values.get(item)*sequence_count)) for item in mis_values.keys()}
  
  for item in frequent_items:
    print "Current item:",item,"Support:",str(item_supports.get(item))
    item_sequences = [sdc_filter(sequences[i], item, item_supports.get(item)) for i in range(len(flattened_sequences)) if item in flattened_sequences[i]]
    print item_sequences
    mis_count = int(math.ceil(mis_values.get(item)*sequence_count))
    r_prefix_span(item, item_sequences, mis_count)


def r_prefix_span(item, item_sequences, min_count):
  s = 1
  

def find_frequent_items(item_sequences, min_support):
  s = 3
    
def sdc_filter(source_list, base_item, base_item_support):
  filtered_list = []    # Declare list to contain filter results
  
  # Recurse for each child list and append result to filtered list    
  if isinstance(source_list[0], list):
    for child_list in source_list:
      filtered_child_list = sdc_filter(child_list, base_item, base_item_support)
      if filtered_child_list:
        filtered_list.append(filtered_child_list)  
    
  else:   # Remove items that do not satisfy support difference constraint
    for item in source_list:
      print "Item:",item,"Support:",item_supports.get(item),"Diff:",abs(item_supports.get(item) - base_item_support)
      if not item == base_item and abs(item_supports.get(item) - base_item_support) > sdc:
        continue
      else:
        filtered_list.append(item)

  return filtered_list    # Return the filtered list from current recursion


def main():
  args = sys.argv[1:]   # Get the arguments
  
  if not args or not len(args) == 4:
    _exit()
    
  if ( not args[0] == '--data' or not os.path.isfile(args[1]) or 
       not args[2] == '--sup' or not os.path.isfile(args[3]) ):
    _exit()
    
  # Define global variables to hold data sequences, MIS values and SDC
  global sequences, mis_values, sdc
  sequences = []
  mis_values = {}
  sdc = 0
  
  # Read the data file
  file = open(args[1], 'rU')
  text = file.read();
  file.close()
  
  # Parse the data file to create nested list of data sequences
  text = text.replace('<{', '').replace('}>', '')
  sequences = text.split("\n")
  sequences = [ sequence.split("}{") for sequence in sequences if sequence]
  sequences = [[[item.strip() for item in itemset.split(",")] for itemset in sequence] for sequence in sequences]

  # Read the support file
  file = open(args[3], 'rU')
  text = file.read()
  file.close()
  
  # Parse the support file to create support dict and retrieve support difference constraint
  mis_values = { match[0]: float(match[1]) for match in re.findall(r'MIS\((\w+)\)\s+=\s+(\d*\.?\d*)', text) }
  sdc = float(re.search(r'SDC\s=\s(\d*\.?\d*)', text).group(1))
  
  # Run the Multiple Support Prefix Span algorithm
  begin_msps()


def _exit(message=None):
  if message == None:
    message = 'usage: --data datafile --sup supportfile'
  print message
  sys.exit(1)

  
if __name__ == '__main__':
  main()  