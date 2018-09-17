import zipfile
import xlrd
import sys
import os
import glob
import shutil
import csv

def ProcessBart(tmpDir, dataDir, SQLConn=None, schema='cls', table='bart'):
    cleanTmp(tmpDir)
    unzipFiles(dataDir, tmpDir)
    processExcelFiles(tmpDir)
    print("FINISHED")
    return


def cleanTmp(tmpDir):
    """
    Create a clean temp directory at the specified location.
    """

    tmpDir = os.path.abspath(tmpDir)
    # if tmpDir exists, delete and remake it
    if os.path.isdir(tmpDir):
        shutil.rmtree(tmpDir)
        os.mkdir(tmpDir)
    else:
        os.mkdir(tmpDir)


def getFilepaths(directory):
    """
    Walk through directory and all subdirectories.
    Returns a list of absolute filepaths of files in directory.
    """

    filepaths = []
    directory = os.path.abspath(directory)
    f = os.walk(directory)
    for dir_, _, filename in f:
        for file_ in filename:
            filepaths.append(os.path.join(dir_, file_))

    return filepaths


def unzipFiles(dataDir, tmpDir):
    """
    Unzips all .zip files in dataDir and outputs into tmpDir
    """

    filepaths = getFilepaths(dataDir)

    for file_ in filepaths:
        # check if file is a zip file
        if zipfile.is_zipfile(file_):
            with zipfile.ZipFile(file_, 'r') as zfile:
                zfile.extractall(tmpDir)

def standardize_daytype(daytype):
    if daytype == 'Wkdy' or daytype == 'Weekday':
        return 'weekday'
    elif daytype == 'Sat' or daytype == 'Saturday':
        return 'saturday'
    elif daytype == 'Sun' or daytype == 'Sunday':
        return 'sunday'
    else:
        return None


def processExcelFiles(tmpDir):
    filepaths = getFilepaths(tmpDir)

    to_csv = []
    #iterate files
    for xls in filepaths:
        xl = xlrd.open_workbook(xls)
        sheet_names = xl.sheet_names()

        # iterate sheets
        for sheet in sheet_names:
            daytype = sheet.split()[0]
            daytype = standardize_daytype(daytype)
            # Skip Clipper/Fastpass sheets
            if daytype is None:
                continue

            sh = xl.sheet_by_name(sheet)

            if daytype == 'weekday':
                date = xlrd.xldate_as_datetime(sh.cell_value(0, 6), 0)
                month = date.month
                year = date.year

            # Get exit stations
            col_i = 1
            exit_stations = []
            while sh.cell_value(1, col_i) != 'Exits':
                exit_stations.append(sh.cell_value(1, col_i))
                col_i += 1

            # Get entry stations
            row_i = 2
            entry_stations = []
            while sh.cell_value(row_i, 0) != 'Entries':
                entry_stations.append(sh.cell_value(row_i, 0))
                row_i += 1
            
            # Fix names for number based stations (ie 19th, 16th)
            exit_stations = [ str(int(station)) if type(station) == float else station for station in exit_stations ]
            entry_stations = [ str(int(station)) if type(station) == float else station for station in entry_stations ]

            # Iterate over all cells and create a list of tuples containing information for each row of sql table
            reshaped_data = []
            exit_ix = 0
            for r_ix in range(2, row_i):
                entry_ix = 0
                for c_ix in range(1, col_i):
                    reshaped_data.append(
                        (month, year, daytype, entry_stations[entry_ix], exit_stations[exit_ix], sh.cell_value(r_ix, c_ix))
                    )
                    entry_ix += 1
                exit_ix += 1

            # append reshaped data to to_csv list
            to_csv = to_csv + reshaped_data

    output_to_csv(to_csv, tmpDir)


def output_to_csv(to_csv, tmpDir):
    outputPath = os.path.join(tmpDir, 'toLoad.csv')
    with open(outputPath, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for line in to_csv:
            writer.writerow(line)


if __name__ == "__main__":
    dataDir = sys.argv[1]
    tmpDir = sys.argv[2]

    ProcessBart(tmpDir, dataDir)
