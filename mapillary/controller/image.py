"""
mapillary.controllers.image
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the image filtering and analysis business logic functionalities of the
Mapillary Python SDK.

For more information, please check out https://www.mapillary.com/developer/api-documentation/

:copyright: (c) 2021 Facebook
:license: MIT LICENSE
"""

# Configs
from config.api.entities import Entities
from config.api.vector_tiles import VectorTiles

# Exception Handling
from models.exceptions import InvalidImageResolution, InvalidImageKey
from controller.rules.verify import image_check, image_bbox_check, sequence_bbox_check

# Client
from models.client import Client

# Utils
from utils.format import geojson_to_feature_object, merged_features_list_to_geojson
from utils.filter import pipeline

# Library imports
import json
import mercantile
from requests import HTTPError
from vt2geojson.tools import vt_bytes_to_geojson


def get_image_close_to_controller(
    longitude: float,
    latitude: float,
    kwargs: dict,
) -> dict:
    """Extracting the GeoJSON for the image data near the [longitude, latitude] coordinates

    :param longitude: The longitude
    :type longitude: float

    :param latitude: The latitude
    :type latitude: float

    :param kwargs.min_date: The minimum date to filter till
    :type kwargs.min_date: str

    :param kwargs.max_date: The maximum date to filter upto
    :type kwargs.max_date: str

    :param kwargs.daterange: A list of a range to filter by
    :type kwargs.daterange: list

    :param kwargs.radius: The radius that the geometry points will lie in
    :type kwargs.radius: float

    :param kwargs.image_type: Either 'pano', 'flat' or 'all'
    :type kwargs.image_type: str

    :param kwargs.organization_id: The organization to retrieve the data for
    :type kwargs.organization_id: str

    :param kwargs.fields: Fields to pass to the endpoint
    :type kwargs.fields: list[str]

    :return: GeoJSON
    :rtype: dict
    """

    # TODO: Requirement# 2

    # Checking if a non valid key
    # has been passed to the function
    # If that is the case, throw an exception
    image_check(kwargs=kwargs)

    return {"Message": "Hello, World!"}


def get_image_looking_at_controller(
    coordinates_looker: tuple,
    coordinates_at: tuple,
    kwargs: dict,
) -> dict:
    """Extracting the GeoJSON for the image data from a 'looker' and 'at' coordinate view

    :param coordinates_looker: The tuple of coordinates of the position of the looking from
    coordinates, in the format (long, lat)
    :type longitude: tuple

    :param coordinates_at: The tuple of coordinates of the position of the looking at
    coordinates, in the format (long, lat)
    :type latitude: tuple

    :param kwargs.min_date: The minimum date to filter till
    :type kwargs.min_date: str

    :param kwargs.max_date: The maximum date to filter upto
    :type kwargs.max_date: str

    :param kwargs.daterange: A list of a range to filter by
    :type kwargs.daterange: list

    :param kwargs.radius: The radius that the geometry points will lie in
    :type kwargs.radius: float

    :param kwargs.image_type: Either 'pano', 'flat' or 'all'
    :type kwargs.image_type: str

    :param kwargs.organization_id: The organization to retrieve the data for
    :type kwargs.organization_id: str

    :param kwargs.fields: Fields to pass to the endpoint
    :type kwargs.fields: list[str]

    :return: GeoJSON
    :rtype: dict
    """

    # TODO: Requirement# 3

    # Checking if a non valid key
    # has been passed to  the function
    # If that is the case, throw an exception
    image_check(kwargs=kwargs)

    return {"Message": "Hello, World!"}


def get_image_thumbnail_controller(image_id, resolution: int) -> str:
    """This controller holds the business logic for retrieving
    an image thumbnail with a specific resolution (256, 1024, or 2048)
    using an image ID/key

    :param image_id: Image key as the argument

    :param resolution: Option for the thumbnail size, with available resolutions:
    256, 1024, and 2048

    :return: A URL for the thumbnail
    :rtype: str
    """

    # check if the entered resolution is one of the supported image sizes
    if resolution not in [256, 1024, 2048]:
        raise InvalidImageResolution(resolution)

    try:
        res = Client().get(Entities.get_image(image_id, [f"thumb_{resolution}_url"]))
    except HTTPError:
        # If given ID is an invalid image ID, let the user know
        raise InvalidImageKey(image_id)

    thumbnail = json.loads(res.content.decode("utf-8"))[f"thumb_{resolution}_url"]

    return thumbnail


