#!/usr/bin/python

import base64
import logging
import os
import socket
import stat
import subprocess
import sys
import urllib2
from collections import OrderedDict
from optparse import OptionParser
from time import sleep

__author__ = 'luke beer - eat.lemons@gmail.com - https://github.com/lukebeer'

""" This script will install all required packages and configure SELinux, sysstat, snmp etc.
    This will prepare a minimum/lean CentOS or RHEL 5/6/7 OS ready for any fresh Broadworks installation.

    * Bare metal server to a running AS in as little as 5 minuets without the need of kickstart, generic ISOs will do.

    * The script can perform unattended automated installations of the following releases for all core server types.

   - 17.sp4.197
   - 18.0.890
   - 20.sp1.606
   - 21.sp1.551


    WTF?
    ===========
    1) Install OS, minimal install, nice and lean.
    2) run script: bash-$ python bwbootstrap.py
    3) Follow steps
    4) Make a brew

"""

logger = logging.getLogger('BroadworksBootstrap')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

XCHANGE_USERNAME = os.getenv('XCHANGE_USER', 'mail@example.com')
XCHANGE_PASSWORD = os.getenv('XCHANGE_PASS', 'password')

bss_url = 'http://xchange.broadsoft.com/XchangeRepos/GA/__RELEASE__/bss/Linux/'
ips_url = 'http://xchange.broadsoft.com/XchangeRepos/GA/_RELEASE__/ips/'
swm_url = 'http://xchange.broadsoft.com/XchangeRepos/GA/co/noarch/'

general_options = {
    'BROADWORKS_USERNAME': 'bwadmin',
    'NTP_CONFIG': 'CLIENT',
    'SCHEDULED_TASK': [
        'dbSyncCheck minute 360',
        'autoCleanup date 4 4 44',
        'backup daily 8 15',
        'tech-support day friday 16 00',
        'cpuMon minute 720',
        'healthmon minute 30',
        'dbMaint day tuesday 7 30']
}

