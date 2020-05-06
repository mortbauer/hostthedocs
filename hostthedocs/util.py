"""
Provides utility methods.
"""

import os
import logging
import zipfile
import tarfile


logger = logging.getLogger()

class FileExpander(object):
    """
    Manager for exanding compressed project files.

    It automatically detects the compression method and allocates
    the right handler.

    Currently the supported methods are:
    - zip
    - tar

    # This is potentially insecure, we are only accepting things from trusted sources.
    #
    # overwriting files with arbitary crafted archive seems to be prevented in
    # zipfile module but not in tarfile 
    # https://ajinabraham.com/blog/exploiting-insecure-file-extraction-in-python-for-code-execution
    # https://docs.python.org/2/library/zipfile.html#zipfile.ZipFile.extract
    # 
    # still possible to have a zip bomb: https://bugs.python.org/issue39341
    """

    ZIP_EXTENSIONS = ('.zip', )
    TAR_EXTENSIONS = ('.tar', '.tgz', '.tar.gz', '.tar.bz2')

    def __init__(self, uploaded_file):
        self.filename = uploaded_file.filename
        # there is an issue with SpooledTemporaryFile and seekable attribute
        # https://bugs.python.org/issue35112 which is apperantly used at least
        # by zip, therefore call rollover which should result in a real file
        # like object according to the docs
        uploaded_file.file.rollover()
        self.file = uploaded_file.file._file
        self._handle = None

    @classmethod
    def detect_compression_method(cls, filename):
        """
        Attempt to detect the compression method from the filename extension.

        :param str extension: The file extension.
        :return: The compression method ('zip' or 'tar').
        :raises ValueError: If fails to detect the compression method.
        """
        if any(filename.endswith(ext) for ext in cls.ZIP_EXTENSIONS):
            return 'zip'
        if any(filename.endswith(ext) for ext in cls.TAR_EXTENSIONS):
            return 'tar'

        raise ValueError('Unknown compression method for %s' % filename)

    def __enter__(self):
        method = self.detect_compression_method(self.filename)
        if method == 'zip':
            self._handle = zipfile.ZipFile(self.file)
        elif method == 'tar':
            raise ValueError('Unsupported method %s' % method)
            # self._handle = tarfile.open(fileobj=self.file, mode='r:*')
        else:
            raise ValueError('Unsupported method %s' % method)

        return self._handle

    def __exit__(self, exc_type, exc_value, traceback):
        self._handle.close()
