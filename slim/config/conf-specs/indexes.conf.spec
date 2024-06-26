@placement search-head, indexer
#   Version 20170103
#
# This file contains all possible options for an indexes.conf file.  Use
# this file to configure Khulnasoft's indexes and their properties.
#
# There is an indexes.conf in $KHULNASOFT_HOME/etc/system/default/.  To set
# custom configurations, place an indexes.conf in
# $KHULNASOFT_HOME/etc/system/local/. For examples, see indexes.conf.example.
# You must restart Khulnasoft to enable configurations.
#
# To learn more about configuration files (including precedence) please see
# the documentation located at
# http://docs.khulnasoft.com/Documentation/Khulnasoft/latest/Admin/Aboutconfigurationfiles
#
# CAUTION:  You can drastically affect your Khulnasoft installation by changing
# these settings.  Consult technical support
# (http://www.khulnasoft.com/page/submit_issue) if you are not sure how to
# configure this file.
#
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

sync = <nonnegative integer>
* The index processor syncs events every <integer> number of events.
* Set to 0 to disable.
* Highest legal value is 32767
* Defaults to 0.

defaultDatabase = <index name>
* If no index is specified during search, Khulnasoft searches the default index.
* The specified index displays as the default in Khulnasoft Manager settings.
* Defaults to "main".

queryLanguageDefinition = <path to file>
* DO NOT EDIT THIS SETTING. SERIOUSLY.
* The path to the search language definition file.
* Defaults to $KHULNASOFT_HOME/etc/searchLanguage.xml.

lastChanceIndex = <index name>
* Gives ability to define a last chance index for events destined for
  non-existent indexes.
* If an event arrives whose index destination key points to an index that is
  not configured (such as when using index=<index name> in the input stanza or
  by a setting in a transform), it will route that event to the index specified
  by this setting.  The index destination key of that event will be overwritten
  with the specified index name before routing.
* <index name> must name an existing enabled index.  Khulnasoft will not start if
  this is not the case.
* If this setting is not defined or is empty, it will drop such events.
* If set to "default", then the default index specified by the
  "defaultDatabase" will be used as a last chance index.
* Defaults to empty.

memPoolMB = <positive integer>|auto
* Determines how much memory is given to the indexer memory pool. This
  restricts the number of outstanding events in the indexer at any given
  time.
* Must be greater than 0; maximum value is 1048576 (which corresponds to 1 TB)
* Setting this too high can lead to khulnasoftd memory usage going up
  substantially.
* Setting this too low can degrade khulnasoftd indexing performance.
* Setting this to "auto" or an invalid value will cause Khulnasoft to autotune
  this parameter.
* Defaults to "auto".
  * The values derived when "auto" is seen are as follows:
    * System Memory Available less than ... | memPoolMB
                   1 GB                     |    64  MB
                   2 GB                     |    128 MB
                   8 GB                     |    128 MB
                   8 GB or higher           |    512 MB
* Only set this value if you are an expert user or have been advised to by
  Khulnasoft Support.
* CARELESSNESS IN SETTING THIS MAY LEAD TO PERMANENT BRAIN DAMAGE OR
  LOSS OF JOB.

indexThreads = <nonnegative integer>|auto
* Determines the number of threads to use for indexing.
* Must be at least 1 and no more than 16.
* This value should not be set higher than the number of processor cores in
  the box.
* If khulnasoftd is also doing parsing and aggregation, the number should be set
  lower than the total number of processors minus two.
* Setting this to "auto" or an invalid value will cause Khulnasoft to autotune
  this parameter.
* Only set this value if you are an expert user or have been advised to by
  Khulnasoft Support.
* CARELESSNESS IN SETTING THIS MAY LEAD TO PERMANENT BRAIN DAMAGE OR
  LOSS OF JOB.
* Defaults to "auto".

rtRouterThreads = 0|1
* Set this to 1 if you expect to use non-indexed real time searches regularly.  Index
  throughput drops rapidly if there are a handful of these running concurrently on the system.
* If you are not sure what "indexed vs non-indexed" real time searches are, see
  README of indexed_realtime* settings in limits.conf
* NOTE: This is not a boolean value, only 0 or 1 is accepted.  In the future, we
  may allow more than a single thread, but current implementation
  only allows one to create a single thread per pipeline set

rtRouterQueueSize = <positive integer>
* Defaults to 10000
* This setting is only relevant if rtRouterThreads != 0
* This queue sits between the indexer pipeline set thread (producer) and the rtRouterThread
* Changing the size of this queue may impact real time search performance

assureUTF8 = true|false
* Verifies that all data retrieved from the index is proper by validating
  all the byte strings.
  * This does not ensure all data will be emitted, but can be a workaround
    if an index is corrupted in such a way that the text inside it is no
    longer valid utf8.
* Will degrade indexing performance when enabled (set to true).
* Can only be set globally, by specifying in the [default] stanza.
* Defaults to false.

enableRealtimeSearch = true|false
* Enables real-time searches.
* Defaults to true.

suppressBannerList = <comma-separated list of strings>
* suppresses index missing warning banner messages for specified indexes
* Defaults to empty

maxRunningProcessGroups = <positive integer>
* khulnasoftd fires off helper child processes like khulnasoft-optimize,
  recover-metadata, etc.  This param limits how many child processes can be
  running at any given time.
* This maximum applies to entire khulnasoftd, not per index.  If you have N
  indexes, there will be at most maxRunningProcessGroups child processes,
  not N*maxRunningProcessGroups
* Must maintain maxRunningProcessGroupsLowPriority < maxRunningProcessGroups
* This is an advanced parameter; do NOT set unless instructed by Khulnasoft
  Support
* Highest legal value is 4294967295
* Defaults to 8 (note: up until 5.0 it defaulted to 20)

maxRunningProcessGroupsLowPriority = <positive integer>
* Of the maxRunningProcessGroups (q.v.) helper child processes, at most
  maxRunningProcessGroupsLowPriority may be low-priority (e.g. fsck) ones.
* This maximum applies to entire khulnasoftd, not per index.  If you have N
  indexes, there will be at most maxRunningProcessGroupsLowPriority
  low-priority child processes, not N*maxRunningProcessGroupsLowPriority
* Must maintain maxRunningProcessGroupsLowPriority < maxRunningProcessGroups
* This is an advanced parameter; do NOT set unless instructed by Khulnasoft
  Support
* Highest legal value is 4294967295
* Defaults to 1

bucketRebuildMemoryHint = <positive integer>[KB|MB|GB]|auto
* Suggestion for the bucket rebuild process for the size (bytes) of tsidx
  file it will try to build.
* Larger files use more memory in rebuild, but rebuild will fail if there is
  not enough.
* Smaller files make the rebuild take longer during the final optimize step.
* Note: this value is not a hard limit on either rebuild memory usage or
  tsidx size.
* This is an advanced parameter, do NOT set this unless instructed by Khulnasoft
  Support.
* Defaults to "auto", which varies by the amount of physical RAM on the host
  *  less than 2GB RAM = 67108864 (64MB) tsidx
  *  2GB to 8GB RAM = 134217728 (128MB) tsidx
  *  more than 8GB RAM = 268435456 (256MB) tsidx
* If not "auto", then must be 16MB-1GB.
* Value may be specified using a size suffix: "16777216" or "16MB" are
  equivalent.
* Inappropriate use of this parameter will cause khulnasoftd to not start if
  rebuild is required.
* Highest legal value (in bytes) is 4294967295

inPlaceUpdates = true|false
* If true, metadata updates are written to the .data files directly
* If false, metadata updates are written to a temporary file and then moved
  into place
* Intended for advanced debugging of metadata issues
* Setting this parameter to false (to use a temporary file) will impact
  indexing performance, particularly with large numbers of hosts, sources,
  or sourcetypes (~1 million, across all indexes.)
* This is an advanced parameter; do NOT set unless instructed by Khulnasoft
  Support
* Defaults to true

serviceOnlyAsNeeded = true|false
* Causes index service (housekeeping tasks) overhead to be incurred only
  after index activity.
* Indexer module problems may be easier to diagnose when this optimization
  is disabled (set to false).
* Defaults to true.

serviceSubtaskTimingPeriod = <positive integer>
* Subtasks of indexer service task will be timed on every Nth execution,
  where N = value of this parameter, in seconds.
* Smaller values will give greater accuracy; larger values will lessen timer
  overhead.
* Timer measurements will be found in metrics.log, marked
  "group=subtask_seconds, task=indexer_service"
* Highest legal value is 4294967295
* We strongly suggest value of this parameter divide evenly into value of
  'rotatePeriodInSecs' parameter.
* Defaults to 30

