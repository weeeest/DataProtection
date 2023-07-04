from itertools import combinations
import pandas as pd
import itertools
import copy
import uuid


class NoGeneralization(Exception):
  pass

# class NotImplemented(Exception)

class ValueGeneralization:

  def __init__(self, level) :
    self.level = level

  def generalize(self, value):
    raise NotImplementedError

  def __copy__(self):
    result = self.__class__(self.level)
    result.__dict__.update(self.__dict__)

    return result

  def __deepcopy__(self, memo=None):
    result = self.__class__(self.level)
    result.__dict__ = copy.deepcopy(self.__dict__)
    return result

  def __str__(self):
    attributes = [f"{key}={getattr(self, key)}" for key in self.__dict__]
    return f"Node({', '.join(attributes)})"

class Gender(ValueGeneralization):

  def generalize(self, value):
    if self.level == 0:
      return value
    elif self.level == 1:
      return 'p'
    else:
      raise NoGeneralization("The level is not defined")

class Customer_Age(ValueGeneralization):

  def generalize(self, value):
    if self.level == 0:
      return value
    elif self.level == 1:
      return self.first_level_generalize(value)
    else:
      raise NoGeneralization("The level is not defined")

  def first_level_generalize(self, value):
    if int(value) >= 0 and int(value) < 20:
      return '0 - 20'
    if int(value) >= 20 and int(value) < 30:
      return '20 - 30'
    if int(value) >= 30 and int(value) < 40:
      return '30 - 40'
    if int(value) >= 40 and int(value) < 50:
      return '40 - 50'
    if int(value) >= 60:
      return '60 + '

class Income(ValueGeneralization):

  def generalize(self, value):
    if self.level == 0:
      return value
    elif self.level == 1:
      return self.first_level_generalize(value)
    else:
      raise NoGeneralization("The level is not defined")

  def first_level_generalize(self, value):
    if int(value) >= 0 and int(value) < 40000:
      return '0 - 40k'
    if int(value) >= 40000 and int(value) < 60000:
      return '40k - 60k'
    if int(value) >= 60000 and int(value) < 80000:
      return '60k - 80k'
    if int(value) >= 80000 and int(value) < 100000:
      return '80k - 100k'
    if int(value) >= 100000 and int(value) < 120000:
      return '100k - 120k'
    if int(value) >= 120000:
      return '120k + '

class Zipcode(ValueGeneralization):

  def generalize(self, value):
    if self.level == 0:
      return value
    elif self.level == 1:
      return self.first_level_generalize(value)
    elif self.level == 2:
      return self.second_level_generalize(value)
    elif self.level == 3:
      return self.third_level_generalize(value)
    else:
      raise NoGeneralization("The level is not defined")

  def first_level_generalize(self, value):
    return str(value)[:-1] + '*'

  def second_level_generalize(self, value):
    return str(value)[:-2] + '**'

  def third_level_generalize(self, value):
    return str(value)[:-3] + '***'

# Q = ['Gender', 'Customer_Age', 'Income', 'Zipcode' ]

def get_frequenct_set(df, columns):
  return df.groupby(columns).size()

def is_K_Anonymous(df, q, k):
  frequency = get_frequenct_set(df, q)
  for fr in frequency:
    if fr < k:
      return False
  return True

class Node:
  def __init__(self):
    self.id = uuid.uuid4()
    self.anonymized = False
    self.marked = False
    self.direct_nodes = []
    self.height = 0

  def __copy__(self):
    result = Node()
    result.__dict__ = copy.copy(self.__dict__)
    result.id = uuid.uuid4()
    return result

  def __deepcopy__(self, memo=None):
    result = Node()
    result.__dict__= copy.deepcopy(self.__dict__)
    result.id = uuid.uuid4()
    return result

  def __str__(self):
    attributes = [f"{key}={str(getattr(self, key))}" for key in self.__dict__]
    return f"Node({', '.join(attributes)})"

def is_direct_generalization(n1, n2, columns):
  one_diff = False
  for column in columns:
    level_diff = getattr(n2, column).level - getattr(n1, column).level
    if level_diff == 1 and not one_diff:
      one_diff = True
    elif level_diff != 0:
      return False

  return True

def add_direct_generalization(nodes, columns):
  for n1 in nodes:
    n1.direct_nodes = []
    for n2 in nodes:
      if n1.id == n2.id:
        continue
      if is_direct_generalization(n1, n2, columns):
        n1.direct_nodes.append(n2.id)

  return nodes

def create_hirarchy(generalization_combination, columns):
  result = []
  node = None
  height = 0
  indexes = [list(range(generalization_combination[key] +1 )) for key in columns]
  combinations = list(itertools.product(*indexes))
  for combination in combinations:
    node = Node()
    for i in range(len(columns)):
      setattr(node, columns[i], globals()[columns[i]](combination[i]))

    result.append(node)

  return add_direct_generalization(result, columns)

def generalize_row(row, node, columns):
  for column in columns:
    row[column] = getattr(node, column).generalize(row[column])

  return row

def mark_direc_generalization(nodes, node):
  for n in nodes:
    if n.id in node.direct_nodes:
      n.is_marked = True
  return nodes

def incognito(df, k, Q, generalization_combination):
  n = len(Q)
  nodes = []
  S = [[] for _ in range(n)]
  columns  = []
  for i in range(1, len(Q) + 1):
    column_combination = [list(comb) for comb in combinations(Q, i)]
    # for each size of possible Q for example at first try to one, two and so on untile size of attributes
    for columns in column_combination:
      nodes = create_hirarchy(generalization_combination, columns)
      for node in nodes:
        if not node.marked:
          node.marked = True
          new_df = df.apply(generalize_row, args=(node,columns), axis=1)
          if is_K_Anonymous(new_df, columns, k):
            node.anonymized = True
            S[i].append(node)
            for n in nodes:
              if n.id in node.direct_nodes:
                n.is_marked = True
                S[i].append(n)


  return S


if __name__ == "__main__":
	df = pd.read_csv('BankChurners_real.csv')

	Q = ['Gender', 'Customer_Age', 'Income', 'Zipcode' ]
	generalization_combination = {'Gender' : 1, 'Customer_Age' : 1, 'Income' : 1, 'Zipcode' : 3}

	s = incognito(df, 2, Q, generalization_combination )
	for _ in s:
  		for d in _:
   			print(d)