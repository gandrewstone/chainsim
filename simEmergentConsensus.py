from chainsim import *


def runChainSplitSbyL(MinerClass, smallPct, largePct,preforktime=1000, postforktime=100000):
  """
  Returns the number of chain tips in the final full blockchain.  There is one tip per chain fork.
  """
  random.seed()  # 1)

  chain = Blockchain()
  # Create a group of miners with EB=1MB, AD=4, and generate size = 1MB
  miner = MinerClass(smallPct, 1000000,  4, 1000000, chain)
  # Create a 2nd group of miners with EB=2MB, AD=4, and generate size = 2MB
  minerb = MinerClass(largePct, 2000000, 4, 2000000, chain)

  for i in range(1,preforktime):     # Everyone is mining smaller blocks.
    miner.mine()                     # So just let "miner" mine
 
  for i in range(1,postforktime):    # Now its time to mine big and smaller blocks
    miner.mine()                     # so let both mine
    minerb.mine()                    # this call order doesn't matter because successful mining is random

  #chain.p()
  #chain.printChain(chain.start,0)
  forkLens = chain.getForkLengths()
  return (len(chain.tips), forkLens)

def runChainSplit2(MinerClass,s,l,iterations=100):
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
    (numForks, forkLengths) = runChainSplitSbyL(MinerClass,s,l)
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

#  runChainSplit2(0.00,1)
#  runChainSplit2(0.0001,.999)

  print "BUIP001 + trailing fix"
  print "           SPLIT : max fork depth, { X:Y where X runs had Y forks }"
  runChainSplit2(Miner,0.50,0.50)
  runChainSplit2(Miner,0.40,0.60)
  runChainSplit2(Miner,0.333,0.667)
  runChainSplit2(Miner,0.25,0.75)
  runChainSplit2(Miner,0.20,0.80)
  runChainSplit2(Miner,0.10,0.90)
  runChainSplit2(Miner,0.05,0.95)

  
  print "Original BUIP001 commit (does not move to the chain tip if EB/AD is exceeded)"
  print "           SPLIT : max fork depth, { X:Y where X runs had Y forks }"
  runChainSplit2(MinerTrailingBug,0.50,0.50)
  runChainSplit2(MinerTrailingBug,0.40,0.60)
  runChainSplit2(MinerTrailingBug,0.333,0.667)
  runChainSplit2(MinerTrailingBug,0.25,0.75)
  runChainSplit2(MinerTrailingBug,0.20,0.80)
  runChainSplit2(MinerTrailingBug,0.10,0.90)
  runChainSplit2(MinerTrailingBug,0.05,0.95)



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
  

  
