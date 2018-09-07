import zipfile
import sys
import os
import glob

def ProcessBart(tmpDir, dataDir, SQLConn=None, schema='cls', table='bart'):
    return

def unzipFiles(dataDir):

    # walk through dataDir in create list of absolute paths for all files
    filepaths = []
    dataDir = os.path.abspath(dataDir)
    f = os.walk(dataDir)
    for dir_, _, filename in f:
        for file_ in filename:
            filepaths.append(os.path.join(dir_, file_))

    for file_ in filepaths:
        # check if file is a zip file
        if zipfile.is_zipfile(file_):
            with zipfile.ZipFile(file_, 'r') as zfile:
                zfile.extractall('/tmp/')
    return

if __name__ == "__main__":
    dataDir = sys.argv[1]
    unzipFiles(dataDir)
