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


def main():
  args = sys.argv[1:]   # Get the arguments
  
  if not args or not len(args) == 4:
    _exit()
    
  if ( not args[0] == '--data' or not os.path.isfile(args[1]) or 
       not args[2] == '--sup' or not os.path.isfile(args[3]) ):
    _exit()
    
  # Define global variables
  global output_patterns, sdc
  output_patterns = []    # To hold the output frequent sequential patterns
  
  # Read the data file
  in_file = open(args[1], 'rU')
  text = in_file.read();
  in_file.close()
  
  # Parse the data in_file to create nested list of data sequences
  text = text.replace('<{', '').replace('}>', '')
  sequences = text.split("\n")
  sequences = [ sequence.split("}{") for sequence in sequences if sequence]
  sequences = [[[item.strip() for item in itemset.split(",")] for itemset in sequence] for sequence in sequences]

  # Read the support file
  in_file = open(args[3], 'rU')
  text = in_file.read()
  in_file.close()
  
  # Parse the support in_file to create support dict and retrieve support difference constraint
  mis_values = { match[0]: float(match[1]) for match in re.findall(r'MIS\((\w+)\)\s+=\s+(\d*\.?\d*)', text) }
  sdc = float(re.search(r'SDC\s=\s(\d*\.?\d*)', text).group(1))
  
  # Run the Multiple Support Prefix Span algorithm
  begin_msps(sequences, mis_values, sdc)


def _exit(message=None):
  if message == None:
    message = 'usage: --data datafile --sup supportfile'
  print message
  sys.exit(1)
  

def begin_msps(sequences, mis_values, sdc):
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
  del flattened_sequences
  
  # Get the sorted list of frequent items i.e items with sup(i) >= MIS(i)
  frequent_items = sorted([item for item in actual_supports.keys() if actual_supports.get(item) >= mis_values.get(item)],key=mis_values.get)
  
#  print flattened_sequences 
#  print frequent_items


  # Iterate through frequent items to get sequential patterns
  for item in frequent_items:
    # Get the minimum item support count for item i.e count(MIS(item))
    mis_count = int(math.ceil(mis_values.get(item)*len(sequences)))
    
#    print "Current item:",item,'-----------------------------------------------',"MIS:",mis_count, "Sup:",support_counts.get(item)
       
    # Get the sequences containing that item and filter them to remove elements that do not satisfy SDC i.e. |sup(j) - sup(item)| > sdc
    item_sequences = [sdc_filter_on_item(sequence, item, actual_supports.get(item), actual_supports, sdc) for sequence in sequences if has_item(sequence, item)]
#    print "ItemSeq:", item_sequences
    
    # Run the restricted Prefix-Span to get sequential patterns
    r_prefix_span(item, item_sequences, mis_count)
    
    # Remove the item from original sequences
    sequences = remove_item(sequences, item)
    
  # End of the mining algorithm, print output
  write_output(output_patterns)


def write_output(output_list):
  output_list = sorted(output_list,key=pattern_length)
  output_text = ''
  
  cur_length = 1
  
  while True:
    cur_length_patterns = filter (lambda a: pattern_length(a) == cur_length, output_list)
    if not cur_length_patterns:
      break
    
    output_text += "The number of length " + str(cur_length) + " sequential patterns is " + str(len(cur_length_patterns)) + "\n"
    
    for (pattern,sup_count) in cur_length_patterns:
      str_pattern = "<{" + "}{".join([item for itemset in pattern for item in itemset]) + "}>"
      output_text += "Pattern: " + str_pattern + " Count: " + str(sup_count) + "\n"
    
    cur_length += 1
    
    output_text += "\n"
  
  print output_text
    
      
def pattern_length(output_tuple):
  output_list = output_tuple[0]
  
  while isinstance(output_list[0], list):
    output_list = list(itertools.chain(*output_list))
  
  return len(output_list)


def remove_item(source_list, item_to_del):
  filtered_list = []    # Declare list to contain filter results
  
  # Check to see if list has sub lists as items   
  if source_list and isinstance(source_list[0], list):
    
    for child_list in source_list:
      filtered_child_list = remove_item(child_list, item_to_del)    # Recurse for filtering each child_list
      
      if filtered_child_list:   # Append only non-empty lists
        filtered_list.append(filtered_child_list)  
    
  else:   # Remove item from the list
    filtered_list = filter (lambda a: a != item_to_del, source_list)

  return filtered_list    # Return the filtered list from current recursion
  
  
