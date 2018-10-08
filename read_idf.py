import os
import csv
import numpy as np
import matplotlib.pyplot as plt


def parse_idf(filepath):
    ivfile = open(filepath, encoding="ISO-8859-1").readlines()
    # First, read the metadata
    lnum = 0
    metadata = {"method": "",
                "technique": "",
                "title": "",
                "stages": None,
                "interval": None,
                "points": None
                }

    for line in ivfile:
        # Currently configured for only "TR" method
        if "Method=" in line:
            (dum, metadata["method"]) = line.split(sep="=")
            metadata["method"] = metadata["method"].rstrip()
        if "Technique=" in line:
            (dum, metadata["technique"]) = line.split(sep="=")
            metadata["technique"] = metadata["technique"].rstrip()
        if "Title=" in line[0:6]:
            (dum, metadata["title"]) = line.split(sep="=")
            metadata["title"] = metadata["title"].rstrip()
        if "Stages=" in line:
            (dum, stages) = line.split(sep="=")
            metadata["stages"] = int(stages)
        if "Interval time=" in line:
            (dum, interval) = line.split(sep="=")
            metadata["interval"] = float(interval)
        if "primary_data" in line:
            break  # Stops here!
        lnum += 1

    # Second, read the  plot data
    ncols = int(ivfile[lnum+1])
    npoints = int(ivfile[lnum+2])
    metadata["points"] = npoints

    lnum += 3
    col1 = []
    col2 = []
    col3 = []
    for lnum in range(lnum, lnum+npoints):
        (val1, val2, val3) = ivfile[lnum].split()
        col1.append(float(val1))
        col2.append(float(val2))
        col3.append(float(val3))

    time = np.array(col1)

    if (metadata["technique"] == "Mixed Mode") or (metadata["technique"] == "ChronoAmperometry"):
        print(metadata["technique"])
        # Current in column 2
        amps = np.array(col2)
        volts = np.array(col3)
    elif metadata["technique"] == "ChronoPotentiometry":
        # Current in column 3
        volts = np.array(col2)
        amps = np.array(col3)
    else:
        print("Unrecognised technique: " + metadata["technique"])
        return None, None

    dt = (time[1] - time[0])
    charge = np.array([amps[0]*dt])

    for ind in range(1, npoints):
        charge = np.append(charge, charge[ind-1] + amps[ind]*dt) # ... charge in A*s

    charge = charge * 1000./3600.  # ... convert charge to mAh.

    data = {"time": time,
            "charge": charge,
            "amps": amps,
            "volts": volts}

    return data, metadata


def make_plot(scanid, data, metadata):
    time = data["time"]
    amps = data["amps"]
    volts = data["volts"]
    title = metadata["title"]
    technique = metadata["technique"]

    fig, ax1 = plt.subplots()
    fig.suptitle(technique + ": " + title, verticalalignment="top")

    color = 'tab:red'
    ax1.set_xlabel('Time / s')
    ax1.set_ylabel('Current / mA', color=color)  # Note...
    ax1.plot(time, amps*1.0e3, color=color)      # ...Current in mA.
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('Potential / V', color=color)  # we already handled the x-label with ax1
    ax2.plot(time, volts, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    # fig.legend()
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.subplots_adjust(top=0.9)
    fig.savefig((scanid +".pdf"), bbox_inches='tight')
    plt.close(fig)
    return


def i_v_stats(time, charge, current, voltage):
    stats = {"integ_i": 0,
             "lims_i": (None,None),
             "lims_v": (None,None),
             "duration": 0
             }
    # Scan duration
    stats["duration"] = time[-1]
    #  Max/min V
    stats["lims_v"] = (np.amin(voltage), np.amax(voltage))
    # Max/min I
    stats["lims_i"] = (np.amin(current), np.amax(current))
    # Total charge
    stats["integ_i"] = charge[-1]

    return stats


def analyse_file(fpath, fname):
    scanid = fname[0:4]
    datfile = os.path.join(fpath, fname)

    # Get data and plot it
    (data, metadata) = parse_idf(datfile)
    stats = i_v_stats(data["time"], data["charge"], data["amps"], data["volts"])
    make_plot(scanid, data, metadata)

    # Record data to file
    datfile = os.path.join(os.path.dirname(__file__), scanid + ".dat")
    with open(datfile, "w") as txtfile:
        npoints = len(data["time"])
        line = "time\tcharge\tamps\tvolts\n" # The header
        txtfile.write(line)

        for ind in range(0, npoints):
            line = "{:f}\t{:f}\t{:f}\t{:f}\n".format(
                data["time"][ind],
                data["charge"][ind],
                data["amps"][ind],
                data["volts"][ind],
            )
            txtfile.write(line)


    # Record scan parameters
    outfile = os.path.join(os.path.dirname(__file__), "scan_summary.csv")

    with open(outfile, "a") as csvfile:
        fieldnames = ["Scan ID",
                      "Technique",
                      "Title",
                      "Charge",
                      "µAmps min",
                      "µAmps max",
                      "Volts min",
                      "Volts max"]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # writer.writeheader()
        newrow = {"Scan ID": scanid,
                  "Technique": metadata["technique"],
                  "Title": metadata["title"],
                  "Charge": stats["integ_i"],
                  "µAmps min": stats["lims_i"][0]*1.0e6,
                  "µAmps max": stats["lims_i"][1]*1.0e6,
                  "Volts min": stats["lims_v"][0],
                  "Volts max": stats["lims_v"][1]
                  }
        writer.writerow(newrow)
    return


# fpath = "./resources/ivium/NaHalfcell-2_2-precrash/"
# fpath = "./resources/ivium/NaHalfcell-2_2-postcrash/"
# fpath = "./resources/ivium/NaHalfcell-2_5/"
fpath = "./resources/ivium/NaHalfcell-2_5-1Himaging/"


with open(fpath+"queuefile.in") as qfile:

    for line in sorted(qfile):
        fname = line.rsplit("\n")[0]
        print("Processing " + fname)
        analyse_file(fpath, fname)

print("All files processed in " + fpath + "queuefile.in")  # Make it easy to select the file
