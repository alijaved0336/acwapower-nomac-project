"use client";

import { FC, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { TMapOverviewSelectFilters } from "../../../../../types/mapOverview.types";
import { Flex, theme } from "antd";
import { Tooltip } from "react-leaflet";

import { paddingToken } from "../../../../../styles/themes/tokens/padding";
import { sizeToken } from "../../../../../styles/themes/tokens/size";

import { waterIcon } from "@/constants/svg.constant";
import PlantCard from "./PlantCard";
import { useGetMapDataQuery } from "@/store/api/energyApi";
import { Cluster, Plant } from "../../../../../types/energy.types";
import {
  DndContext,
  DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";

import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import Spinner from "../../../../common/Spinner";
import { cn } from "../../../../../utils/cn";
import { parseAndRound } from "../../../../../utils/numberUtils";
import DraggableZoomControl from "../../../../common/maps/DraggableZoomControl";
import MapDroppable from "../../../../common/maps/MapDroppable";
import { useAppSelector } from "@/hooks";
import ChartSpinner from "../../../../common/ChartSpinner";

// Regional bounds to include both KSA and UAE
const REGIONAL_BOUNDS = L.latLngBounds(
  [16.0, 34.0], // Southwest corner (KSA southern border)
  [32.5, 60.0] // Northeast corner (extended east to include UAE)
);

// Initial positions for customZoomControl component (will be set to bottom-left after mount)
const INITIAL_POSITION = { x: 10, y: 10 };

// Tile layer URLs for different themes
const TILE_LAYERS = {
  light: {
    url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: "abcd" as const,
  },
  dark: {
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: "abcd" as const,
  },
} as const;

// Component to handle initial regional bounds on map load
const InitialRegionalBounds = () => {
  const map = useMap();

  useEffect(() => {
    map.fitBounds(REGIONAL_BOUNDS, {
      padding: [20, 20],
      animate: false, // No animation on initial load
    });
  }, [map]);

  return null;
};

const FitBoundsOnMarkers = ({
  coordinates,
}: {
  coordinates: [number, number][];
}) => {
  const map = useMap();

  useEffect(() => {
    // Always show full regional bounds regardless of plant coordinates
    // This ensures the map is always zoomed out to show the entire region (KSA + UAE)
    map.fitBounds(REGIONAL_BOUNDS, {
      padding: [20, 20],
      animate: true,
      duration: 1,
    });
  }, [coordinates, map]);

  return null;
};

const MapEventHandler = () => {
  useMapEvents({
    load: () => {},
    error: (e) => {
      console.error("Map error:", e);
    },
    tileload: () => {},
    tileerror: (e) => {
      console.error("Tile loading error:", e);
    },
  });
  return null;
};

type MapOverviewProps = {
  allClusters: Array<Cluster>;
  selectedFilters: TMapOverviewSelectFilters;
  selectedPlants: Array<Plant>;
  availablePlants: Array<Plant>;
  plantsLoading?: boolean;
  localPlantsLoading?: boolean;
  onFilterChange: (
    key: keyof TMapOverviewSelectFilters,
    value: TMapOverviewSelectFilters[keyof TMapOverviewSelectFilters]
  ) => void;
};

const MapOverview: FC<MapOverviewProps> = ({
  selectedPlants,
  plantsLoading = false,
  localPlantsLoading = false,
}) => {
  const { token } = theme.useToken();

  // Get theme mode from Redux
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";

  // Get map data to access plant_kpis
  const { data: mapData } = useGetMapDataQuery(undefined);

  const [zoomControlPos, setZoomControlPos] = useState(INITIAL_POSITION);
  const hasInitialized = useRef(false);
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 0.2,
      },
    })
  );

  // Set initial position to bottom-left after map container is available
  useEffect(() => {
    if (hasInitialized.current) return;

    const mapContainer = document.querySelector(".leaflet-container");
    if (!mapContainer) return;

    const COMPONENT_HEIGHT = 95;
    const LEFT_PADDING = 16;
    const BOTTOM_PADDING = 26;

    const mapHeight = mapContainer.clientHeight;
    if (mapHeight === 0) return;

    const bottomY = mapHeight - COMPONENT_HEIGHT - BOTTOM_PADDING;

    setZoomControlPos({
      x: LEFT_PADDING,
      y: bottomY,
    });
    hasInitialized.current = true;
  }, []);

  // Helper function to get KPI data for a plant
  const getPlantKpiData = useCallback(
    (plantType: string) => {
      if (!mapData?.plant_kpis) return null;

      const plantTypeToApiKey: Record<string, string> = {
        "Jubail Energy Plant": "Jubail Energy Plant",
        "Jubail 3A IWP": "Jubail Energy Plant",
        "Jubail-Jazlah": "Jubail Energy Plant",
        "Rabigh Energy Plant": "Rabigh Energy Plant",
        "Rabigh 3 IWP": "Rabigh Energy Plant",
        Rabigh3: "Rabigh Energy Plant",
        "STPC Energy Plant": "STPC Energy Plant",
        "Shuaibah 2 IWP (STPC)": "STPC Energy Plant",
        STPC: "STPC Energy Plant",
        "UAQ Energy Plant": "UAQ Energy Plant",
        "Umm Al Quwain IWP": "UAQ Energy Plant",
        UAQ: "UAQ Energy Plant",
      };

      const apiKey = plantTypeToApiKey[plantType] || plantType;

      const kpiData: { [key: string]: string } = {};
      mapData.plant_kpis.forEach((kpi) => {
        kpiData[kpi.kpi.toLowerCase()] =
          (kpi[apiKey as keyof typeof kpi] as string) || "N/A";
      });

      return kpiData;
    },
    [mapData?.plant_kpis]
  );

  const createEnergyIcon = () =>
    L.divIcon({
      html: waterIcon,
      className: "custom-div-icon",
      iconSize: [40, 40],
      iconAnchor: [20, 20],
    });

  const plantCoordinates = useMemo(() => {
    const coords =
      selectedPlants
        ?.map((plant, index) => {
          if (!plant.coordinates) {
            console.warn("MapOverview: Plant has no coordinates:", plant);
            return [0, 0] as [number, number];
          }

          let baseCoord: [number, number];

          if (Array.isArray(plant.coordinates)) {
            baseCoord = plant.coordinates;
          } else if (
            plant.coordinates.lat !== undefined &&
            plant.coordinates.lon !== undefined
          ) {
            baseCoord = [plant.coordinates.lat, plant.coordinates.lon];
          } else {
            console.warn(
              "MapOverview: Invalid coordinate structure:",
              plant.coordinates
            );
            return [0, 0] as [number, number];
          }

          const offsetLat = index * 0.001;
          const offsetLon = index * 0.001;
          const adjustedCoord: [number, number] = [
            baseCoord[0] + offsetLat,
            baseCoord[1] + offsetLon,
          ];
          return adjustedCoord;
        })
        .filter((coord) => coord[0] !== 0 || coord[1] !== 0) || [];
    return coords;
  }, [selectedPlants]);

  const markers = useMemo(() => {
    return selectedPlants
      ?.filter((plant) => plant.coordinates)
      .map((plant, index) => {
        let basePosition: [number, number];

        if (!plant.coordinates) {
          return null;
        }

        if (Array.isArray(plant.coordinates)) {
          basePosition = plant.coordinates;
        } else if (
          plant.coordinates.lat !== undefined &&
          plant.coordinates.lon !== undefined
        ) {
          basePosition = [plant.coordinates.lat, plant.coordinates.lon];
        } else {
          console.warn(
            "MapOverview: Skipping plant with invalid coordinates:",
            plant
          );
          return null;
        }

        const offsetLat = index * 0.001;
        const offsetLon = index * 0.001;
        const position: [number, number] = [
          basePosition[0] + offsetLat,
          basePosition[1] + offsetLon,
        ];

        const uniqueKey = `energy-${plant.plant_type || `${plant.id}-${plant.name}`}`;
        const kpiData = getPlantKpiData(plant?.plant_type || plant?.name || "");
        const clusterName =
          plant.plant_type === "Umm Al Quwain IWP" ||
          plant.name === "Umm Al Quwain IWP"
            ? "MEASA"
            : "KSA";

        return (
          <Marker key={uniqueKey} position={position} icon={createEnergyIcon()}>
            <Tooltip
              direction="top"
              offset={[0, -10]}
              opacity={1}
              className="plant-tooltip"
            >
              <div style={{ pointerEvents: "none" }}>
                <PlantCard
                  plantType={plant?.plant_type || plant?.name || ""}
                  production={parseAndRound(
                    kpiData?.production?.replace(/[^\d.]/g, "") || "0"
                  )}
                  sec={parseAndRound(kpiData?.sec || "3.01")}
                  availability={parseAndRound(
                    kpiData?.availability?.replace(/[^\d.]/g, "") || "0"
                  )}
                  quality={kpiData?.quality || "OK"}
                  dailyDispatch={kpiData?.["daily dispatch"] || "N/A"}
                  dailyDispatchPercentage={
                    kpiData?.["daily dispatch percentage"] || "0"
                  }
                  clusterName={clusterName}
                />
              </div>
            </Tooltip>
          </Marker>
        );
      });
  }, [selectedPlants, getPlantKpiData]);

  const isLoadingPlants = plantsLoading || localPlantsLoading;

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, delta } = event;

      if (active.id === "zoom-control") {
        const newX = zoomControlPos.x + delta.x;
        const newY = zoomControlPos.y + delta.y;

        const mapContainer = document.querySelector(".leaflet-container");
        if (!mapContainer) return;

        const mapWidth = mapContainer.clientWidth;
        const mapHeight = mapContainer.clientHeight;

        const COMPONENT_WIDTH = 100;
        const COMPONENT_HEIGHT = 95;
        const LEFT_PADDING = 16;
        const BOTTOM_PADDING = 8;
        const TOP_PADDING = 8;
        const RIGHT_PADDING = 16;

        const constrainedX = Math.max(
          LEFT_PADDING,
          Math.min(newX, mapWidth - COMPONENT_WIDTH - RIGHT_PADDING)
        );
        const constrainedY = Math.max(
          TOP_PADDING,
          Math.min(newY, mapHeight - COMPONENT_HEIGHT - BOTTOM_PADDING)
        );

        setZoomControlPos({
          x: constrainedX,
          y: constrainedY,
        });
      }
    },
    [zoomControlPos]
  );

  return (
    <DndContext onDragEnd={handleDragEnd} sensors={sensors}>
      <div
        style={{ width: "100%" }}
        className={cn("h-full", {
          "relative opacity-50": isLoadingPlants,
        })}
      >
        {isLoadingPlants && <ChartSpinner />}
        <MapContainer
          className="shadow-lg"
          center={[24.25, 47.0]}
          attributionControl={false}
          zoomControl={false}
          zoom={6}
          minZoom={5}
          maxZoom={18}
          worldCopyJump={false}
          scrollWheelZoom={true}
          maxBounds={REGIONAL_BOUNDS}
          maxBoundsViscosity={1.0}
          style={{
            height: "100%",
            width: "100%",
            zIndex: "0",
            borderRadius: sizeToken.sizeMS,
            border: `1px solid ${token.colorBorder}`,
          }}
        >
          {isDark ? (
            <TileLayer
              key="dark"
              attribution={TILE_LAYERS.dark.attribution}
              url={TILE_LAYERS.dark.url}
              subdomains={TILE_LAYERS.dark.subdomains}
              maxZoom={19}
              errorTileUrl="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
              crossOrigin=""
            />
          ) : (
            <TileLayer
              key="light"
              attribution={TILE_LAYERS.light.attribution}
              url={TILE_LAYERS.light.url}
              subdomains={TILE_LAYERS.light.subdomains}
              maxZoom={19}
              errorTileUrl="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
              crossOrigin=""
            />
          )}

          <InitialRegionalBounds />
          <MapEventHandler />
          <MapDroppable>
            <DraggableZoomControl
              position={zoomControlPos}
              bounds={REGIONAL_BOUNDS}
            />
          </MapDroppable>

          {markers}
          {/* {waterPlants.map((plant) => (
            <Marker
              key={`water-${plant.id}`}
              position={plant.coordinates}
              icon={createWaterIcon()}
            >
              <Popup minWidth={456} maxWidth={456}>
                <PlantCard
                  plantType="WATER"
                  production={100}
                  sec={100}
                  availability={100}
                  quality={"OK"}
                  dailyDispatch={"N/A"}
                  dailyDispatchPercentage={"0"}
                />
              </Popup>
            </Marker>
          ))} */}

          <FitBoundsOnMarkers coordinates={plantCoordinates ?? []} />
        </MapContainer>
      </div>
    </DndContext>
  );
};

export default MapOverview;
export type { MapOverviewProps };
