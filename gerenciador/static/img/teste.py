import _thread
import time

f= open("guru99.txt","w+")

def run(id):
  try:
    f.write("\nthread: %d" % id )
  except:
    pass

for i in range(5):
    for i in range(100000):
        try:
            _thread.start_new_thread( run, (i, ) )
        except:
            print("erro")
    
while True:
    pass