processTrackerServiceInterval = <nonnegative integer>
* Controls how often, in seconds, indexer checks status of the child OS
  processes it had launched to see if it can launch new processes for queued
  requests.
* If set to 0, indexer will check child process status every second.
* Highest legal value is 4294967295
* Defaults to 15

maxBucketSizeCacheEntries = <nonnegative integer>
* This value is not longer needed and its value is ignored.

tsidxStatsHomePath = <path on server>
* An absolute path that specifies where Khulnasoft creates namespace data with
  'tscollect' command
* If the directory does not exist, we attempt to create it.
* Optional. If this is unspecified, we default to the 'tsidxstats' directory
  under $KHULNASOFT_DB
* CAUTION: Path "$KHULNASOFT_DB" must be writable.

hotBucketTimeRefreshInterval = <positive integer>
* Controls how often each index refreshes the available hot bucket times
  used by the indexes REST endpoint.
* Refresh will occur every N times service is performed for each index.
  * For busy indexes, this is a multiple of seconds.
  * For idle indexes, this is a multiple of the second-long-periods in
    which data is received.
* This tunable is only intended to relax the frequency of these refreshes in
* the unexpected case that it adversely affects performance in unusual
  production scenarios.
* This time is tracked on a per-index basis, and thus can be adjusted
  on a per-index basis if needed.
* If, for some reason, you want have the index information refreshed with
  every service (and accept minor performance overhead), you can use the
  value 1.
* Defaults to 10 (services).

#**************************************************************************
# PER INDEX OPTIONS
# These options may be set under an [<index>] entry.
#
# Index names must consist of only numbers, letters, periods, underscores,
# and hyphens.
#**************************************************************************

disabled = true|false
* Toggles your index entry off and on.
* Set to true to disable an index.
* Defaults to false.

deleted = true
* If present, means that this index has been marked for deletion: if khulnasoftd
  is running, deletion is in progress; if khulnasoftd is stopped, deletion will
  re-commence on startup.
* Normally absent, hence no default.
* Do NOT manually set, clear, or modify value of this parameter.
* Seriously: LEAVE THIS PARAMETER ALONE.

homePath = <path on index server>
* An absolute path that contains the hotdb and warmdb for the index.
* It is recommended that you specify the path with the following syntax:
     homePath = $KHULNASOFT_DB/$_index_name/db
  At runtime, Khulnasoft expands "$_index_name" to the name of the index. For example,
  if the index name is "newindex", homePath becomes "$KHULNASOFT_DB/newindex/db".
* Khulnasoftd keeps a file handle open for warmdbs at all times.
* May contain a volume reference (see volume section below) in place of $KHULNASOFT_DB.
* CAUTION: The parent path "$KHULNASOFT_DB/$_index_name/" must be writable.
* Required. Khulnasoft will not start if an index lacks a valid homePath.
* Must restart khulnasoftd after changing this parameter; index reload will not
  suffice.
* We strongly recommend that you avoid the use of other environment variables in
  index paths, aside from the possible exception of KHULNASOFT_DB.
  * As an exception, KHULNASOFT_DB is explicitly managed by the provided software,
    so most possible downsides here do not exist.
  * Environment variables could be different from launch to launch of the
    software, causing severe problems with management of indexed data,
    including:
    * Data in the prior location will not be searchable.
    * The indexer may not be able to write to the new location, causing outages
      and/or data loss.
    * Writing to a new, unexpected location could lead to disk exhaustion
      causing additional operational problems.
    * Recovery from such a scenario will require manual intevention and bucket
      renaming, especially difficult in an index clustered environment.
    * In all circumstances, Khulnasoft Diag, the diagnostic tool we use to support
      you, will have no way to determine the correct values for the environment
      variables, so cannot reliably operate.  You may need to manually acquire
      information about your index buckets in troubleshooting scenarios.
  * Generally speaking, volumes provide a more appropriate way to control the
    storage location for indexes in a general way.

coldPath = <path on index server>
* An absolute path that contains the colddbs for the index.
* It is recommended that you specify the path with the following syntax:
     coldPath = $KHULNASOFT_DB/$_index_name/colddb
  At runtime, Khulnasoft expands "$_index_name" to the name of the index. For example,
  if the index name is "newindex", coldPath becomes "$KHULNASOFT_DB/newindex/colddb".
* Cold databases are opened as needed when searching.
* May contain a volume reference (see volume section below) in place of $KHULNASOFT_DB.
* CAUTION: Path must be writable.
* Required. Khulnasoft will not start if an index lacks a valid coldPath.
* Must restart khulnasoftd after changing this parameter; index reload will not
  suffice.
* We strongly recommend that you avoid the use of environment variables in
  index paths, aside from the possible exception of KHULNASOFT_DB.  See homePath
  for the complete rationale.

thawedPath = <path on index server>
* An absolute path that contains the thawed (resurrected) databases for the
  index.
* May NOT contain a volume reference.
* CAUTION: Path must be writable.
* Required. Khulnasoft will not start if an index lacks a valid thawedPath.
* Must restart khulnasoftd after changing this parameter; index reload will not
  suffice.
* We strongly recommend that you avoid the use of environment variables in
  index paths, aside from the possible exception of KHULNASOFT_DB.  See homePath
  for the complete rationale.

bloomHomePath = <path on index server>
* Location where the bloomfilter files for the index are stored.
* If specified, bloomHomePath must be defined in terms of a volume definition
  (see volume section below).
* If bloomHomePath is not specified, bloomfilter files for index will be
  stored inline, inside bucket directories.
* CAUTION: Path must be writable.
* Must restart khulnasoftd after changing this parameter; index reload will not
  suffice.
* We strongly recommend that you avoid the use of environment variables in
  index paths, aside from the possible exception of KHULNASOFT_DB.  See homePath
  for the complete rationale.

createBloomfilter = true|false
* Controls whether to create bloomfilter files for the index.
* TRUE: bloomfilter files will be created. FALSE: not created.
* Defaults to true.

summaryHomePath = <path on index server>
* An absolute path where transparent summarization results for data in this
  index should be stored. Must be different for each index and may be on any
  disk drive.
* It is recommended that you specify the path with the following syntax:
     summaryHomePath = $KHULNASOFT_DB/$_index_name/summary
  At runtime, Khulnasoft expands "$_index_name" to the name of the index. For example,
  if the index name is "newindex", summaryHomePath becomes "$KHULNASOFT_DB/newindex/summary".
* May contain a volume reference (see volume section below) in place of $KHULNASOFT_DB.
* Volume reference must be used if data retention based on data size is
  desired.
* CAUTION: Path must be writable.
* If not specified, Khulnasoft creates a directory 'summary' in the same
  location as homePath
* For example, if homePath is "/opt/khulnasoft/var/lib/khulnasoft/index1/db",
    then summaryHomePath would be "/opt/khulnasoft/var/lib/khulnasoft/index1/summary".
* CAUTION: The parent path "/opt/khulnasoft/var/lib/khulnasoft/index1" must be writable.
* Must restart khulnasoftd after changing this parameter; index reload will not
  suffice.
* We strongly recommend that you avoid the use of environment variables in
  index paths, aside from the possible exception of KHULNASOFT_DB.  See homePath
  for the complete rationale.
* Defaults to unset.

tstatsHomePath = <path on index server>
* Required.
* Location where datamodel acceleration TSIDX data for this index should be
  stored
* MUST be defined in terms of a volume definition (see volume section below)
* Must restart khulnasoftd after changing this parameter; index reload will not
  suffice.
* CAUTION: Path must be writable.
* Defaults to volume:_khulnasoft_summaries/$_index_name/datamodel_summary,
  where $_index_name is runtime-expanded to the name of the index

remotePath = <root path for remote volume, prefixed by a URI-like scheme>
* Optional.
* Presence of this parameter means that this index uses remote storage, instead
  of the local file system, as the main repository for bucket storage. The
  index processor works with a cache manager to fetch buckets locally, as
  necessary, for searching and to evict them from local storage as space fills
  up and they are no longer needed for searching.
* This setting must be defined in terms of a storageType=remote volume
  definition. See the volume section below.
* The path portion that follows the volume reference is relative to the path
  specified for the volume.  For example, if the path for a volume "v1" is
  "s3://bucket/path" and "remotePath" is "volume:v1/idx1",   then the fully
  qualified path will be "s3://bucket/path/idx1".  The rules for resolving the
  relative path with the absolute path specified in the volume can vary
  depending on the underlying storage type.
* If "remotePath" is specified, the "coldPath" and "thawedPath" attributes are
  ignored.  However, they still must be specified.

maxBloomBackfillBucketAge = <nonnegative integer>[smhd]|infinite
* If a (warm or cold) bloomfilter-less bucket is older than this, Khulnasoft
  will not create a bloomfilter for that bucket.
