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
    col1 = []; col2 = []; col3 = []
    for lnum in range(lnum, lnum+npoints):
        (val1, val2, val3) = ivfile[lnum].split()
        col1.append(float(val1))
        col2.append(float(val2))
        col3.append(float(val3))

    time = np.array(col1)
    y1 = np.array(col2)
    y2 = np.array(col3)
    data = {"time": time,
            "y1": y1,
            "y2":y2}

    return(data, metadata)


def make_plot(scanid, data, metadata):
    time = data["time"]
    y1 = data["y1"]
    y2 = data["y2"]
    title = metadata["title"]

    fig, ax1 = plt.subplots()
    fig.suptitle(title, verticalalignment="top")

    color = 'tab:red'
    ax1.set_xlabel('Time / s')
    ax1.set_ylabel('Current / mA', color=color)  # Note...
    ax1.plot(time, y1*1.0e3, color=color)        # ...Current in mA.
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('Potential / V', color=color)  # we already handled the x-label with ax1
    ax2.plot(time, y2, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    # fig.legend()
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.subplots_adjust(top=0.9)
    fig.savefig((scanid +".pdf"), bbox_inches='tight')
    plt.close(fig)
    return


def i_v_stats(time, current, voltage):
    stats = {"integ_i": 0,
             "lims_i": (None,None),
             "lims_v": (None,None)
             }
    # Max/min V
    stats["lims_v"] = (np.amin(voltage), np.amax(voltage))
    # Max/min I
    stats["lims_i"] = (np.amin(current), np.amax(current))
    # Integrate I
    dt = time[1] - time[0]
    Q = 0
    for val in current:
        Q += val*dt

    stats["integ_i"] = Q
    return stats


def analyse_file(fpath, fname):
    scanid = fname[0:4]
    datfile = os.path.join(fpath, fname)

    # Get data and plot it
    (data, metadata) = parse_idf(datfile)
    stats = i_v_stats(data["time"], data["y1"], data["y2"])
    make_plot(scanid, data, metadata)

    # Record scan parameters
    outfile = os.path.join(os.path.dirname(__file__), "scan_summary.csv")

    with open(outfile, "a") as csvfile:
        fieldnames = ["Scan ID",
                      "Technique",
                      "Title",
                      "Charge",
                      "Amps min",
                      "Amps max",
                      "Volts min",
                      "Volts max"]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # writer.writeheader()
        newrow = {"Scan ID": scanid,
                  "Technique": metadata["technique"],
                  "Title": metadata["title"],
                  "Charge": stats["integ_i"],
                  "Amps min": stats["lims_i"][0],
                  "Amps max": stats["lims_i"][1],
                  "Volts min": stats["lims_v"][0],
                  "Volts max": stats["lims_i"][1]
                  }
        writer.writerow(newrow)
    return


# fpath = "./resources/ivium/171101-NaHalfcell-2_5/"  # DONE!
# fpath = "./resources/ivium/171214-NaHalfcell-2_5/"  # DONE!
# fpath = "./resources/ivium/171019-NaHalfcell-2_2/" # BAD DATA ORDERING... BREAK UP MANUALLY
# fpath = "./resources/ivium/NaHalfcell-2_2-precrash/"
fpath = "./resources/ivium/NaHalfcell-2_2-postcrash/"

with open(fpath+"queuefile.in") as qfile:

    for line in qfile:
        fname = line.rsplit("\n")[0]
        print("Processing " + fname)
        analyse_file(fpath, fname)

print("All files processed in " + fpath + "queuefile.in")  # Make it easy to select the file
