@placement search-head
#   Version 20170103
#
# This file contains possible attributes and values for configuring global
# saved search actions in alert_actions.conf.  Saved searches are configured
# in savedsearches.conf.
#
# There is an alert_actions.conf in $KHULNASOFT_HOME/etc/system/default/.
# To set custom configurations, place an alert_actions.conf in
# $KHULNASOFT_HOME/etc/system/local/.  For examples, see
# alert_actions.conf.example. You must restart Khulnasoft to enable
# configurations.
#
# To learn more about configuration files (including precedence) please see
# the documentation located at
# http://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/Aboutconfigurationfiles

# GLOBAL SETTINGS
# Use the [default] stanza to define any global settings.
#  * You can also define global settings outside of any stanza, at the top
#    of the file.
#  * Each conf file should have at most one default stanza. If there are
#    multiple default stanzas, attributes are combined. In the case of
#    multiple definitions of the same attribute, the last definition in the
#    file wins.
#  * If an attribute is defined at both the global level and in a specific
#    stanza, the value in the specific stanza takes precedence.

maxresults = <integer>
* Set the global maximum number of search results sent via alerts.
* Defaults to 100.

hostname = [protocol]<host>[:<port>]
* Sets the hostname used in the web link (url) sent in alerts.
* This value accepts two forms.
  * hostname
       examples: khulnasoftserver, khulnasoftserver.example.com
  * protocol://hostname:port
       examples: http://khulnasoftserver:8000, https://khulnasoftserver.example.com:443
* When this value is a simple hostname, the protocol and port which
  are configured within khulnasoft are used to construct the base of
  the url.
* When this value begins with 'http://', it is used verbatim.
  NOTE: This means the correct port must be specified if it is not
  the default port for http or https.
* This is useful in cases when the Khulnasoft server is not aware of
  how to construct an externally referenceable url, such as SSO
  environments, other proxies, or when the Khulnasoft server hostname
  is not generally resolvable.
* Defaults to current hostname provided by the operating system,
  or if that fails, "localhost".
* When set to empty, default behavior is used.

ttl     = <integer>[p]
* Optional argument specifying the minimum time to live (in seconds)
  of the search artifacts, if this action is triggered.
* If p follows integer, then integer is the number of scheduled periods.
* If no actions are triggered, the artifacts will have their ttl determined
  by the "dispatch.ttl" attribute in savedsearches.conf.
* Defaults to 10p
* Defaults to 86400 (24 hours)   for: email, rss
* Defaults to   600 (10 minutes) for: script
* Defaults to   120 (2 minutes)  for: summary_index, populate_lookup

maxtime = <integer>[m|s|h|d]
* The maximum amount of time that the execution of an action is allowed to
  take before the action is aborted.
* Use the d, h, m and s suffixes to define the period of time:
  d = day, h = hour, m = minute and s = second.
  For example: 5d means 5 days.
* Defaults to 5m for everything except rss.
* Defaults to 1m for rss.

track_alert = [1|0]
* Indicates whether the execution of this action signifies a trackable alert.
* Defaults to 0 (false).

command = <string>
* The search command (or pipeline) which is responsible for executing
  the action.
* Generally the command is a template search pipeline which is realized
  with values from the saved search - to reference saved search
  field values wrap them in dollar signs ($).
* For example, to reference the savedsearch name use $name$. To
  reference the search, use $search$

is_custom = [1|0]
* Specifies whether the alert action is based on the custom alert
  actions framework and is supposed to be listed in the search UI.

payload_format = [xml|json]
* Configure the format the alert script receives the configuration via
  STDIN.
* Defaults to "xml"

label = <string>
* For custom alert actions: Define the label shown in the UI. If not
  specified, the stanza name will be used instead.

description = <string>
* For custom alert actions: Define the description shown in the UI.

icon_path = <string>
* For custom alert actions: Define the icon shown in the UI for the alert
  action. The path refers to appserver/static within the app where the
  alert action is defined in.

alert.execute.cmd = <string>
* For custom alert actions: Explicitly specify the command to be executed
  when the alert action is triggered. This refers to a binary or script
  in the bin folder of the app the alert action is defined in, or to a
  path pointer file, also located in the bin folder.