configs = {
    'as': {
        'software': {
            '17.sp4.197': {
                'installer': 'AS_Rel_17.sp4_1.197.Linux-x86_64.bin',
                'patch': 'IP.as.17.sp4.197.ip20140430.Linux-x86_64.tar.gz'
            },
            '18.0.890': {
                'installer': 'AS_Rel_18.0_1.890.Linux-x86_64.bin',
                'patch': 'IP.as.18.0.890.ip20140505.Linux-x86_64.tar.gz'
            },
            '20.sp1.606': {
                'installer': 'AS_Rel_20.sp1_1.606.Linux-x86_64.bin',
                'patch': 'IP.as.20.sp1.606.ip20150211.Linux-x86_64.tar.gz'
            },
            '21.sp1.551': {
                'installer': 'AS_Rel_21.sp1_1.551.Linux-x86_64.bin',
                'patch': 'IP.as.21.sp1.551.ip20150224.Linux-x86_64.tar.gz'
            }
        },
        'options': {
            'SERVER_TYPE': 'ApplicationServer',
            'REDHOSTNAME': socket.getfqdn(),
            'REDPRIMARYHOSTNAME': socket.getfqdn(),
            'REDPRIMARY': 'true',
            'REDPEERS': '{%s->%s,}' % (socket.getfqdn(), socket.getfqdn()),
            'REDREPPORT': '17888',
            'APP_SERVER_ID': socket.gethostname(),
            'VIRTUALDOMAIN': socket.getfqdn(),
            'JASS': 'false',
            'FTP_ON': 'true',
            'TFTP_ON': 'false',
            'TELNET_ON': 'true',
            'USESSL': 'true',
    Fresh install        'FULLSSL': 'false',
            'NTP_SERVER': 'pool.ntp.org',
            'APACHEHOSTNAME': socket.getfqdn(),
            'REDUNDANTSERVER': 'false',
            'HAS_DATABASE': 'true',
            'SERVER_DSN': 'AppServer',
            'SERVER_CLIENT_DSN': 'AppServerClient',
            'MAINTENANCE_DSN': 'Maintenance',
            'MAINTENANCE_CLIENT_DSN': 'MaintenanceClient',
            'SERVER_ PHYSICAL_STORE': 'AppServerClient',
            'DSN_SIZE': '512',
            'TEMP_SIZE': '170',
            'USE_TT_LOG_DIR': 'false',
            'IMS_MODE': 'false'
        }
    },
    'ms': {
        'software': {
            '17.sp4.197': {
                'installer': 'MS_Rel_17.sp4_1.197.Linux-x86_64.bin',
                'patch': 'IP.ms.17.sp4.197.ip20130426.Linux-x86_64.tar.gz'
            },
            '18.0.890': {
                'installer': 'MS_Rel_18.0_1.890.Linux-x86_64.bin',
                'patch': 'IP.ms.18.0.890.ip20121210.Linux-x86_64.tar.gz'
            },
            '20.sp1.606': {
                'installer': 'MS_Rel_20.sp1_1.606.Linux-x86_64.bin',
                'patch': 'IP.ms.20.sp1.606.ip20141117.Linux-x86_64.tar.gz'
            },
            '21.sp1.551': {
                'installer': 'MS_Rel_21.sp1_1.551.Linux-x86_64.bin',
                'patch': 'IP.ms.21.sp1.551.ip20150224.Linux-x86_64.tar.gz'
            }
        },
        'options': {
            'SERVER_TYPE': 'MediaServer',
            'JASS': 'false',
            'NTP_SERVER': 'pool.ntp.org',
            'FTP_ON': 'true',
            'TFTP_ON': 'false',
            'VIRTUALIZATION_ON': 'false',
            'TELNET_ON': 'true'
        }
    },
    'ns': {
        'software': {
            '17.sp4.197': {
                'installer': 'NS_Rel_17.sp4_1.197.Linux-x86_64.bin',
                'patch': 'IP.ns.17.sp4.197.ip20140430.Linux-x86_64.tar.gz'
            },
            '18.0.890': {
                'installer': 'NS_Rel_18.0_1.890.Linux-x86_64.bin',
                'patch': 'IP.ns.18.0.890.ip20140505.Linux-x86_64.tar.gz'
            },
            '20.sp1.606': {
                'installer': 'NS_Rel_20.sp1_1.606.Linux-x86_64.bin',
                'patch': 'IP.ns.20.sp1.606.ip20141117.Linux-x86_64.tar.gz'
            },
            '21.sp1.551': {
                'installer': 'NS_Rel_21.sp1_1.551.Linux-x86_64.bin',
                'patch': 'IP.ns.21.sp1.551.ip20150224.Linux-x86_64.tar.gz'
            }
        },
        'options': {
            'SERVER_TYPE': 'NetworkServer',
            'REDHOSTNAME': socket.getfqdn(),
            'REDPRIMARYHOSTNAME': socket.getfqdn(),
            'REDPRIMARY': 'true',
            'REDPEERS': '{%s->%s,}' % (socket.getfqdn(), socket.getfqdn()),
            'REDREPPORT': '17888',
            'JASS': 'false',
            'FTP_ON': 'true',
            'TFTP_ON': 'false',
            'TELNET_ON': 'true',
            'NTP_SERVER': 'pool.ntp.org',
            'REDUNDANTSERVER': 'false',
            'HAS_DATABASE': 'true',
            'SERVER_DSN': 'NetworkServer',
            'SERVER_CLIENT_DSN': 'NetworkServerClient',
            'MAINTENANCE_DSN': 'Maintenance',
            'MAINTENANCE_CLIENT_DSN': 'MaintenanceClient',
            'SERVER_PHYSICAL_STORE': 'NetworkServer',
            'DSN_SIZE': '512',
            'TEMP_SIZE': '170',
            'USE_TT_LOG_DIR': 'false',
            'IMS_MODE': 'false',
            'DIALPLAN.32': 'TRUE',
            'DIALPLAN.34': 'TRUE',
            'DIALPLAN.39': 'TRUE',
            'DIALPLAN.41': 'TRUE',
            'DIALPLAN.44': 'TRUE',
            'DIALPLAN.49': 'TRUE'
        }
    },
    'ps': {
        'software': {
            '17.sp4.197': {
                'installer': 'PS_Rel_17.sp4_1.197.Linux-x86_64.bin',
                'patch': 'IP.ps.17.sp4.197.ip20130426.Linux-x86_64.tar.gz'
            },
            '18.0.890': {
                'installer': 'PS_Rel_18.0_1.890.Linux-x86_64.bin',
                'patch': 'IP.ps.18.0.890.ip20130121.Linux-x86_64.tar.gz'
            },
            '20.sp1.606': {
                'installer': 'PS_Rel_20.sp1_1.606.Linux-x86_64.bin',
                'patch': 'IP.ps.20.sp1.606.ip20141117.Linux-x86_64.tar.gz'
            },
            '21.sp1.551': {
                'installer': 'PS_Rel_21.sp1_1.551.Linux-x86_64.bin',
                'patch': 'IP.ps.21.sp1.551.ip20150720.Linux-x86_64.tar.gz'
            }
        },
        'options': {
            'SERVER_TYPE': 'ProfileServer',
            'JASS': 'false',
            'NTP_SERVER': 'pool.ntp.org',
            'FTP_ON': 'false',
            'TFTP_ON': 'false',
            'VIRTUALIZATION_ON': 'false',
            'TELNET_ON': 'true'
        }
    },
    'xsp': {
        'software': {
            '17.sp4.197': {
                'installer': 'XSP_Rel_17.sp4_1.197.Linux-x86_64.bin',
                'patch': 'IP.xsp.17.sp4.197.ip20130426.Linux-x86_64.tar.gz'
            },
            '18.0.890': {
                'installer': 'XSP_Rel_18.0_1.890.Linux-x86_64.bin',
                'patch': 'IP.xsp.18.0.890.ip20121210.Linux-x86_64.tar.gz'
            },
            '20.sp1.606': {
                'installer': 'XSP_Rel_20.sp1_1.606.Linux-x86_64.bin',
                'patch': 'IP.xsp.20.sp1.606.ip20141117.Linux-x86_64.tar.gz'
            },
            '21.sp1.551': {
                'installer': 'XSP_Rel_21.sp1_1.551.Linux-x86_64.bin',
                'patch': 'IP.xsp.21.sp1.551.ip20150224.Linux-x86_64.tar.gz',
            }
        },
        'options': {
            'SERVER_TYPE': 'XtendedServicesPlatform',
            'JASS': 'false',
            'NTP_SERVER': 'pool.ntp.org',
            'FTP_ON': 'false',
            'TFTP_ON': 'false',
            'VIRTUALIZATION_ON': 'false',
            'TELNET_ON': 'true'
        }
    },
}

