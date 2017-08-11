hlp = """
    Timing experiments spawning multiple processes to limit the execution time.
    CSI does not work due to unknown subprocessing (oct2py) issues.
"""

import os
import csv
import time
import datetime
import numpy as np
import itertools as it
from examples.snr.snr import generate_data, test
from multiprocessing import Manager, Process
from mklaren.regression.ridge import RidgeMKL


# Global method list
METHODS = list(RidgeMKL.mkls.keys()) + ["Mklaren", "ICD", "Nystrom", "RFF", "FITC"]

def wrapsf(Ksum, Klist, inxs, X, Xp, y, f, method, return_dict):
    """ Worker thread ; compute method running time;
        funky behaviour on OSX if you run a simple np.linalg.inv ; works on Ubuntu; """
    r = test(Ksum, Klist, inxs, X, Xp, y, f, methods=(method,), lbd=0.1)
    return_dict[method] = r[method]["time"]
    return

def process():
    """ Run main loop. """

    # Fixed hyperparameters
    n_range = np.logspace(2, 6, 9).astype(int)
    rank_range = [5, 10, 30]
    p_range = [1, 3, 10]
    limit = 3600 # 60 minutes

    # Safe guard dict to kill off the methods that go over the limit
    # Set a prior limit to full-rank methods to 1e5
    off_limits = dict([(m, int(2e5)) for m in RidgeMKL.mkls.keys()])

    # Fixed output
    # Create output directory
    d = datetime.datetime.now()
    dname = os.path.join("..", "output", "snr", "timings",
                         "%d-%d-%d" % (d.year, d.month, d.day))
    if not os.path.exists(dname): os.makedirs(dname)
    rcnt = len(os.listdir(dname))
    fname = os.path.join(dname, "results_%d.csv" % rcnt)
    print("Writing to %s ..." % fname)

    # Output
    header = ["n", "p", "method", "lambda", "rank", "limit", "time"]
    fp = open(fname, "w", buffering=0)
    writer = csv.DictWriter(fp, fieldnames=header)
    writer.writeheader()

    # Main loop
    for P, rank, n in it.product(p_range, rank_range, n_range):

        # Generate a dataset of give rank
        gamma_range = np.logspace(-3, 6, P)
        Ksum, Klist, inxs, X, Xp, y, f = generate_data(n=n,
                                                       rank=rank,
                                                       inducing_mode="uniform",
                                                       noise=1.0,
                                                       gamma_range=gamma_range,
                                                       input_dim=1,
                                                       signal_sampling="weights")
        # Print after dataset generation
        d = datetime.datetime.now()
        print("%s\tn=%d rank=%d p=%d" % (d, n, rank, P))

        # Evaluate methods
        manager = Manager()
        return_dict = manager.dict()
        jobs = dict()
        for method in METHODS:
            if off_limits.get(method, np.inf) <= n:
                print("%s is off limit for n=%d rank=%d p=%d" % (method, n, rank, P))
                return_dict[method] = float("inf")
                continue
            p = Process(target=wrapsf, name="test",
                        args=(Ksum, Klist, inxs, X, Xp,
                              y, f, method, return_dict))
            p.start()
            jobs[method] = p

        # Kill jobs exceeding time limit
        time_start = time.time()
        while True:
            time.sleep(1)
            alive = any([p.is_alive() for p in jobs.values()])
            if not alive:
                break
            t = time.time() - time_start
            if t > limit:
                for method, p in jobs.items():
                    if p.is_alive():
                        # Terminate process and store method to off limits for this n
                        # Note that this is the minimal point in (n, p, rank) for which if doesn't work
                        print("%s REGISTERED for n=%d rank=%d p=%d" % (method, n, rank, P))
                        return_dict[method] = float("inf")
                        off_limits[method] = min(off_limits.get(method, np.inf), n)
                        p.terminate()

        # Write to output
        for method, value in return_dict.items():
            row = {"n": n, "p": P, "method": method, "limit": limit,
                   "lambda": 0.1, "rank": rank, "time": value}
            writer.writerow(row)


if __name__ == "__main__":
    process()