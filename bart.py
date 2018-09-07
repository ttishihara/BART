import zipfile
import sys
import os
import glob
import shutil

def ProcessBart(tmpDir, dataDir, SQLConn=None, schema='cls', table='bart'):
    return


def cleanTmp(tmpDir):
    tmpDir = os.path.abspath(tmpDir)
    # if tmpDir exists, delete and remake it
    if os.path.isdir(tmpDir):
        shutil.rmtree(tmpDir)
        os.mkdir(tmpDir)
    else:
        os.mkdir(tmpDir)


def getFilepaths(directory):
    filepaths = []
    directory = os.path.abspath(directory)
    f = os.walk(directory)
    for dir_, _, filename in f:
        for file_ in filename:
            filepaths.append(os.path.join(dir_, file_))

    return filepaths


def unzipFiles(dataDir, tmpDir):
    filepaths = getFilepaths(dataDir)

    for file_ in filepaths:
        # check if file is a zip file
        if zipfile.is_zipfile(file_):
            with zipfile.ZipFile(file_, 'r') as zfile:
                
                zfile.extractall(tmpDir)
    return

if __name__ == "__main__":
    dataDir = sys.argv[1]
    tmpDir = sys.argv[2]
    cleanTmp(tmpDir)
    unzipFiles(dataDir, tmpDir)
