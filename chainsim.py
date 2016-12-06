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
    self.id = createNum           # A unique count describing the order of block creation across the entire simulation.  Used to identify the block, similar to the hash
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
      s = "->h%ds%db%d" % (block.height,block.size/1000000,block.id)
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
    self.block={}                       # For efficiency this simulation just keeps a single copy of the blockchain.  Any miner-specific block can be stored here

  def getTip(self):
    eb = self.excessive
    ad = self.acceptdepth
    bc = self.blockchain
    tips = []
    for tip in bc.tips:
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
          tips.append(tip)  # If AD is exceeded, choose the tip
    tips = sorted(tips,key=lambda x: x.height, reverse=True)
    # TODO random if tips are =
    return tips[0]
    
  def mine(self,size=None):
    """Attempt to mine a block.  The chance of successfully mining a block is proportional to this node's configured hash power."""
    if size is None: size = self.generatesize
    if self.hasher(1):
      blk = self.getTip()
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


class MinerTrailingBug(Miner):
  """This miner fixes an issue where block sizes that persistently exceed the EB cause the miners to always trail the chain tip."""
  def __init__(self, hashpct, eb,ad, gensize, blockchain=None):
    """constructor, pass the hash as a fraction of 1, the excessive block size, the accept depth, the generation size, and the blockchain"""
    Miner.__init__(self,hashpct, eb,ad,gensize,blockchain)

  def getTip(self):
    eb = self.excessive
    ad = self.acceptdepth
    bc = self.blockchain
    tips = []
    for tip in bc.tips:
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
          tips.append(pos)  # so the block AD behind is the tip.
    tips = sorted(tips,key=lambda x: x.height, reverse=True)
    # TODO random if tips are =
    return tips[0]


class MinerBUIP041(Miner):
  """This miner fixes an issue where block sizes that persistently exceed the EB cause the miners to always trail the chain tip."""
  def __init__(self, hashpct, eb,ad, gensize, blockchain=None):
    """constructor, pass the hash as a fraction of 1, the excessive block size, the accept depth, the generation size, and the blockchain"""
    Miner.__init__(self,hashpct, eb,ad,gensize,blockchain)

  def getTip(self):
    eb = self.excessive
    ad = self.acceptdepth
    bc = self.blockchain
    tips = []
    for tip in bc.tips:
      if tip.biggestSize <= eb:  # there's no chance this blockchain is excessive
        tips.append(tip)
      else:
        # Calculate EEB
        pos = tip
        EEB = 0
        gates = []
        maxblocksize = 0
        for i in range(0,144):
          data = self.block.get(pos.id,None)
          maxblocksize = max(pos.size,maxblocksize)

          if data:              
            if data.get("excessive",False) == True:
              EEB = max(EEB,pos.size)
              
          pos = pos.parent  # go to previous block
        if EEB == 0:  # There were no excessively marked blocks
          EEB = max(maxblocksize, self.excessive)    

        if tip.size > EEB:  # an excessive block, let's calculate the accept depth
          ADfraction = math.floor(self.acceptdepth*(tip.size - EEB)/self.excessive)
          if EEB == self.excessive:
            EAD = self.acceptdepth + ADfraction
          else:
            EAD = ADfraction
          self.block[tip.id]["EAD"] = EAD            
          gates.append((tip.height,pos))
          
        # Now look for any other excessive blocks are still waiting for
        pos = tip
        tipdist = 0
        for i in range(0,144):
          data = self.block.get(pos.id,None)
          if data:
            EAD = data.get("EAD", 0)
            if EAD > 0:  # We already calculated this tip so add it rather than recalc
              if tipdist >= EAD:                
                gates.append((pos.height,pos))
          pos = pos.parent
          tipdist+=1

        # find the earliest one
        gates.sort(key=lambda x: x[0])

        tips.append(gates[0])

    tips = sorted(tips,key=lambda x: x.height, reverse=True)
    # TODO random if tips are =
    return tips[0]



  

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
  miner = Miner(0.5, 1000000, 4,1000000,chain)
  minerb = Miner(0.5, 2000000, 4,2000000,chain)
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
