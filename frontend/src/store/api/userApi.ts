// api/userApi.ts
import { createApi } from "@reduxjs/toolkit/query/react";
import type { User } from "@/types/user";
import { baseQueryWithReauth } from "../services/baseQueryWithReauth";
import { ApiResponse } from "../../types/api.types";

export const userApi = createApi({
  reducerPath: "userApi",

  baseQuery: baseQueryWithReauth(),
  tagTypes: ["User"],
  endpoints: (builder) => ({
    // GET /api/users/
    getAllUsers: builder.query<User[], void>({
      query: () => ({ method: "GET", url: "/user/" }),
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: "User" as const, id })),
              { type: "User", id: "LIST" },
            ]
          : [{ type: "User", id: "LIST" }],
      transformResponse: (response: ApiResponse<User[]>) => response.data,
      transformErrorResponse: (response) => response,
    }),

    // GET /api/users/:id/
    getUserById: builder.query<User, string>({
      query: (id) => ({ method: "GET", url: `/${id}/` }),
      providesTags: (result, _error, id) => [{ type: "User", id }],
    }),

    // PUT /api/users/:id/
    updateUser: builder.mutation<User, Partial<User> & { id: string }>({
      query: ({ id, ...patch }) => ({
        url: `/${id}/`,
        method: "PUT",
        body: patch,
      }),
      invalidatesTags: (result, _error, { id }) => [{ type: "User", id }],
    }),

    // DELETE /api/users/:id/
    deleteUser: builder.mutation<{ success: boolean; id: string }, string>({
      query: (id) => ({
        url: `/${id}/`,
        method: "DELETE",
      }),
      invalidatesTags: (result, _error, id) => [
        { type: "User", id },
        { type: "User", id: "LIST" },
      ],
    }),
  }),
});

// Export hooks for usage in functional components
export const {
  useGetAllUsersQuery,
  useGetUserByIdQuery,
  useUpdateUserMutation,
  useDeleteUserMutation,
} = userApi;

export default userApi;
