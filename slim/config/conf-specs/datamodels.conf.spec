@placement search-head
#   Version 20170103
#
# This file contains possible attribute/value pairs for configuring
# data models.  To configure a datamodel for an app, put your custom
# datamodels.conf in $KHULNASOFT_HOME/etc/apps/MY_APP/local/

# For examples, see datamodels.conf.example.  You must restart Khulnasoft to
# enable configurations.

# To learn more about configuration files (including precedence) please see
# the documentation located at
# http://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/Aboutconfigurationfiles

# GLOBAL SETTINGS
# Use the [default] stanza to define any global settings.
#   * You can also define global settings outside of any stanza, at the top
#     of the file.
#   * Each conf file should have at most one default stanza. If there are
#     multiple default stanzas, attributes are combined. In the case of
#     multiple definitions of the same attribute, the last definition in the
#     file wins.
#   * If an attribute is defined at both the global level and in a specific
#     stanza, the value in the specific stanza takes precedence.


[<datamodel_name>]
* Each stanza represents a data model. The data model name is the stanza name.

acceleration = <bool>
* Set acceleration to true to enable automatic acceleration of this data model.
* Automatic acceleration creates auxiliary column stores for the fields
  and values in the events for this datamodel on a per-bucket basis.
* These column stores take additional space on disk, so be sure you have the
  proper amount of disk space. Additional space required depends on the
  number of events, fields, and distinct field values in the data.
* The Khulnasoft software creates and maintains these column stores on a schedule
  you can specify with 'acceleration.cron_schedule.' You can query
  them with the 'tstats' command.

acceleration.earliest_time = <relative-time-str>
* Specifies how far back in time the Khulnasoft software should keep these column
  stores (and create if acceleration.backfill_time is not set).
* Specified by a relative time string. For example, '-7d' means 'accelerate
  data within the last 7 days.'
* Defaults to an empty string, meaning 'keep these stores for all time.'

acceleration.backfill_time = <relative-time-str>
* ADVANCED: Specifies how far back in time the Khulnasoft software should create
  its column stores.
* ONLY set this parameter if you want to backfill less data than the
  retention period set by 'acceleration.earliest_time'. You may want to use
  this parameter to limit your time window for column store creation in a large
  environment where initial creation of a large set of column stores is an
  expensive operation.
* WARNING: Do not set 'acceleration.backfill_time' to a
  narrow time window. If one of your indexers is down for a period longer
  than this backfill time, you may miss accelerating a window of your incoming
  data.
* MUST be set to a more recent time than 'acceleration.earliest_time'. For
  example, if you set 'acceleration.earliest_time' to '-1y' to retain your
  column stores for a one year window, you could set 'acceleration.backfill_time'
  to '-20d' to create column stores that only cover the last 20 days. However,
  you cannot set 'acceleration.backfill_time' to '-2y', because that goes
  farther back in time than the 'acceleration.earliest_time' setting of '-1y'.
* Defaults to empty string (unset). When 'acceleration.backfill_time' is unset,
  the Khulnasoft software always backfills fully to 'acceleration.earliest_time.'

acceleration.max_time = <unsigned int>
* The maximum amount of time that the column store creation search is
  allowed to run (in seconds).
* Note that this is an approximate time, as the 'summarize' search only
  finishes on clean bucket boundaries to avoid wasted work.
* Defaults to: 3600
* An 'acceleration.max_time' setting of '0' indicates that there is no time
  limit.

acceleration.cron_schedule = <cron-string>
* Cron schedule to be used to probe/generate the column stores for this
  data model.
* Defaults to: */5 * * * *

acceleration.manual_rebuilds = <bool>
* ADVANCED: When set to 'true,' this setting prevents outdated summaries from
  being rebuilt by the 'summarize' command.
* Normally, during the creation phase, the 'summarize' command automatically
  rebuilds summaries that are considered to be out-of-date, such as when the
  configuration backing the data model changes.
