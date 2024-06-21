#   Version 20170103
#
# *** DEPRECATED ***
#
#
# This file contains potential attribute/value pairs to use when configuring
# Windows registry monitoring. The procmon-filters.conf file contains the
# regular expressions you create to refine and filter the processes you want
# Khulnasoft to monitor. You must restart Khulnasoft to enable configurations.
#
# To learn more about configuration files (including precedence) please see the
# documentation located at
# http://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/Aboutconfigurationfiles

#### find out if this file is still being used.

[<stanza name>]
* Name of the filter being defined.

proc = <string>
* Regex specifying process image that you want Khulnasoft to monitor.

type = <string>
* Regex specifying the type(s) of process event that you want Khulnasoft to
  monitor.

hive = <string>
* Not used in this context, but should always have value ".*"
