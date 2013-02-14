#!/usr/bin/python

'''
Created on Feb 12, 2013

@author: Saurabh Dingolia
'''

import sys
import os
import re
import math  
import itertools
from collections import Counter


def begin_msps():
  if (  sequences == None or len(sequences) == 0 or
        mis_values == None or len(mis_values) == 0  ):
    print 'Invalid data sequence or minimum support values'
    return;
  
  # Total no. of data sequences
  sequence_count = len(sequences)
  
  # Get the item support for each item i.e. sup(i)
  global actual_supports
  flattened_sequences = [ list(set(itertools.chain(*sequence))) for sequence in sequences ]
  support_counts = dict(Counter(item for flattened_sequence in flattened_sequences for item in flattened_sequence)) 
  actual_supports = {item:support_counts.get(item)/float(sequence_count) for item in support_counts.keys()}
  
  # Get the sorted list of frequent items i.e items with sup(i) >= MIS(i)
  frequent_items = sorted([item for item in actual_supports.keys() if actual_supports.get(item) >= mis_values.get(item)],key=mis_values.get)
  
#  print flattened_sequences 
#  print frequent_items

  # Iterate through frequent items to get sequential patterns  
  for item in frequent_items:
    # Get the sequences containing that item and filter them to remove elements that do not satisfy SDC i.e. |sup(j) - sup(item)| > sdc 
    print "Current item:",item,'-----------------------------------------------'
    item_sequences = [sdc_filter_on_item(sequences[i], item, actual_supports.get(item)) for i in range(len(flattened_sequences)) if item in flattened_sequences[i]]
    
    # Get the minimum item support count for item i.e count(MIS(item))
    mis_count = int(math.ceil(mis_values.get(item)*len(item_sequences)))
    
    # Run the restricted Prefix-Span to get sequential patterns
    r_prefix_span(item, item_sequences, mis_count)


def sdc_filter_on_item(source_list, base_item, base_item_support):
  filtered_list = []    # Declare list to contain filter results
  
  # Recurse for each child list and append result to filtered list    
  if isinstance(source_list[0], list):
    for child_list in source_list:
      filtered_child_list = sdc_filter_on_item(child_list, base_item, base_item_support)    # Recurse for filtering each child_list
      if filtered_child_list:   # Append only the non-empty lists
        filtered_list.append(filtered_child_list)  
    
  else:   # Remove items that do not satisfy support difference constraint
    for item in source_list:
#      print "Item:",item,"Support:",item_supports.get(item),"Diff:",abs(item_supports.get(item) - base_item_support)
      if not item == base_item and abs(actual_supports.get(item) - base_item_support) > sdc:  # Item doesn't satisfy SDC
        continue
      else:   # Item satisfies SDC
        filtered_list.append(item)

  return filtered_list    # Return the filtered list from current recursion


def r_prefix_span(base_item, item_sequences, mis_count):
  sequential_patterns = []    # To hold the output frequent sequential patterns
  
  # Remove the infrequent items from the sequence database
  item_sequences = remove_infrequent_items(item_sequences, mis_count)
  print item_sequences
  
  # Add the base_item as a 1-length sequential pattern to the output database
  sequential_patterns.append([[base_item]])
  
  # Get the frequent items and length one frequent sequences from them
  frequent_items = list(set(itertools.chain(*(itertools.chain(*item_sequences)))))
  len_1_freq_sequences = [[[item]] for item in frequent_items]
#  print len_1_freq_sequences
  for freq_sequence in len_1_freq_sequences:
    print "Pattern:",freq_sequence
    prefix_span(freq_sequence, 1, item_sequences, base_item, mis_count)
  

def prefix_span(prefix, prefix_length , item_sequences, base_item, mis_count):    
  projected_db = []
  
  for sequence in item_sequences:
    cur_pr_itemset = cur_sq_itemset = 0
    
    while cur_pr_itemset < len(prefix) and cur_sq_itemset < len(sequence):
      if contains(sequence[cur_sq_itemset], prefix[cur_pr_itemset]):
        cur_pr_itemset += 1
      else:
        cur_sq_itemset += 1
    
    if cur_pr_itemset == len(prefix):
      projected_sequence = project_sequence(prefix[-1][-1], sequence[cur_sq_itemset:])
      if projected_sequence:
        projected_db.append(projected_sequence)
  
  print projected_db
  
  if not has_item(prefix, base_item):
    projected_db = [projected_sequence for projected_sequence in projected_db if has_item(projected_sequence, base_item)]
        
  print projected_db
  sdc_filter(projected_db)


def sdc_filter(source_list):
  s =1


def project_sequence(prefix_last_item, suffix):
  if prefix_last_item == suffix[0][-1]:
    return suffix[1:]
  else:
    suffix[0] = ['_'] + suffix[0][suffix[0].index(prefix_last_item)+1:]
    return suffix

def contains(big, small):
  return len(set(big).intersection(set(small))) == len(small)


def has_item(source_list, item):
  while isinstance(source_list[0], list):
    source_list = list(set(itertools.chain(*source_list)))
    
  return item in source_list  


def remove_infrequent_items(item_sequences, min_support_count):
  # Get the support count for each item in supplied sequence database
  flattened_sequences = [ list(set(itertools.chain(*sequence))) for sequence in item_sequences ]
  support_counts = dict(Counter(item for flattened_sequence in flattened_sequences for item in flattened_sequence))
  
  # Remove the infrequent items from the sequence database  
  filtered_item_sequences = [[[item for item in itemset if support_counts.get(item) >= min_support_count]for itemset in sequence] for sequence in item_sequences]
  
  # Remove the empty itemsets
  filtered_item_sequences = [[itemset for itemset in sequence if itemset] for sequence in filtered_item_sequences]
  return filtered_item_sequences    # Return the new sequence database
    
  
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