* When set to 0, bloomfilters are never backfilled
* When set to "infinite", bloomfilters are always backfilled
* NB that if createBloomfilter=false, bloomfilters are never backfilled
  regardless of the value of this parameter
* Highest legal value in computed seconds is 2 billion, or 2000000000, which
  is approximately 68 years.
* Defaults to 30d.

enableOnlineBucketRepair = true|false
* Controls asynchronous "online fsck" bucket repair, which runs concurrently
  with Khulnasoft
* When enabled, you do not have to wait until buckets are repaired, to start
  Khulnasoft
* When enabled, you might observe a slight performance degradation
* Defaults to true.

enableDataIntegrityControl = true|false
* If set to true, hashes are computed on the rawdata slices and stored for
  future data integrity checks
* If set to false, no hashes are computed on the rawdata slices
* It has a global default value of false

# The following options can be set either per index or globally (as defaults
# for all indexes).  Defaults set globally are overridden if set on a
# per-index basis.

maxWarmDBCount = <nonnegative integer>
* The maximum number of warm buckets.
* Warm buckets are located in the <homePath> for the index.
* If set to zero, Khulnasoft will not retain any warm buckets
  (will roll them to cold as soon as it can)
* Highest legal value is 4294967295
* Defaults to 300.

maxTotalDataSizeMB = <nonnegative integer>
* The maximum size of an index (in MB).
* If an index grows larger than the maximum size, the oldest data is frozen.
* This parameter only applies to hot, warm, and cold buckets.  It does not
  apply to thawed buckets.
* Highest legal value is 4294967295
* Defaults to 500000.

maxGlobalDataSizeMB = <nonnegative integer>
* The maximum amount of local disk space (in MB) that a remote storage
  enabled index can occupy, shared across all peers in the cluster.
* This attribute controls the disk space that the index occupies on the peers
  only. It does not control the space that the index occupies on remote storage.
* If the size that an index occupies across all peers exceeds the maximum size,
  the oldest data is frozen.
* For example, assume that the attribute is set to 500 for a four-peer cluster,
  and each peer holds a 100 MB bucket for the index. If a new bucket of size
  200 MB is then added to one of the peers, the cluster freezes the oldest bucket
  in the cluster, no matter which peer the bucket resides on.
* This value applies only to hot and warm buckets. It does not apply to cold
  or thawed buckets.
* The maximum allowable value is 4294967295
* Defaults to 0, which means that it does not limit the space that the index
  can occupy on the peers.

rotatePeriodInSecs = <positive integer>
* Controls the service period (in seconds): how often khulnasoftd performs
  certain housekeeping tasks.  Among these tasks are:
  * Check if a new hotdb needs to be created.
  * Check if there are any cold DBs that should be frozen.
  * Check whether buckets need to be moved out of hot and cold DBs, due to
    respective size constraints (i.e., homePath.maxDataSizeMB and
    coldPath.maxDataSizeMB)
* This value becomes the default value of the rotatePeriodInSecs attribute
  for all volumes (see rotatePeriodInSecs in the Volumes section)
* Highest legal value is 4294967295
* Defaults to 60.

frozenTimePeriodInSecs = <nonnegative integer>
* Number of seconds after which indexed data rolls to frozen.
* If you do not specify a coldToFrozenScript, data is deleted when rolled to
  frozen.
* IMPORTANT: Every event in the DB must be older than frozenTimePeriodInSecs
  before it will roll. Then, the DB will be frozen the next time khulnasoftd
  checks (based on rotatePeriodInSecs attribute).
* Highest legal value is 4294967295
* Defaults to 188697600 (6 years).

warmToColdScript = <script path>
* Specifies a script to run when moving data from warm to cold.
* This attribute is supported for backwards compatibility with versions
  older than 4.0.  Migrating data across filesystems is now handled natively
  by khulnasoftd.
* If you specify a script here, the script becomes responsible for moving
  the event data, and Khulnasoft-native data migration will not be used.
* The script must accept two arguments:
  * First: the warm directory (bucket) to be rolled to cold.
  * Second: the destination in the cold path.