def get_images_in_bbox_controller(
    bbox: dict, layer: str, zoom: int, filters: dict
) -> str:
    """For getting a complete list of images that lie within a bounding box,
     that can be filered via the filters argument

    :param bbox: A bounding box representation
    example: {
        'west': 'BOUNDARY_FROM_WEST',
        'south': 'BOUNDARY_FROM_SOUTH',
        'east': 'BOUNDARY_FROM_EAST',
        'north': 'BOUNDARY_FROM_NORTH'
    }
    :type bbox: dict

    :param filters.max_date: The max date that can be filtered upto
    :type filters.max_date: str

    :param filters.min_date: The min date that can be filtered from
    :type filters.min_date: str

    :param filters.image_type: Either 'pano', 'flat' or 'all'
    :type filters.image_type: str

    :param filters.compass_angle:
    :type filters.compass_angle: float

    :param filters.organization_id:
    :type filters.organization_id: int

    :param filters.sequence_id:
    :type filters.sequence_id: str

    '''
    :raise InvalidKwargError: Raised when a function is called with the invalid keyword argument(s)
    that do not belong to the requested API end call
    '''

    :return: GeoJSON
    :rtype: str
    """

    # Check if the given filters are valid ones
    filters["zoom"] = filters.get("zoom", zoom)
    filters = image_bbox_check(filters) if layer == "image" else sequence_bbox_check(filters)

    # Instantiate the Client
    client = Client()

    # filtered images or sequence data will be appended to this list
    filtered_results = []

    # A list of tiles that are either confined within or intersect with the bbox
    tiles = list(
        mercantile.tiles(
            east=bbox["east"],
            south=bbox["south"],
            west=bbox["west"],
            north=bbox["north"],
            zooms=zoom,
        )
    )

    for tile in tiles:
        url = (
            VectorTiles.get_image_layer(x=tile.x, y=tile.y, z=tile.z)
            if layer == "image"
            else VectorTiles.get_sequence_layer(x=tile.x, y=tile.y, z=tile.z)
        )

        # Get the response from the API
        res = client.get(url)
        # If the response is not valid, raise an exception
        res.raise_for_status()

        # Get the GeoJSON response by decoding the byte tile
        geojson = vt_bytes_to_geojson(
            b_content=res.content, layer=layer, z=tile.z, x=tile.x, y=tile.y
        )

        # Separating feature objects from the decoded data
        unfiltered_results = geojson_to_feature_object(geojson)

        # Filter the unfiltered results by the given filters
        filtered_results.extend(pipeline(
            data=unfiltered_results,
            components=[
                {"filter": "features_in_bounding_box", "bbox": bbox}
                if layer == "image"
                else {},
                {'filter': 'max_date', 'max_timestamp': filters.get("max_date")}
                if filters['max_date'] is not None
                else {},
                {'filter': 'min_date', 'min_timestamp': filters.get("min_date")}
                if filters['min_date'] is not None
                else {},
                {'filter': 'image_type', 'type': filters.get("image_type")}
                if filters['image_type'] is not None or filters['image_type'] != "all"
                else {},
                {'filter': 'organization_id', 'organization_ids': filters.get("organization_id")}
                if filters['organization_id'] is not None
                else {},
                {'filter': 'sequence_id', 'ids': filters.get("sequence_id")}
                if layer == "image" and filters['sequence_id'] is not None
                else {},
                {'filter': 'compass_angle', 'angles': filters.get("compass_angle")}
                if layer == "image" and filters['compass_angle'] is not None 
                else {},
            ]
        ))

    return merged_features_list_to_geojson(filtered_results)


def get_images_in_shape_controller(
    data: dict, is_geojson: bool = True, kwargs: dict = None
) -> dict:
    """For extracting images that lie within a shape, either GeoJSON or a Bounding Box, and merges
    the results of the found GeoJSON(s) into a single object - by merging all the features into
    one list in a feature collection.

    A bounding box is in the list order of ([east, south, west, north])

    :param data: GeoJSON | Bounding Box (Bbox)
    :type data: dict | list

    :param is_geojson: True if GeoJSON object will be passed, else False if Bbox, defaults to True
    :type is_geojson: bool

    :param kwargs.max_date: The max date that can be filtered upto
    :type kwargs.max_date: str

    :param kwargs.min_date: The min date that can be filtered from
    :type kwargs.min_date: str

    :param kwargs.is_pano: Either 'pano', 'flat' or 'all'
    :type kwargs.is_pano: str

    '''
    :raise InvalidKwargError: Raised when a function is called with the invalid keyword argument(s)
    that do not belong to the requested API end call
    '''

    :return: GeoJSON
    :rtype: dict
    """

    # TODO: Requirement# 9

    image_bbox_check(kwargs)

    return {"Message": "Hello, World!"}