def sdc_filter_on_item(source_list, base_item, base_item_support, supports, sdc):
  filtered_list = []    # Declare list to contain filter results
  
  # Check to see if list has sub lists as items    
  if source_list and isinstance(source_list[0], list):
    for child_list in source_list:
      filtered_child_list = sdc_filter_on_item(child_list, base_item, base_item_support, supports, sdc)    # Recurse for filtering each child_list
      if filtered_child_list:   # Append only the non-empty lists
        filtered_list.append(filtered_child_list)  
    
  else:   # Remove items that do not satisfy support difference constraint
    for item in source_list:
#      print "Item:",item,"Support:",item_supports.get(item),"Diff:",abs(item_supports.get(item) - base_item_support)
      if not item == base_item and abs(supports.get(item) - base_item_support) > sdc:  # Item doesn't satisfy SDC
        continue
      else:   # Item satisfies SDC
        filtered_list.append(item)

  return filtered_list    # Return the filtered list from current recursion


def r_prefix_span(base_item, item_sequences, mis_count):
  # Remove the infrequent items from the sequence database
#  item_sequences = remove_infrequent_items(item_sequences, mis_count)
  
  # Get the frequent items and construct length one frequent sequences from them
  freq_item_sequences = remove_infrequent_items(item_sequences, mis_count)
  frequent_items = list(set(itertools.chain(*(itertools.chain(*freq_item_sequences)))))
  del freq_item_sequences
  
  # Get length-1 frequent sequences
  len_1_freq_sequences = [ [[item]] for item in frequent_items ]
  
  # Add the base_item 1-length sequential pattern to the output database
  if has_item(len_1_freq_sequences, base_item):
    output_patterns.append(([[base_item]], support_count(item_sequences, base_item)))
      
  for freq_sequence in len_1_freq_sequences:
    prefix_span(freq_sequence, item_sequences, base_item, mis_count)
  

def prefix_span(prefix, item_sequences, base_item, mis_count):
#  print "Prefix:",prefix
      
  # Compute the projected database for the current prefix
  projected_db = compute_projected_database(prefix, item_sequences, base_item, mis_count)
#  print "DB:", projected_db
  
  # Find the prefix_length + 1 sequential patterns 
  if projected_db:    # Check if the projected database has any sequences
    prefix_last_itemset = prefix[-1]
    all_template_1_items = []
    all_template_2_items = []
    
    for proj_sequence in projected_db:
      itemset_index = 0
      template_1_items = []
      template_2_items = []
      
      while itemset_index < len(proj_sequence):
        cur_itemset = proj_sequence[itemset_index]
        
        if has_item(cur_itemset, '_'):
          template_1_items += cur_itemset[1:]
        
        else:
          if contains(cur_itemset, prefix_last_itemset):
            template_1_items += cur_itemset[cur_itemset.index(prefix_last_itemset[-1])+1:]
          
          template_2_items += cur_itemset  
        
        itemset_index += 1
      
#      print "T 1 items:@@",  
#      print template_1_items
#        
#      print "T 2 items:@@",
#      print template_2_items 
      
      all_template_1_items += list(set(template_1_items))
      all_template_2_items += list(set(template_2_items))
      
    dict_template_1 = dict(Counter(item for item in all_template_1_items))
    dict_template_2 = dict(Counter(item for item in all_template_2_items))
    
#    print "T 1 items:@@",  
#    print dict_template_1
#    
#    print "T 2 items:@@",
#    print dict_template_2 
    
    sequential_patterns = []
    
    for item, sup_count in dict_template_1.iteritems():
      if sup_count >= mis_count:
        sequential_patterns.append((prefix[:-1] + [prefix[-1] + [item]], sup_count))
    
    for item, sup_count in dict_template_2.iteritems():
      if sup_count >= mis_count:
        sequential_patterns.append((prefix + [[item]], sup_count))
    
#    print "SQ Patterns:@@"
#    print sequential_patterns  
        
    for (seq_pattern, sup_count) in sequential_patterns:
      output_patterns.append((seq_pattern, sup_count))
      prefix_span(seq_pattern, item_sequences, base_item, mis_count)
      
    