packages = ['imake.x86_64', 'basesystem.noarch', 'gdb.x86_64', 'nss-softokn-freebl.x86_64', 'gpm-libs.x86_64',
            'bash.x86_64', 'unzip.x86_64', 'info.x86_64', 'libjpeg-turbo.x86_64', 'libtalloc.x86_64', 'nss-util.x86_64',
            'alsa-lib.x86_64', 'sed.x86_64', 'libmng.x86_64', 'libstdc++.x86_64', 'atk.x86_64', 'libgpg-error.x86_64',
            'libcollection.x86_64', 'grep.x86_64', 'libXfont.x86_64', 'libidn.x86_64', 'libvorbis.x86_64',
            'libgcrypt.x86_64', 'urw-fonts.noarch', 'checkpolicy.x86_64', 'libnl.x86_64', 'pth.x86_64', 'cvs.x86_64',
            'p11-kit.x86_64', 'patch.x86_64', 'nss-softokn.x86_64', 'gmp.x86_64', 'libxcb.x86_64', 'psmisc.x86_64',
            'pam_ldap.x86_64', 'procps.x86_64', 'poppler.x86_64', 'pinentry.x86_64', 'cups.x86_64', 'make.x86_64',
            'xz-lzma-compat.x86_64', 'less.x86_64', 'ed.x86_64', 'cracklib-dicts.x86_64', 'libgudev1.x86_64',
            'hwdata.noarch', 'perl-ExtUtils-MakeMaker.x86_64', 'nss.x86_64', 'libX11-common.noarch', 'logrotate.x86_64',
            'cairo.x86_64', 'keyutils-libs.x86_64', 'libXrandr.x86_64', 'libcurl.x86_64', 'libXt.x86_64',
            'rpm-libs.x86_64', 'libXtst.x86_64', 'mysql-libs.x86_64', 'mesa-dri1-drivers.x86_64', 'libcap-ng.x86_64',
            'time.x86_64', 'python-pycurl.x86_64', 'redhat-lsb-printing.x86_64', 'python-iniparse.noarch',
            'phonon-backend-gstreamer.x86_64', 'ustr.x86_64', 'redhat-lsb-compat.x86_64', 'gamin.x86_64',
            'nss-pam-ldapd.x86_64', 'grubby.x86_64', 'compat-expat1.x86_64', 'dbus-glib.x86_64', 'libss.x86_64',
            'iptables.x86_64', 'libselinux-devel.x86_64', 'initscripts.x86_64', 'openssl-devel.x86_64',
            'device-mapper-event-libs.x86_64', 'e2fsprogs.x86_64', 'cryptsetup-luks-libs.x86_64',
            'syslinux-nonlinux.noarch', 'plymouth.x86_64', 'cronie-anacron.x86_64', 'dosfstools.x86_64',
            'selinux-policy.noarch', 'glibc-common.x86_64', 'dracut-kernel.noarch', 'glibc-devel.x86_64',
            'system-config-firewall-base.noarch', 'nscd.x86_64', 'openssh-clients.x86_64', 'dhclient.x86_64',
            'grub.x86_64', 'bridge-utils.x86_64', 'nmap.x86_64', 'perl-Pod-Simple.x86_64', 'lm_sensors-libs.x86_64',
            'mpfr.x86_64', 'boost-wave.x86_64', 'boost-serialization.x86_64', 'ppl.x86_64', 'libtool-ltdl.x86_64',
            'libtool.x86_64', 'lm_sensors.x86_64', 'libgcc.x86_64', 'filesystem.x86_64', 'xinetd.x86_64',
            'ncurses-base.x86_64', 'tzdata.noarch', 'elfutils-libelf-devel.x86_64', 'vim-common.x86_64',
            'ncurses-libs.x86_64', 'vim-enhanced.x86_64', 'libattr.x86_64', 'bind-utils.x86_64', 'zlib.x86_64',
            'popt.x86_64', 'fontconfig.x86_64', 'audit-libs.x86_64', 'libpng.x86_64', 'libacl.x86_64', 'libSM.x86_64',
            'nspr.x86_64', 'qt.x86_64', 'readline.x86_64', 'libtiff.x86_64', 'libselinux.x86_64', 'libtdb.x86_64',
            'shadow-utils.x86_64', 'libogg.x86_64', 'libuuid.x86_64', 'libldb.x86_64', 'libblkid.x86_64',
            'libfontenc.x86_64', 'file-libs.x86_64', 'foomatic-db-filesystem.noarch', 'dbus-libs.x86_64',
            'openjpeg-libs.x86_64', 'pcre.x86_64', 'gnutls.x86_64', 'lua.x86_64', 'mesa-dri-filesystem.x86_64',
            'cyrus-sasl-lib.x86_64', 'xorg-x11-font-utils.x86_64', 'expat.x86_64', 'libtheora.x86_64',
            'elfutils-libelf.x86_64', 'qt-sqlite.x86_64', 'bzip2.x86_64', 'samba4-libs.x86_64',
            'libselinux-utils.x86_64', 'xml-common.noarch', 'cpio.x86_64', 'libpath_utils.x86_64', 'libxml2.x86_64',
            'pixman.x86_64', 'tcp_wrappers-libs.x86_64', 'c-ares.x86_64', 'libtasn1.x86_64', 'gettext.x86_64',
            'p11-kit-trust.x86_64', 'gstreamer.x86_64', 'device-mapper-persistent-data.x86_64', 'libvisual.x86_64',
            'libnih.x86_64', 'libdhash.x86_64', 'file.x86_64', 'bc.x86_64', 'libusb.x86_64', 'libXau.x86_64',
            'libutempter.x86_64', 'mailx.x86_64', 'net-tools.x86_64', 'gdbm-devel.x86_64', 'tar.x86_64',
            'libref_array.x86_64', 'db4-utils.x86_64', 'poppler-data.noarch', 'poppler-utils.x86_64', 'binutils.x86_64',
            'dbus.x86_64', 'diffutils.x86_64', 'foomatic-db-ppds.noarch', 'dash.x86_64', 'xz.x86_64', 'groff.x86_64',
            'man.x86_64', 'coreutils-libs.x86_64', 'libsss_idmap.x86_64', 'cracklib.x86_64', 'cdparanoia-libs.x86_64',
            'coreutils.x86_64', 'cyrus-sasl-gssapi.x86_64', 'module-init-tools.x86_64', 'db4-cxx.x86_64',
            'redhat-logos.noarch', 'perl-Test-Harness.x86_64', 'libpciaccess.x86_64', 'perl-ExtUtils-ParseXS.x86_64',
            'nss-sysinit.x86_64', 'perl-Test-Simple.x86_64', 'openldap.x86_64', 'libX11.x86_64', 'libedit.x86_64',
            'libXrender.x86_64', 'mingetty.x86_64', 'libXi.x86_64', 'libXcursor.x86_64', 'libssh2.x86_64',
            'libXft.x86_64', 'gnupg2.x86_64', 'libXdamage.x86_64', 'curl.x86_64', 'ghostscript.x86_64', 'rpm.x86_64',
            'qt3.x86_64', 'fipscheck.x86_64', 'libXxf86vm.x86_64', 'ethtool.x86_64', 'mesa-libGL.x86_64',
            'plymouth-core-libs.x86_64', 'mesa-libGLU.x86_64', 'libffi.x86_64', 'libXcomposite.x86_64',
            'python-libs.x86_64', 'hicolor-icon-theme.noarch', 'python-urlgrabber.noarch', 'redhat-lsb-core.x86_64',
            'rpm-python.x86_64', 'slang.x86_64', 'newt-python.x86_64', 'libsemanage.x86_64', 'pkgconfig.x86_64',
            'glib2.x86_64', 'libuser.x86_64', 'yum-metadata-parser.x86_64', 'yum.noarch', 'dhcp-common.x86_64',
            'policycoreutils.x86_64', 'iproute.x86_64', 'util-linux-ng.x86_64', 'udev.x86_64', 'device-mapper.x86_64',
            'openssh.x86_64', 'lvm2-libs.x86_64', 'tcpdump.x86_64', 'device-mapper-multipath-libs.x86_64',
            'mtools.x86_64', 'libdrm.x86_64', 'rsyslog.x86_64', 'postfix.x86_64', 'cronie.x86_64',
            'iptables-ipv6.x86_64', 'kbd-misc.noarch', 'dracut.noarch', 'kernel.x86_64',
            'selinux-policy-targeted.noarch', 'device-mapper-multipath.x86_64', 'lvm2.x86_64', 'openssh-server.x86_64',
            'b43-openfwwf.noarch', 'iscsi-initiator-utils.x86_64', 'authconfig.x86_64', 'efibootmgr.x86_64',
            'audit.x86_64', 'xfsprogs.x86_64', 'attr.x86_64', 'rootfiles.noarch', 'libpcap.x86_64', 'screen.x86_64',
            'perl-Pod-Escapes.x86_64', 'perl-version.x86_64', 'perl-Module-Pluggable.x86_64', 'boost-system.x86_64',
            'boost-filesystem.x86_64', 'boost-thread.x86_64', 'libicu.x86_64', 'boost-date-time.x86_64',
            'boost-graph.x86_64', 'automake.noarch', 'tcl.x86_64', 'dmidecode.x86_64', 'ntpdate.x86_64',
            'libgomp.x86_64', 'cloog-ppl.x86_64', 'boost-program-options.x86_64', 'boost-signals.x86_64', 'gcc.x86_64',
            'gcc-c++.x86_64', 'boost.x86_64', 'ntp.x86_64', 'libthai.x86_64', 'gstreamer-plugins-base.x86_64',
            'qt-x11.x86_64', 'redhat-lsb-graphics.x86_64', 'redhat-lsb.x86_64', 'sssd.x86_64', 'lsof.x86_64',
            'expat-devel.x86_64', 'libcom_err.x86_64', 'openssl.x86_64', 'e2fsprogs-libs.x86_64',
            'libsepol-devel.x86_64', 'zlib-devel.x86_64', 'krb5-devel.x86_64', 'perl-WWW-Curl.x86_64',
            'openssl-static.x86_64', 'parted.x86_64', 'glibc.x86_64', 'net-snmp-libs.x86_64', 'glibc-headers.x86_64',
            'net-snmp.x86_64', 'sysstat.x86_64', 'expect.x86_64', 'setup.noarch', 'compat-libstdc++-33.x86_64',
            'kernel-firmware.noarch', 'libaio-devel.x86_64', 'bind-libs.x86_64', 'libcap.x86_64', 'freetype.x86_64',
            'chkconfig.x86_64', 'libICE.x86_64', 'db4.x86_64', 'libtevent.x86_64', 'libsepol.x86_64',
            'lcms-libs.x86_64', 'bzip2-libs.x86_64', 'jasper-libs.x86_64', 'gawk.x86_64', 'avahi-libs.x86_64',
            'libudev.x86_64', 'cups-libs.x86_64', 'sqlite.x86_64', 'ghostscript-fonts.noarch', 'xz-libs.x86_64',
            'pytalloc.x86_64', 'findutils.x86_64', 'iso-codes.noarch', 'which.x86_64', 'mesa-private-llvm.x86_64',
            'sysvinit-tools.x86_64', 'gstreamer-tools.x86_64', 'ca-certificates.noarch', 'pax.x86_64', 'upstart.x86_64',
            'tmpwatch.x86_64', 'MAKEDEV.x86_64', 'portreserve.x86_64', 'vim-minimal.x86_64', 'libini_config.x86_64',
            'liboil.x86_64', 'm4.x86_64', 'foomatic-db.noarch', 'ncurses.x86_64', 'perl-CGI.x86_64', 'gzip.x86_64',
            'libipa_hbac.x86_64', 'pam.x86_64', 'db4-devel.x86_64', 'plymouth-scripts.x86_64', 'perl-devel.x86_64',
            'nss-tools.x86_64', 'libXext.x86_64', 'gdbm.x86_64', 'libXfixes.x86_64', 'libXinerama.x86_64',
            'gpgme.x86_64', 'foomatic.x86_64', 'fipscheck-lib.x86_64', 'mesa-dri-drivers.x86_64',
            'pciutils-libs.x86_64', 'libXv.x86_64', 'python.x86_64', 'at.x86_64', 'pygpgme.x86_64', 'pango.x86_64',
            'newt.x86_64', 'gtk2.x86_64', 'libaio.x86_64', 'sssd-client.x86_64', 'shared-mime-info.x86_64',
            'rsync.x86_64', 'yum-plugin-fastestmirror.noarch', 'krb5-libs.x86_64', 'centos-release.x86_64',
            'libcom_err-devel.x86_64', 'iputils.x86_64', 'keyutils-libs-devel.x86_64', 'device-mapper-libs.x86_64',
            'openssl-perl.x86_64', 'device-mapper-event.x86_64', 'kpartx.x86_64', 'genisoimage.x86_64',
            'cyrus-sasl.x86_64', 'wodim.x86_64', 'crontabs.noarch', 'kbd.x86_64', 'kernel-headers.x86_64',
            'fuse.x86_64', 'ksh.x86_64', 'cryptsetup-luks.x86_64', 'mdadm.x86_64', 'passwd.x86_64', 'sudo.x86_64',
            'acl.x86_64', 'dstat.noarch', 'perl-libs.x86_64', 'perl.x86_64', 'autoconf.noarch', 'boost-regex.x86_64',
            'cpp.x86_64', 'boost-python.x86_64', 'boost-iostreams.x86_64', 'boost-test.x86_64',
            'libstdc++-devel.x86_64', 'unixODBC.x86_64']

