from pandas import DataFrame
import folium
import branca.colormap as cm
from pathlib import Path


def convex_hull_xy(points_xy: list[tuple[float, float]]):
    """
    Compute convex hull using Andrew's monotonic chain algorithm.

    Args:
        points_xy: list of (x, y) tuples

    Returns:
        list of (x, y) tuples in order. Returns [] if <3 unique points.
    """
    pts = sorted(set(points_xy))
    if len(pts) < 3:
        return []

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


def create_cluster_map(
    sample: DataFrame,
    cluster_top_tags: list[str],
    year: int | str,
    show_points: bool = True,
    show_noise: bool = False,
    save_dir: Path | None = None,
):
    """
    Create a folium map with polygons, points and popups.

    Args:
        sample: DataFrame with columns 'cluster', 'lat', 'long', 'similar_year', 'url'
        cluster_top_tags: dict mapping cluster_id to list of top tags
        year: year identifier for the map title and filename
        show_points: bool, whether to show individual points
        show_noise: bool, whether to show noise points (cluster_id == -1)
        save_dir: Path object for output directory. If None, doesn't save.

    Returns:
        folium.Map object
    """
    if save_dir is None:
        save_dir = Path("./data/explore/")
    save_dir.mkdir(parents=True, exist_ok=True)

    m = folium.Map(location=[45.7615, 4.83], zoom_start=16)
    cluster_ids = sorted([c for c in sample["cluster"].unique() if c != -1])

    # Create colormap
    if len(cluster_ids) == 0:
        colormap = None
    else:
        colormap = cm.linear.Paired_12.scale(min(cluster_ids), max(cluster_ids))
        colormap.add_to(m)

    fg_similar = folium.FeatureGroup(name="Similar year (circles)", show=True)
    fg_nonsimilar = folium.FeatureGroup(name="Not similar year (squares)", show=True)

    # Draw cluster polygons
    for cluster_id in cluster_ids:
        cluster_df = sample[sample["cluster"] == cluster_id]

        pts_xy = list(zip(cluster_df["long"].astype(float), cluster_df["lat"].astype(float)))
        hull_xy = convex_hull_xy(pts_xy)

        if not hull_xy:
            continue

        color = colormap(cluster_id) if colormap is not None else "gray"
        hull_latlon = [(y, x) for (x, y) in hull_xy]

        folium.Polygon(
            locations=hull_latlon,
            color=color,
            weight=3,
            fill=True,
            fill_opacity=0.2,
            fill_color=color,
            tooltip=f"Cluster&nbsp;{cluster_id}&nbsp;(n={len(cluster_df)})<br/>Tags: {', '.join(cluster_top_tags.get(cluster_id, []))}",
        ).add_to(m)

    # Draw individual points
    if show_points:
        for _, row in sample.iterrows():
            cluster_id = int(row["cluster"])

            if cluster_id == -1 and not show_noise:
                continue

            if cluster_id == -1:
                color = "gray"
            else:
                color = colormap(cluster_id)

            is_similar = bool(row["similar_year"])
            url = row["url"]

            if is_similar:
                folium.CircleMarker(
                    location=[row["lat"], row["long"]],
                    radius=6,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.55,
                    popup=f"Cluster:&nbsp;{cluster_id}<br/><a href='{url}' target='_blank'>link</a>",
                ).add_to(fg_similar)
            else:
                folium.RegularPolygonMarker(
                    location=[row["lat"], row["long"]],
                    number_of_sides=4,
                    radius=6,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.55,
                    popup=f"Cluster:&nbsp;{cluster_id}<br/><a href='{url}' target='_blank'>link</a>",
                ).add_to(fg_nonsimilar)

        fg_similar.add_to(m)
        fg_nonsimilar.add_to(m)

    folium.LayerControl().add_to(m)

    # Save map
    output_path = save_dir / f"{year}_clusters_map.html"
    m.save(str(output_path))
    print(f"Cluster map saved to {output_path}")

    return m