def compute_projected_database(prefix, item_sequences, base_item, mis_count):
  projected_db = []
  
  for sequence in item_sequences:
    cur_pr_itemset = 0
    cur_sq_itemset = 0
    
    while cur_pr_itemset < len(prefix) and cur_sq_itemset < len(sequence):
      if contains(sequence[cur_sq_itemset], prefix[cur_pr_itemset]):
        cur_pr_itemset += 1
        if cur_pr_itemset == len(prefix): break
      
      cur_sq_itemset += 1
    
    if cur_pr_itemset == len(prefix):
      projected_sequence = project_sequence(prefix[-1][-1], sequence[cur_sq_itemset:])
      if projected_sequence:
        projected_db.append(projected_sequence)
  
  # Remove the sequences that do not contain the base item if the prefix does not contain the base item
    if not has_item(prefix, base_item):
      projected_db = [projected_sequence for projected_sequence in projected_db if projected_sequence and has_item(projected_sequence, base_item)]
  
  # Remove the infrequent items
  projected_db = remove_infrequent_items(projected_db, mis_count)
  
  # Check if any frequent items are left
  validation_db = remove_empty_elements([[[item for item in itemset if not item == '_'] for itemset in sequence] for sequence in projected_db])
  
  if validation_db:
    # Remove sequences that do not satisfy SDC
    projected_db = sdc_filter(projected_db)
    
    return remove_empty_elements(projected_db)
  
  else:
    return validation_db
    
    
def project_sequence(prefix_last_item, suffix):
    suffix_first_itemset = suffix[0]
    if prefix_last_item == suffix_first_itemset[-1]:
      return suffix[1:]
    else:
      suffix_first_itemset = ['_'] + suffix_first_itemset[suffix_first_itemset.index(prefix_last_item)+1:]
      return suffix
  

def support_count(sequences, req_item):
  flattened_sequences = [ list(set(itertools.chain(*sequence))) for sequence in sequences ]
  support_counts = dict(Counter(item for flattened_sequence in flattened_sequences for item in flattened_sequence))
  
  return support_counts.get(req_item)

  
def contains(big, small):
  return len(set(big).intersection(set(small))) == len(small)


def has_item(source_list, item):
  if source_list:
    while isinstance(source_list[0], list):
      source_list = list(itertools.chain(*source_list))
    
    return item in source_list  
  return False


def sdc_filter(projected_database):
  filtered_database = [[itemset for itemset in sequence if is_sdc_satisfied(itemset)] for sequence in projected_database]
#  flattened_sequences = [ list(set(itertools.chain(*sequence))) for sequence in projected_database ]
#  filtered_database = [sequence for i,sequence in enumerate(projected_database) if is_sequence_sdc_satisfied(flattened_sequences[i])]  
  return filtered_database


def is_sdc_satisfied(itemset):
  if not itemset:
    return False
  
  for item1 in itemset:
    sup_item1 = actual_supports.get(item1)
    for item2 in itemset:
      if abs(sup_item1 - actual_supports.get(item2)) > sdc:
        return False
      
  return True


def is_sequence_sdc_satisfied(sequence):
  if not sequence:
    return False
  
  for item1 in sequence:
    sup_item1 = actual_supports.get(item1)
    for item2 in sequence:
      if abs(sup_item1 - actual_supports.get(item2)) > sdc:
        return False
      
  return True        
        

def remove_infrequent_items(item_sequences, min_support_count):
  # Get the support count for each item in supplied sequence database
  flattened_sequences = [ list(set(itertools.chain(*sequence))) for sequence in item_sequences ]
  support_counts = dict(Counter(item for flattened_sequence in flattened_sequences for item in flattened_sequence))
  
  # Remove the infrequent items from the sequence database  
  filtered_item_sequences = [[[item for item in itemset if support_counts.get(item) >= min_support_count]for itemset in sequence] for sequence in item_sequences]
  
  return remove_empty_elements(filtered_item_sequences)    # Return the new sequence database
    

def remove_empty_elements(source_list):
  filtered_list = []    # Declare list to contain filter results
  
  # Check to see if list has sub lists as items   
  if source_list and isinstance(source_list[0], list):
        
    for child_list in source_list:
      filtered_child_list = remove_empty_elements(child_list)    # Recurse for filtering each child_list
      
      if filtered_child_list:   # Append only non-empty lists
        filtered_list.append(filtered_child_list)
  
  else:
    filtered_list = source_list 
   
  return filtered_list    # Return the filtered list from current recursion

  
if __name__ == '__main__':
  main()  