* If a path pointer file (*.path) is specified, the contents of the file
  is read and the result is used as the command to be executed.
  Environment variables in the path pointer file are substituted.
* If a python (*.py) script is specified it will be prefixed with the
  bundled python interpreter.

alert.execute.cmd.arg.<n> = <string>
* Provide additional arguments to the alert action execution command.
  Environment variables are substituted.

################################################################################
# EMAIL: these settings are prefaced by the [email] stanza name
################################################################################

[email]
* Set email notification options under this stanza name.
* Follow this stanza name with any number of the following
  attribute/value pairs.
* If you do not specify an entry for each attribute, Khulnasoft will
  use the default value.

from = <string>
* Email address from which the alert originates.
* Defaults to khulnasoft@$LOCALHOST.

to      = <string>
* The To email address receiving the alert.

cc      = <string>
* Any cc email addresses receiving the alert.

bcc     = <string>
* Any bcc email addresses receiving the alert.

message.report = <string>
* Specify a custom email message for scheduled reports.
* Includes the ability to reference attributes from the result,
  saved search, or job

message.alert = <string>
* Specify a custom email message for alerts.
* Includes the ability to reference attributes from result,
  saved search, or job

subject = <string>
* Specify an alternate email subject if useNSSubject is false.
* Defaults to KhulnasoftAlert-<savedsearchname>.

subject.alert = <string>
* Specify an alternate email subject for an alert.
* Defaults to KhulnasoftAlert-<savedsearchname>.

subject.report = <string>
* Specify an alternate email subject for a scheduled report.
* Defaults to KhulnasoftReport-<savedsearchname>.

useNSSubject = [1|0]
* Specify whether to use the namespaced subject (i.e subject.report) or
  subject.

footer.text = <string>
* Specify an alternate email footer.
* Defaults to "If you believe you've received this email in error, please see your Khulnasoft administrator.\r\n\r\nkhulnasoft > the engine for machine data."

format = [table|raw|csv]
* Specify the format of inline results in the email.
* Accepted values:  table, raw, and csv.
* Previously accepted values plain and html are no longer respected
  and equate to table.
* To make emails plain or html use the content_type attribute.

include.results_link = [1|0]
* Specify whether to include a link to the results.

include.search = [1|0]
* Specify whether to include the search that caused an email to be sent.

include.trigger = [1|0]
* Specify whether to show the trigger condition that caused the alert to
  fire.

include.trigger_time = [1|0]
* Specify whether to show the time that the alert was fired.

include.view_link = [1|0]
* Specify whether to show the title and a link to enable the user to edit
  the saved search.

content_type = [html|plain]
* Specify the content type of the email.
  * plain sends email as plain text
  * html sends email as a multipart email that include both text and html.

sendresults = [1|0]
* Specify whether the search results are included in the email. The
  results can be attached or inline, see inline (action.email.inline)
* Defaults to 0 (false).

inline = [1|0]
* Specify whether the search results are contained in the body of the alert
  email.
* If the events are not sent inline, they are attached as a csv text.
* Defaults to 0 (false).

priority = [1|2|3|4|5]
* Set the priority of the email as it appears in the email client.
* Value mapping: 1 highest, 2 high, 3 normal, 4 low, 5 lowest.
* Defaults to 3.

mailserver = <host>[:<port>]
* You must have a Simple Mail Transfer Protocol (SMTP) server available
  to send email. This is not included with Khulnasoft.
* Specifies the SMTP mail server to use when sending emails.
* <host> can be either the hostname or the IP address.
* Optionally, specify the SMTP <port> that Khulnasoft should connect to.
* When the "use_ssl" attribute (see below) is set to 1 (true), you
  must specify both <host> and <port>.
  (Example: "example.com:465")
* Defaults to $LOCALHOST:25.

use_ssl    = [1|0]
* Whether to use SSL when communicating with the SMTP server.
* When set to 1 (true), you must also specify both the server name or
  IP address and the TCP port in the "mailserver" attribute.
* Defaults to 0 (false).

use_tls    = [1|0]
* Specify whether to use TLS (transport layer security) when
  communicating with the SMTP server (starttls)