* Searches and other activities are paused while the script is running.
* Contact Khulnasoft Support (http://www.khulnasoft.com/page/submit_issue) if you
  need help configuring this setting.
* The script must be in $KHULNASOFT_HOME/bin or a subdirectory thereof.
* Defaults to empty.

coldToFrozenScript = [path to script interpreter] <path to script>
* Specifies a script to run when data will leave the khulnasoft index system.
  * Essentially, this implements any archival tasks before the data is
    deleted out of its default location.
* Add "$DIR" (quotes included) to this setting on Windows (see below
  for details).
* Script Requirements:
  * The script must accept one argument:
    * An absolute path to the bucket directory to archive.
  * Your script should work reliably.
    * If your script returns success (0), Khulnasoft will complete deleting
      the directory from the managed index location.
    * If your script return failure (non-zero), Khulnasoft will leave the bucket
      in the index, and try calling your script again several minutes later.
    * If your script continues to return failure, this will eventually cause
      the index to grow to maximum configured size, or fill the disk.
  * Your script should complete in a reasonable amount of time.
    * If the script stalls indefinitely, it will occupy slots.
    * This script should not run for long as it would occupy
      resources which will affect indexing.
* If the string $DIR is present in this setting, it will be expanded to the
  absolute path to the directory.
* If $DIR is not present, the directory will be added to the end of the
  invocation line of the script.
  * This is important for Windows.
    * For historical reasons, the entire string is broken up by
      shell-pattern expansion rules.
    * Since windows paths frequently include spaces, and the windows shell
      breaks on space, the quotes are needed for the script to understand
      the directory.
* If your script can be run directly on your platform, you can specify just
  the script.
  * Examples of this are:
    * .bat and .cmd files on Windows
    * scripts set executable on UNIX with a #! shebang line pointing to a
      valid interpreter.
* You can also specify an explicit path to an interpreter and the script.
    * Example:  /path/to/my/installation/of/python.exe path/to/my/script.py

* Khulnasoft ships with an example archiving script in that you SHOULD NOT USE
  $KHULNASOFT_HOME/bin called coldToFrozenExample.py
  * DO NOT USE the example for production use, because:
    * 1 - It will be overwritten on upgrade.
    * 2 - You should be implementing whatever requirements you need in a
          script of your creation.  If you have no such requirements, use
          coldToFrozenDir
* Example configuration:
  * If you create a script in bin/ called our_archival_script.py, you could use:
    UNIX:
        coldToFrozenScript = "$KHULNASOFT_HOME/bin/python" "$KHULNASOFT_HOME/bin/our_archival_script.py"
    Windows:
        coldToFrozenScript = "$KHULNASOFT_HOME/bin/python" "$KHULNASOFT_HOME/bin/our_archival_script.py" "$DIR"
* The example script handles data created by different versions of khulnasoft
  differently. Specifically data from before 4.2 and after are handled
  differently. See "Freezing and Thawing" below:
* The script must be in $KHULNASOFT_HOME/bin or a subdirectory thereof.

coldToFrozenDir = <path to frozen archive>
* An alternative to a coldToFrozen script - simply specify a destination
  path for the frozen archive
* Khulnasoft will automatically put frozen buckets in this directory
* For information on how buckets created by different versions are
  handled, see "Freezing and Thawing" below.
* If both coldToFrozenDir and coldToFrozenScript are specified,
  coldToFrozenDir will take precedence
* Must restart khulnasoftd after changing this parameter; index reload will not
  suffice.
* May NOT contain a volume reference.

# Freezing and Thawing (this should move to web docs
4.2 and later data:
  * To archive: remove files except for the rawdata directory, since rawdata
    contains all the facts in the bucket.
  * To restore: run khulnasoft rebuild <bucket_dir> on the archived bucket, then
    atomically move the bucket to thawed for that index
4.1 and earlier data:
  * To archive: gzip the .tsidx files, as they are highly compressible but
    cannot be recreated
  * To restore: unpack the tsidx files within the bucket, then atomically
    move the bucket to thawed for that index

compressRawdata = true|false
* This parameter is ignored. The khulnasoftd process always compresses raw data.

maxConcurrentOptimizes = <nonnegative integer>
* The number of concurrent optimize processes that can run against the hot
  DB.
* This number should be increased if:
  * There are always many small tsidx files in the hot DB.
  * After rolling, there are many tsidx files in warm or cold DB.
* Must restart khulnasoftd after changing this parameter; index reload will not
  suffice.
* Highest legal value is 4294967295
* Defaults to 6

maxDataSize = <positive integer>|auto|auto_high_volume
* The maximum size in MB for a hot DB to reach before a roll to warm is
  triggered.
* Specifying "auto" or "auto_high_volume" will cause Khulnasoft to autotune this
  parameter (recommended).
* You should use "auto_high_volume" for high-volume indexes (such as the
  main index); otherwise, use "auto".  A "high volume index" would typically
  be considered one that gets over 10GB of data per day.
* Defaults to "auto", which sets the size to 750MB.
* "auto_high_volume" sets the size to 10GB on 64-bit, and 1GB on 32-bit
  systems.
* Although the maximum value you can set this is 1048576 MB, which
  corresponds to 1 TB, a reasonable number ranges anywhere from 100 to
  50000.  Before proceeding with any higher value, please seek approval of
  Khulnasoft Support.
* If you specify an invalid number or string, maxDataSize will be auto
  tuned.
* NOTE: The maximum size of your warm buckets may slightly exceed
  'maxDataSize', due to post-processing and timing issues with the rolling
  policy.

rawFileSizeBytes = <positive integer>
* Deprecated in version 4.2 and later. We will ignore this value.
* Rawdata chunks are no longer stored in individual files.
* If you really need to optimize the new rawdata chunks (highly unlikely),
  edit rawChunkSizeBytes

rawChunkSizeBytes = <positive integer>
* Target uncompressed size in bytes for individual raw slice in the rawdata
  journal of the index.
* If 0 is specified, rawChunkSizeBytes will be set to the default value.
* NOTE: rawChunkSizeBytes only specifies a target chunk size. The actual
  chunk size may be slightly larger by an amount proportional to an
  individual event size.
* WARNING: This is an advanced parameter. Only change it if you are
  instructed to do so by Khulnasoft Support.
* Must restart khulnasoftd after changing this parameter; index reload will not
  suffice.
* Highest legal value is 18446744073709551615
* Defaults to 131072 (128KB).

minRawFileSyncSecs = <nonnegative decimal>|disable
* How frequently we force a filesystem sync while compressing journal
  slices.  During this interval, uncompressed slices are left on disk even
  after they are compressed.  Then we force a filesystem sync of the
  compressed journal and remove the accumulated uncompressed files.
* If 0 is specified, we force a filesystem sync after every slice completes
  compressing.
* Specifying "disable" disables syncing entirely: uncompressed slices are
  removed as soon as compression is complete
* Some filesystems are very inefficient at performing sync operations, so
  only enable this if you are sure it is needed
* Must restart khulnasoftd after changing this parameter; index reload will not
  suffice.
* No exponent may follow the decimal.
* Highest legal value is 18446744073709551615
* Defaults to "disable".

maxMemMB = <nonnegative integer>
* The amount of memory to allocate for indexing.
* This amount of memory will be allocated PER INDEX THREAD, or, if
  indexThreads is set to 0, once per index.
* IMPORTANT:  Calculate this number carefully. khulnasoftd will crash if you set
  this number higher than the amount of memory available.
* The default is recommended for all environments.
* Highest legal value is 4294967295
* Defaults to 5.

maxHotSpanSecs = <positive integer>
* Upper bound of timespan of hot/warm buckets in seconds.
* NOTE: If you set this too small, you can get an explosion of hot/warm
  buckets in the filesystem.
* If you set this parameter to less than 3600, it will be automatically
  reset to 3600, which will then activate snapping behavior (see below).
* This is an advanced parameter that should be set
  with care and understanding of the characteristics of your data.
* If set to 3600 (1 hour), or 86400 (1 day), becomes also the lower bound
  of hot bucket timespans.  Further, snapping behavior (i.e. ohSnap)
  is activated, whereby hot bucket boundaries will be set at exactly the
  hour or day mark, relative to local midnight.
* Highest legal value is 4294967295
* Defaults to 7776000 seconds (90 days).
* Note that this limit will be applied per ingestion pipeline. For more
  information about multiple ingestion pipelines see parallelIngestionPipelines
  in server.conf.spec file.
* With N parallel ingestion pipelines, each ingestion pipeline will write to
  and manage its own set of hot buckets, without taking into account the state
  of hot buckets managed by other ingestion pipelines.  Each ingestion pipeline
  will independently apply this setting only to its own set of hot buckets.

maxHotIdleSecs = <nonnegative integer>
* Provides a ceiling for buckets to stay in hot status without receiving any
  data.
* If a hot bucket receives no data for more than maxHotIdleSecs seconds,
  Khulnasoft rolls it to warm.
* This setting operates independently of maxHotBuckets, which can also cause
  hot buckets to roll.
* A value of 0 turns off the idle check (equivalent to infinite idle time).
* Highest legal value is 4294967295
* Defaults to 0.

maxHotBuckets = <positive integer>
* Maximum hot buckets that can exist per index.
* When maxHotBuckets is exceeded, Khulnasoft rolls the least recently used (LRU)
  hot bucket to warm.
* Both normal hot buckets and quarantined hot buckets count towards this
  total.
* This setting operates independently of maxHotIdleSecs, which can also
  cause hot buckets to roll.
* Highest legal value is 4294967295
* Defaults to 3.
* Note that this limit will be applied per ingestion pipeline. For more
  information about multiple ingestion pipelines see parallelIngestionPipelines
  in server.conf.spec file.
* With N parallel ingestion pipelines the maximum number of hot buckets across
  all of the ingestion pipelines will be N * maxHotBuckets but maxHotBuckets
  for each ingestion pipeline.  Each ingestion pipeline will independently
  write to and manage up to maxHotBuckets number of hot buckets.  As a
  consequence of this, when multiple ingestion pipelines are used, there may
  be multiple (dependent on number of ingestion pipelines configured) hot
  buckets with events with overlapping time ranges.

minHotIdleSecsBeforeForceRoll = <nonnegative integer>|auto
* When there are no existing hot buckets that can fit new events because of
  their timestamps and the constraints on the index (refer to maxHotBuckets,
  maxHotSpanSecs and quarantinePastSecs), if any hot bucket has been idle
  (i.e. not receiving any data) for minHotIdleSecsBeforeForceRoll number of
  seconds, a new bucket will be created to receive these new events and the
  idle bucket will be rolled to warm.
* If no hot bucket has been idle for minHotIdleSecsBeforeForceRoll number of seconds,
  or if minHotIdleSecsBeforeForceRoll has been set to zero, then a best fit bucket
  will be chosen for these new events from the existing set of hot buckets.
* This setting operates independently of maxHotIdleSecs, which causes hot buckets
  to roll after they have been idle for maxHotIdleSecs number of seconds,
  *regardless* of whether new events can fit into the existing hot buckets or not
  due to an event timestamp.  minHotIdleSecsBeforeForceRoll, on the other hand,
  controls a hot bucket roll *only* under the circumstances when the timestamp
  of a new event cannot fit into the existing hot buckets given the other
  parameter constraints on the system (parameters such as maxHotBuckets,
  maxHotSpanSecs and quarantinePastSecs).
* auto: Specifying "auto" will cause Khulnasoft to autotune this parameter
  (recommended). The value begins at 600 seconds but automatically adjusts upwards for
  optimal performance. Specifically, the value will increase when a hot bucket rolls
  due to idle time with a significantly smaller size than maxDataSize. As a consequence,
  the outcome may be fewer buckets, though these buckets may span wider earliest-latest
  time ranges of events.
* 0: A value of 0 turns off the idle check (equivalent to infinite idle time).
  Setting this to zero means that we will never roll a hot bucket for the
  reason that an event cannot fit into an existing hot bucket due to the
  constraints of other parameters.  Instead, we will find a best fitting
  bucket to accommodate that event.
* Highest legal value is 4294967295.
* NOTE: If you set this configuration, there is a chance that this could lead to
  frequent hot bucket rolls depending on the value. If your index contains a
  large number of buckets whose size-on-disk falls considerably short of the
  size specified in maxDataSize, and if the reason for the roll of these buckets
  is due to "caller=lru", then setting the parameter value to a larger value or
  to zero may reduce the frequency of hot bucket rolls (see AUTO above). You may check
  khulnasoftd.log for a similar message below for rolls due to this setting.
    INFO  HotBucketRoller - finished moving hot to warm bid=_internal~0~97597E05-7156-43E5-85B1-B0751462D16B idx=_internal from=hot_v1_0 to=db_1462477093_1462477093_0 size=40960 caller=lru maxHotBuckets=3, count=4 hot buckets,evicting_count=1 LRU hots
* Defaults to "auto".

quarantinePastSecs = <positive integer>
* Events with timestamp of quarantinePastSecs older than "now" will be
  dropped into quarantine bucket.
* This is a mechanism to prevent the main hot buckets from being polluted
  with fringe events.
* Highest legal value is 4294967295
* Defaults to 77760000 (900 days).

quarantineFutureSecs = <positive integer>
* Events with timestamp of quarantineFutureSecs newer than "now" will be
  dropped into quarantine bucket.
* This is a mechanism to prevent main hot buckets from being polluted with
  fringe events.
* Highest legal value is 4294967295
* Defaults to 2592000 (30 days).

maxMetaEntries = <nonnegative integer>
* Sets the maximum number of unique lines in .data files in a bucket, which
  may help to reduce memory consumption
* If exceeded, a hot bucket is rolled to prevent further increase
* If your buckets are rolling due to Strings.data hitting this limit, the
  culprit may be the 'punct' field in your data.  If you do not use punct,
  it may be best to simply disable this (see props.conf.spec)
  * NOTE: since at least 5.0.x, large strings.data from punct will be rare.
* There is a delta between when maximum is exceeded and bucket is rolled.
* This means a bucket may end up with epsilon more lines than specified, but
  this is not a major concern unless excess is significant
* If set to 0, this setting is ignored (it is treated as infinite)
* Highest legal value is 4294967295

syncMeta = true|false
* When "true", a sync operation is called before file descriptor is closed
  on metadata file updates.
* This functionality was introduced to improve integrity of metadata files,
  especially in regards to operating system crashes/machine failures.
* NOTE: Do not change this parameter without the input of a Khulnasoft support
  professional.
* Must restart khulnasoftd after changing this parameter; index reload will not
  suffice.
* Defaults to true.

serviceMetaPeriod = <positive integer>
* Defines how frequently metadata is synced to disk, in seconds.
* Defaults to 25 (seconds).
* You may want to set this to a higher value if the sum of your metadata
  file sizes is larger than many tens of megabytes, to avoid the hit on I/O
  in the indexing fast path.
* Highest legal value is 4294967295

partialServiceMetaPeriod = <positive integer>
* Related to serviceMetaPeriod.  If set, it enables metadata sync every
  <integer> seconds, but only for records where the sync can be done
  efficiently in-place, without requiring a full re-write of the metadata
  file.  Records that require full re-write will be synced at
  serviceMetaPeriod.
* <integer> specifies how frequently it should sync.  Zero means that this
  feature is turned off and serviceMetaPeriod is the only time when metadata
  sync happens.
* If the value of partialServiceMetaPeriod is greater than
  serviceMetaPeriod, this setting will have no effect.
* By default it is turned off (zero).
* This parameter is ignored if serviceOnlyAsNeeded = true (the default).
* Highest legal value is 4294967295

throttleCheckPeriod = <positive integer>
* Defines how frequently Khulnasoft checks for index throttling condition,
  in seconds.
* NOTE: Do not change this parameter without the input of a Khulnasoft Support
  professional.
* Highest legal value is 4294967295
* Defaults to 15

maxTimeUnreplicatedWithAcks = <nonnegative decimal>
* Important if you have enabled indexer acknowledgements (ack) on forwarders
  and have replication enabled (via Index Clustering)
* This parameter puts an upper limit on how long events can sit unacknowledged
  in a raw slice
* To disable this, you can set to 0, but this is NOT recommended!!!
* NOTE: This is an advanced parameter; make sure you understand the settings
        on all your forwarders before changing this.  This number should not
        exceed ack timeout configured on any forwarders, and should indeed
        be set to at most half of the minimum value of that timeout.  You
        can find this setting in outputs.conf readTimeout setting, under
        the tcpout stanza.
* Highest legal value is 2147483647
* Defaults to 60 (seconds)

maxTimeUnreplicatedNoAcks = <nonnegative decimal>
* Important only if replication is enabled for this index, otherwise ignored
* This parameter puts an upper limit on how long an event can sit in raw
  slice.
* If there are any ack''d events sharing this raw slice, this parameter will
  not apply (maxTimeUnreplicatedWithAcks will be used instead)
* Highest legal value is 2147483647
* To disable this, you can set to 0; please be careful and understand the
  consequences before changing this parameter
* Defaults to 60 (seconds)

isReadOnly = true|false
* Set to true to make an index read-only.
* If true, no new events can be added to the index, but the index is still
  searchable.
* Must restart khulnasoftd after changing this parameter; index reload will not
  suffice.
* Defaults to false.

homePath.maxDataSizeMB = <nonnegative integer>
* Specifies the maximum size of homePath (which contains hot and warm
  buckets).
* If this size is exceeded, Khulnasoft will move buckets with the oldest value
  of latest time (for a given bucket) into the cold DB until homePath is
  below the maximum size.
* If this attribute is missing or set to 0, Khulnasoft will not constrain the
  size of homePath.
* Highest legal value is 4294967295
* Defaults to 0.

coldPath.maxDataSizeMB = <nonnegative integer>
* Specifies the maximum size of coldPath (which contains cold buckets).
* If this size is exceeded, Khulnasoft will freeze buckets with the oldest value
  of latest time (for a given bucket) until coldPath is below the maximum
  size.
* If this attribute is missing or set to 0, Khulnasoft will not constrain size
  of coldPath
* If we freeze buckets due to enforcement of this policy parameter, and
  coldToFrozenScript and/or coldToFrozenDir archiving parameters are also
  set on the index, these parameters *will* take into effect
* Highest legal value is 4294967295
* Defaults to 0.

disableGlobalMetadata = true|false
* NOTE: This option was introduced in 4.3.3, but as of 5.0 it is obsolete
  and ignored if set.
* It used to disable writing to the global metadata.  In 5.0 global metadata
  was removed.

repFactor = <nonnegative integer>|auto
* Only relevant if this instance is a clustering slave (but see note about
  "auto" below).
* See server.conf spec for details on clustering configuration.
* Value of 0 turns off replication for this index.
* If set to "auto", slave will use whatever value the master has.
* Highest legal value is 4294967295
* Defaults to 0.

minStreamGroupQueueSize = <nonnegative integer>
* Minimum size of the queue that stores events in memory before committing
  them to a tsidx file.  As Khulnasoft operates, it continually adjusts this
  size internally.  Khulnasoft could decide to use a small queue size and thus
  generate tiny tsidx files under certain unusual circumstances, such as
  file system errors.  The danger of a very low minimum is that it can
  generate very tiny tsidx files with one or very few events, making it
  impossible for khulnasoft-optimize to catch up and optimize the tsidx files
  into reasonably sized files.
* Defaults to 2000.
* Only set this value if you have been advised to by Khulnasoft Support.
* Highest legal value is 4294967295

streamingTargetTsidxSyncPeriodMsec = <nonnegative integer>
* Period we force sync tsidx files on streaming targets. This setting is
  needed for multi-site clustering where streaming targets may be primary.
* if set to 0, we never sync (equivalent to infinity)

journalCompression = gzip|lz4
* Select compression algorithm for rawdata journal file
* Defaults to gzip

enableTsidxReduction = true|false
* By enabling this setting, you turn on the tsidx reduction capability. This causes the
  indexer to reduce the tsidx files of buckets, when the buckets reach the age specified
  by timePeriodInSecBeforeTsidxReduction.
* Defaults to false.

suspendHotRollByDeleteQuery = true|false
* When the "delete" search command is run, all buckets containing data to be deleted are
  marked for updating of their metadata files. The indexer normally first rolls any hot buckets,
  as rolling must precede the metadata file updates.
* When suspendHotRollByDeleteQuery is set to true, the rolling of hot buckets for the "delete"
  command is suspended. The hot buckets, although marked, do not roll immediately, but instead
  wait to roll in response to the same circumstances operative for any other hot buckets; for
  example, due to reaching a limit set by maxHotBuckets, maxDataSize, etc. When these hot buckets
  finally roll, their metadata files are then updated.
* Defaults to false

tsidxReductionCheckPeriodInSec = <positive integer>
* Time period between service runs to reduce the tsidx files for any buckets that have
  reached the age specified by timePeriodInSecBeforeTsidxReduction.
* Defaults to 600 (seconds).

timePeriodInSecBeforeTsidxReduction = <positive integer>
* Age at which buckets become eligible for tsidx reduction.
  The bucket age is the difference between the current time
  and the timestamp of the bucket's latest event.
* Defaults to 604800 (seconds).

#**************************************************************************
# PER PROVIDER FAMILY OPTIONS
# A provider family is a way of collecting properties that are common to
# multiple providers. There are no properties that can only be used in a
# provider family, and not in a provider. If the same property is specified
# in a family, and in a provider belonging to that family, then the latter
# value "wins".
#
# All family stanzas begin with "provider-family:". For example:
# [provider-family:family_name]
# vix.mode=stream
# vix.command = java
# vix.command.arg.1 = -Xmx512m
# ....
#**************************************************************************

#**************************************************************************
# PER PROVIDER OPTIONS
# These options affect External Resource Providers. All provider stanzas
# begin with "provider:". For example:
#   [provider:provider_name]
#   vix.family                  = hadoop
#   vix.env.JAVA_HOME           = /path/to/java/home
#   vix.env.HADOOP_HOME         = /path/to/hadoop/client/libraries
#
# Each virtual index must reference a provider.
#**************************************************************************
vix.family = <family>
* A provider family to which this provider belongs.
* The only family available by default is "hadoop". Others may be added.

vix.mode = stream|report
* Usually specified at the family level.
* Typically should be "stream". In general, do not use "report" without
  consulting Khulnasoft Support.

vix.command = <command>
* The command to be used to launch an external process for searches on this
  provider.
* Usually specified at the family level.

vix.command.arg.<N> = <argument>
* The Nth argument to the command specified by vix.command.
* Usually specified at the family level, but frequently overridden at the
  provider level, for example to change the jars used depending on the
  version of Hadoop to which a provider connects.

vix.<property name> = <property value>
* All such properties will be made available as "configuration properties" to
  search processes on this provider.
* For example, if this provider is in the Hadoop family, the configuration
  property "mapreduce.foo = bar" can be made available to the Hadoop
  via the property "vix.mapreduce.foo = bar".

vix.env.<env var name> = <env var variable>
* Will create an environment variable available to search processes on this
  provider.
* For example, to set the JAVA_HOME variable to "/path/java" for search
  processes on this provider, use "vix.env.JAVA_HOME = /path/java".

#**************************************************************************
# PER PROVIDER OPTIONS -- HADOOP
# These options are specific to ERPs with the Hadoop family.
# NOTE: Many of these properties specify behavior if the property is not
#       set. However, default values set in system/default/indexes.conf
#       take precedence over the "unset" behavior.
#**************************************************************************

vix.javaprops.<JVM system property name> = <value>
* All such properties will be used as Java system properties.
* For example, to specify a Kerberos realm (say "foo.com") as a Java
  system property, use the property
  "vix.javaprops.java.security.krb5.realm = foo.com".

vix.mapred.job.tracker = <logical name or server:port>
* In high-availability mode, use the logical name of the Job Tracker.
* Otherwise, should be set to server:port for the single Job Tracker.
* Note: this property is passed straight to Hadoop. Not all such properties
  are documented here.

vix.fs.default.name = <logical name or hdfs://server:port>
* In high-availability mode, use the logical name for a list of Name Nodes.
* Otherwise, use the URL for the single Name Node.
* Note: this property is passed straight to Hadoop. Not all such properties
  are documented here.

vix.khulnasoft.setup.onsearch = true|false
* Whether to perform setup (install & bundle replication) on search.
* Defaults to false.

vix.khulnasoft.setup.package = current|<path to file>
* Khulnasoft .tgz package to install and use on data nodes
  (in vix.khulnasoft.home.datanode).
* Uses the current install if set to value 'current' (without quotes).

vix.khulnasoft.home.datanode = <path to dir>
* Path to where khulnasoft should be installed on datanodes/tasktrackers, i.e.
  KHULNASOFT_HOME.
* Required.

vix.khulnasoft.home.hdfs = <path to dir>
* Scratch space for this Khulnasoft instance on HDFS
* Required.

vix.khulnasoft.search.debug = true|false
* Whether to run searches against this index in debug mode. In debug mode,
  additional information is logged to search.log.
* Optional. Defaults to false.

vix.khulnasoft.search.recordreader = <list of classes>
* Comma separated list of data preprocessing classes.
* Each such class must extend BaseKhulnasoftRecordReader and return data to be
  consumed by Khulnasoft as the value.

vix.khulnasoft.search.splitter = <class name>
* Set to override the class used to generate splits for MR jobs.
* Classes must implement com.khulnasoft.mr.input.SplitGenerator.
* Unqualified classes will be assumed to be in the package com.khulnasoft.mr.input.
* To search Parquet files, use ParquetSplitGenerator.
* To search Hive files, use HiveSplitGenerator.

vix.khulnasoft.search.mr.threads = <postive integer>
* Number of threads to use when reading map results from HDFS
* Numbers less than 1 will be treated as 1.
* Numbers greater than 50 will be treated as 50.
* If not set, defaults to 10.

vix.khulnasoft.search.mr.maxsplits = <positive integer>
* Maximum number of splits in an MR job.
* If not set, defaults to 10000.

vix.khulnasoft.search.mr.minsplits = <positive integer>
* Number of splits for first MR job associated with a given search.
* If not set, defaults to 100.

vix.khulnasoft.search.mr.splits.multiplier = <decimal greater than or equal to 1.0>
* Factor by which the number of splits is increased in consecutive MR jobs for
  a given search, up to the value of maxsplits.
* If not set, defaults to 10.

vix.khulnasoft.search.mr.poll = <positive integer>
* Polling period for job status, in milliseconds.
* If not set, defaults to 1000 (ie. 1 second).

vix.khulnasoft.search.mr.mapper.output.replication = <positive integer>
* Replication level for mapper output.
* Defaults to 3.

vix.khulnasoft.search.mr.mapper.output.gzlevel = <integer between 0 and 9, inclusive>
* The compression level used for the mapper output.
* Defaults to 2.

vix.khulnasoft.search.mixedmode = true|false
* Whether mixed mode execution is enabled.
* Defaults to true.

vix.khulnasoft.search.mixedmode.maxstream = <nonnegative integer>
* Max # of bytes to stream during mixed mode.
* Value = 0 means there's no stream limit.
* Will stop streaming after the first split that took the value over the limit.
* If not set, defaults to 10 GB.

vix.khulnasoft.jars = <list of paths>
* Comma delimited list of Khulnasoft dirs/jars to add to the classpath in the
  Search Head and MR.

vix.env.HUNK_THIRDPARTY_JARS = <list of paths>
* Comma delimited list of 3rd-party dirs/jars to add to the classpath in the
  Search Head and MR.

vix.khulnasoft.impersonation = true|false
* Enable/disable user impersonation.

vix.khulnasoft.setup.bundle.replication = <positive integer>
* Set custom replication factor for bundles on HDFS.
* Must be an integer between 1 and 32767.
* Increasing this setting may help performance on large clusters by decreasing
  the average access time for a bundle across Task Nodes.
* Optional. If not set, the default replication factor for the file-system
  will apply.

vix.khulnasoft.setup.bundle.max.inactive.wait = <positive integer>
* A positive integer represent a time interval in seconds.
* Defaults to 5.
* While a task waits for a bundle being replicated to the same node by another
  task, if the bundle file is not modified for this amount of time, the task
  will begin its own replication attempt.

vix.khulnasoft.setup.bundle.poll.interval = <positive integer>
* A positive number, representing a time interval in milliseconds.
* Defaults to 100.
* While a task waits for a bundle to be installed by another task on the same
  node, it will check once per interval whether that installation is complete.

vix.khulnasoft.setup.bundle.setup.timelimit = <positive integer>
* A postive number, representing a time duration in milliseconds.
* Defaults to 20,000 (i.e. 20 seconds).
* A task will wait this long for a bundle to be installed before it quits.

vix.khulnasoft.setup.package.replication = true|false
* Set custom replication factor for the Khulnasoft package on HDFS. This is the
  package set in the property vix.khulnasoft.setup.package.
* Must be an integer between 1 and 32767.
* Increasing this setting may help performance on large clusters by decreasing
  the average access time for the package across Task Nodes.
* Optional. If not set, the default replication factor for the file-system
  will apply.

vix.khulnasoft.setup.package.max.inactive.wait = <positive integer>
* A positive integer represent a time interval in seconds.
* Defaults to 5.
* While a task waits for a Khulnasoft package being replicated to the same node by
  another task, if the package file is not modified for this amount of time,
  the task will begin its own replication attempt.

vix.khulnasoft.setup.package.poll.interval = <positive integer>
* A positive number, representing a time interval in milliseconds.
* Defaults to 100.
* While a task waits for a Khulnasoft package to be installed by another task on
  the same node, it will check once per interval whether that installation is
  complete.

vix.khulnasoft.setup.package.setup.timelimit = <positive integer>
* A positive number, representing a time duration in milliseconds.
* Defaults to 20,000 (i.e. 20 seconds).
* A task will wait this long for a Khulnasoft package to be installed before it quits.

vix.khulnasoft.search.column.filter = true|false
* Enables/disables column filtering. When enabled, Hunk will trim columns that
  are not necessary to a query on the Task Node, before returning the results
  to the search process.
* Should normally increase performance, but does have its own small overhead.
* Works with these formats: CSV, Avro, Parquet, Hive.
* If not set, defaults to true.

#
# Kerberos properties
#

vix.kerberos.principal = <kerberos principal name>
* Specifies principal for Kerberos authentication.
* Should be used with vix.kerberos.keytab and either
  1) vix.javaprops.java.security.krb5.realm and
     vix.javaprops.java.security.krb5.kdc, or
  2) security.krb5.conf