* The Khulnasoft software considers a summary to be outdated when:
	* The data model search stored in its metadata no longer matches its current
	  data model search.
	* The search stored in its metadata cannot be parsed.
    * A lookup table associated with the data model is altered.
* NOTE: If the Khulnasoft software finds a partial summary be outdated, it always
  rebuilds that summary so that a bucket summary only has results corresponding to
  one datamodel search.
* Defaults to: false

acceleration.max_concurrent = <unsigned int>
* The maximum number of concurrent acceleration instances for this data
  model that the scheduler is allowed to run.
* Defaults to: 2

acceleration.schedule_priority = default | higher | highest
* Raises the scheduling priority of a search:
  + "default": No scheduling priority increase.
  + "higher": Scheduling priority is higher than other data model searches.
  + "highest": Scheduling priority is higher than other searches regardless of
    scheduling tier except real-time-scheduled searches with priority = highest
    always have priority over all other searches.
  + Hence, the high-to-low order (where RTSS = real-time-scheduled search, CSS
    = continuous-scheduled search, DMAS = data-model-accelerated search, d =
    default, h = higher, H = highest) is:
      RTSS(H) > DMAS(H) > CSS(H)
      > RTSS(h) > RTSS(d) > CSS(h) > CSS(d)
      > DMAS(h) > DMAS(d)
* The scheduler honors a non-default priority only when the search owner has
  the 'edit_search_schedule_priority' capability.
* Defaults to: default
* WARNING: Having too many searches with a non-default priority will impede the
  ability of the scheduler to minimize search starvation.  Use this setting
  only for mission-critical searches.

acceleration.hunk.compression_codec = <string>
* Applicable only to Hunk Data models. Specifies the compression codec to
  be used for the accelerated orc/parquet files.

acceleration.hunk.dfs_block_size = <unsigned int>
* Applicable only to Hunk data models. Specifies the block size in bytes for
  the compression files.

acceleration.hunk.file_format = <string>
* Applicable only to Hunk data models. Valid options are "orc" and "parquet"


#******** Dataset Related Attributes ******
# These attributes affect your interactions with datasets in Khulnasoft Web and should
# not be changed under normal conditions. Do not modify them unless you are sure you
# know what you are doing.

dataset.description = <string>
* User-entered description of the dataset entity.

dataset.type = [datamodel|table]
* The type of dataset:
  + "datamodel": An individual data model dataset.
  + "table": A special root data model dataset with a search where the dataset is
    defined by the dataset.commands attribute.
* Default: datamodel

dataset.commands = [<object>(, <object>)*]
* When the dataset.type = "table" this stringified JSON payload is created by the
  table editor and defines the dataset.

dataset.fields = [<string>(, <string>)*]
* Automatically generated JSON payload when dataset.type = "table" and the root
  data model dataset's search is updated.

dataset.display.diversity = [latest|random|diverse|rare]
* The user-selected diversity for previewing events contained by the dataset:
  + "latest": search a subset of the latest events
  + "random": search a random sampling of events
  + "diverse": search a diverse sampling of events
  + "rare": search a rare sampling of events based on clustering
* Default: latest

dataset.display.sample_ratio = <int>
* The integer value used to calculate the sample ratio for the dataset diversity.
  The formula is 1 / <int>.
* The sample ratio specifies the likelihood of any event being included in the
  sample.
* For example, if sample_ratio = 500 each event has a 1/500 chance of being
  included in the sample result set.
* Default: 1

dataset.display.limiting = <int>
* The limit of events to search over when previewing the dataset.
* Default: 100000

dataset.display.currentCommand = <int>
* The currently selected command the user is on while editing the dataset.

dataset.display.mode = [table|datasummary]
* The type of preview to use when editing the dataset:
  + "table": show individual events/results as rows.
  + "datasummary": show field values as columns.
* Default: table

dataset.display.datasummary.earliestTime = <time-str>
* The earliest time used for the search that powers the datasummary view of
  the dataset.

dataset.display.datasummary.latestTime = <time-str>
* The latest time used for the search that powers the datasummary view of
  the dataset.