* Defaults to 0 (false).

auth_username   = <string>
* The username to use when authenticating with the SMTP server. If this is
  not defined or is set to an empty string, no authentication is attempted.
  NOTE: your SMTP server might reject unauthenticated emails.
* Defaults to empty string.

auth_password   = <password>
* The password to use when authenticating with the SMTP server.
  Normally this value will be set when editing the email settings, however
  you can set a clear text password here and it will be encrypted on the
  next Khulnasoft restart.
* Defaults to empty string.

sendpdf = [1|0]
* Specify whether to create and send the results as a PDF.
* Defaults to 0 (false).

sendcsv = [1|0]
* Specify whether to create and send the results as a csv file.
* Defaults to 0 (false).

pdfview = <string>
* Name of view to send as a PDF

reportPaperSize = [letter|legal|ledger|a2|a3|a4|a5]
* Default paper size for PDFs
* Accepted values: letter, legal, ledger, a2, a3, a4, a5
* Defaults to "letter".

reportPaperOrientation = [portrait|landscape]
* Paper orientation: portrait or landscape
* Defaults to "portrait".

reportIncludeKhulnasoftLogo = [1|0]
* Specify whether to include a Khulnasoft logo in Integrated PDF Rendering
* Defaults to 1 (true)

reportCIDFontList = <string>
* Specify the set (and load order) of CID fonts for handling
  Simplified Chinese(gb), Traditional Chinese(cns),
  Japanese(jp), and Korean(kor) in Integrated PDF Rendering.
* Specify in a space-separated list
* If multiple fonts provide a glyph for a given character code, the glyph
  from the first font specified in the list will be used
* To skip loading any CID fonts, specify the empty string
* Defaults to "gb cns jp kor"

reportFileName = <string>
    * Specify the name of attached pdf or csv
    * Defaults to "$name$-$time:%Y-%m-%d$"

width_sort_columns = <bool>
* Whether columns should be sorted from least wide to most wide left to right.
* Valid only if format=text
* Defaults to true

preprocess_results = <search-string>
* Supply a search string to Khulnasoft to preprocess results before emailing
  them. Usually the preprocessing consists of filtering out unwanted
  internal fields.
* Defaults to empty string (no preprocessing)

pdf.footer_enabled = [1 or 0]
  * Set whether or not to display footer on PDF.
  * Defaults to 1.

pdf.header_enabled = [1 or 0]
  * Set whether or not to display header on PDF.
  * Defaults to 1.

pdf.logo_path = <string>
  * Define pdf logo by syntax <app>:<path-to-image>
  * If set, PDF will be rendered with this logo instead of Khulnasoft one.
  * If not set, Khulnasoft logo will be used by default
  * Logo will be read from $KHULNASOFT_HOME/etc/apps/<app>/appserver/static/<path-to-image> if <app> is provided.
  * Current app will be used if <app> is not provided.

pdf.header_left = [logo|title|description|timestamp|pagination|none]
  * Set which element will be displayed on the left side of header.
  * Nothing will be display if this option is not been set or set to none
  * Defaults to None, nothing will be displayed on this position.

pdf.header_center = [logo|title|description|timestamp|pagination|none]
  * Set which element will be displayed on the center of header.
  * Nothing will be display if this option is not been set or set to none
  * Defaults to description

pdf.header_right = [logo|title|description|timestamp|pagination|none]
  * Set which element will be displayed on the right side of header.
  * Nothing will be display if this option is not been set or set to none
  * Defaults to None, nothing will be displayed on this position.

pdf.footer_left = [logo|title|description|timestamp|pagination|none]
  * Set which element will be displayed on the left side of footer.
  * Nothing will be display if this option is not been set or set to none
  * Defaults to logo

pdf.footer_center = [logo|title|description|timestamp|pagination|none]
  * Set which element will be displayed on the center of footer.
  * Nothing will be display if this option is not been set or set to none
  * Defaults to title

pdf.footer_right = [logo|title|description|timestamp|pagination|none]
  * Set which element will be displayed on the right side of footer.
  * Nothing will be display if this option is not been set or set to none
  * Defaults to timestamp,pagination

