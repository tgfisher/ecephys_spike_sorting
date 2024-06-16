"""
Additional module written by Emily Aery Jones, 19 May 2022; edited by Charlotte Herber March 2023
"""
from argschema import ArgSchemaParser
import os
from pathlib import Path
import time
import numpy as np
import pandas as pd

from ...common.utils import write_cluster_group_tsv, getFileVersion


def filter_by_metrics(args):
    """Filtering via the prephy filters arguments

    this file seems to:
        (_note '- [ ]' lines include TODOs along with the summary point._)

    - gets the current 'cluster_metrics_file' which is the base for this:
      metrics.csv?
    - get the current 'waveform_metrics_file' which is the base for this:
      waveform_metrics.csv?
    - csv read the 'cluster_metrics_file', `metrics = pd.read_csv(metrics_file)`
        - if no 'snr' column then it merges the 'waveform_metrics_file' in.
            `metrics.merge(pd.read_csv(waveform_metrics_file))`
    - csv read cluster groups
    - np load cluster_Table.npy into `cluster_map = np.load("...cluster_table.npy")`
    - drop zero spike clusters from cluster_map. (why would those exist?)
    - add a 'depth' field to metrics, _very nice_
    - save a copy of the original cluster labels.
    - [ ] loop through the metrics rows, _these would be the clusters I guess_.
      _Some of this logic is very hard to read and cold be reduced to much more
      readable logical variables._
        - get the cluster group label
        - finding "noise" -- triggered by wide_halfwidth_max param > halfwidth_max param:
            - [ ] flagging those with halfwidth max larger than "max" and less than
              "wide_max" for a repolarization slope check: noise if repo_slope
              too slow. unnecessary bitwise &, this should be fixed_
            -increment noise clusters
        - [ ] finding "noise" -- triggered any of the following: snr exceeding min,
          halfwidth exceeding wide max, firing rate below mua min, depth being
          too high. _nonstandard bitwise | 'or', this should be fixed._
        - rescue "mua" -- triggered by having all these things: good isi, good
          contamination rate, good firing rate.
        - [ ] downgrade "good" -- triggered by any of the following: greated than 3
          ISI violations, high contam_rate, or firing rate too low. _checking
          for firing rate again doesn't make sense. Firing rate already was
          checked above in the catch all logic and those rows were labeled
          'noise'. """

    print('ecephys spike sorting: pre-Phy filters module\n\n')

    start = time.time()

    #v when this module was written changes were made to getFileVersion...
    #v  however, other modules use this function and I believe it could cause
    #v  clobbering. Notes to self about the operation of these functions.
    #v
    #v changed getFileVersion -- It has altered file return and version logic:
    #v
    #v examples of how the file logic works "inconsistently":
    #v - e.g. blah_1.npy returned if options are blah.npy and blah_1.npy, it
    #v   returns the "current" versionof the 'blah' file version series.
    #v - e.g. blah.npy is returned if if the file does not exist, no base file
    #v   (no blah.npy) then it will return the "next" (first) version of the 'blah'
    #v   file version series.
    #v - e.g. blah.npy is returned if the file blah.npy exists, it returns the
    #v   "current" version of the 'blah' file version series.
    #v
    #v examples of how the version numbers are overlapping and confusing.
    #v - version=0 for if no blah file
    #v - version=0 if the blah file exists
    #v - version=1 if the blah file is _1
    #v
    #v I'd like to fix this module to work with the OG getFileVersion so that the
    #v other modules work properly.
    #v
    #v It returns the 'next' file and the version has the following logic:
    #v
    #v Original getFileVersion -- returns "next" file and "current" version.
    #v   Admittedly, the version being behind the file tag (e.g. _1 is the
    #v   version=2) is strange and could take the zero-index brained pythonista
    #v   for a loop.
    #v
    #v examples of how the file logic works "consistently":
    #v - e.g. blah_2.npy returned if options are blah.npy and blah_1.npy, it
    #v   returns the "next" version of the 'blah' file version series.
    #v - e.g. blah.npy is returned if if the file does not exist, no base file
    #v   (no blah.npy). This is the "next" (first) version of the 'blah' file
    #v   version series.
    #v - e.g. blah_1.npy is returned if the file blah.npy exists. It returns the
    #v   "next" version of the 'blah' file version series.
    #v
    #v examples of how the version numbers are overlapping and confusing.
    #v - version=0 for if no blah file
    #v - version=1 if the blah file exists
    #v - version=2 if the blah file is _1

    def _get_current_metrics(base_file_path, metrics_version):
        if metrics_version == 0:
            raise Exception(
                f"Needs a version of the {base_file_path.stem} to work. Place this module last."
            )
        elif metrics_version == 1:
            return pd.read_csv(base_file_path)
        else:
            # use the previous/recent metrics file
            recent_metrics_file_path = base_file_path.with_stem(
                base_file_path.stem + f"_{metrics_version-1}"
            )
            return pd.read_csv(recent_metrics_file_path)

    # find the correct metrics file (eg metrics.csv, metrics_1.csv, ...)
    metrics_file_path = Path(args['cluster_metrics']['cluster_metrics_file'])
    out_metrics_file, metrics_version = getFileVersion(metrics_file_path)


    waveform_metrics_file_path = Path(args['waveform_metrics']['waveform_metrics_file'])
    _next_waveform_metrics_file, waveform_metrics_version = getFileVersion(waveform_metrics_file_path)


    # read the metrics files and join with waveforms if previous module failed to
    metrics = _get_current_metrics(metrics_file_path, metrics_version)
    if 'snr' not in metrics.columns:
        waveform_metrics = _get_current_metrics(
            waveform_metrics_file_path,
            waveform_metrics_version,
        )
        metrics = metrics.merge(waveform_metrics, left_on='cluster_id', right_on='cluster_id')

    # read cluster assignments
    clusters_file = os.path.join(
        args['directories']['kilosort_output_directory'],
        args['ephys_params']['cluster_group_file_name'],
    )
    clusters = pd.read_csv(clusters_file, sep='\t')

    # load channels for each cluster to get depths
    cluster_map = np.load(
        os.path.join(args['directories']['kilosort_output_directory'], 'clus_Table.npy')
    )

    # remove clusters without spikes
    cluster_map = cluster_map[~(cluster_map[:,0] == 0)]

    # convert from channel # to depth (floor(ch/2+1)*20)
    depths = cluster_map[:,1]/2+1
    depths = depths.astype(int)
    metrics['depth'] = depths*20

    # save a copy of the original labels
    clusters_original = clusters.rename(columns={'group':'original_group'})
    clusters_original.to_csv(clusters_file[:-4]+'_original.tsv', sep='\t', index=False)

    # change the labels that meet MUA filters
    labels = [ ]
    mua_clusters = 0
    noise_clusters = 0
    good_clusters = 0

    filter_params = args["prephy_filters_params"]
    for i, row in metrics.iterrows():
        # start with original label; overwrite
        label = clusters['group'].loc[clusters['cluster_id']==row['cluster_id']].item()

        # find noise clusters

        # for HPC: allow wider waveforms as long as they are not too flat
        if args['prephy_filters_params']['halfwidth_max'] < args['prephy_filters_params']['wide_halfwidth_max']:
            if (row['halfwidth'] > args['prephy_filters_params']['halfwidth_max']) & \
                (row['halfwidth'] < args['prephy_filters_params']['wide_halfwidth_max']):
                    if row['repolarization_slope'] < args['prephy_filters_params']['repo_slope']:
                        label = 'noise'
                        noise_clusters += 1

        if ((row['snr']<args['prephy_filters_params']['snr_min']) | \
            (row['halfwidth']>args['prephy_filters_params']['wide_halfwidth_max']) | \
            (row['firing_rate']<args['prephy_filters_params']['mua_fr_min']) | \
            (row['depth']>args['prephy_filters_params']['depth'])):
                label = 'noise'
                noise_clusters += 1

        # "rescue" MUA designated units that meet these criteria
        elif (label=='mua') & \
            ((row['isi_viol'] <= args['prephy_filters_params']['isi_viol_max']) & \
            (row['contam_rate'] <= args['prephy_filters_params']['contam_rate_max']) & \
            (row['firing_rate'] >= args['prephy_filters_params']['mua_fr_min'])):
                label = 'good'
                good_clusters += 1

                labels.append(label)

                continue

        # label good units MUA if they meet these criteria (adjusted num viol allowed up from 1 to 3, allowed lower FR due to longer sessions)
        elif (label=='good') & \
            (((row['isi_viol'] > args['prephy_filters_params']['isi_viol_max']) & (row['num_viol']>3)) | \
            (row['contam_rate'] > args['prephy_filters_params']['contam_rate_max']) | \
            (row['firing_rate'] < args['prephy_filters_params']['mua_fr_min'])):
                label = 'mua'
                mua_clusters += 1

        labels.append(label)

    # write output
    write_cluster_group_tsv(
        metrics['cluster_id'],
        labels,
    	args['directories']['kilosort_output_directory'],
    	args['ephys_params']['cluster_group_file_name']
    )
    print(
        f'Reclassified {mua_clusters} good clusters as MUA, {good_clusters}',
        f'MUA clusters as good, and {noise_clusters} clusters as noise from',
        f'{len(metrics)} clusters'
    )

    execution_time = time.time() - start
    print('total time: ' + str(np.around(execution_time,2)) + ' seconds\n')

    return {
        "execution_time" : execution_time,
        "quality_metrics_output_file" : args['cluster_metrics']['cluster_metrics_file']
    } # output manifest

def main():

    from ._schemas import InputParameters, OutputParameters

    mod = ArgSchemaParser(
        schema_type=InputParameters,
        output_schema_type=OutputParameters,
    )

    output = filter_by_metrics(mod.args)

    output.update({"input_parameters": mod.args})
    if "output_json" in mod.args:
        mod.output(output, indent=2)
    else:
        print(mod.get_output_json(output))

if __name__ == "__main__":
    main()
