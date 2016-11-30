import random
import pdb
import threading

import logging

class Chaintip:
  def __init__(self):
    self.biggestblock

class Block:
  """Models a block in the bitcoin blockchain"""    
  def __init__(self,size,parent=None,height=0,createNum=0):
    self.size = size             # How big is the block
    self.height = height         # Block height -- how many blocks precede this one
    self.children = []           
    self.parent = parent         # Reference this block's parent
    self.biggestSize = max(self.parent.biggestSize if self.parent else size, size)
    self.b = createNum           # A unique count describing the order of block creation across the entire simulation
    self.chainMarker = 0              # This marker can be used by algorithms that iterate thru the blockchain
    createNum+=1

  def __str__(self):
    return "h: %d size: %d" % (self.height, self.biggestSize)


class Blockchain:
  def __init__(self):
    self.createNum=0
    self.start = Block(0,createNum=0)
    self.tips = set([self.start])

  def getForkLengths(self):
    ret = []
    tipList = list(self.tips)
    tipList.sort(key = lambda x: x.height, reverse=True)  # Sort by newest blocks
    chainNum = 0
    for t in tipList:  # Go thru every tip from newest block to less new blocks
      chainNum += 1
      length = 0
      block = t
      while block.parent and block.chainMarker==0:  # if there is a parent not on another chain, loop
        block.chainMarker = chainNum
        length += 1
        block = block.parent
      ret.append(length)
    return ret


  def getTip(self,eb,ad):
    tips = []
    for tip in self.tips:
      if tip.biggestSize <= eb:
        tips.append(tip)
      else:
        pos = tip
        skip=False
        for i in range(0,ad):
          pos = pos.parent
          if pos.biggestSize <= eb:  # haven't gone far enough to exceed AD
            tips.append(pos)
            skip=True
            break
	if (not skip) and pos.biggestSize >= eb:  # accept depth exceeded
          tips.append(tip)
    tips = sorted(tips,key=lambda x: x.height, reverse=True)
    # TODO random if tips are =
    return tips[0]

  def extend(self,blk,size):
    self.createNum+=1
    t = Block(size,blk, blk.height+1,createNum=self.createNum)
    blk.children.append(t)
    self.tips.discard(blk)
    self.tips.add(t)

  def printChain(self,block,offset):
    recurse = []
    print " "*offset,
    while block:
      s = "->h%ds%db%d" % (block.height,block.size/1000000,block.b)
      print s,
      offset += len(s)+1
      if len(block.children)>1:
        for c in block.children[1:]:
          recurse.append((c,offset))
      if len(block.children): block = block.children[0]
      else: break
    print
    for r in recurse:
      self.printChain(r[0], r[1])
   

  def p(self):
    print "TIPS:"
    t = list(self.tips)
    t.sort(cmp = lambda x,y: x.height < y.height)
    for tip in t:
      print str(tip)

class Miner:
  def __init__(self, hashpct, eb,ad, gensize, blockchain=None):
    """constructor, pass the hash as a fraction of 1, the excessive block size, the accept depth, the generation size, and the blockchain"""
    self.hashpct = hashpct
    self.excessive = eb                 # BU's excessive block parameter
    self.acceptdepth = ad               # BU's accept depth parameter
    self.blockchain = blockchain        # this node's blockchain data
    self.generatesize = gensize         # How big of a block will this node mine (it is assumed that there are enough txs)

  def mine(self,size=None):
    """Attempt to mine a block.  The chance of successfully mining a block is proportional to this node's configured hash power."""
    if size is None: size = self.generatesize
    if self.hasher(1):
      blk = self.blockchain.getTip(self.excessive, self.acceptdepth)
      self.blockchain.extend(blk, size)
      return True
    return False

  def hasher(self,interval):
    """(internal) Simulate hashing for an interval"""
    for i in range(0,interval):
      r = random.random()
      if r <= self.hashpct*(1.0/600.0):
        return True
    return False


def TestChain(args):
  random.seed()  # 1)

  chain = Blockchain()
  miner = Miner(1.0,1000000, 4,1000000,chain)
  result = [0]
  for i in range(1,10000):
    if miner.mine():
      result.append(i)
  chain.p()

def TestChainSplit(args):
  random.seed()  # 1)

  chain = Blockchain()
  miner = Miner(0.5,1000000, 4,1000000,chain)
  minerb = Miner(0.5,2000000, 4,2000000,chain)
  result = [0]
  for i in range(1,1000):
    if miner.mine():
      result.append(i)
  for i in range(1,10000):
    if miner.mine():
      result.append(i)
    if minerb.mine():
      result.append(i)
  chain.p()
  pdb.set_trace()
  chain.printChain(chain.start,0)


