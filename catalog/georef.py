"""Georeferencing: turn control points into a real-world position for a map image.

Every way of aligning a map (clicking points by hand now; importing a GeoTIFF or a
published georeference later) ends by saving ControlPoint rows and calling
apply_georeference(). That way there is only one piece of math to trust and test.
"""

import math

# Roughly how many meters one degree of latitude covers (close enough for error reports)
METERS_PER_DEGREE = 111_320


# === FIT ===
# Finds the best affine transform (shift + scale + rotation + skew) that takes
# image pixels (x, y) to (lat, lng), using least squares over all the points.
# points: a list of (x, y, lat, lng) tuples. Needs 3+ points that are not in a line.
# Returns a function to_latlng(x, y) -> (lat, lng).
# ponytail: an affine fit in lat/lng degrees is accurate at city scale; a large
# sheet (a whole state) would need a projected or polynomial fit instead.
def fit_affine(points):
    if len(points) < 3:
        raise ValueError("At least 3 control points are needed.")

    # Center the pixel coordinates so the math stays numerically stable
    n = len(points)
    mean_x = sum(p[0] for p in points) / n
    mean_y = sum(p[1] for p in points) / n
    mean_lat = sum(p[2] for p in points) / n
    mean_lng = sum(p[3] for p in points) / n
    dx = [p[0] - mean_x for p in points]
    dy = [p[1] - mean_y for p in points]

    # Spread of the points on the image; det near zero means they sit in a line
    sxx = sum(a * a for a in dx)
    syy = sum(b * b for b in dy)
    sxy = sum(a * b for a, b in zip(dx, dy))
    det = sxx * syy - sxy * sxy
    if det <= 1e-9 * (sxx + syy) ** 2:
        raise ValueError(
            "Control points are in a straight line; spread them across the map."
        )

    # Solve the 2x2 least-squares system for one output (lat or lng):
    # value = cx * x + cy * y + offset
    def solve(values, mean_value):
        dv = [v - mean_value for v in values]
        sxv = sum(a * v for a, v in zip(dx, dv))
        syv = sum(b * v for b, v in zip(dy, dv))
        cx = (syy * sxv - sxy * syv) / det
        cy = (sxx * syv - sxy * sxv) / det
        offset = mean_value - cx * mean_x - cy * mean_y
        return cx, cy, offset

    lat_cx, lat_cy, lat_0 = solve([p[2] for p in points], mean_lat)
    lng_cx, lng_cy, lng_0 = solve([p[3] for p in points], mean_lng)

    # The fitted transform: pixel in, [lat, lng] out
    def to_latlng(x, y):
        return (lat_cx * x + lat_cy * y + lat_0, lng_cx * x + lng_cy * y + lng_0)

    return to_latlng


# === ERROR ===
# Root-mean-square distance (meters) between each clicked real-world spot and
# where the fitted transform puts its pixel. Tells staff how good the alignment is.
def rms_error_meters(points, to_latlng):
    total = 0.0
    for x, y, lat, lng in points:
        fit_lat, fit_lng = to_latlng(x, y)
        # Longitude degrees shrink toward the poles, so scale by cos(latitude)
        north_m = (fit_lat - lat) * METERS_PER_DEGREE
        east_m = (fit_lng - lng) * METERS_PER_DEGREE * math.cos(math.radians(lat))
        total += north_m**2 + east_m**2
    return math.sqrt(total / len(points))


# === APPLY ===
# Fits a map from its saved control points and stores the result on the map:
# the three overlay corners, the N/S/E/W box used by search, and the error.
# Raises ValueError (from fit_affine) if the points can't be fitted.
def apply_georeference(hmap):
    points = list(hmap.control_points.values_list("x", "y", "lat", "lng"))
    to_latlng = fit_affine(points)

    # Image size in pixels (Pillow reads it from the file)
    width, height = hmap.image.width, hmap.image.height

    # Where each corner of the image lands on the real map
    top_left = to_latlng(0, 0)
    top_right = to_latlng(width, 0)
    bottom_left = to_latlng(0, height)
    bottom_right = to_latlng(width, height)
    hmap.corners = {
        "topleft": list(top_left),
        "topright": list(top_right),
        "bottomleft": list(bottom_left),
    }

    # A rotated image's bounding box comes from all four corners
    all_corners = [top_left, top_right, bottom_left, bottom_right]
    hmap.north = max(c[0] for c in all_corners)
    hmap.south = min(c[0] for c in all_corners)
    hmap.east = max(c[1] for c in all_corners)
    hmap.west = min(c[1] for c in all_corners)

    # 3 points always fit exactly (error 0 no matter how sloppy the clicks), so
    # accuracy can only be measured from the 4th point on; None means "unknown"
    hmap.rms_error = rms_error_meters(points, to_latlng) if len(points) > 3 else None
    hmap.is_georeferenced = True
    hmap.save()
    return hmap
