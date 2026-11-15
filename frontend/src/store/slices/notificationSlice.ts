import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export type NotificationSeverity = "success" | "error" | "warning" | "info";

export interface Notification {
  id: string;
  message: string;
  severity: NotificationSeverity;
  duration?: number;
  action?: {
    label: string;
    handler: () => void;
  };
  persistent?: boolean;
  timestamp: number;
}

export interface NotificationState {
  notifications: Notification[];
  maxNotifications: number;
}

const initialState: NotificationState = {
  notifications: [],
  maxNotifications: 5,
};

// Helper function to generate unique IDs
const generateId = (): string => {
  return `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

const notificationSlice = createSlice({
  name: "notifications",
  initialState,
  reducers: {
    addNotification: {
      reducer: (state, action: PayloadAction<Notification>) => {
        // Remove oldest notification if we've hit the limit
        if (state.notifications.length >= state.maxNotifications) {
          state.notifications.shift();
        }
        state.notifications.push(action.payload);
      },
      prepare: (notification: Omit<Notification, "id" | "timestamp">) => ({
        payload: {
          ...notification,
          id: generateId(),
          timestamp: Date.now(),
          duration:
            notification.duration ??
            (notification.severity === "error" ? 6000 : 4000),
        },
      }),
    },

    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(
        (notification) => notification.id !== action.payload
      );
    },

    clearAllNotifications: (state) => {
      state.notifications = [];
    },

    clearNotificationsBySeverity: (
      state,
      action: PayloadAction<NotificationSeverity>
    ) => {
      state.notifications = state.notifications.filter(
        (notification) => notification.severity !== action.payload
      );
    },

    updateNotification: (
      state,
      action: PayloadAction<{ id: string; updates: Partial<Notification> }>
    ) => {
      const { id, updates } = action.payload;
      const index = state.notifications.findIndex(
        (notification) => notification.id === id
      );
      if (index !== -1) {
        state.notifications[index] = {
          ...state.notifications[index],
          ...updates,
        };
      }
    },

    setMaxNotifications: (state, action: PayloadAction<number>) => {
      state.maxNotifications = Math.max(1, action.payload);
      // Trim notifications if new limit is lower
      if (state.notifications.length > state.maxNotifications) {
        state.notifications = state.notifications.slice(
          -state.maxNotifications
        );
      }
    },
  },
});

export const {
  addNotification,
  removeNotification,
  clearAllNotifications,
  clearNotificationsBySeverity,
  updateNotification,
  setMaxNotifications,
} = notificationSlice.actions;

export default notificationSlice;
