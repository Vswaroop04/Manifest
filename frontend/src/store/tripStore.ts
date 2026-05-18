import { create } from "zustand";

interface TripState {
  tripId: string | null;
  activeTab: "map" | "logs";
  selectedEventId: string | null;
  setTripId: (id: string | null) => void;
  setActiveTab: (tab: "map" | "logs") => void;
  setSelectedEventId: (id: string | null) => void;
  reset: () => void;
}

export const useTripStore = create<TripState>((set) => ({
  tripId: null,
  activeTab: "map",
  selectedEventId: null,
  setTripId: (id) => set({ tripId: id, activeTab: "map", selectedEventId: null }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setSelectedEventId: (id) => set({ selectedEventId: id }),
  reset: () => set({ tripId: null, activeTab: "map", selectedEventId: null }),
}));
