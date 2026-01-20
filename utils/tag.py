from pandas import DataFrame
from collections import Counter


def get_cluster_top_tags(sample: DataFrame, tags_to_delete: set[str], n_top_tags: int = 5):
    """
    Get top N tags for each cluster in the sample.

    Args:
        sample: DataFrame with 'cluster' and 'tags' columns
        tags_to_delete: set of tags to exclude from results
        n_top_tags: number of top tags to extract per cluster

    Returns:
        dict mapping cluster_id to list of top tag strings
    """
    cluster_top_tags = {}

    for cluster_id in sample["cluster"].unique():
        if cluster_id == -1:  # Skip noise
            continue

        cluster_data = sample[sample["cluster"] == cluster_id]
        all_cluster_tags = []

        for tags_list in cluster_data["tags"]:
            if tags_list and isinstance(tags_list, list):
                all_cluster_tags.extend([tag for tag in tags_list if tag not in tags_to_delete])

        if all_cluster_tags:
            tag_counts = Counter(all_cluster_tags)
            top_tags = tag_counts.most_common(n_top_tags)
            cluster_top_tags[cluster_id] = [tag for tag, count in top_tags]
        else:
            cluster_top_tags[cluster_id] = []

    return cluster_top_tags
