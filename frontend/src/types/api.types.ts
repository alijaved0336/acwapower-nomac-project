import { BackendRole } from "./role.types";

// Base API response structure
export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
  success: boolean;
  status?: number;
}

// Standard API response structure with success, message, and data
export interface StandardApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data: T;
}

// Pagination

export interface PaginationFilter {
  page: number;
  limit: number;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export type PaginatedResponse<T> = ApiResponse<Paginated<T>>;

// Request configuration
export interface ApiRequestConfig {
  requiresAuth?: boolean;
  retries?: number;
  timeout?: number;
}

// Authentication types
export interface LoginRequest {
  email: string;
  password: string;
}

// Internal API authentication types
export interface InternalAuthRequest {
  name: string;
  email: string;
  sub: string;
  picture: string | null; // Always included, but can be null
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

// Generic CRUD operations
export interface CreateRequest<T> {
  data: Omit<T, "id" | "createdAt" | "updatedAt">;
}

export interface UpdateRequest<T> {
  id: string;
  data: Partial<Omit<T, "id" | "createdAt" | "updatedAt">>;
}

export interface DeleteRequest {
  id: string;
}

export interface ListRequest {
  page?: number;
  limit?: number;
  search?: string;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  filters?: Record<string, unknown>;
}

// ---- Types ----
export interface InternalAuthRequest {
  name: string;
  email: string;
  sub: string;
  picture: string | null;
}

export interface BackendUser {
  id: string;
  name: string;
  email: string;
  picture: string | null;
  sub: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  role_id: string | null;
  role: BackendRole | null;
}

export interface InternalAuthResponse {
  access_token: string;
  refresh_token: string;
  user: BackendUser;
}

export type AssignRoleForm = {
  userId: string;
  roleId: string;
};

export type DateFilter = {
  from_date: string;
  to_date: string;
};
