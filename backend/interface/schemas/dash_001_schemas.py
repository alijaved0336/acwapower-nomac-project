from drf_yasg import openapi

param_group = openapi.Parameter(
    "group",
    openapi.IN_QUERY,
    description="Group name",
    type=openapi.TYPE_STRING,
    required=True,
)

param_plant = openapi.Parameter(
    "plant",
    openapi.IN_QUERY,
    description="Plant name",
    type=openapi.TYPE_STRING,
    required=True,
)

param_cluster = openapi.Parameter(
    "cluster",
    openapi.IN_QUERY,
    description="Cluster name",
    type=openapi.TYPE_STRING,
    required=True,
)

groups_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "groups": openapi.Schema(
            type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
        )
    },
)

plants_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "plants": openapi.Schema(
            type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
        )
    },
)

clusters_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "clusters": openapi.Schema(
            type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
        )
    },
)

mapdata_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    description="Map coordinates and KPIs payload",
    properties={
        "coordinates": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "lat": openapi.Schema(type=openapi.TYPE_NUMBER),
                "lon": openapi.Schema(type=openapi.TYPE_NUMBER),
            },
        ),
        "kpis": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "production": openapi.Schema(type=openapi.TYPE_NUMBER),
                "efficiency": openapi.Schema(type=openapi.TYPE_NUMBER),
            },
        ),
    },
)

groups_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "groups": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_STRING),
            description="List of available groups",
        )
    },
)

plants_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "plants": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_STRING),
            description="List of plants in the cluster",
        )
    },
)

clusters_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "clusters": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_STRING),
            description="List of all clusters",
        )
    },
)

mapdata_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT, description="All plants with their KPIs and coordinates"
)

error_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message")
    },
)

legacy_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "energyPlants": openapi.Schema(
            type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
        ),
        "waterPlants": openapi.Schema(
            type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
        ),
        "plantKpiData": openapi.Schema(
            type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)
        ),
    },
)
