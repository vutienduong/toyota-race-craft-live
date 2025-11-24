"use client";

import React, { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

// Barber Motorsports Park coordinates
const BARBER_TRACK = {
  center: [-86.4625, 33.5419] as [number, number],
  zoom: 15.5,
  // Track outline (approximate GPS coordinates)
  coordinates: [
    [-86.4640, 33.5430],
    [-86.4635, 33.5425],
    [-86.4630, 33.5418],
    [-86.4625, 33.5410],
    [-86.4620, 33.5405],
    [-86.4615, 33.5408],
    [-86.4610, 33.5415],
    [-86.4615, 33.5422],
    [-86.4620, 33.5428],
    [-86.4628, 33.5432],
    [-86.4635, 33.5433],
    [-86.4640, 33.5430],
  ],
};

interface VehiclePosition {
  vehicleId: string;
  lat: number;
  lon: number;
  speed: number;
  heading: number;
  position: number;
  lapDistance: number;
}

interface TrackMapProps {
  vehicles?: VehiclePosition[];
  focusedVehicle?: string;
  showRacingLine?: boolean;
}

export function TrackMap({
  vehicles = [],
  focusedVehicle,
  showRacingLine = true,
}: TrackMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markers = useRef<{ [key: string]: mapboxgl.Marker }>({});
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Note: In production, use actual Mapbox token from environment variable
    // For demo purposes, we'll create a basic map
    mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "";

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: BARBER_TRACK.center,
      zoom: BARBER_TRACK.zoom,
      pitch: 45, // 3D view
      bearing: 0,
    });

    map.current.on("load", () => {
      if (!map.current) return;

      // Add track outline
      map.current.addSource("track", {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: {
            type: "LineString",
            coordinates: BARBER_TRACK.coordinates,
          },
        },
      });

      map.current.addLayer({
        id: "track-outline",
        type: "line",
        source: "track",
        paint: {
          "line-color": "#ffffff",
          "line-width": 8,
          "line-opacity": 0.8,
        },
      });

      map.current.addLayer({
        id: "track-center",
        type: "line",
        source: "track",
        paint: {
          "line-color": "#3b82f6",
          "line-width": 3,
          "line-opacity": 0.6,
        },
      });

      // Add racing line if enabled
      if (showRacingLine) {
        map.current.addLayer({
          id: "racing-line",
          type: "line",
          source: "track",
          paint: {
            "line-color": "#22c55e",
            "line-width": 2,
            "line-dasharray": [2, 2],
            "line-opacity": 0.5,
          },
        });
      }

      setMapLoaded(true);
    });

    // Cleanup
    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, [showRacingLine]);

  // Update vehicle markers
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    // Remove old markers
    Object.keys(markers.current).forEach((id) => {
      if (!vehicles.find((v) => v.vehicleId === id)) {
        markers.current[id].remove();
        delete markers.current[id];
      }
    });

    // Add/update vehicle markers
    vehicles.forEach((vehicle) => {
      const isFocused = vehicle.vehicleId === focusedVehicle;

      if (!markers.current[vehicle.vehicleId]) {
        // Create new marker
        const el = document.createElement("div");
        el.className = "vehicle-marker";
        el.style.width = isFocused ? "20px" : "14px";
        el.style.height = isFocused ? "20px" : "14px";
        el.style.borderRadius = "50%";
        el.style.backgroundColor = isFocused ? "#3b82f6" : "#6b7280";
        el.style.border = isFocused ? "3px solid #ffffff" : "2px solid #ffffff";
        el.style.boxShadow = "0 2px 4px rgba(0,0,0,0.3)";
        el.style.transform = `rotate(${vehicle.heading}deg)`;
        el.style.transition = "all 0.3s ease";

        // Add position label
        const label = document.createElement("div");
        label.className = "vehicle-label";
        label.textContent = `P${vehicle.position}`;
        label.style.position = "absolute";
        label.style.top = "-20px";
        label.style.left = "50%";
        label.style.transform = "translateX(-50%)";
        label.style.color = "#ffffff";
        label.style.fontSize = "10px";
        label.style.fontWeight = "bold";
        label.style.textShadow = "0 1px 2px rgba(0,0,0,0.8)";
        el.appendChild(label);

        const marker = new mapboxgl.Marker(el)
          .setLngLat([vehicle.lon, vehicle.lat])
          .setPopup(
            new mapboxgl.Popup({ offset: 25 }).setHTML(
              `
              <div style="color: #000; padding: 4px;">
                <strong>${vehicle.vehicleId}</strong><br/>
                Position: P${vehicle.position}<br/>
                Speed: ${Math.round(vehicle.speed)} km/h<br/>
                Distance: ${Math.round(vehicle.lapDistance)}m
              </div>
              `
            )
          )
          .addTo(map.current!);

        markers.current[vehicle.vehicleId] = marker;
      } else {
        // Update existing marker
        markers.current[vehicle.vehicleId].setLngLat([vehicle.lon, vehicle.lat]);

        const el = markers.current[vehicle.vehicleId].getElement();
        el.style.width = isFocused ? "20px" : "14px";
        el.style.height = isFocused ? "14px" : "14px";
        el.style.backgroundColor = isFocused ? "#3b82f6" : "#6b7280";
        el.style.border = isFocused ? "3px solid #ffffff" : "2px solid #ffffff";
        el.style.transform = `rotate(${vehicle.heading}deg)`;

        const label = el.querySelector(".vehicle-label") as HTMLDivElement;
        if (label) {
          label.textContent = `P${vehicle.position}`;
        }
      }
    });

    // Center on focused vehicle
    if (focusedVehicle && map.current) {
      const vehicle = vehicles.find((v) => v.vehicleId === focusedVehicle);
      if (vehicle) {
        map.current.easeTo({
          center: [vehicle.lon, vehicle.lat],
          zoom: 16,
          duration: 1000,
        });
      }
    }
  }, [vehicles, focusedVehicle, mapLoaded]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="absolute inset-0 rounded-lg overflow-hidden" />

      {/* Map controls overlay */}
      <div className="absolute top-4 right-4 bg-background/80 backdrop-blur-sm rounded-lg p-3 space-y-2">
        <div className="text-xs font-semibold">Track: Barber</div>
        <div className="flex items-center gap-2 text-xs">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <span>Your Position</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <div className="w-3 h-3 rounded-full bg-gray-500"></div>
          <span>Rivals</span>
        </div>
        {showRacingLine && (
          <div className="flex items-center gap-2 text-xs">
            <div className="w-8 h-0.5 bg-green-500 opacity-50"></div>
            <span>Racing Line</span>
          </div>
        )}
      </div>

      {/* Vehicle count */}
      <div className="absolute bottom-4 left-4 bg-background/80 backdrop-blur-sm rounded-lg px-3 py-2 text-sm">
        {vehicles.length} {vehicles.length === 1 ? "Vehicle" : "Vehicles"} on Track
      </div>
    </div>
  );
}