ordered_configs = OrderedDict(sorted(configs.items(), key=lambda t: t[0]))


def opts():
    usage = '%s [-u url] [-n names] [-p prefix]' % sys.argv[0]
    op = OptionParser(usage=usage)
    release_help = '\n'
    vers = []
    for t in sorted(ordered_configs.keys()):
        vers.extend(ordered_configs[t]['software'].keys())
    op.add_option('-a', '--auto', dest='autoinstall', action='store_true', help='Auto update, configure, reboot & install')
    op.add_option('-t', '--type', dest='type', help='\n'.join(sorted(ordered_configs.keys())))
    op.add_option('-r', '--release', dest='release', help=', '.join(sorted(set(vers))))
    op.add_option('--prep', dest='sysprep', action='store_true',
                  help='Download/update required packages & configure system')
    op.add_option('--skipprep', dest='skipprep', action='store_true',
                  help='Skip system prep')
    op.add_option('--install', dest='install', action='store_true',
                  help='Perform install assuming system is configured already')
    op.add_option('--download', dest='download_only', action='store_true', help='Download software only')
    (o, args) = op.parse_args()
    result = {}
    if o.type and o.release:
        result['type'] = o.type
        result['options'] = ordered_configs[o.type]['options']
        result['release'] = o.release
    if not result:
        print
        op.print_help()
        print "\n\n \x1b[36m*** Defaulting to interactive menu, ctl+c to cancel ***\x1b[0m "
        return None, o
    else:
        return result, o