pdf.html_image_rendering = <bool>
  * Whether images in HTML should be rendered.
  * If enabling rendering images in HTML breaks the pdf for whatever reason,
  * it could be disabled by setting this flag to False,
  * so the old HTML rendering will be used.
  * Defaults to True.

sslVersions = <versions_list>
* Comma-separated list of SSL versions to support.
* The versions available are "ssl3", "tls1.0", "tls1.1", and "tls1.2".
* The special version "*" selects all supported versions.  The version "tls"
  selects all versions tls1.0 or newer.
* If a version is prefixed with "-" it is removed from the list.
* SSLv2 is always disabled; "-ssl2" is accepted in the version list but does nothing.
* When configured in FIPS mode, ssl3 is always disabled regardless
  of this configuration.
* Defaults to "*,-ssl2" (anything newer than SSLv2).

sslVerifyServerCert = true|false
* If this is set to true, you should make sure that the server that is
  being connected to is a valid one (authenticated).  Both the common
  name and the alternate name of the server are then checked for a
  match if they are specified in this configuration file.  A
  certificiate is considered verified if either is matched.
* If this is set to true, make sure 'server.conf/[sslConfig]/sslRootCAPath'
  has been set correctly.
* Default is false.

sslCommonNameToCheck = <commonName1>, <commonName2>, ...
* Optional. Defaults to no common name checking.
* Check the common name of the server's certificate against this list of names.
* 'sslVerifyServerCert' must be set to true for this setting to work.

sslAltNameToCheck =  <alternateName1>, <alternateName2>, ...
* Optional. Defaults to no alternate name checking.
* Check the alternate name of the server's certificate against this list of names.
* If there is no match, assume that Khulnasoft is not authenticated against this
  server.
* 'sslVerifyServerCert' must be set to true for this setting to work.

cipherSuite = <cipher suite string>
* If set, Khulnasoft uses the specified cipher string for the communication with
  with the SMTP server.
* If not set, Khulnasoft uses the default cipher string provided by OpenSSL.
* This is used to ensure that the client does not make connections using
  weak encryption protocols.
* Default is 'TLSv1+HIGH:TLSv1.2+HIGH:@STRENGTH'.

################################################################################
# RSS: these settings are prefaced by the [rss] stanza
################################################################################

[rss]
* Set RSS notification options under this stanza name.
* Follow this stanza name with any number of the following
  attribute/value pairs.
* If you do not specify an entry for each attribute, Khulnasoft will
  use the default value.

items_count = <number>
* Number of saved RSS feeds.
* Cannot be more than maxresults (in the global settings).
* Defaults to 30.

################################################################################
# script: Used to configure any scripts that the alert triggers.
################################################################################
[script]
filename = <string>
* The filename, with no path, of the script to trigger.
* The script should be located in: $KHULNASOFT_HOME/bin/scripts/
* For system shell scripts on Unix, or .bat or .cmd on windows, there
  are no further requirements.
* For other types of scripts, the first line should begin with a #!
  marker, followed by a path to the interpreter that will run the script.
  * Example: #!C:\Python27\python.exe
* Defaults to empty string.

################################################################################
# summary_index: these settings are prefaced by the [summary_index] stanza
################################################################################
[summary_index]
inline = [1|0]
* Specifies whether the summary index search command will run as part of the
  scheduled search or as a follow-on action. This is useful when the results
  of the scheduled search are expected to be large.
* Defaults to 1 (true).

_name = <string>
* The name of the summary index where Khulnasoft will write the events.
* Defaults to "summary".

################################################################################
# populate_lookup: these settings are prefaced by the [populate_lookup] stanza
################################################################################
[populate_lookup]
dest = <string>
* Name of the lookup table to populate (stanza name in transforms.conf) or
  the lookup file path to where you want the data written. If a path is
  specified it MUST be relative to $KHULNASOFT_HOME and a valid lookups
  directory.
  For example: "etc/system/lookups/<file-name>" or
  "etc/apps/<app>/lookups/<file-name>"
* The user executing this action MUST have write permissions to the app for
  this action to work properly.

[<custom_alert_action>]
