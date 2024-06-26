#   Version 20170103
#
# This file contains attribute/value pairs for configuring externalized strings
# in messages.conf.
#
# There is a messages.conf in $KHULNASOFT_HOME/etc/system/default/.  To set custom
# configurations, place a messages.conf in $KHULNASOFT_HOME/etc/system/local/. You
# must restart Khulnasoft to enable configurations.
#
# To learn more about configuration files (including precedence) please see the
# documentation located at
# http://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/Aboutconfigurationfiles
#
# For the full list of all messages that can be overridden, check out
# $KHULNASOFT_HOME/etc/system/default/messages.conf
#
# The full name of a message resource is component_key + ':' + message_key.
# After a descriptive message key, append two underscores, and then use the
# letters after the % in printf style formatting, surrounded by underscores.
#
# For example, assume the following message resource is defined:
#
#   [COMPONENT:MSG_KEY__D_LU_S]
#   message = FunctionX returned %d, expected %lu.
#   action  = See %s for details.
#
# The message key expected 3 printf style arguments (%d, %lu, %s), which can be
# in either the message or action fields but mist appear in the same order.
#
# In addition to the printf style arguments above, some custom UI patterns are
# allowed in the message and action fields. These patterns will be rendered by
# the UI before displaying the text.
#
# For example, linking to a specific Khulnasoft page can be done using this pattern:
#
#   [COMPONENT:MSG_LINK__S]
#   message = License key '%s' is invalid.
#   action  = See [[/manager/system/licensing|Licensing]] for details.
#
# Another custom formatting option is for date/time arguments. If the argument
# should be rendered in local time and formatted to a specific langauge, simply
# provide the unix timestamp and prefix the printf style argument with "$t".
# This will hint that the argument is actually a timestamp (not a number) and
# should be formatted into a date/time string.
#
# The language and timezone used to render the timestamp is determined during
# render time given the current user viewing the message - it is not required to
# provide these details here.
#
# For example, assume the following message resource is defined:
#
#   [COMPONENT:TIME_BASED_MSG__LD]
#   message = Component exception @ $t%ld.
#   action  = See khulnasoftd.log for details.
#
# The first argument is prefixed with "$t", and therefore will be treated as a
# unix timestamp. It will be formatted as a date/time string.
#
# For these and other examples, check out
# $KHULNASOFT_HOME/etc/system/README/messages.conf.example
#


############################################################################
# Component
############################################################################

[<component>]

name = <string>
* The human-readable name used to prefix all messages under this component
* Required

############################################################################
# Message
############################################################################

[<component>:<key>]

message = <string>
* The message string describing what and why something happened
* Required

action = <string>
* The action string describing the next steps in reaction to the message
* Defaults to nothing

severity = critical|error|warn|info|debug
* The severity of the message
* Defaults to warn

capabilities = <capability list>
* The capabilities required to view the message, comma separated
* Defaults to nothing

help = <location string>
* The location string to link users to specific documentation
* Defaults to nothing
