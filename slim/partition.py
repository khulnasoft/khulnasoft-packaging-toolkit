#!/usr/bin/env python
# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

from os import path
import sys
import json

import slim.app
import slim.command
import slim.utils


# Argument parser definition

parser = slim.command.SlimArgumentParser(
    description='split an app source package into a set of targeted deployment packages',
    epilog='The targeted deployment packages created are based on user-defined deployment specifications. A deployment '
           'specification can contain any combination of three different types of Khulnasoft workloads: indexer (named as '
           '"_indexers"), search head (named as "_search_heads") and forwarder (named as "_forwarders").'
)

parser.add_app_package()
parser.add_argument_help()
parser.add_installation()
parser.add_output_directory(description='deployment packages')
parser.add_repository()
parser.add_combine_search_head_indexer_workloads()
parser.add_forwarder_workloads()
parser.add_deployment_packages()
parser.add_target_os()

# Command-specific arguments

# TODO: Make this the default state for 'partition' and remove the 'install' options to split logically (?)
# What's the use case for not updating the input installation graph, if there is one? Is the output installation graph
# not always potentially useful to customers using the CLI to partition an app? Why force customers to run another
# command to achieve the same end: partitioning an app and then updating an installation graph?

parser.add_argument(
    '-p', '--partition-only',
    action='store_const', const=True, default=False,
    help='verify installation graph to ensure it is unchanged after partitioning; useful when you are partitioning an '
         'app for re-deployment')


def main(args):

    slim.utils.SlimLogger.step('Extracting source from ', slim.utils.encode_filename(args.source), '...')
    app_source = get_app_source(args.source, None)
    server_collection = get_app_server_class_collection(args.installation, args.repository)

    if args.partition_only:
        if args.target_os:
            slim.utils.SlimLogger.information('"target-os: %s" is ignored because --partition-only is used.'
                                              % args.target_os)
    else:
        slim.utils.SlimLogger.step('Adding ', app_source.qualified_id, ' to installation graph...')

        server_collection.add(app_source, get_deployment_specifications(
            args.deployment_packages, args.combine_search_head_indexer_workloads, args.forwarder_workloads
        ), args.target_os)
        slim.utils.SlimLogger.exit_on_error()

        # Save the resulting installation graph, even if there are no changes; when len(deployment_packages) == 0

        filename = path.join(args.output_dir, 'installation-update.json')
        server_collection.save(filename)

        slim.utils.SlimLogger.information('Saved updated installation graph to ', slim.utils.encode_filename(filename))

    _partition(app_source, server_collection, args.output_dir, partition_all=True)


def partition(source, installation_graph, output_dir):

    if isinstance(installation_graph, dict):
        installation_graph = json.dumps(installation_graph)

    string_io_type = slim.command.SlimStringIOArgument(name="installation_graph.json")
    installation = string_io_type(value=installation_graph)

    slim.utils.SlimLogger.step('Extracting source from ', slim.utils.encode_filename(source), '...')

    app_source = get_app_source(source, None)
    server_collection = get_app_server_class_collection(installation, slim.utils.slim_configuration.repository_path)

    _partition(app_source, server_collection, output_dir, partition_all=False)


def _partition(app_source, server_collection, output_dir, partition_all):
    """ Partition an app into deployment packages targeting a collection of server classes.

    :param app_source: Represents the app to be partitioned.
    :type app_source: AppSource

    :param server_collection: Represents the set of server classes.
    :type server_collection: ServerClassCollections

    :param output_dir: Path to output directory
    :type output_dir: string

    :param partition_all:
    :type partition_all: bool

    """
    slim.utils.SlimLogger.step('Partitioning ', app_source.qualified_id, '...')
    deployment_packages = server_collection.partition(app_source, output_dir, partition_all)

    if len(deployment_packages) > 0:
        app_id = app_source.qualified_id
        slim.utils.SlimLogger.information('Generated deployment packages for ', app_id,
                                          ':\n  ', '\n  '.join(deployment_packages))
    else:
        slim.utils.SlimLogger.information(
            'No deployment packages generated for ', app_source.id, ' because there is nothing meaningful to deploy'
        )

# Wrapper functions to handle errors


def get_app_source(package, configuration):
    app_source = slim.app.AppSource(package, configuration)
    slim.utils.SlimLogger.exit_on_error()
    return app_source


def get_app_server_class_collection(installation, repository):
    server_classes = slim.app.AppServerClassCollection.load(installation, repository)
    slim.utils.SlimLogger.exit_on_error()
    return server_classes


def get_deployment_specifications(
        deployment_specifications, combine_search_head_indexer_workloads, forwarder_deployment_specifications
):
    deployment_specifications = slim.app.AppDeploymentSpecification.get_deployment_specifications(
        deployment_specifications, combine_search_head_indexer_workloads, forwarder_deployment_specifications)
    slim.utils.SlimLogger.exit_on_error()
    return deployment_specifications


if __name__ == '__main__':
    # noinspection PyBroadException
    try:
        main(parser.parse_args(sys.argv[1:]))
    except SystemExit:
        raise
    except:
        slim.utils.SlimLogger.set_debug(True)
        slim.utils.SlimLogger.fatal(exception_info=sys.exc_info())
