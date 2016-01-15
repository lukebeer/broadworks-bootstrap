# broadworks-bootstrap
CentOS/RHEL 5/6/7 fresh install to running installed &amp; running Broadworks Rel17/18/20/21 AS/NS/MS/PS/XSP while the kettle is brewing.

```
[root@as1 ~]# python bwbootstrap.py 

Usage: bwbootstrap.py [-u url] [-n names] [-p prefix]

Options:
  -h, --help            show this help message and exit
  -a, --auto            Auto update, configure, reboot & install
  -t TYPE, --type=TYPE  as ms ns ps xsp
  -r RELEASE, --release=RELEASE
                        17.sp4.197, 18.0.890, 20.sp1.606, 21.sp1.551
  --prep                Download/update required packages & configure system
  --skipprep            Skip system prep
  --install             Perform install assuming system is configured already
  --download            Download software only


 *** Defaulting to interactive menu, ctl+c to cancel *** 

  0. AS
  1. MS
  2. NS
  3. PS
  4. XSP

<> select server type (eg: 0 or AS): 
```