vix.kerberos.keytab = <kerberos keytab path>
* Specifies path to keytab for Kerberos authentication.
* See usage note with vix.kerberos.principal.


#
# The following properties affect the KhulnasoftMR heartbeat mechanism. If this
# mechanism is turned on, the KhulnasoftMR instance on the Search Head updates a
# heartbeat file on HDFS. Any MR job spawned by report or mix-mode searches
# checks the heartbeat file. If it is not updated for a certain time, it will
# consider KhulnasoftMR to be dead and kill itself.
#

vix.khulnasoft.heartbeat = true|false
* Turn on/off heartbeat update on search head, and checking on MR side.
* If not set, defaults to true.

vix.khulnasoft.heartbeat.path = <path on HDFS>
* Path to heartbeat file.
* If not set, defaults to <vix.khulnasoft.home.hdfs>/dispatch/<sid>/

vix.khulnasoft.heartbeat.interval = <positive integer>
* Frequency with which the Heartbeat will be updated on the Search Head.
* Unit is millisecond.
* Default value is 6 seconds (6000).
* Minimum value is 1000. Smaller values will cause an exception to be thrown.

vix.khulnasoft.heartbeat.threshold = <postive integer>
* The number of times the MR job will detect a missing heartbeat update before
  it considers KhulnasoftMR dead and kills itself.
