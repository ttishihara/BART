import zipfile
import xlrd
import sys
import os
import glob
import shutil
import csv
import psycopg2



def ProcessBart(tmpDir, dataDir, SQLConn=None, schema='cls', table='bart'):
    cleanTmp(tmpDir)
    unzipFiles(dataDir, tmpDir)
    toLoad = processExcelFiles(tmpDir)
    output_to_csv(toLoad, tmpDir)
    loadIntoDB(SQLConn, schema, table, tmpDir)
    print("FINISHED")
    return


def cleanTmp(tmpDir):
    """
    Create a clean temp directory at the specified location.
    If the temp directory exists, recreate it.
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
                # extract contents of zipfile into temp directory
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
    """
    Process all .xls files in tmpDir and reshapes it into the format
    we need for uploading to our SQL database.

    Returns a list of tuples where each tuple contains information for one row.
    """
    filepaths = getFilepaths(tmpDir)

    to_csv = []
    #iterate over xls files
    for xls in filepaths:
        xl = xlrd.open_workbook(xls)
        sheet_names = xl.sheet_names()

        # iterate over sheets in each xls file
        for sheet in sheet_names:
            daytype = sheet.split()[0]
            daytype = standardize_daytype(daytype)
            # Skip Clipper/Fastpass sheets
            if daytype is None:
                continue

            sh = xl.sheet_by_name(sheet)

            # get month and year from cell G1 of the first sheet
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
            
            # Fix names for numerically named stations (ie 19th, 16th)
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

            # append reshaped data to overall list
            to_csv = to_csv + reshaped_data


    return to_csv


def output_to_csv(to_csv, tmpDir):
    """
    Takes a list of tuples and creates a .csv file in the 
    specified temp directory.
    """
    outputPath = os.path.join(tmpDir, 'toLoad.csv')
    with open(outputPath, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for line in to_csv:
            writer.writerow(line)

def loadIntoDB(SQLConn, schema, table, tmpDir):
    """
    Gets toLoad.csv from the temp directory, creates the table, and 
    uploads the contents of toLoad.csv.
    """

    SQLCursor = SQLConn.cursor()
    query1='DROP TABLE IF EXISTS '+ '{0}.{1}'.format(schema,table);
    SQLCursor.execute(query1)
    SQLCursor.execute("""
      CREATE TABLE %s.%s
      (
      mon int
      , yr int
      , daytype varchar(15)
      , start varchar(2)
      , term varchar(2)
      , riders float
      );""" % (schema, table))
    path = os.path.abspath(os.path.join(tmpDir, 'toLoad.csv'))
    SQLCursor.execute("""COPY %s.%s FROM '%s' CSV;"""
                      % (schema, table, path))
    SQLConn.commit()


if __name__ == "__main__":
    dataDir = sys.argv[1]
    tmpDir = sys.argv[2]
    #SQLconnR = psycopg2.connect(" dbname='tomo' user='tomo' host ='localhost' password = '' ")
    ProcessBart(tmpDir, dataDir, SQLconnR)

