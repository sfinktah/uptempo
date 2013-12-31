uptempo
=======

** Modify Temperature of certain 3D printers derived from Delta Micro Factory Corporation **
---

* This has only been tested on Mac OS. *

** Theory of Operation **

* Send print to printer
* Quit application
* Run this script

It would seem, that even if you re re-initialise and re-print a previous job, the temperature settings will stay.  But when printing a new job, it seems to reset temperature.

---

Tested on Mac OS X, requires python usb library (I forget what it's called, probably py-usb).

You can initialise, "re-print last job", or what not... but if you send a new print job, it will change the temperature back to default.

You can even reload the factory application and watch the print temperature and progress and what not.


