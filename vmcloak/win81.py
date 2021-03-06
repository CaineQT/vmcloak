# Copyright (C) 2014-2015 Jurriaan Bremer.
# This file is part of VMCloak - http://www.vmcloak.org/.
# See the file 'docs/LICENSE.txt' for copying permission.

import logging
import os.path

from vmcloak.abstract import OperatingSystem
from vmcloak.misc import ini_read
from vmcloak.rand import random_string
from vmcloak.verify import valid_serial_key

log = logging.getLogger(__name__)

class Windows81(OperatingSystem):
    name = 'win81'
    service_pack = 2
    mount = '/mnt/win81'
    nictype = '82540EM'
    osdir = os.path.join('sources', '$oem$', '$1')
    interface = "Ethernet"
    genisoargs = [
        '-no-emul-boot', '-iso-level', '2', '-udf', '-J', '-l', '-D', '-N',
        '-joliet-long', '-relaxed-filenames',
    ]

    # List of preferences when multiple Windows 8.1 types are available.
    preference = "pro", "enterprise", "home"

    ARCH = None

    def _autounattend_xml(self, product):
        values = {
            'PRODUCTKEY': self.serial_key,
            'COMPUTERNAME': random_string(8, 14),
            'USERNAME': random_string(8, 12),
            'PASSWORD': random_string(8, 16),
            "PRODUCT": product.upper(),
            "ARCH": self.ARCH,
            "INTERFACE": self.interface,
        }

        buf = open(os.path.join(self.path, 'autounattend.xml'), 'rb').read()
        for key, value in values.items():
            buf = buf.replace('@%s@' % key, value)

        return buf

    def isofiles(self, outdir, tmp_dir=None):
        products = []

        product_ini = os.path.join(outdir, "sources", "product.ini")
        mode, conf = ini_read(product_ini)

        for line in conf.get("BuildInfo", []):
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            if key != "staged":
                continue

            for product in value.split(","):
                products.append(product.lower())

            break

        for preference in self.preference:
            if preference in products:
                product = preference
                break
        else:
            if products:
                product = products[0]
            else:
                product = self.preference[0]

        if self.product and self.product.lower() not in self.preference:
            log.error("The product version of Windows 8.1 that was specified "
                      "on the command-line is not known by us, ignoring it.")
            self.product = None

        with open(os.path.join(outdir, 'autounattend.xml'), 'wb') as f:
            f.write(self._autounattend_xml(self.product or product))

    def set_serial_key(self, serial_key):
        if serial_key and not valid_serial_key(serial_key):
            log.error('The provided serial key has an incorrect encoding.')
            log.info('Example encoding, AAAAA-BBBBB-CCCCC-DDDDD-EEEEE.')
            return False

        # https://technet.microsoft.com/en-us/library/jj612867.aspx
        self.serial_key = serial_key or 'GCRJD-8NW9H-F2CDX-CCM8D-9D6T9'
        return True

class Windows81x64(Windows81):
    ARCH = "amd64"

class Windows81x86(Windows81):
    ARCH = "x86"