* Default value is 10.

## The following sections are specific to data input types.

#
# Sequence file
#

vix.khulnasoft.search.recordreader.sequence.ignore.key = true|false
* When reading sequence files, if this key is enabled, events will be expected
  to only include a value. Otherwise, the expected representation is
  key+"\t"+value.
* Defaults to true.

#
# Avro
#

vix.khulnasoft.search.recordreader.avro.regex = <regex>
* Regex that files must match in order to be considered avro files.
* Optional. Defaults to \.avro$

#
# Parquet
#

vix.khulnasoft.search.splitter.parquet.simplifyresult = true|false
* If enabled, field names for map and list type fields will be simplified by
  dropping intermediate "map" or "element" subfield names. Otherwise, a field
  name will match parquet schema completely.
* Defaults to true.

#
# Hive
#

vix.khulnasoft.search.splitter.hive.ppd = true|false
* Enable or disable Hive ORC Predicate Push Down.
* If enabled, ORC PPD will be applied whenever possible to prune unnecessary
  data as early as possible to optimize the search.
* If not set, defaults to true.

vix.khulnasoft.search.splitter.hive.fileformat = textfile|sequencefile|rcfile|orc
* Format of the Hive data files in this provider.
* If not set, defaults to "textfile".

vix.khulnasoft.search.splitter.hive.dbname = <DB name>
* Name of Hive database to be accessed by this provider.
* Optional. If not set, defaults to "default".