def runChainSplitSbyL(smallPct, largePct,preforkblocks=1000, postforkblocks=100000):
  """
  Returns the number of chain tips in the final full blockchain.  There is one tip per chain fork.
  """
  random.seed()  # 1)

  chain = Blockchain()
  # Create a group of miners with EB=1MB, AD=4, and generate size = 1MB
  miner = Miner(smallPct, 1000000,  4, 1000000, chain)
  # Create a 2nd group of miners with EB=2MB, AD=4, and generate size = 2MB
  minerb = Miner(largePct, 2000000, 4, 2000000, chain)

  for i in range(1,preforkblocks):   # Everyone is mining smaller blocks.
    miner.mine()                     # So just let "miner" mine
 
  for i in range(1,postforkblocks):  # Now its time to mine big and smaller blocks
    miner.mine()                     # so let both mine
    minerb.mine()                    # this call order doesn't matter because successful mining is random

  #chain.p()
  #chain.printChain(chain.start,0)
  forkLens = chain.getForkLengths()
  return (len(chain.tips), forkLens)

def runChainSplit2(s,l,iterations=100):
  """Run many iterations of a 2-way chain split, where a group of miners start producing 
     and accepting larger blocks.

     Pass the small block hashpower as a fraction of 1,
     the large block hashpower as a fraction of 1,
     and the number of iterations to run.

     This routine prints out data in the following format:
     0.950000/0.050000: {0: 97, 1: 3, ...}
     ^ largeblk  ^small  ^ 97 runs had no fork
                                ^ 3 runs had one fork
  """
  results = []
  maxForkLen=0
  for i in range(0,iterations):
    (numForks, forkLengths) = runChainSplitSbyL(s,l)
    numForks -= 1  # Because the main chain isn't a fork
    results.append(numForks)
    forkLengths.sort(reverse=True)
    logging.info("%f/%f.%d: fork lengths: %s" % (l,s, i, str(forkLengths)))
    if len(forkLengths) > 1:  # because main chain is forkLengths[0]
      if maxForkLen < forkLengths[1]: maxForkLen = forkLengths[1]
  rd = {}
  for r in results:
    t = rd.get(r,0)
    rd[r] = t+1
  print "%f/%f: %d, %s" % (l,s, maxForkLen, str(rd))
  


def Test():
  random.seed()  # 1)

  print "           SPLIT : max fork depth, { X:Y where X runs had Y forks }"
#  runChainSplit2(0.00,1)
#  runChainSplit2(0.0001,.999)
  runChainSplit2(0.50,0.50)
  runChainSplit2(0.40,0.60)
  runChainSplit2(0.333,0.667)
  runChainSplit2(0.25,0.75)
  runChainSplit2(0.20,0.80)
  runChainSplit2(0.10,0.90)
  runChainSplit2(0.05,0.95)



def Testthreaded():
  t=[]
  t.append(threading.Thread(target=runChainSplit2, args=(0.50,0.50)))
  t.append(threading.Thread(target=runChainSplit2, args=(0.40,0.60)))
  t.append(threading.Thread(target=runChainSplit2, args=(0.333,0.667)))
  t.append(threading.Thread(target=runChainSplit2, args=(0.25,0.75)))
  t.append(threading.Thread(target=runChainSplit2, args=(0.20,0.80)))
  t.append(threading.Thread(target=runChainSplit2, args=(0.10,0.90)))
  t.append(threading.Thread(target=runChainSplit2, args=(0.05,0.95)))

  for th in t:
    th.start()
  for th in t:
    th.join()
  
def Test100Pct(args):
  """ This old test just tests that it all works without a chain split"""
  random.seed()  # 1)

  miner = Miner(1.0, 1000000, 4, 1000000)
  result = [0]
  for i in range(1,1000000):
    if miner.hasher(1):
      result.append(i)

  print result
  
  prior = result[0]
  totalInterval = 0
  for i in result[1:]:
    interval = i - prior
    prior = i
    print interval
    totalInterval += interval
  
  avgInterval = totalInterval/(len(result)-1)
  print "average interval: ", avgInterval


def noop():
  results = []
  for i in range(1,1000):
    results.append(TestChainSplitSbyL(0.25,0.75)-1)
  print results
  rd = {}
  for r in results:
    t = rd.get(r,0)
    rd[r] = t+1
  print "75/25:", rd

  results = []
  for i in range(1,1000):
    results.append(TestChainSplitSbyL(0.333,0.667)-2)
  print results
  rd = {}
  for r in results:
    t = rd.get(r,0)
    rd[r] = t+1
  print "66/33:", rd



  #TestChainSplit([])
  #TestChain([])
  #Test100Pct([])

  
