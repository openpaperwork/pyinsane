#!/usr/bin/env python3

import os
import pickle
import sys


if __name__ == "__main__":
    length_size = len(pickle.pack("i", 0))

    try:
        os.unlink(sys.argv[2])
    except:
        pass
    try:
        os.unlink(sys.argv[1])
    except:
        pass

    os.mkfifo(sys.argv[1], mode=0o600)
    os.mkfifo(sys.argv[2], mode=0o600)

    fifo_s2c = os.open(sys.argv[1], os.O_RDONLY)
    fifo_c2s = os.open(sys.argv[2], os.O_WRONLY)

    try:
        print ("Ready")

        while True:
            cmd = input()
            print ("> {}".format(cmd))
            cmd = {"command": cmd}
            cmd = pickle.dumps(cmd)
            length = pickle.pack("i", len(cmd))
            os.write(fifo_c2s, length)
            os.write(fifo_c2s, cmd)

            length = os.read(fifo_s2c, length_size)
            length = pickle.unpack("i", length)[0]
            result = os.read(fifo_s2c, length)
            result = pickle.loads(result)
            print ("< {}".format(result))
    finally:
        os.close(fifo_s2c)
        os.close(fifo_c2s)