vix.khulnasoft.search.splitter.hive.tablename = <table name>
* Table accessed by this provider.
* Required property.

vix.khulnasoft.search.splitter.hive.columnnames = <list of column names>
* Comma-separated list of file names.
* Required if using Hive, not using metastore.

vix.khulnasoft.search.splitter.hive.columntypes = string:float:int # COLON separated list of column types, required
* Colon-separated list of column- types.
* Required if using Hive, not using metastore.

vix.khulnasoft.search.splitter.hive.serde = <SerDe class>
* Fully-qualified class name of SerDe.
* Required if using Hive, not using metastore, and if specified in creation of Hive table.

vix.khulnasoft.search.splitter.hive.serde.properties = <list of key-value pairs>
* Comma-separated list of "key=value" pairs.
* Required if using Hive, not using metastore, and if specified in creation of Hive table.

vix.khulnasoft.search.splitter.hive.fileformat.inputformat = <InputFormat class>
* Fully-qualified class name of an InputFormat to be used with Hive table data.

vix.khulnasoft.search.splitter.hive.rowformat.fields.terminated = <delimiter>
* Will be set as the Hive SerDe property "field.delim".
* Optional.

vix.khulnasoft.search.splitter.hive.rowformat.escaped = <escape char>
* Will be set as the Hive SerDe property "escape.delim".
* Optional.

vix.khulnasoft.search.splitter.hive.rowformat.lines.terminated = <delimiter>
* Will be set as the Hive SerDe property "line.delim".
* Optional.

vix.khulnasoft.search.splitter.hive.rowformat.mapkeys.terminated  = <delimiter>
* Will be set as the Hive SerDe property "mapkey.delim".
* Optional.

vix.khulnasoft.search.splitter.hive.rowformat.collectionitems.terminated = <delimiter>
* Will be set as the Hive SerDe property "colelction.delim".
* Optional.

#
# Archiving
#

vix.output.buckets.max.network.bandwidth = 0|<bits per second>
* Throttles network bandwidth to <bits per second>
* Defaults to 0, meaning no throttling.
* Set at provider level. Applied to all virtual indexes using a provider with this setting.

#**************************************************************************
# PER VIRTUAL INDEX OPTIONS
# These options affect virtual indexes. Like indexes, these options may
# be set under an [<virtual-index>] entry.
#
# Virtual index names have the same constraints as normal index names.
#
# Each virtual index must reference a provider. I.e:
# [virtual_index_name]
# vix.provider = <provider_name>
#
# All configuration keys starting with "vix." will be passed to the
# external resource provider (ERP).
#**************************************************************************

vix.provider = <provider_name>
* Name of the external resource provider to use for this virtual index.

#**************************************************************************
# PER VIRTUAL INDEX OPTIONS -- HADOOP
# These options are specific to ERPs with the Hadoop family.
#**************************************************************************

#
# The vix.input.* configurations are grouped by an id.
# Inputs configured via the UI always use '1' as the id.
# In this spec we'll use 'x' as the id.
#

vix.input.x.path = <path>
* Path in a hadoop filesystem (usually HDFS or S3).
* May contain wildcards.
* Checks the path for data recursively when ending with '...'
* Can extract fields with ${field}. I.e: "/data/${server}/...", where server
  will be extracted.
* May start with a schema.
  * The schema of the path specifies which hadoop filesystem implementation to
    use. Examples:
    * hdfs://foo:1234/path, will use a HDFS filesystem implementation
    * s3a://s3-bucket/path, will use a S3 filesystem implementation

vix.input.x.accept = <regex>
* Specifies a whitelist regex.
* Only files within the location given by matching vix.input.x.path, whose
  paths match this regex, will be searched.

vix.input.x.ignore = <regex>
* Specifies a blacklist regex.
* Searches will ignore paths matching this regex.
* These matches take precedence over vix.input.x.accept matches.

vix.input.x.required.fields = <comma separated list of fields>
* Fields that will be kept in search results even if the field is not required by the search

# Earliest time extractions - For all 'et' settings, there's an equivalent 'lt' setting.
vix.input.x.et.regex = <regex>
* Regex extracting earliest time from vix.input.x.path

vix.input.x.et.format = <java.text.SimpleDateFormat date pattern>
* Format of the extracted earliest time.
* See documentation for java.text.SimpleDateFormat

vix.input.x.et.offset = <seconds>
* Offset in seconds to add to the extracted earliest time.

vix.input.x.et.timezone = <java.util.SimpleTimeZone timezone id>
* Timezone in which to interpret the extracted earliest time.
* Examples: "America/Los_Angeles" or "GMT-8:00"

vix.input.x.et.value = mtime|<epoch time in milliseconds>
* Sets the earliest time for this virtual index.
* Can be used instead of extracting times from the path via vix.input.x.et.regex
* When set to "mtime", uses the file modification time as the earliest time.

# Latest time extractions - See "Earliest time extractions"

vix.input.x.lt.regex = <regex>
* Latest time equivalent of vix.input.x.et.regex

vix.input.x.lt.format = <java.text.SimpleDateFormat date pattern>
* Latest time equivalent of vix.input.x.et.format

vix.input.x.lt.offset = <seconds>
* Latest time equivalent of vix.input.x.et.offset

vix.input.x.lt.timezone = <java.util.SimpleTimeZone timezone id>
* Latest time equivalent of vix.input.x.et.timezone

vix.input.x.lt.value = <mod time>
* Latest time equivalent of vix.input.x.et.value

#
# Archiving
#

vix.output.buckets.path = <hadoop path>
* Path to a hadoop filesystem where buckets will be archived

vix.output.buckets.older.than = <seconds>
* Buckets must be this old before they will be archived.
* A bucket's age is determined by the the earliest _time field of any event in
  the bucket.

vix.output.buckets.from.indexes = <comma separated list of khulnasoft indexes>
* List of (non-virtual) indexes that will get archived to this (virtual) index.