def createUnattenededInstallConfig(save_as, server_config):
    config = dict(general_options.items() + server_config.items())
    createDirForFile(save_as)
    try:
        fh = open(save_as, 'w')
        for k, v in config.iteritems():
            if type(v) == str:
                fh.write("%s=%s\n" % (k, v))
            if type(v) == set:
                fh.write("".join(["%s=%s\n" % (k, v) for v in v]))
        fh.close()
        logger.info("\x1b[32mCreated unattended installation file %s\x1b[0m" % save_as)
    except IOError, e:
        logger.error("\x1b[31mUnattended config build failed: %s\x1b[0m" % e)


def chunk_report(bytes_so_far, chunk_size, total_size):
    percent = float(bytes_so_far) / total_size
    percent = round(percent * 100, 2)
    sys.stdout.write("Downloaded %d of %d bytes (%0.2f%%)\r" %
                     (bytes_so_far, total_size, percent))
    if bytes_so_far >= total_size:
        sys.stdout.write('\n')


def get_latest_swman():
    try:
        request = urllib2.Request(swm_url)
        base64string = base64.encodestring('%s:%s' % (XCHANGE_USERNAME, XCHANGE_PASSWORD)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        result = urllib2.urlopen(request)
        data = result.read()
        return [x for x in sorted(data.splitlines()) if x.endswith('.bin')][-1]
    except:
        logger.error('\x1b[31mUnable to identify latest software manager version, defaulting to version: 549314\x1b[0m')
        return 'swmanager_549314.bin'


def download(base_url, item, save_as=None, chunk_size=8192, report_hook=chunk_report):
    if save_as:
        createDirForFile(save_as)
    request = urllib2.Request(base_url + item)
    base64string = base64.encodestring('%s:%s' % (XCHANGE_USERNAME, XCHANGE_PASSWORD)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    response = urllib2.urlopen(request)
    total_size = response.info().getheader('Content-Length').strip()
    total_size = int(total_size)
    bytes_so_far = 0
    fh = open(save_as or item, 'w')
    while 1:
        chunk = response.read(chunk_size)
        fh.write(chunk)
        bytes_so_far += len(chunk)
        if not chunk:
            break
        if report_hook:
            report_hook(bytes_so_far, chunk_size, total_size)
    fh.close()
    logger.info("\x1b[32mWrote file %s\x1b[0m" % save_as)
    return bytes_so_far


def createDirForFile(item):
    if '/' not in item:
        return
    if not os.path.isdir(os.path.dirname(item)):
        try:
            os.makedirs(os.path.dirname(item))
            logger.info("\x1b[32mCreated directory %s\x1b[0m" % os.path.dirname(item))
        except OSError or IOError, e:
            logger.error("\x1b[31mFailed to make directory: %s\x1b[0m" % e)


def setExecute(item):
    try:
        st = os.stat(item)
        os.chmod(item, st.st_mode | stat.S_IXOTH)
        logger.info("\x1b[32mSet mode +x on %s\x1b[0m" % item)
    except Exception, e:
        logger.error("\x1b[31m%s\x1b[0m" % e)


def configure_os():
    while True:
        ans = raw_input("Do you wish to pre-configure the OS and reboot? [y/n]: ").lower()
        if ans == 'n':
            break
        if ans != 'y':
            continue
        logger.info("\x1b[32mDisabling selinux\x1b[0m")
        subprocess.Popen('sed -i.orig -e s/SELINUX=.*$/SELINUX=disabled/g /etc/selinux/config', shell=True).wait()
        sleep(0.5)
        logger.info("\x1b[32mChanging snmpd OID\x1b[0m")
        subprocess.Popen('sed -i.orig -e s/.1.3.6.1.2.1.1/.1.3.6.1.2.1/g /etc/snmp/snmpd.conf', shell=True).wait()
        sleep(0.5)
        logger.info("\x1b[32mUpdating sysstat collection to every 5 minuets\x1b[0m")
        subprocess.Popen(
            "sed -i.orig 's|\*/[0-9]\+ \* \* \* \* root /usr/lib64/sa/sa1|\*/5 \* \* \* \* root /usr/lib64/sa/sa1|g' /etc/cron.d/sysstat",
            shell=True).wait()
        sleep(0.5)
        logger.info("\x1b[32mAdding snmpd to 3 4 5 runlevels\x1b[0m")
        subprocess.Popen(
            '/sbin/chkconfig --add snmpd; /sbin/chkconfig --level 345 snmpd resetpriorities; /etc/init.d/snmpd start',
            shell=True).wait()
        sleep(0.5)
        logger.info("\x1b[32mDisabling iptables\x1b[0m")
        subprocess.Popen('/etc/init.d/iptables stop; /sbin/chkconfig iptables off', shell=True).wait()
        sleep(0.5)
        logger.info("\x1b[32mDisabled ipv6\x1b[0m")
        with open('/etc/sysctl.conf', 'a+') as fh:
            fh.write('\nnet.ipv6.conf.all.disable_ipv6 = 1\n')
            fh.write('net.ipv6.conf.default.disable_ipv6 = 1\n')
            fh.write('net.ipv6.conf.lo.disable_ipv6 = 1\n')
        logger.info("\x1b[32mBroadworks prerequisites complete.\x1b[0m")


def menu():
    global ordered_configs
    output = "\n"
    for n, item in enumerate(ordered_configs):
        output += "  %d. %s\n" % (n, item.upper())
    print output
    while True:
        ans = raw_input("<> select server type (eg: 0 or AS): ")
        try:
            type, data = ordered_configs.items()[int(ans)]
            data['software'] = OrderedDict(sorted(data['software'].items(), key=lambda t: t[0]))
        except ValueError:
            type = ordered_configs[ans.lower()]
        except:
            raise
        output = "\n"
        for n, item in enumerate(data['software']):
            output += "  %d. %s\n" % (n, item.upper())
        print output
        ans = raw_input("<> select release number: ")
        try:
            release, result = data['software'].items()[int(ans)]
        except ValueError:
            release, result = data['software'][ans.lower()]
        except:
            raise
        result['type'] = type
        result['options'] = data['options']
        result['release'] = release
        return result


def main():
    if not os.geteuid() == 0:
        logger.critical("\x1b[31mMust be executed as root user\x1b[0m")
        sys.exit(1)
    result, o = opts()
    if not result:
        result = menu()
        if result.get('type') and result.get('release'):
            o.autoinstall = True
    if o.autoinstall or o.sysprep or not o.skipprep:
        subprocess.Popen('yum -y install %s' % ' '.join(packages), shell=True).wait()
        sleep(1)
        configure_os()
        while True:
            ans = raw_input("\x1b[34mReboot and trigger automated Broadworks installation? y/n: \x1b[0m")
            if ans == 'y' or ans == 'Y':
                subprocess.Popen('echo "python /root/bwbootstrap.py --autoinstall --type=%s --release=%s" >> /root/.bashrc'
                                 % (result.get('type'), result.get('release')), shell=True).wait()
                sleep(0.5)
                logger.info("\x1b[32mAutolaunch armed, rebooting.....\x1b[0m")
                os.system('reboot')
            if ans == 'n' or ans == 'N':
                break
        sys.exit()
    if o.autoinstall or o.install:
        path = '/bw/install/'
        logger.info("\x1b[32mBootstrapping install for Broadworks %s %s \x1b[0m" % (
            result.get('options').get('SERVER_TYPE'), result.get('release')))
        download(bss_url.replace('__RELEASE__', result.get('release')), result.get('installer'),
                 "%s%s" % (path, result.get('installer')))
        download(ips_url.replace('__RELEASE__', result.get('release')), result.get('patch'),
                 "%s%s" % (path, result.get('patch')))
        swmanager = get_latest_swman()
        download(swm_url, swmanager, "%s%s" % (path, swmanager))
        setExecute("%s%s" % (path, swmanager))
        setExecute("%s%s" % (path, result.get('installer')))
        createUnattenededInstallConfig("%sunattended.conf" % path, result.get('options'))
        if not o.download_only:
            os.chdir(path)
            subprocess.Popen(
                './%s -patch %s%s %s%s' % (result.get('installer'), path, result.get('patch'), path, "unattended.conf"),
                shell=True).wait()
            subprocess.Popen("sed -i '/python \/root\/bwbootstrap.py --install/d' /root/.bashrc", shell=True).wait()
    logger.info("\x1b[32mFinished\x1b[0m")


if __name__ == '__main__':
    main()