vix.unified.search.cutoff_sec = <seconds>
* Window length before present time that configures where events are retrieved
  for unified search
* Events from now to now-cutoff_sec will be retrieved from the khulnasoft index
  and events older than cutoff_sec will be retrieved from the archive index

#**************************************************************************
# PER VIRTUAL INDEX OR PROVIDER OPTIONS -- HADOOP
# These options can be set at either the virtual index level or provider
# level, for the Hadoop ERP.
#
# Options set at the virtual index level take precedence over options set
# at the provider level.
#
# Virtual index level prefix:
# vix.input.<input_id>.<option_suffix>
#
# Provider level prefix:
# vix.khulnasoft.search.<option_suffix>
#**************************************************************************

# The following options are just defined by their <option_suffix>

#
# Record reader options
#

recordreader.<name>.<conf_key> = <conf_value>
* Sets a configuration key for a RecordReader with <name> to <conf_value>

recordreader.<name>.regex = <regex>
* Regex specifying which files this RecordReader can be used for.

recordreader.journal.buffer.size = <bytes>
* Buffer size used by the journal record reader

recordreader.csv.dialect = default|excel|excel-tab|tsv
* Set the csv dialect for csv files
* A csv dialect differs on delimiter_char, quote_char and escape_char.
* Here is a list of how the different dialects are defined in order delim,
  quote, and escape:
  * default   = ,  " \
  * excel     = ,  " "
  * excel-tab = \t " "
  * tsv       = \t " \

#
# Splitter options
#

splitter.<name>.<conf_key> = <conf_value>
* Sets a configuration key for a split generator with <name> to <conf_value>

splitter.file.split.minsize = <bytes>
* Minimum size in bytes for file splits.
* Defaults to 1.

splitter.file.split.maxsize = <bytes>
* Maximum size in bytes for file splits.
* Defaults to Long.MAX_VALUE.

#**************************************************************************
# Volume settings.  This section describes settings that affect the volume-
# optional and volume-mandatory parameters only.
#
# All volume stanzas begin with "volume:". For example:
#   [volume:volume_name]
#   path = /foo/bar
#
# These volume stanzas can then be referenced by individual index
# parameters, e.g. homePath or coldPath.  To refer to a volume stanza, use
# the "volume:" prefix. For example, to set a cold DB to the example stanza
# above, in index "hiro", use:
#   [hiro]
#   coldPath = volume:volume_name/baz
# This will cause the cold DB files to be placed under /foo/bar/baz.  If the
# volume spec is not followed by a path
# (e.g.  "coldPath=volume:volume_name"), then the cold path would be
# composed by appending the index name to the volume name ("/foo/bar/hiro").
#
# If "path" is specified with a URI-like value (e.g., "s3://bucket/path"),
# this is a remote storage volume.  A remote storage volume can only be
# referenced by a remotePath parameter, as described above.  An Amazon S3
# remote path might look like "s3://bucket/path", whereas an NFS remote path
# might look like "file:///mnt/nfs".  The name of the scheme ("s3" or "file"
# from these examples) is important, because it can indicate some necessary
# configuration specific to the type of remote storage.  To specify a
# configuration under the remote storage volume stanza, you use parameters
# with the pattern "remote.<scheme>.<param name>". These parameters vary
# according to the type of remote storage.  For example, remote storage of
# type S3 might require that you specify an access key and a secret key.
# You would do this through the "remote.s3.access_key" and
# "remote.s3.secret_key" parameters.
#
# Note: thawedPath may not be defined in terms of a volume.
# Thawed allocations are manually controlled by Khulnasoft administrators,
# typically in recovery or archival/review scenarios, and should not
# trigger changes in space automatically used by normal index activity.
#**************************************************************************

storageType = local | remote
* Optional.
* Specifies whether the volume definition is for indexer local storage or remote
  storage. Only the remotePath attribute references a remote volume.
* Defaults to: local.

path = <path on server>
* Required.
* If storageType = local:
  * The path attribute points to the location on the file system where all indexes
   that will use this volume reside.
   * This location must not overlap with the location for any other volume or index.
* If storageType = remote:
  * The path attribute points to the remote storage location where indexes reside.
  * The format for this attribute is: <scheme>://<remote-location-specifier>
    * The "scheme" identifies a supported external storage system type.
    * The "remote-location-specifier" is an external system-specific string for
       identifying a location inside the storage system.
  * These external systems are supported:
     - Object stores that support AWS's S3 protocol. These use the scheme "s3".
       For example, "path=s3://mybucket/some/path".
     - POSIX file system, potentially a remote filesystem mounted over NFS. These
       use the scheme "file". For example, "path=file:///mnt/cheap-storage/some/path".

maxVolumeDataSizeMB = <positive integer>
* Optional, ignored for storageType=remote
* If set, this attribute limits the total size of all databases that reside
  on this volume to the maximum size specified, in MB.  Note that this it
  will act only on those indexes which reference this volume, not on the
  total size of the path set in the path attribute of this volume.
* If the size is exceeded, Khulnasoft will remove buckets with the oldest value
  of latest time (for a given bucket) across all indexes in the volume,
  until the volume is below the maximum size.  This is the trim operation.
  Note that this can cause buckets to be chilled [moved to cold] directly
  from a hot DB, if those buckets happen to have the least value of
  latest-time (LT) across all indexes in the volume.
* Highest legal value is 4294967295, lowest legal value is 1.

rotatePeriodInSecs = <nonnegative integer>
* Optional, ignored for storageType=remote
* Specifies period of trim operation for this volume.
* If not set, the value of global rotatePeriodInSecs attribute is inherited.
* Highest legal value is 4294967295

remote.* = <String>
* Optional.
* With remote volumes, communication between the indexer and the external
  storage system may require additional configuration, specific to the type of
  storage system. You can pass configuration information to the storage
  system by specifying the settings through the following schema:
  remote.<scheme>.<config-variable> = <value>.
  For example: remote.s3.access_key = ACCESS_KEY

################################################################
##### S3 specific settings
################################################################

remote.s3.header.<http-method-name>.<header-field-name> = <String>
* Optional.
* Enable server-specific features, such as reduced redundancy, encryption, and so on,
  by passing extra HTTP headers with the REST requests.
  The <http-method-name> can be any valid HTTP method. For example, GET, PUT, or ALL,
  for setting the header field for all HTTP methods.
* Example: remote.s3.header.PUT.x-amz-storage-class = REDUCED_REDUNDANCY

remote.s3.access_key = <String>
* Optional.
* Specifies the access key to use when authenticating with the remote storage
  system supporting the S3 API.
* If not specified, the indexer will look for these environment variables:
  AWS_ACCESS_KEY_ID or AWS_ACCESS_KEY (in that order).
* If the environment variables are not set and the indexer is running on EC2,
  the indexer attempts to use the access key from the IAM role.
* Default: unset

remote.s3.secret_key = <String>
* Optional.
* Specifies the secret key to use when authenticating with the remote storage
  system supporting the S3 API.
* If not specified, the indexer will look for these environment variables:
  AWS_SECRET_ACCESS_KEY or AWS_SECRET_KEY (in that order).
* If the environment variables are not set and the indexer is running on EC2,
  the indexer attempts to use the secret key from the IAM role.
* Default: unset

remote.s3.signature_version = v2|v4
* Optional.
* The signature version to use when authenticating with the remote storage
  system supporting the S3 API.
* If not specified, it defaults to v2.
* For aws:kms server-side encryption, you must use signature_version=v4.

remote.s3.auth_region = <String>
* Optional
* The authentication region to use when signing the requests when interacting with the remote
  storage system supporting the S3 API. If unset, Khulnasoft will attempt to automatically extract
  the value from the endpoint URL
* Defaults: unset

remote.s3.endpoint = <URL>
* Required.
* The URL of the remote storage system supporting the S3 API.
* The scheme, http or https, can be used to enable or disable SSL connectivity
  with the endpoint.
* If not specified and the indexer is running on EC2, the endpoint will be
  constructed automatically based on the EC2 region of the instance where the
  indexer is running, as follows: https://s3-<region>.amazonaws.com
* Example: https://s3-us-west-2.amazonaws.com

remote.s3.timeout.connect = <unsigned int>
* Optional
* Set the connection timeout, in milliseconds, to use when interacting with S3 for this volume
* Defaults: 5000

remote.s3.timeout.read = <unsigned int>
* Optional
* Set the read timeout, in milliseconds, to use when interacting with S3 for this volume
* Defaults: 60000

remote.s3.timeout.write = <unsigned int>
* Optional
* Set the write timeout, in milliseconds, to use when interacting with S3 for this volume
* Defaults: 60000
